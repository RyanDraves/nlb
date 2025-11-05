import logging
import pathlib

from nlb.buffham import parser
from nlb.buffham import schema_bh

T = ' ' * 4  # Indentation


TYPE_MAP = {
    schema_bh.FieldType.UINT8_T: 'int',
    schema_bh.FieldType.UINT16_T: 'int',
    schema_bh.FieldType.UINT32_T: 'int',
    schema_bh.FieldType.UINT64_T: 'int',
    schema_bh.FieldType.INT8_T: 'int',
    schema_bh.FieldType.INT16_T: 'int',
    schema_bh.FieldType.INT32_T: 'int',
    schema_bh.FieldType.INT64_T: 'int',
    schema_bh.FieldType.FLOAT32: 'float',
    schema_bh.FieldType.FLOAT64: 'float',
    schema_bh.FieldType.STRING: 'str',
    schema_bh.FieldType.BYTES: 'bytes',
}


def _get_imported_name(relative_name: str) -> str:
    """Get the imported name from a relative name.

    Examples:
    - 'nlb.buffham.constants.foo' -> 'constants_bh.foo'
    - 'foo' -> 'foo'
    """
    if '.' in relative_name:
        namespace, name = relative_name.rsplit('.', 1)
        module = namespace.rsplit('.', 1)[-1] + '_bh'
        return f'{module}.{name}'
    return relative_name


def _py_type(field: parser.Field, primary_namespace: str) -> str:
    """Get the Python type hint for the field."""
    if field.obj_name is not None:
        type_str = _get_imported_name(
            parser.relative_name(field.obj_name, primary_namespace)
        )
    elif field.pri_type is schema_bh.FieldType.LIST:
        assert field.sub_type is not None
        type_str = f'list[{TYPE_MAP[field.sub_type]}]'
    else:
        type_str = TYPE_MAP[field.pri_type]

    if field.optional:
        type_str += ' | None'

    return type_str


def _get_constant_name(reference: str) -> str:
    """Get the constant name from a full name.

    Assumes local constants are already trimmed of their namespace.

    Examples:
    - 'nlb.buffham.constants.foo' -> 'constants_bh.FOO'
    - 'foo' -> 'FOO'
    """
    if '.' in reference:
        split = reference.rsplit('.', 2)
        split[-2] = split[-2] + '_bh'
        split[-1] = split[-1].upper()
        return '.'.join(split[-2:])
    return reference.upper()


def generate_constant(constant: parser.Constant) -> str:
    """Generate a Python constant definition from a Constant."""
    definition = ''

    if constant.comments:
        for comment in constant.comments:
            definition += f'#{comment}\n'
    references = {ref: _get_constant_name(ref) for ref in constant.references}
    value = constant.value
    for ref, name in references.items():
        value = value.replace(f'{{{ref}}}', name)
    if constant.type is schema_bh.FieldType.STRING:
        value = f"'{value}'"
    definition += f'{constant.name.upper()} = {value}'

    if constant.inline_comment:
        definition += f'  #{constant.inline_comment}'

    definition += '\n'

    return definition


def generate_enum(enum: parser.Enum) -> str:
    """Generate a Python enum definition from an Enum."""
    definition = '\n'

    if enum.comments:
        for comment in enum.comments:
            definition += f'#{comment}\n'
    definition += f'class {enum.name}(enum.Enum):\n'

    for field in enum.fields:
        if field.comments:
            for comment in field.comments:
                definition += f'{T}#{comment}\n'
        definition += f'{T}{field.name} = {field.value}'
        if field.inline_comment:
            definition += f'  #{field.inline_comment}'
        definition += '\n'

    definition += '\n'

    return definition


