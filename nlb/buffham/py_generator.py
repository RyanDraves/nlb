import logging
import pathlib

from nlb.buffham import parser

T = ' ' * 4  # Indentation


TYPE_MAP = {
    parser.FieldType.UINT8_T: 'int',
    parser.FieldType.UINT16_T: 'int',
    parser.FieldType.UINT32_T: 'int',
    parser.FieldType.UINT64_T: 'int',
    parser.FieldType.INT8_T: 'int',
    parser.FieldType.INT16_T: 'int',
    parser.FieldType.INT32_T: 'int',
    parser.FieldType.INT64_T: 'int',
    parser.FieldType.FLOAT32: 'float',
    parser.FieldType.FLOAT64: 'float',
    parser.FieldType.STRING: 'str',
    parser.FieldType.BYTES: 'bytes',
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
    if field.message:
        return _get_imported_name(field.message.get_relative_name(primary_namespace))

    if field.pri_type is parser.FieldType.LIST:
        assert field.sub_type is not None
        return f'list[{TYPE_MAP[field.sub_type]}]'

    return TYPE_MAP[field.pri_type]


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
    if constant.type is parser.FieldType.STRING:
        value = f"'{value}'"
    definition += f'{constant.name.upper()} = {value}'

    if constant.inline_comment:
        definition += f'  #{constant.inline_comment}'

    definition += '\n'

    return definition


def generate_message(
    message: parser.Message, stub: bool, primary_namespace: str
) -> str:
    """Generate a Python dataclass definition from a Message."""

    definition = ('@dataclasses.dataclass\n' 'class {name}:').format(name=message.name)

    if message.comments:
        # Create a docstring
        definition += f'\n{T}"""{message.comments[0].lstrip()}'
        for comment in message.comments[1:]:
            if comment:
                definition += f'\n{T}{comment.lstrip()}'
            else:
                definition += f'\n'
        definition += f'\n{T}"""\n'

    for field in message.fields:
        if field.comments:
            for comment in field.comments:
                definition += f'\n{T}#{comment}'
        definition += f'\n{T}{field.name}: {_py_type(field, primary_namespace)}'
        if field.inline_comment:
            definition += f'  #{field.inline_comment}'

    # Add serializer method
    definition += f'\n\n{T}def serialize(self) -> bytes:'
    if stub:
        definition += ' ...\n'
    else:
        definition += f'\n{T}{T}buffer = bytes()'
        for field in message.fields:
            if field.iterable:
                definition += (
                    f"\n{T}{T}buffer += struct.pack('<H', len(self.{field.name}))"
                )
                if field.pri_type is parser.FieldType.LIST:
                    definition += f"\n{T}{T}buffer += struct.pack(f'<{{len(self.{field.name})}}{field.format}', *self.{field.name})"
                else:
                    definition += f'\n{T}{T}buffer += self.{field.name}'
                    if field.pri_type is parser.FieldType.STRING:
                        definition += f".encode()"
            elif field.pri_type is parser.FieldType.MESSAGE:
                definition += f'\n{T}{T}buffer += self.{field.name}.serialize()'
            else:
                definition += f"\n{T}{T}buffer += struct.pack('<{field.format}', self.{field.name})"
        definition += f'\n{T}{T}return buffer\n'

    # Add deserializer method
    definition += f'\n{T}@classmethod'
    definition += f'\n{T}def deserialize(cls, buffer: bytes) -> tuple[Self, int]:'
    if stub:
        definition += ' ...\n'
    else:
        offset = 0
        offset_str = ''
        for field in message.fields:
            if field.pri_type is parser.FieldType.LIST:
                definition += f"\n{T}{T}{field.name}_size = struct.unpack_from('<H', buffer, {offset}{offset_str})[0]"
                offset += 2
                definition += f"\n{T}{T}{field.name} = list(struct.unpack_from(f'<{{{field.name}_size}}{field.format}', buffer, {offset}{offset_str}))"
                offset_str += f' + {field.name}_size * {field.size}'
            elif field.pri_type in (parser.FieldType.STRING, parser.FieldType.BYTES):
                definition += f"\n{T}{T}{field.name}_size = struct.unpack_from('<H', buffer, {offset}{offset_str})[0]"
                offset += 2
                definition += f"\n{T}{T}{field.name} = buffer[{offset}{offset_str}:{offset}{offset_str} + {field.name}_size]"
                if field.pri_type is parser.FieldType.STRING:
                    definition += f".decode()"
                offset_str += f' + {field.name}_size * {field.size}'
            elif field.pri_type is parser.FieldType.MESSAGE:
                assert field.message is not None
                definition += f'\n{T}{T}{field.name}, {field.name}_size = {_get_imported_name(field.message.get_relative_name(primary_namespace))}.deserialize(buffer[{offset}{offset_str}:])'
                offset_str += f' + {field.name}_size'
            else:
                definition += f"\n{T}{T}{field.name} = struct.unpack_from('<{field.format}', buffer, {offset}{offset_str})[0]"
                offset += field.size
        definition += f'\n{T}{T}return cls('
        for field in message.fields:
            definition += f'\n{T}{T}{T}{field.name}={field.name},'
        definition += f'\n{T}{T}), {offset}{offset_str}\n'

    definition += '\n'

    return definition


def generate_registry(
    transactions: list[parser.Transaction], publishes: list[parser.Publish], stub: bool
) -> str:
    """Generate a registry for transactions."""

    definition = 'REGISTRY: dict[int, Type[bh.BuffhamLike]]'

    if stub:
        definition += ' = ...\n\n'
    else:
        definition += ' = {\n'
        for transaction in transactions:
            definition += f'{T}{transaction.request_id}: {transaction.send.name},\n'
        for publish in publishes:
            definition += f'{T}{publish.request_id}: {publish.send.name},\n'
        definition += '}\n\n'

    return definition


def generate_serializer(
    name: str, ctx: parser.ParseContext, primary_namespace: str, stub: bool
) -> str:
    """Generate a serializer with a defined registry for transactions."""

    definition = (
        f'class {name}Serializer(bh_cobs.BhCobs):\n'
        f'{T}def __init__(self, registry: bh_cobs.Registry | None = None):'
    )

    if stub:
        definition += ' ...\n\n'
    else:
        definition += f'\n' f'{T}{T}registry = (registry or {{}}) | REGISTRY'

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
        f'class {name}Node['
        'CommsTransporter: transporter.TransporterLike, '
        'LogTransporter: transporter.TransporterLike]('
        f'bh.BhNode[{name}Serializer, CommsTransporter, LogTransporter]'
        '):\n'
        f'{T}def __init__('
        'self, '
        f'serializer: {name}Serializer | None = None, '
        'comms_transporter: CommsTransporter | None = None, '
        'log_transporter: LogTransporter | None = None):'
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
            f'{_get_imported_name(transaction.receive.get_relative_name(primary_namespace))}, '
            f'{_get_imported_name(transaction.send.get_relative_name(primary_namespace))}'
            f'] = ...\n'
        )
    else:
        definition += (
            f'{transaction.name.upper()} = bh.Transaction['
            f'{_get_imported_name(transaction.receive.get_relative_name(primary_namespace))}, '
            f'{_get_imported_name(transaction.send.get_relative_name(primary_namespace))}'
            f']({transaction.request_id})\n'
        )

    return definition


