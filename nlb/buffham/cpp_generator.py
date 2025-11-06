import pathlib

from nlb.buffham import parser
from nlb.buffham import schema_bh

T = ' ' * 4  # Indentation

TYPE_MAP = {
    schema_bh.FieldType.BOOL: 'bool',
    schema_bh.FieldType.UINT8_T: 'uint8_t',
    schema_bh.FieldType.UINT16_T: 'uint16_t',
    schema_bh.FieldType.UINT32_T: 'uint32_t',
    schema_bh.FieldType.UINT64_T: 'uint64_t',
    schema_bh.FieldType.INT8_T: 'int8_t',
    schema_bh.FieldType.INT16_T: 'int16_t',
    schema_bh.FieldType.INT32_T: 'int32_t',
    schema_bh.FieldType.INT64_T: 'int64_t',
    schema_bh.FieldType.FLOAT32: 'float',
    schema_bh.FieldType.FLOAT64: 'double',
    schema_bh.FieldType.STRING: 'std::string',
    schema_bh.FieldType.BYTES: 'std::vector<uint8_t>',
}


def _to_snake_case(name: str) -> str:
    """Convert a title case name to snake case."""
    return name[0].lower() + ''.join(
        f'_{c.lower()}' if c.isupper() else c for c in name[1:]
    )


def _to_konstant_case(name: str) -> str:
    """Convert to kTitleCase from a full name.

    Assumes local constants are already trimmed of their namespace.

    Examples:
    - 'nlb.buffham.constants.foo' -> 'nlb::buffham::constants::kFoo'
    - 'foo' -> 'kFoo'
    """
    if '.' in name:
        parts = name.split('.')
        return '::'.join(parts[:-2]) + '::k' + parts[-1].title().replace('_', '')

    return 'k' + name.title().replace('_', '')


def _generate_comment(comments: list[str], tabs: str) -> str:
    """Generate a comment block.

    Does not inlude a trailing newline.
    """
    definition = ''
    if len(comments) > 1:
        definition += f'{tabs}/*'
        for comment in comments:
            if comment:
                definition += f'\n{tabs}{comment.lstrip()}'
            else:
                definition += '\n'
        definition += f'\n{tabs} */'
    elif comments:
        definition += f'{tabs}//{comments[0]}'
    return definition


def _get_namespaced_name(relative_name: str) -> str:
    """Get the namespaced name for a relative name."""
    split = relative_name.split('.')
    return '::'.join(split[:-2] + split[-1:])


def _cpp_type(field: schema_bh.Field, primary_namespace: str) -> str:
    """Get the C++ type for the field."""
    if field.obj_name is not None:
        type_str = _get_namespaced_name(
            parser.relative_name(field.obj_name, primary_namespace)
        )
    elif field.pri_type is schema_bh.FieldType.LIST:
        assert field.sub_type is not None
        type_str = f'std::vector<{TYPE_MAP[field.sub_type]}>'
    else:
        type_str = TYPE_MAP[field.pri_type]

    if field.is_optional:
        type_str = f'std::optional<{type_str}>'

    return type_str


