import pathlib

from nlb.buffham import parser

T = ' ' * 4  # Indentation

TYPE_MAP = {
    parser.FieldType.UINT8_T: 'uint8_t',
    parser.FieldType.UINT16_T: 'uint16_t',
    parser.FieldType.UINT32_T: 'uint32_t',
    parser.FieldType.UINT64_T: 'uint64_t',
    parser.FieldType.INT8_T: 'int8_t',
    parser.FieldType.INT16_T: 'int16_t',
    parser.FieldType.INT32_T: 'int32_t',
    parser.FieldType.INT64_T: 'int64_t',
    parser.FieldType.FLOAT32: 'float',
    parser.FieldType.FLOAT64: 'double',
    parser.FieldType.STRING: 'std::string',
    parser.FieldType.BYTES: 'std::vector<uint8_t>',
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


def _cpp_type(field: parser.Field, primary_namespace: str) -> str:
    """Get the C++ type for the field."""
    if field.message:
        return _get_namespaced_name(field.message.get_relative_name(primary_namespace))

    if field.pri_type is parser.FieldType.LIST:
        assert field.sub_type is not None
        return f'std::vector<{TYPE_MAP[field.sub_type]}>'

    return TYPE_MAP[field.pri_type]


def generate_message(message: parser.Message, primary_namespace: str, hpp: bool) -> str:
    """Generate a struct definition from a Message."""
    definition = ''
    ns = '' if hpp else f'{message.name}::'
    tab = T if hpp else ''

    if hpp:
        if message.comments:
            definition += _generate_comment(message.comments, '') + '\n'

        definition += f'struct {message.name} {{'

        for field in message.fields:
            if field.comments:
                definition += '\n' + _generate_comment(field.comments, T)
            definition += f'\n{T}{_cpp_type(field, primary_namespace)} {field.name};'
            if field.inline_comment:
                definition += f'  // {field.inline_comment}'
        definition += '\n\n'

    # Add serializer method
    definition += (
        f'{tab}std::span<uint8_t> {ns}serialize(std::span<uint8_t> buffer) const'
    )

    if hpp:
        definition += ';\n\n'
    else:
        definition += ' {'
        offset = 0
        offset_str = ''
        for field in message.fields:
            if field.iterable:
                definition += (
                    f'\n{tab}{T}uint16_t {field.name}_size = {field.name}.size();'
                    f'\n{tab}{T}memcpy(buffer.data() + {offset}{offset_str}, &{field.name}_size, 2);'
                )
                offset += 2
                definition += f'\n{tab}{T}memcpy(buffer.data() + {offset}{offset_str}, {field.name}.data(), {field.name}_size * {field.size});'
                offset_str += f' + {field.name}_size * {field.size}'
            elif field.pri_type is parser.FieldType.MESSAGE:
                definition += f'\n{tab}{T}auto {field.name}_buffer = {field.name}.serialize(buffer.subspan({offset}{offset_str}));'
                offset_str += f' + {field.name}_buffer.size()'
            else:
                definition += f'\n{tab}{T}memcpy(buffer.data() + {offset}{offset_str}, &{field.name}, {field.size});'
                offset += field.size
        definition += f'\n{tab}{T}return buffer.subspan(0, {offset}{offset_str});\n'
        definition += f'{tab}}}\n\n'

    # Add deserializer method
    qualifiers = 'static ' if hpp else ''
    definition += f'{tab}{qualifiers}std::pair<{message.name}, std::span<const uint8_t> > {ns}deserialize(std::span<const uint8_t> buffer)'
    if hpp:
        definition += ';\n'
    else:
        definition += ' {'
        offset = 0
        offset_str = ''
        message_name = _to_snake_case(message.name)
        definition += f'\n{tab}{T}{message.name} {message_name};'
        for field in message.fields:
            if field.iterable:
                definition += (
                    f'\n{tab}{T}uint16_t {field.name}_size;'
                    f'\n{tab}{T}memcpy(&{field.name}_size, buffer.data() + {offset}{offset_str}, 2);'
                )
                offset += 2
                definition += (
                    f'\n{tab}{T}{message_name}.{field.name}.resize({field.name}_size);'
                )
                definition += f'\n{tab}{T}memcpy({message_name}.{field.name}.data(), buffer.data() + {offset}{offset_str}, {field.name}_size * {field.size});'
                offset_str += f' + {field.name}_size * {field.size}'
            elif field.pri_type is parser.FieldType.MESSAGE:
                definition += f'\n{tab}{T}auto {field.name}_buffer = buffer.subspan({offset}{offset_str});'
                definition += f'\n{tab}{T}std::tie({message_name}.{field.name}, {field.name}_buffer) = {_cpp_type(field, primary_namespace)}::deserialize({field.name}_buffer);'
                offset_str += f' + {field.name}_buffer.size()'
            else:
                definition += f'\n{tab}{T}memcpy(&{message_name}.{field.name}, buffer.data() + {offset}{offset_str}, {field.size});'
                offset += field.size

        definition += f'\n{tab}{T}return {{{message_name}, buffer.subspan(0, {offset}{offset_str})}};\n'
        definition += f'{tab}}}\n'

    if hpp:
        definition += '};\n'
    definition += '\n'

    return definition


def generate_project_class(
    name: str, transactions: list[parser.Transaction], primary_namespace: str
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
            f'{T}{T}node.template register_handler<{_get_namespaced_name(transaction.receive.get_relative_name(primary_namespace))}, '
            f'{transaction.send.name}>({transaction.request_id}, '
            f'std::bind(&{name}::{transaction.name}, this, std::placeholders::_1));\n'
        )
    definition += f'{T}}}\n\n'

    # Add each transaction method
    for transaction in transactions:
        if transaction.comments:
            definition += _generate_comment(transaction.comments, T) + '\n'
        definition += f'{T}{_get_namespaced_name(transaction.send.get_relative_name(primary_namespace))} {transaction.name}(const {_get_namespaced_name(transaction.receive.get_relative_name(primary_namespace))} &{_to_snake_case(transaction.receive.name)});\n'

    # Add a pIMPL struct
    definition += f'{T[::2]}private:\n'
    definition += f'{T}struct {name}Impl;\n'
    definition += f'{T}{name}Impl *impl_;\n'

    definition += '};\n\n'

    return definition


def generate_publishes(publishes: list[parser.Publish]) -> str:
    """Generate a publish definition."""
    definition = ''

    if not publishes:
        return definition

    definition += 'enum PublishIds : uint8_t {\n'
    for publish in publishes:
        if publish.comments:
            definition += _generate_comment(publish.comments, T) + '\n'
        definition += f'{T}{publish.name.upper()} = {publish.request_id},\n'
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


def generate_constant(constant: parser.Constant) -> str:
    """Generate a constant definition."""

    definition = ''

    if constant.comments:
        definition += _generate_comment(constant.comments, '') + '\n'
    references = {ref: _to_konstant_case(ref) for ref in constant.references}
    value = constant.value
    for ref, name in references.items():
        value = value.replace(f'{{{ref}}}', name)
    extra_type = ''
    if constant.type is parser.FieldType.STRING:
        value = f'"{value}"'
        # Gotta use string_view for constexpr strings
        extra_type = '_view'
    definition += f'constexpr {TYPE_MAP[constant.type]}{extra_type} {_to_konstant_case(constant.name)} = {value};'

    if constant.inline_comment:
        definition += f'  //{constant.inline_comment}'

    definition += '\n'

    return definition


def generate_cpp(
    ctx: parser.ParseContext, primary_namespace: str, outfile: pathlib.Path, hpp: bool
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
                '#include <span>\n'
                '#include <string>\n'
                '#include <tuple>\n'
                '#include <vector>\n\n'
            )
        elif parser.FieldType.STRING in [constant.type for constant in bh.constants]:
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
                fp.write('\n\n')

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