def generate_publishes(publishes: list[parser.Publish]) -> str:
    definition = ''

    if not publishes:
        return definition

    definition += '\nclass PublishIds(enum.Enum):\n'

    for publish in publishes:
        for comment in publish.comments:
            definition += f'{T}#{comment}\n'

        definition += f'{T}{publish.name.upper()} = {publish.request_id}\n'

    return definition


def generate_python(
    ctx: parser.ParseContext, primary_namespace: str, outfile: pathlib.Path, stub: bool
) -> None:
    bh = ctx.buffhams[primary_namespace]

    with outfile.open('w') as fp:
        fp.write('# @generated by Buffham\n')

        if len(bh.messages):
            # Add imports
            fp.write('import dataclasses\n')
            if len(bh.publishes):
                fp.write('import enum\n')
            if not stub:
                fp.write('import struct\n')
            fp.write('from typing import Self, Type\n\n')

        if len(bh.transactions):
            # Add imports
            fp.write(
                'from emb.network.serialize import bh_cobs\n'
                'from emb.network.transport import transporter\n'
                'from nlb.buffham import bh\n\n'
            )

        if len(ctx.buffhams) > 1:
            # Add imports
            for namespace in ctx.buffhams:
                if namespace == primary_namespace:
                    continue
                package, module = namespace.rsplit('.', 1)
                fp.write(f'from {package} import {module}_bh\n')
            fp.write('\n')

        # Generate constant definitions
        for constant in bh.constants:
            fp.write(generate_constant(constant))
        if bh.constants:
            fp.write('\n\n')

        # Generate message definitions
        for message in bh.messages:
            fp.write(generate_message(message, stub, primary_namespace))

        # Generate registry
        if len(bh.transactions) or len(bh.publishes):
            fp.write(generate_registry(bh.transactions, bh.publishes, stub))

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