def _generate_serializer(
    message: parser.Message,
    num_optional_fields: int,
    num_optional_bytes: int,
    definition: str,
) -> str:
    definition += ' {'
    definition += f'\n{T}uint16_t offset = 0;'

    if num_optional_fields > 0:
        assert num_optional_bytes == 1, (
            'Only added uint8_t support so far for optional bitfields'
        )
        definition += f'\n{T}uint8_t optional_bitfield = 0;'
        optional_idx = 0
        for field in message.fields:
            if field.is_optional:
                definition += f'\n{T}optional_bitfield |= {field.name}.has_value() ? (1 << {optional_idx}) : 0;'
                optional_idx += 1
        definition += (
            f'\n{T}memcpy(buffer.data(), &optional_bitfield, {num_optional_bytes});'
        )
        definition += f'\n{T}offset += {num_optional_bytes};'

    for field in message.fields:
        field_size = parser.SIZE_MAP[field.sub_type or field.pri_type]
        optional_value = '.value()' if field.is_optional else ''
        access = '->' if field.is_optional else '.'

        if parser.is_field_iterable(field):
            # Get size
            size_expression = f'{field.name}.size()'
            if field.is_optional:
                size_expression = f'{field.name}.has_value() ? {field.name}->size() : 0'
            definition += f'\n{T}uint16_t {field.name}_size = {size_expression};'

            # Write size
            size_read_expression = (
                f'memcpy(buffer.data() + offset, &{field.name}_size, 2)'
            )
            if field.is_optional:
                definition += (
                    f'\n{T}{field.name}.has_value() ? {size_read_expression} : 0;'
                )
                definition += f'\n{T}offset += 2 * {field.name}.has_value();'
            else:
                definition += f'\n{T}{size_read_expression};'
                definition += f'\n{T}offset += 2;'

            if field.sub_type in (
                schema_bh.FieldType.STRING,
                schema_bh.FieldType.BYTES,
            ):
                # Write each item with length prefix
                definition += f'\n{T}for (const auto &item : {field.name}) {{'
                definition += f'\n{T}{T}uint16_t item_size = item.size();'
                definition += f'\n{T}{T}memcpy(buffer.data() + offset, &item_size, 2);'
                definition += f'\n{T}{T}offset += 2;'
                definition += (
                    f'\n{T}{T}memcpy(buffer.data() + offset, item.data(), item_size);'
                )
                definition += f'\n{T}{T}offset += item_size;'
                definition += f'\n{T}}}'
            else:
                # Write data
                data_expression = f'memcpy(buffer.data() + offset, {field.name}{access}data(), {field.name}_size * {field_size})'
                if field.is_optional:
                    data_expression = (
                        f'{field.name}.has_value() ? {data_expression} : 0'
                    )
                definition += f'\n{T}{data_expression};'
                definition += f'\n{T}offset += {field.name}_size * {field_size};'
        elif field.pri_type is schema_bh.FieldType.MESSAGE:
            expression = f'{field.name}.serialize(buffer.subspan(offset))'
            if field.is_optional:
                expression = (
                    f'{field.name}.has_value() ? {expression} : std::span<uint8_t>{{}}'
                )
            definition += f'\n{T}auto {field.name}_buffer = {expression};'
            definition += f'\n{T}offset += {field.name}_buffer.size();'
        elif field.pri_type is schema_bh.FieldType.ENUM:
            # Enums can be treated like their underlying uint8_t type
            expression = f'memcpy(buffer.data() + offset, &{field.name}{optional_value}, {field_size})'
            if field.is_optional:
                definition += f'\n{T}{field.name}.has_value() ? {expression} : 0;'
                definition += f'\n{T}offset += {field_size} * {field.name}.has_value();'
            else:
                definition += f'\n{T}{expression};'
                definition += f'\n{T}offset += {field_size};'
        else:
            expression = f'memcpy(buffer.data() + offset, &{field.name}{optional_value}, {field_size})'
            if field.is_optional:
                definition += f'\n{T}{field.name}.has_value() ? {expression} : 0;'
                definition += f'\n{T}offset += {field_size} * {field.name}.has_value();'
            else:
                definition += f'\n{T}{expression};'
                definition += f'\n{T}offset += {field_size};'
    definition += f'\n{T}return buffer.subspan(0, offset);\n'
    definition += '}\n\n'

    return definition


