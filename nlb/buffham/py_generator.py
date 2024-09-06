import pathlib

from nlb.buffham import parser

T = ' ' * 4  # Indentation


def generate_message(message: parser.Message) -> str:
    """Generate a Python dataclass definition from a Message."""

    definition = ('@dataclasses.dataclass\n' 'class {name}:').format(name=message.name)

    for field in message.fields:
        definition += f'\n{T}{field.name}: {field.py_type}'

    # Add serializer method
    definition += f'\n\n{T}def serialize(self) -> bytes:'
    definition += f'\n{T}{T}buffer = bytes()'
    for field in message.fields:
        if field.iterable:
            definition += f"\n{T}{T}buffer += struct.pack('>H', len(self.{field.name}))"
            if field.pri_type is parser.FieldType.LIST:
                definition += f"\n{T}{T}buffer += struct.pack(f'>{{len(self.{field.name})}}{field.format}', *self.{field.name})"
            else:
                definition += f'\n{T}{T}buffer += self.{field.name}'
                if field.pri_type is parser.FieldType.STRING:
                    definition += f".encode()"
        else:
            definition += (
                f"\n{T}{T}buffer += struct.pack(f'>{field.format}', self.{field.name})"
            )
    definition += f'\n{T}{T}return buffer'

    # Add deserializer method
    definition += f'\n\n{T}@classmethod'
    definition += f'\n{T}def deserialize(cls, buffer: bytes) -> Self:'
    definition += f'\n{T}{T}offset = 0'
    for field in message.fields:
        if field.pri_type is parser.FieldType.LIST:
            definition += f"\n{T}{T}size = struct.unpack_from('>H', buffer, offset)[0]"
            definition += f"\n{T}{T}offset += 2"
            definition += f"\n{T}{T}{field.name} = list(struct.unpack_from(f'>{{size}}{field.format}', buffer, offset))"
            definition += f"\n{T}{T}offset += size * {field.size}"
        elif field.pri_type in (parser.FieldType.STRING, parser.FieldType.BYTES):
            definition += f"\n{T}{T}size = struct.unpack_from('>H', buffer, offset)[0]"
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


"""
class BaseSerializer(cbor2_cobs.Cbor2Cobs):
    def __init__(self, registry: cbor2_cobs.Registry | None = None):
        registry = registry or {}
        registry.update(
            {
                0: LogMessage,
                1: FlashPage,
                2: FlashPage,
            }
        )
        super().__init__(registry)


class BaseNode[Transporter: transporter.TransporterLike](
    dataclass_node.DataclassNode[BaseSerializer, Transporter]
):
    def __init__(
        self,
        serializer: BaseSerializer | None = None,
        transporter: Transporter | None = None,
    ):
        super().__init__(serializer or BaseSerializer(), transporter)

PING = dataclass_node.Transaction[Ping, LogMessage](0)
FLASH_PAGE = dataclass_node.Transaction[FlashPage, FlashPage](1)
READ_FLASH_PAGE = dataclass_node.Transaction[FlashPage, FlashPage](2)
"""


def generate_serializer(name: str, transactions: list[parser.Transaction]) -> str:
    """Generate a serializer with a defined registry for transactions."""

    definition = (
        f'class {name}Serializer(cbor2_cobs.Cbor2Cobs):\n'
        f'{T}def __init__(self, registry: cbor2_cobs.Registry | None = None):\n'
        f'{T}{T}registry = registry or {{}}\n'
    )

    definition += f'{T}{T}registry.update({{\n'
    for i, transaction in enumerate(transactions):
        definition += f'{T}{T}{T}{i}: {transaction.send.name},\n'
    definition += f'{T}{T}}})\n'

    definition += f'{T}{T}super().__init__(registry)\n\n'

    return definition


def generate_node(name: str, transactions: list[parser.Transaction]) -> str:
    """Generate a node that uses the serializer with defined transactions."""

    definition = (
        f'class {name}Node['
        f'Transporter: transporter.TransporterLike]('
        f'dataclass_node.DataclassNode[{name}Serializer, Transporter]'
        f'):\n'
        f'{T}def __init__('
        f'self, '
        f'serializer: {name}Serializer | None = None, '
        f'transporter: Transporter | None = None'
        f'):\n'
        f'{T}{T}super().__init__(serializer or {name}Serializer(), transporter)\n\n'
    )

    return definition


def generate_transaction(transaction: parser.Transaction) -> str:
    """Generate a transaction definition."""

    definition = (
        f'{transaction.name.upper()} = dataclass_node.Transaction['
        f'{transaction.receive.name},'
        f'{transaction.send.name}'
        f']({transaction.request_id})\n'
    )

    return definition


def generate_python(bh: parser.Buffham, outfile: pathlib.Path) -> None:
    with outfile.open('w') as fp:
        if len(bh.messages):
            # Add imports
            fp.write(
                'import dataclasses\n' 'import struct\n' 'from typing import Self\n\n'
            )

        if len(bh.transactions):
            # Add imports
            fp.write(
                'from emb.network.node import dataclass_node\n'
                'from emb.network.serialize import cbor2_cobs\n'
                'from emb.network.transport import transporter\n\n'
            )

        # Generate message definitions
        for message in bh.messages:
            fp.write(generate_message(message))

        # Generate transaction definitions
        if len(bh.transactions):
            fp.write(generate_serializer(bh.name, bh.transactions))
            fp.write(generate_node(bh.name, bh.transactions))
        for transaction in bh.transactions:
            fp.write(generate_transaction(transaction))

    print(outfile.read_text())
