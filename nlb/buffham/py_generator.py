import pathlib

from nlb.buffham import parser

T = ' ' * 4  # Indentation


def generate_message(message: parser.Message, stub: bool) -> str:
    """Generate a Python dataclass definition from a Message."""

    definition = ('@dataclasses.dataclass\n' 'class {name}:').format(name=message.name)

    for field in message.fields:
        definition += f'\n{T}{field.name}: {field.py_type}'

    # Add serializer method
    definition += f'\n\n{T}def serialize(self) -> bytes:'
    if stub:
        definition += ' ...\n'
    else:
        definition += f'\n{T}{T}buffer = bytes()'
        for field in message.fields:
            if field.iterable:
                definition += (
                    f"\n{T}{T}buffer += struct.pack('>H', len(self.{field.name}))"
                )
                if field.pri_type is parser.FieldType.LIST:
                    definition += f"\n{T}{T}buffer += struct.pack(f'>{{len(self.{field.name})}}{field.format}', *self.{field.name})"
                else:
                    definition += f'\n{T}{T}buffer += self.{field.name}'
                    if field.pri_type is parser.FieldType.STRING:
                        definition += f".encode()"
            else:
                definition += f"\n{T}{T}buffer += struct.pack(f'>{field.format}', self.{field.name})"
        definition += f'\n{T}{T}return buffer\n'

    # Add deserializer method
    definition += f'\n{T}@classmethod'
    definition += f'\n{T}def deserialize(cls, buffer: bytes) -> Self:'
    if stub:
        definition += ' ...\n'
    else:
        definition += f'\n{T}{T}offset = 0'
        for field in message.fields:
            if field.pri_type is parser.FieldType.LIST:
                definition += (
                    f"\n{T}{T}size = struct.unpack_from('>H', buffer, offset)[0]"
                )
                definition += f"\n{T}{T}offset += 2"
                definition += f"\n{T}{T}{field.name} = list(struct.unpack_from(f'>{{size}}{field.format}', buffer, offset))"
                definition += f"\n{T}{T}offset += size * {field.size}"
            elif field.pri_type in (parser.FieldType.STRING, parser.FieldType.BYTES):
                definition += (
                    f"\n{T}{T}size = struct.unpack_from('>H', buffer, offset)[0]"
                )
                definition += f"\n{T}{T}offset += 2"
                definition += f"\n{T}{T}{field.name} = buffer[offset:offset + size]"
                if field.pri_type is parser.FieldType.STRING:
                    definition += f".decode()"
                definition += f"\n{T}{T}offset += size"
            else:
                definition += f"\n{T}{T}{field.name} = struct.unpack_from(f'>{field.format}', buffer, offset)[0]"
                definition += f"\n{T}{T}offset += {field.size}"
        definition += f'\n{T}{T}return cls('
        for field in message.fields:
            definition += f'\n{T}{T}{T}{field.name}={field.name},'
        definition += f'\n{T}{T})\n'

    definition += '\n'

    return definition


def generate_serializer(
    name: str, transactions: list[parser.Transaction], stub: bool
) -> str:
    """Generate a serializer with a defined registry for transactions."""

    definition = (
        f'class {name}Serializer(cbor2_cobs.Cbor2Cobs):\n'
        f'{T}def __init__(self, registry: cbor2_cobs.Registry | None = None):'
    )

    if stub:
        definition += ' ...\n\n'
    else:
        definition += f'\n' f'{T}{T}registry = registry or {{}}\n'

        definition += f'{T}{T}registry.update({{\n'
        for i, transaction in enumerate(transactions):
            definition += f'{T}{T}{T}{i}: {transaction.send.name},\n'
        definition += f'{T}{T}}})\n'

        definition += f'{T}{T}super().__init__(registry)\n\n'

    return definition


def generate_node(name: str, stub: bool) -> str:
    """Generate a node that uses the serializer with defined transactions."""

    definition = (
        f'class {name}Node['
        f'Transporter: transporter.TransporterLike]('
        f'dataclass_node.DataclassNode[{name}Serializer, Transporter]'
        f'):\n'
        f'{T}def __init__('
        f'self, '
        f'serializer: {name}Serializer | None = None, '
        f'transporter: Transporter | None = None):'
    )

    if stub:
        definition += ' ...\n\n'
    else:
        definition += (
            f'\n'
            f'{T}{T}super().__init__(serializer or {name}Serializer(), transporter)\n\n'
        )

    return definition


def generate_transaction(transaction: parser.Transaction, stub: bool) -> str:
    """Generate a transaction definition."""

    if stub:
        definition = (
            f'{transaction.name.upper()}: dataclass_node.Transaction['
            f'{transaction.receive.name},'
            f'{transaction.send.name}'
            f'] = ...\n'
        )
    else:
        definition = (
            f'{transaction.name.upper()} = dataclass_node.Transaction['
            f'{transaction.receive.name},'
            f'{transaction.send.name}'
            f']({transaction.request_id})\n'
        )

    return definition


def generate_python(bh: parser.Buffham, outfile: pathlib.Path, stub: bool) -> None:
    with outfile.open('w') as fp:
        if len(bh.messages):
            # Add imports
            fp.write('import dataclasses\n')
            if not stub:
                fp.write('import struct\n')
            fp.write('from typing import Self\n\n')

        if len(bh.transactions):
            # Add imports
            fp.write(
                'from emb.network.node import dataclass_node\n'
                'from emb.network.serialize import cbor2_cobs\n'
                'from emb.network.transport import transporter\n\n'
            )

        # Generate message definitions
        for message in bh.messages:
            fp.write(generate_message(message, stub))

        # Generate transaction definitions
        if len(bh.transactions):
            fp.write(generate_serializer(bh.name, bh.transactions, stub))
            fp.write(generate_node(bh.name, stub))
        for transaction in bh.transactions:
            fp.write(generate_transaction(transaction, stub))