def _generate_deserializer(
    message: parser.Message,
    num_optional_fields: int,
    num_optional_bytes: int,
    primary_namespace: str,
    definition: str,
) -> str:
    definition += ' {'
    definition += f'\n{T}uint16_t offset = 0;'

    if num_optional_fields > 0:
        assert num_optional_bytes == 1, (
            'Only added uint8_t support so far for optional bitfields'
        )
        definition += f'\n{T}uint8_t optional_bitfield;'
        definition += (
            f'\n{T}memcpy(&optional_bitfield, buffer.data(), {num_optional_bytes});'
        )
        definition += f'\n{T}offset += {num_optional_bytes};'

    message_name = _to_snake_case(message.name)
    definition += f'\n{T}{message.name} {message_name};'
    optional_idx = 0
    for field in message.fields:
        field_size = parser.SIZE_MAP[field.sub_type or field.pri_type]
        optional_value = '.emplace()' if field.is_optional else ''
        access = '->' if field.is_optional else '.'

        if parser.is_field_iterable(field):
            # Get size
            definition += f'\n{T}uint16_t {field.name}_size;'
            expression = f'memcpy(&{field.name}_size, buffer.data() + offset, 2)'
            if field.is_optional:
                definition += f'\n{T}(optional_bitfield & (1 << {optional_idx})) ? {expression} : 0;'
                definition += (
                    f'\n{T}offset += 2 * {message_name}.{field.name}.has_value();'
                )
            else:
                definition += f'\n{T}{expression};'
                definition += f'\n{T}offset += 2;'

            # Resize data
            resize_expression = f'{message_name}.{field.name}.resize({field.name}_size)'
            if field.is_optional:
                resize_expression = f'(optional_bitfield & (1 << {optional_idx})) ? {resize_expression} : 0'
            definition += f'\n{T}{resize_expression};'

            if field.sub_type in (
                schema_bh.FieldType.STRING,
                schema_bh.FieldType.BYTES,
            ):
                # Read each item with length prefix
                definition += f'\n{T}for (auto &item : {message_name}.{field.name}) {{'
                definition += f'\n{T}{T}uint16_t item_size;'
                definition += f'\n{T}{T}memcpy(&item_size, buffer.data() + offset, 2);'
                definition += f'\n{T}{T}offset += 2;'
                definition += f'\n{T}{T}item.resize(item_size);'
                definition += (
                    f'\n{T}{T}memcpy(item.data(), buffer.data() + offset, item_size);'
                )
                definition += f'\n{T}{T}offset += item_size;'
                definition += f'\n{T}}}'
            else:
                # Read data
                read_expression = f'memcpy({message_name}.{field.name}{access}data(), buffer.data() + offset, {field.name}_size * {field_size})'
                if field.is_optional:
                    read_expression = f'(optional_bitfield & (1 << {optional_idx})) ? {expression} : 0'
                definition += f'\n{T}{read_expression};'
                definition += f'\n{T}offset += {field.name}_size * {field_size};'
        elif field.pri_type is schema_bh.FieldType.MESSAGE:
            definition += f'\n{T}auto {field.name}_buffer = buffer.subspan(offset);'
            expression = f'{_cpp_type(field, primary_namespace)}::deserialize({field.name}_buffer)'
            if field.is_optional:
                # Return a pair of nullopt and an empty buffer
                expression = f'(optional_bitfield & (1 << {optional_idx})) ? {expression} : std::make_pair(std::nullopt, buffer.subspan(0, 0))'
            definition += f'\n{T}std::tie({message_name}.{field.name}, {field.name}_buffer) = {expression};'
            definition += f'\n{T}offset += {field.name}_buffer.size();'
        elif field.pri_type is schema_bh.FieldType.ENUM:
            # Enums can be treated like their underlying uint8_t type
            expression = f'memcpy(&{message_name}.{field.name}{optional_value}, buffer.data() + offset, {field_size})'
            if field.is_optional:
                definition += f'\n{T}(optional_bitfield & (1 << {optional_idx})) ? {expression} : 0;'
                definition += f'\n{T}offset += {field_size} * {message_name}.{field.name}.has_value();'
            else:
                definition += f'\n{T}{expression};'
                definition += f'\n{T}offset += {field_size};'
        else:
            expression = f'memcpy(&{message_name}.{field.name}{optional_value}, buffer.data() + offset, {field_size})'
            if field.is_optional:
                definition += f'\n{T}(optional_bitfield & (1 << {optional_idx})) ? {expression} : 0;'
                definition += f'\n{T}offset += {field_size} * {message_name}.{field.name}.has_value();'
            else:
                definition += f'\n{T}{expression};'
                definition += f'\n{T}offset += {field_size};'

        if field.is_optional:
            optional_idx += 1

    definition += f'\n{T}return {{{message_name}, buffer.subspan(0, offset)}};\n'
    definition += '}\n'

    return definition