def _generate_serializer(
    message: parser.Message,
    num_optional_fields: int,
    num_optional_bytes: int,
    definition: str,
) -> str:
    definition += f'\n{T}{T}buffer = bytes()'

    # Compute optional bitfield
    if num_optional_fields > 0:
        definition += f'\n{T}{T}optional_bitfield = 0'
        optional_idx = 0
        for field in message.fields:
            if not field.optional:
                continue
            definition += f'\n{T}{T}optional_bitfield |= (1 << {optional_idx}) if self.{field.name} is not None else 0'
            optional_idx += 1
        definition += f"\n{T}{T}buffer += optional_bitfield.to_bytes(length={num_optional_bytes}, byteorder='little', signed=False)"

    for field in message.fields:
        if field.iterable:
            definition += f"\n{T}{T}buffer += struct.pack('<H', len(self.{field.name}))"
            if field.pri_type is schema_bh.FieldType.LIST:
                definition += f"\n{T}{T}buffer += struct.pack(f'<{{len(self.{field.name})}}{field.format}', *self.{field.name})"
            else:
                definition += f'\n{T}{T}buffer += self.{field.name}'
                if field.pri_type is schema_bh.FieldType.STRING:
                    definition += '.encode()'
        elif field.pri_type is schema_bh.FieldType.MESSAGE:
            definition += f'\n{T}{T}buffer += self.{field.name}.serialize()'
        elif field.pri_type is schema_bh.FieldType.ENUM:
            definition += f"\n{T}{T}buffer += struct.pack('<{field.format}', self.{field.name}.value)"
        else:
            definition += (
                f"\n{T}{T}buffer += struct.pack('<{field.format}', self.{field.name})"
            )

        # Conditionally serialize optional fields
        if field.optional:
            definition += f' if self.{field.name} is not None else bytes()'

    definition += f'\n{T}{T}return buffer\n'

    return definition


def _generate_deserializer(
    message: parser.Message,
    num_optional_fields: int,
    num_optional_bytes: int,
    primary_namespace: str,
    definition: str,
) -> str:
    if num_optional_fields > 0:
        definition += f"\n{T}{T}optional_bitfield = int.from_bytes(buffer[:{num_optional_bytes}], byteorder='little', signed=False)"

    offset = num_optional_bytes
    offset_str = ''

    optional_idx = 0
    for field in message.fields:
        if field.pri_type is schema_bh.FieldType.LIST:
            definition += f"\n{T}{T}{field.name}_size = struct.unpack_from('<H', buffer, {offset}{offset_str})[0]"
            offset += 2
            definition += f"\n{T}{T}{field.name} = list(struct.unpack_from(f'<{{{field.name}_size}}{field.format}', buffer, {offset}{offset_str}))"
            offset_str += f' + {field.name}_size * {field.size}'
        elif field.pri_type in (
            schema_bh.FieldType.STRING,
            schema_bh.FieldType.BYTES,
        ):
            definition += f"\n{T}{T}{field.name}_size = struct.unpack_from('<H', buffer, {offset}{offset_str})[0]"
            if field.optional:
                definition += f' if optional_bitfield & (1 << {optional_idx}) else 0'
                offset_str += f' + 2 * ({field.name} is not None)'
            else:
                offset += 2
            definition += f'\n{T}{T}{field.name} = buffer[{offset}{offset_str}:{offset}{offset_str} + {field.name}_size]'
            if field.pri_type is schema_bh.FieldType.STRING:
                definition += '.decode()'
            offset_str += f' + {field.name}_size * {field.size}'
        elif field.pri_type is schema_bh.FieldType.MESSAGE:
            msg = _py_type(field, primary_namespace)
            definition += f'\n{T}{T}{field.name}, {field.name}_size = {msg}.deserialize(buffer[{offset}{offset_str}:])'
            if field.optional:
                definition += (
                    f' if optional_bitfield & (1 << {optional_idx}) else (None, 0)'
                )
            offset_str += f' + {field.name}_size'
        elif field.pri_type is schema_bh.FieldType.ENUM:
            enum_type = _py_type(field, primary_namespace)
            definition += f"\n{T}{T}{field.name} = {enum_type}(struct.unpack_from('<{field.format}', buffer, {offset}{offset_str})[0])"
            if field.optional:
                definition += f' if optional_bitfield & (1 << {optional_idx}) else None'
                offset_str += f' + {field.size} * ({field.name} is not None)'
            else:
                offset += field.size
        else:
            definition += f"\n{T}{T}{field.name} = struct.unpack_from('<{field.format}', buffer, {offset}{offset_str})[0]"
            if field.optional:
                definition += f' if optional_bitfield & (1 << {optional_idx}) else None'
                offset_str += f' + {field.size} * ({field.name} is not None)'
            else:
                offset += field.size

        if field.optional:
            optional_idx += 1

    definition += f'\n{T}{T}return cls('
    for field in message.fields:
        definition += f'\n{T}{T}{T}{field.name}={field.name},'
    definition += f'\n{T}{T}), {offset}{offset_str}\n'

    return definition


