import pathlib

from nlb.buffham import parser

T = ' ' * 4  # Indentation


def _to_snake_case(name: str) -> str:
    """Convert a title case name to snake case."""
    return name[0].lower() + ''.join(
        f'_{c.lower()}' if c.isupper() else c for c in name[1:]
    )


def generate_message(message: parser.Message) -> str:
    """Generate a struct definition from a Message."""

    definition = f'struct {message.name} {{'

    for field in message.fields:
        definition += f'\n{T}{field.cpp_type} {field.name};'

    # Add serializer method
    definition += (
        f'\n\n{T}std::span<uint8_t> serialize(std::span<uint8_t> buffer) const {{'
    )
    offset = 0
    offset_str = ''
    for field in message.fields:
        if field.iterable:
            definition += (
                f"\n{T}{T}uint16_t {field.name}_size = {field.name}.size();"
                f"\n{T}{T}memcpy(buffer.data() + {offset}{offset_str}, &{field.name}_size, 2);"
            )
            offset += 2
            definition += f"\n{T}{T}memcpy(buffer.data() + {offset}{offset_str}, {field.name}.data(), {field.name}_size * {field.size});"
            offset_str += f' + {field.name}_size * {field.size}'
        else:
            definition += f"\n{T}{T}memcpy(buffer.data() + {offset}{offset_str}, &{field.name}, {field.size});"
            offset += field.size
    definition += f'\n{T}{T}return buffer.subspan(0, {offset}{offset_str});\n'
    definition += f'{T}}}\n'

    # Add deserializer method
    offset = 0
    offset_str = ''
    definition += (
        f'\n{T}static {message.name} deserialize(std::span<const uint8_t> buffer) {{'
    )
    message_name = _to_snake_case(message.name)
    definition += f'\n{T}{T}{message.name} {message_name};'
    for field in message.fields:
        if field.iterable:
            definition += (
                f"\n{T}{T}uint16_t {field.name}_size;"
                f"\n{T}{T}memcpy(&{field.name}_size, buffer.data() + {offset}{offset_str}, 2);"
            )
            offset += 2
            definition += (
                f"\n{T}{T}{message_name}.{field.name}.resize({field.name}_size);"
            )
            definition += f"\n{T}{T}memcpy({message_name}.{field.name}.data(), buffer.data() + {offset}{offset_str}, {field.name}_size * {field.size});"
            offset_str += f' + {field.name}_size * {field.size}'
        else:
            definition += f"\n{T}{T}memcpy(&{message_name}.{field.name}, buffer.data() + {offset}{offset_str}, {field.size});"
            offset += field.size

    definition += f'\n{T}{T}return {message_name};\n'
    definition += f'{T}}}\n'

    definition += '};\n\n'

    return definition


def generate_project_class(name: str, transactions: list[parser.Transaction]) -> str:
    """Generate a project class definition."""
    definition = (
        f'class {name} {{\n' f'{T[::2]}public:\n' f'{T}{name}();\n' f'{T}~{name}();\n\n'
    )

    # Add register_handlers method
    definition += (
        f'{T}template <network::serialize::SerializerLike S,\n'
        f'{T}{T}{T}{T}network::transport::TransporterLike T, class... Projects>\n'
        f'{T}void register_handlers(network::node::Node<S, T, Projects...> &node) {{\n'
    )
    for transaction in transactions:
        definition += (
            f'{T}{T}node.template register_handler<{transaction.receive.name}, '
            f'{transaction.send.name}>({transaction.request_id}, '
            f'std::bind(&{name}::{transaction.name}, this, std::placeholders::_1));\n'
        )
    definition += f'{T}}}\n\n'

    # Add each transaction method
    for transaction in transactions:
        definition += f'{T}{transaction.send.name} {transaction.name}(const {transaction.receive.name} &{_to_snake_case(transaction.receive.name)});\n'

    # Add a pIMPL struct
    definition += f'{T[::2]}private:\n'
    definition += f'{T}struct {name}Impl;\n'
    definition += f'{T}{name}Impl *impl_;\n'

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


def generate_cpp(bh: parser.Buffham, outfile: pathlib.Path) -> None:
    with outfile.open('w') as fp:
        fp.write('#pragma once\n\n')

        if len(bh.messages):
            # Add includes
            # TODO: Trim down includes based on message types
            fp.write(
                '#include <inttypes.h>\n'
                '#include <span>\n'
                '#include <string>\n'
                '#include <string.h>\n'
                '#include <vector>\n\n'
            )

        if len(bh.transactions):
            # Add includes
            fp.write(
                '#include "emb/network/node/node.hpp"\n'
                '#include "emb/network/serialize/serializer.hpp"\n'
                '#include "emb/network/transport/transporter.hpp"\n\n'
            )

        fp.write(generate_namespace(bh.namespace))

        # Generate message definitions
        for message in bh.messages:
            fp.write(generate_message(message))

        # Generate transaction definitions
        if len(bh.transactions):
            fp.write(generate_project_class(bh.name, bh.transactions))

        fp.write(generate_end_namespace(bh.namespace))