def generate_message(message: parser.Message, primary_namespace: str, hpp: bool) -> str:
    """Generate a struct definition from a Message."""
    definition = ''
    ns = '' if hpp else f'{message.name}::'
    tab = T if hpp else ''

    if hpp:
        # Docstring
        if message.comments:
            definition += _generate_comment(message.comments, '') + '\n'

        definition += f'struct {message.name} {{'

        # Define fields
        for field in message.fields:
            if field.comments:
                definition += '\n' + _generate_comment(field.comments, T)
            definition += f'\n{T}{_cpp_type(field, primary_namespace)} {field.name};'
            if field.inline_comment:
                definition += f'  //{field.inline_comment}'
        definition += '\n\n'

    num_optional_fields = sum(1 for f in message.fields if f.is_optional)
    num_optional_bytes = (num_optional_fields + 7) // 8

    # Add serializer method
    definition += (
        f'{tab}std::span<uint8_t> {ns}serialize(std::span<uint8_t> buffer) const'
    )

    if hpp:
        definition += ';\n\n'
    else:
        definition = _generate_serializer(
            message, num_optional_fields, num_optional_bytes, definition
        )

    # Add deserializer method
    qualifiers = 'static ' if hpp else ''
    definition += f'{tab}{qualifiers}std::pair<{message.name}, std::span<const uint8_t> > {ns}deserialize(std::span<const uint8_t> buffer)'
    if hpp:
        definition += ';\n'
    else:
        definition = _generate_deserializer(
            message,
            num_optional_fields,
            num_optional_bytes,
            primary_namespace,
            definition,
        )

    if hpp:
        definition += '};\n'
    definition += '\n'

    return definition


def generate_project_class(
    name: str, transactions: list[schema_bh.Transaction], primary_namespace: str
) -> str:
    """Generate a project class definition."""
    definition = f'class {name} {{\n{T[::2]}public:\n{T}{name}();\n{T}~{name}();\n\n'

    # Add initialization method
    definition += f'{T}void initialize();\n\n'

    # Add register_handlers method
    definition += (
        f'{T}template <emb::network::serialize::SerializerLike S,\n'
        f'{T}{T}{T}{T}emb::network::transport::TransporterLike T, class... Projects>\n'
        f'{T}void register_handlers(emb::network::node::Node<S, T, Projects...> &node) {{\n'
    )
    for transaction in transactions:
        definition += (
            f'{T}{T}node.template register_handler<{_get_namespaced_name(parser.relative_name(transaction.receive_name, primary_namespace))}, '
            f'{_get_namespaced_name(parser.relative_name(transaction.send_name, primary_namespace))}>({transaction.request_id}, '
            f'std::bind(&{name}::{transaction.name}, this, std::placeholders::_1));\n'
        )
    definition += f'{T}}}\n\n'

    # Add each transaction method
    for transaction in transactions:
        if transaction.comments:
            definition += _generate_comment(transaction.comments, T) + '\n'
        definition += f'{T}{_get_namespaced_name(parser.relative_name(transaction.send_name, primary_namespace))} {transaction.name}(const {_get_namespaced_name(parser.relative_name(transaction.receive_name, primary_namespace))} &{_to_snake_case(transaction.receive_name.name)});'
        if transaction.inline_comment:
            definition += f'  //{transaction.inline_comment}'
        definition += '\n'

    # Add a pIMPL struct
    definition += f'{T[::2]}private:\n'
    definition += f'{T}struct {name}Impl;\n'
    definition += f'{T}{name}Impl *impl_;\n'

    definition += '};\n\n'

    return definition


def generate_publishes(publishes: list[schema_bh.Publish]) -> str:
    """Generate a publish definition."""
    definition = ''

    if not publishes:
        return definition

    definition += 'enum PublishIds : uint8_t {\n'
    for publish in publishes:
        if publish.comments:
            definition += _generate_comment(publish.comments, T) + '\n'
        definition += f'{T}{publish.name.upper()} = {publish.request_id},'
        if publish.inline_comment:
            definition += f'  //{publish.inline_comment}'
        definition += '\n'
    definition += '};\n\n'

    return definition