def generate_message(
    message: parser.Message, stub: bool, primary_namespace: str
) -> str:
    """Generate a Python dataclass definition from a Message."""

    definition = ('\n@dataclasses.dataclass\nclass {name}:').format(name=message.name)

    # Create a docstring
    if message.comments:
        definition += f'\n{T}"""{message.comments[0].lstrip()}'
        for comment in message.comments[1:]:
            if comment:
                definition += f'\n{T}{comment.lstrip()}'
            else:
                definition += '\n'
        if len(message.comments) > 1:
            definition += f'\n{T}'
        definition += '"""\n'

    # Define fields
    for field in message.fields:
        if field.comments:
            for comment in field.comments:
                definition += f'\n{T}#{comment}'
        definition += f'\n{T}{field.name}: {_py_type(field, primary_namespace)}'
        if field.inline_comment:
            definition += f'  #{field.inline_comment}'

    num_optional_fields = sum(1 for f in message.fields if f.optional)
    num_optional_bytes = (num_optional_fields + 7) // 8

    # Add serializer method
    definition += f'\n\n{T}def serialize(self) -> bytes:'
    if stub:
        definition += ' ...\n'
    else:
        definition = _generate_serializer(
            message, num_optional_fields, num_optional_bytes, definition
        )

    # Add deserializer method
    if not stub:
        definition += '\n'
    definition += f'{T}@classmethod'
    definition += f'\n{T}def deserialize(cls, buffer: bytes) -> tuple[Self, int]:'
    if stub:
        definition += ' ...\n'
    else:
        definition = _generate_deserializer(
            message,
            num_optional_fields,
            num_optional_bytes,
            primary_namespace,
            definition,
        )

    return definition


def generate_registry(
    transactions: list[parser.Transaction],
    publishes: list[parser.Publish],
    primary_namespace: str,
    stub: bool,
) -> str:
    """Generate a registry for transactions."""

    definition = '\nREGISTRY: dict[int, Type[bh.BuffhamLike]]'

    if stub:
        definition += ' = ...\n\n'
    else:
        definition += ' = {\n'
        for transaction in transactions:
            definition += f'{T}{transaction.request_id}: {_get_imported_name(parser.relative_name(transaction.send_name, primary_namespace))},\n'
        for publish in publishes:
            definition += f'{T}{publish.request_id}: {_get_imported_name(parser.relative_name(publish.send_name, primary_namespace))},\n'
        definition += '}\n\n'

    return definition


def generate_serializer(
    name: str, ctx: parser.Parser, primary_namespace: str, stub: bool
) -> str:
    """Generate a serializer with a defined registry for transactions."""

    definition = (
        f'class {name}Serializer(bh_cobs.BhCobs):\n'
        f'{T}def __init__(self, registry: bh_cobs.Registry | None = None):'
    )

    if stub:
        definition += ' ...\n\n'
    else:
        definition += f'\n{T}{T}registry = (registry or {{}}) | REGISTRY'

        if len(ctx.buffhams) == 1:
            definition += '\n'
        else:
            for bh in ctx.buffhams.values():
                if bh.namespace == primary_namespace:
                    continue
                definition += f' | {bh.name}_bh.REGISTRY'
            definition += '\n'

        definition += f'{T}{T}super().__init__(registry)\n\n'

    return definition


def generate_node(name: str, stub: bool) -> str:
    """Generate a node that uses the serializer with defined transactions."""

    definition = (
        f'class {name}Node[\n'
        f'{T}CommsTransporter: transporter.TransporterLike,\n'
        f'{T}LogTransporter: transporter.TransporterLike,\n'
        f'](bh.BhNode[{name}Serializer, CommsTransporter, LogTransporter]):\n'
        f'{T}def __init__(\n'
        f'{T}{T}self,\n'
        f'{T}{T}serializer: {name}Serializer | None = None,\n'
        f'{T}{T}comms_transporter: CommsTransporter | None = None,\n'
        f'{T}{T}log_transporter: LogTransporter | None = None,\n'
        f'{T}):'
    )

    if stub:
        definition += ' ...\n\n'
    else:
        definition += (
            f'\n'
            f'{T}{T}super().__init__(serializer or {name}Serializer(), comms_transporter, log_transporter)\n\n'
        )

    return definition


