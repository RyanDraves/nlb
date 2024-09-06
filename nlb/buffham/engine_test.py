import dataclasses
import unittest

from nlb.buffham import engine
from nlb.buffham import parser


@dataclasses.dataclass
class Ping:
    ping: int


@dataclasses.dataclass
class FlashPage:
    address: int
    read_size: int
    data: list[int]


@dataclasses.dataclass
class LogMessage:
    message: str


class TestEngine(unittest.TestCase):
    PING = parser.Message(
        'Ping',
        [
            parser.Field('ping', parser.FieldType.UINT8_T, None),
        ],
    )
    FLASH_PAGE = parser.Message(
        'FlashPage',
        [
            parser.Field('address', parser.FieldType.UINT32_T, None),
            parser.Field('read_size', parser.FieldType.UINT32_T, None),
            parser.Field('data', parser.FieldType.LIST, parser.FieldType.UINT32_T),
        ],
    )
    LOG_MESSAGE = parser.Message(
        'LogMessage',
        [
            parser.Field('message', parser.FieldType.STRING, None),
        ],
    )

    def test_generate_serializer(self):
        message = self.PING
        serializer = engine.generate_serializer(message)
        instance = Ping(42)
        self.assertEqual(
            serializer(instance),
            int(42).to_bytes(length=1, byteorder='big', signed=False),
        )

        message = self.FLASH_PAGE
        serializer = engine.generate_serializer(message)
        instance = FlashPage(0x1234, 0x5678, [0x9ABC, 0xDEF0])
        self.assertEqual(
            serializer(instance),
            b'\x00\x00\x12\x34\x00\x00\x56\x78\x00\x02\x00\x00\x9A\xBC\x00\x00\xDE\xF0',
        )

        message = self.LOG_MESSAGE
        serializer = engine.generate_serializer(message)
        instance = LogMessage('Hello, World!')
        self.assertEqual(
            serializer(instance),
            # We're ok with not having a null byte since
            # the length is encoded
            b'\x00\x0dHello, World!',
        )

    def test_generate_deserializer(self):
        message = self.PING
        deserializer = engine.generate_deserializer(message, Ping)
        buffer = int(42).to_bytes(length=1, byteorder='big', signed=False)
        self.assertEqual(deserializer(buffer), Ping(42))

        message = self.FLASH_PAGE
        deserializer = engine.generate_deserializer(message, FlashPage)
        buffer = (
            b'\x00\x00\x12\x34\x00\x00\x56\x78\x00\x02\x00\x00\x9A\xBC\x00\x00\xDE\xF0'
        )
        self.assertEqual(
            deserializer(buffer), FlashPage(0x1234, 0x5678, [0x9ABC, 0xDEF0])
        )

        message = self.LOG_MESSAGE
        deserializer = engine.generate_deserializer(message, LogMessage)
        buffer = b'\x00\x0dHello, World!'
        self.assertEqual(deserializer(buffer), LogMessage('Hello, World!'))