def generate_namespace(namespace: list[str]) -> str:
    """Generate a namespace definition."""
    definition = ''

    for part in namespace:
        definition += f'namespace {part} {{\n'

    definition += '\n'

    return definition


def generate_end_namespace(namespace: list[str]) -> str:
    """Generate an end namespace definition."""
    definition = ''

    for part in namespace:
        definition += f'}}  // namespace {part}\n'

    return definition


def generate_constant(constant: schema_bh.Constant) -> str:
    """Generate a constant definition."""

    definition = ''

    if constant.comments:
        definition += _generate_comment(constant.comments, '') + '\n'
    references = {ref: _to_konstant_case(ref) for ref in constant.references}
    value = constant.value
    for ref, name in references.items():
        value = value.replace(f'{{{ref}}}', name)
    extra_type = ''
    if constant.type is schema_bh.FieldType.STRING:
        value = f'"{value}"'
        # Gotta use string_view for constexpr strings
        extra_type = '_view'
    definition += f'constexpr {TYPE_MAP[constant.type]}{extra_type} {_to_konstant_case(constant.name)} = {value};'

    if constant.inline_comment:
        definition += f'  //{constant.inline_comment}'

    definition += '\n'

    return definition


def generate_enum(enum: parser.Enum) -> str:
    """Generate a C++ enum definition from an Enum."""
    definition = ''

    if enum.comments:
        definition += _generate_comment(enum.comments, '') + '\n'

    definition += f'enum class {enum.name} : uint8_t {{\n'
    for field in enum.fields:
        if field.comments:
            definition += _generate_comment(field.comments, T) + '\n'
        definition += f'{T}{field.name} = {field.value},'
        if field.inline_comment:
            definition += f'  //{field.inline_comment}'
        definition += '\n'
    definition += '};\n\n'

    return definition


def generate_cpp(
    ctx: parser.Parser, primary_namespace: str, outfile: pathlib.Path, hpp: bool
) -> None:
    bh = ctx.buffhams[primary_namespace]

    with outfile.open('w') as fp:
        if hpp:
            fp.write('#pragma once\n\n')
        else:
            fp.write(f'#include "{primary_namespace.replace(".", "/")}_bh.hpp"\n\n')

        if len(bh.messages):
            # Add includes
            # TODO: Trim down includes based on message types / move some
            # includes to the cc file
            fp.write(
                '#include <cinttypes>\n'
                '#include <cstring>\n'
                '#include <optional>\n'
                '#include <span>\n'
                '#include <string>\n'
                '#include <tuple>\n'
                '#include <vector>\n\n'
            )
        elif schema_bh.FieldType.STRING in [constant.type for constant in bh.constants]:
            fp.write('#include <string>\n\n')

        if len(bh.transactions) and hpp:
            # Add includes
            fp.write(
                '#include "emb/network/node/node.hpp"\n'
                '#include "emb/network/serialize/serializer.hpp"\n'
                '#include "emb/network/transport/transporter.hpp"\n\n'
            )

        if len(ctx.buffhams) > 1:
            # Add includes for other namespaces
            for namespace in ctx.buffhams:
                if namespace != primary_namespace:
                    fp.write(f'#include "{namespace.replace(".", "/")}_bh.hpp"\n')
            fp.write('\n')

        fp.write(generate_namespace(bh.namespace.split('.')[:-1]))

        # Generate constant definitions
        if hpp:
            for constant in bh.constants:
                fp.write(generate_constant(constant))
            if bh.constants:
                fp.write('\n')

        # Generate enum definitions
        if hpp:
            for enum in bh.enums:
                fp.write(generate_enum(enum))

        # Generate message definitions
        for message in bh.messages:
            fp.write(generate_message(message, primary_namespace, hpp))

        # Generate transaction definitions
        if len(bh.transactions) and hpp:
            fp.write(
                generate_project_class(
                    bh.name.title(), bh.transactions, primary_namespace
                )
            )

        # Generate publish definitions
        if hpp:
            fp.write(generate_publishes(bh.publishes))

        fp.write(generate_end_namespace(bh.namespace.split('.')[:-1]))