def generate_transaction(
    transaction: parser.Transaction, stub: bool, primary_namespace: str
) -> str:
    """Generate a transaction definition."""

    definition = ''
    if transaction.comments:
        for comment in transaction.comments:
            definition += f'#{comment}\n'
    if stub:
        definition += (
            f'{transaction.name.upper()}: bh.Transaction['
            f'{_get_imported_name(parser.relative_name(transaction.receive_name, primary_namespace))}, '
            f'{_get_imported_name(parser.relative_name(transaction.send_name, primary_namespace))}'
            f'] = ...'
        )
        if transaction.inline_comment:
            definition += f'  #{transaction.inline_comment}'
        definition += '\n'
    else:
        definition += (
            f'{transaction.name.upper()} = bh.Transaction['
            f'{_get_imported_name(parser.relative_name(transaction.receive_name, primary_namespace))}, '
            f'{_get_imported_name(parser.relative_name(transaction.send_name, primary_namespace))}'
            f']({transaction.request_id})'
        )
        if transaction.inline_comment:
            definition += f'  #{transaction.inline_comment}'
        definition += '\n'

    return definition


def generate_publishes(publishes: list[parser.Publish]) -> str:
    definition = ''

    if not publishes:
        return definition

    definition += '\nclass PublishIds(enum.Enum):\n'

    for publish in publishes:
        for comment in publish.comments:
            definition += f'{T}#{comment}\n'

        definition += f'{T}{publish.name.upper()} = {publish.request_id}'
        if publish.inline_comment:
            definition += f'  #{publish.inline_comment}'
        definition += '\n'

    return definition


def generate_python(
    ctx: parser.Parser, primary_namespace: str, outfile: pathlib.Path, stub: bool
) -> None:
    bh = ctx.buffhams[primary_namespace]

    with outfile.open('w') as fp:
        fp.write('# @generated by Buffham')

        sys_imports: list[str] = []
        if len(bh.messages):
            # Add imports
            sys_imports.append('import dataclasses')
            if len(bh.publishes) or len(bh.enums):
                sys_imports.append('import enum')
            if not stub:
                sys_imports.append('import struct')
            import_type = ', Type' if len(bh.transactions) or len(bh.publishes) else ''
            sys_imports.append(f'from typing import Self{import_type}')
        if len(bh.enums):
            if 'import enum' not in sys_imports:
                sys_imports.append('import enum')
        if sys_imports:
            fp.write('\n')
            for imp in sys_imports:
                fp.write(f'{imp}\n')

        if len(bh.transactions):
            # Add imports
            fp.write(
                '\nfrom emb.network.serialize import bh_cobs\n'
                'from emb.network.transport import transporter\n'
                'from nlb.buffham import bh\n'
            )

        if len(ctx.buffhams) > 1:
            fp.write('\n')
            # Add imports
            for namespace in ctx.buffhams:
                if namespace == primary_namespace:
                    continue
                package, module = namespace.rsplit('.', 1)
                fp.write(f'from {package} import {module}_bh\n')

        # Generate constant definitions
        if bh.constants:
            fp.write('\n')
        for constant in bh.constants:
            fp.write(generate_constant(constant))

        # Generate enum definitions
        for enum in bh.enums:
            fp.write(generate_enum(enum))

        # Generate message definitions
        for message in bh.messages:
            fp.write(generate_message(message, stub, primary_namespace))

        # Generate registry
        if len(bh.transactions) or len(bh.publishes):
            fp.write(
                generate_registry(
                    bh.transactions, bh.publishes, primary_namespace, stub
                )
            )

        # Generate transaction definitions
        if len(bh.transactions):
            fp.write(generate_serializer(bh.name.title(), ctx, primary_namespace, stub))
            fp.write(generate_node(bh.name.title(), stub))
        for transaction in bh.transactions:
            fp.write(generate_transaction(transaction, stub, primary_namespace))

        # Generate publish definitions
        fp.write(generate_publishes(bh.publishes))

    logging.debug(f'{stub=}')
    logging.debug(outfile.read_text())
