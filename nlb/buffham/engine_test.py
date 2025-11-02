import dataclasses
import unittest

from nlb.buffham import engine
from nlb.buffham import parser
from nlb.buffham import schema_bh


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


@dataclasses.dataclass
class NestedMessage:
    flag: int
    inner: LogMessage
    data: list[int]
    nested: Ping


class TestEngine(unittest.TestCase):
    PING = parser.Message(
        'Ping',
        [
            parser.Field('ping', schema_bh.FieldType.UINT8_T, None),
        ],
    )
    FLASH_PAGE = parser.Message(
        'FlashPage',
        [
            parser.Field('address', schema_bh.FieldType.UINT32_T, None),
            parser.Field('read_size', schema_bh.FieldType.UINT32_T, None),
            parser.Field(
                'data', schema_bh.FieldType.LIST, schema_bh.FieldType.UINT32_T
            ),
        ],
    )
    LOG_MESSAGE = parser.Message(
        'LogMessage',
        [
            parser.Field('message', schema_bh.FieldType.STRING, None),
        ],
    )
    NESTED_MESSAGE = parser.Message(
        'NestedMessage',
        [
            parser.Field('flag', schema_bh.FieldType.UINT8_T, None),
            parser.Field('inner', schema_bh.FieldType.MESSAGE, None, LOG_MESSAGE),
            parser.Field('data', schema_bh.FieldType.LIST, schema_bh.FieldType.INT32_T),
            parser.Field('nested', schema_bh.FieldType.MESSAGE, None, PING),
        ],
    )

    def test_generate_serializer(self):
        message = self.PING
        serializer = engine.generate_serializer(message)
        instance = Ping(42)
        self.assertEqual(
            serializer(instance),
            int(42).to_bytes(length=1, byteorder='little', signed=False),
        )

        message = self.FLASH_PAGE
        serializer = engine.generate_serializer(message)
        instance = FlashPage(0x1234, 0x5678, [0x9ABC, 0xDEF0])
        self.assertEqual(
            serializer(instance),
            b'\x34\x12\x00\x00\x78\x56\x00\x00\x02\x00\xbc\x9a\x00\x00\xf0\xde\x00\x00',
        )

        message = self.LOG_MESSAGE
        serializer = engine.generate_serializer(message)
        instance = LogMessage('Hello, World!')
        self.assertEqual(
            serializer(instance),
            # We're ok with not having a null byte since
            # the length is encoded
            b'\x0d\x00Hello, World!',
        )

    def test_generate_nested_serializer(self):
        message = self.NESTED_MESSAGE
        serializer = engine.generate_serializer(message)
        instance = NestedMessage(
            0x42, LogMessage('Hello, World!'), [-1, -2, -3], Ping(42)
        )
        self.assertEqual(
            serializer(instance),
            b'B\r\x00Hello, World!\x03\x00\xff\xff\xff\xff\xfe\xff\xff\xff\xfd\xff\xff\xff*',
        )

    def test_generate_deserializer(self):
        message = self.PING
        deserializer = engine.generate_deserializer(message, Ping)
        buffer = int(42).to_bytes(length=1, byteorder='little', signed=False)
        msg, size = deserializer(buffer)
        self.assertEqual(msg, Ping(42))
        self.assertEqual(size, len(buffer))

        message = self.FLASH_PAGE
        deserializer = engine.generate_deserializer(message, FlashPage)
        buffer = (
            b'\x34\x12\x00\x00\x78\x56\x00\x00\x02\x00\xbc\x9a\x00\x00\xf0\xde\x00\x00'
        )
        msg, size = deserializer(buffer)
        self.assertEqual(msg, FlashPage(0x1234, 0x5678, [0x9ABC, 0xDEF0]))
        self.assertEqual(size, len(buffer))

        message = self.LOG_MESSAGE
        deserializer = engine.generate_deserializer(message, LogMessage)
        buffer = b'\x0d\x00Hello, World!'
        msg, size = deserializer(buffer)
        self.assertEqual(msg, LogMessage('Hello, World!'))
        self.assertEqual(size, len(buffer))

    def test_generate_nested_deserializer(self):
        message = self.NESTED_MESSAGE
        deserializer = engine.generate_deserializer(message, NestedMessage)
        buffer = b'B\r\x00Hello, World!\x03\x00\xff\xff\xff\xff\xfe\xff\xff\xff\xfd\xff\xff\xff*'
        msg, size = deserializer(buffer)
        self.assertEqual(
            msg,
            NestedMessage(0x42, LogMessage('Hello, World!'), [-1, -2, -3], Ping(42)),
        )
        self.assertEqual(size, len(buffer))
