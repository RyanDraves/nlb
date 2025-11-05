import dataclasses
import enum
import unittest
from typing import Optional, Union

from nlb.buffham import engine
from nlb.buffham import parser
from nlb.buffham import schema_bh


class Verbosity(enum.Enum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2


@dataclasses.dataclass
class Ping:
    ping: int


@dataclasses.dataclass
class FlashPage:
    address: int
    data: list[int]
    read_size: int | None


@dataclasses.dataclass
class LogMessage:
    message: str
    verbosity: Verbosity


@dataclasses.dataclass
class NestedMessage:
    flag: int | None
    inner: LogMessage
    data: list[int]
    nested: Ping | None


@dataclasses.dataclass
class StringLists:
    messages: list[str]
    buffers: list[bytes]


@dataclasses.dataclass
class OptionalTest:
    a: int
    b: int | None
    c: Ping
    d: Union[Ping, None]
    e: float
    f: Optional[float]


class TestEngine(unittest.TestCase):
    PING = parser.Message(
        'Ping',
        [
            parser.Field(
                'ping',
                schema_bh.FieldType.UINT8_T,
            ),
        ],
    )
    FLASH_PAGE = parser.Message(
        'FlashPage',
        [
            parser.Field(
                'address',
                schema_bh.FieldType.UINT32_T,
            ),
            parser.Field(
                'data', schema_bh.FieldType.LIST, schema_bh.FieldType.UINT32_T
            ),
            parser.Field(
                'read_size',
                schema_bh.FieldType.UINT32_T,
                optional=True,
            ),
        ],
    )
    LOG_MESSAGE = parser.Message(
        'LogMessage',
        [
            parser.Field(
                'message',
                schema_bh.FieldType.STRING,
            ),
            parser.Field(
                'verbosity',
                schema_bh.FieldType.ENUM,
            ),
        ],
    )
    NESTED_MESSAGE = parser.Message(
        'NestedMessage',
        [
            parser.Field(
                'flag',
                schema_bh.FieldType.UINT8_T,
                optional=True,
            ),
            parser.Field(
                'inner',
                schema_bh.FieldType.MESSAGE,
                obj_name=parser.Name(LOG_MESSAGE.name, ''),
            ),
            parser.Field(
                'data',
                schema_bh.FieldType.LIST,
                schema_bh.FieldType.INT32_T,
            ),
            parser.Field(
                'nested',
                schema_bh.FieldType.MESSAGE,
                optional=True,
                obj_name=parser.Name(PING.name, ''),
            ),
        ],
    )
    STRING_LISTS = parser.Message(
        'StringLists',
        [
            parser.Field(
                'messages',
                schema_bh.FieldType.LIST,
                schema_bh.FieldType.STRING,
            ),
            parser.Field(
                'buffers',
                schema_bh.FieldType.LIST,
                schema_bh.FieldType.BYTES,
            ),
        ],
    )

    def setUp(self) -> None:
        self.message_registry = {
            ('', self.PING.name): self.PING,
            ('', self.FLASH_PAGE.name): self.FLASH_PAGE,
            ('', self.LOG_MESSAGE.name): self.LOG_MESSAGE,
            ('', self.NESTED_MESSAGE.name): self.NESTED_MESSAGE,
            ('', self.STRING_LISTS.name): self.STRING_LISTS,
        }

    def test_split_optional(self):
        self.assertEqual(
            engine.split_optional(OptionalTest.__dataclass_fields__['a'].type),
            (int, False),
        )
        self.assertEqual(
            engine.split_optional(OptionalTest.__dataclass_fields__['b'].type),
            (int, True),
        )
        self.assertEqual(
            engine.split_optional(OptionalTest.__dataclass_fields__['c'].type),
            (Ping, False),
        )
        self.assertEqual(
            engine.split_optional(OptionalTest.__dataclass_fields__['d'].type),
            (Ping, True),
        )
        self.assertEqual(
            engine.split_optional(OptionalTest.__dataclass_fields__['e'].type),
            (float, False),
        )
        self.assertEqual(
            engine.split_optional(OptionalTest.__dataclass_fields__['f'].type),
            (float, True),
        )

    def test_generate_serializer(self):
        message = self.PING
        serializer = engine.generate_serializer(message, self.message_registry)
        instance = Ping(42)
        self.assertEqual(
            serializer(instance),
            int(42).to_bytes(length=1, byteorder='little', signed=False),
        )

        message = self.FLASH_PAGE
        serializer = engine.generate_serializer(message, self.message_registry)
        instance = FlashPage(0x1234, [0x9ABC, 0xDEF0], 0x5678)
        self.assertEqual(
            serializer(instance),
            b'\x01\x34\x12\x00\x00\x02\x00\xbc\x9a\x00\x00\xf0\xde\x00\x00\x78\x56\x00\x00',
        )

        message = self.LOG_MESSAGE
        serializer = engine.generate_serializer(message, self.message_registry)
        instance = LogMessage('Hello, World!', Verbosity.MEDIUM)
        self.assertEqual(
            serializer(instance),
            # We're ok with not having a null byte since
            # the length is encoded
            b'\x0d\x00Hello, World!\x01',
        )

    def test_generate_nested_serializer(self):
        message = self.NESTED_MESSAGE
        serializer = engine.generate_serializer(message, self.message_registry)
        instance = NestedMessage(
            0x42, LogMessage('Hello, World!', Verbosity.LOW), [-1, -2, -3], Ping(42)
        )
        self.assertEqual(
            serializer(instance),
            b'\x03B\r\x00Hello, World!\x00\x03\x00\xff\xff\xff\xff\xfe\xff\xff\xff\xfd\xff\xff\xff*',
        )

    def test_generate_string_lists_serializer(self):
        message = self.STRING_LISTS
        serializer = engine.generate_serializer(message, self.message_registry)
        instance = StringLists(
            messages=['hello', 'world'],
            buffers=[b'\x01\x02\x03', b'\x04\x05'],
        )
        self.assertEqual(
            serializer(instance),
            b'\x02\x00\x05\x00hello\x05\x00world\x02\x00\x03\x00\x01\x02\x03\x02\x00\x04\x05',
        )

    def test_generate_deserializer(self):
        message = self.PING
        deserializer = engine.generate_deserializer(
            message, self.message_registry, Ping
        )
        buffer = int(42).to_bytes(length=1, byteorder='little', signed=False)
        msg, size = deserializer(buffer)
        self.assertEqual(msg, Ping(42))
        self.assertEqual(size, len(buffer))

        message = self.FLASH_PAGE
        deserializer = engine.generate_deserializer(
            message, self.message_registry, FlashPage
        )
        buffer = b'\x01\x34\x12\x00\x00\x02\x00\xbc\x9a\x00\x00\xf0\xde\x00\x00\x78\x56\x00\x00'
        msg, size = deserializer(buffer)
        self.assertEqual(msg, FlashPage(0x1234, [0x9ABC, 0xDEF0], 0x5678))
        self.assertEqual(size, len(buffer))

        message = self.LOG_MESSAGE
        deserializer = engine.generate_deserializer(
            message, self.message_registry, LogMessage
        )
        buffer = b'\x0d\x00Hello, World!\x02'
        msg, size = deserializer(buffer)
        self.assertEqual(msg, LogMessage('Hello, World!', Verbosity.HIGH))
        self.assertEqual(size, len(buffer))

    def test_generate_nested_deserializer(self):
        message = self.NESTED_MESSAGE
        deserializer = engine.generate_deserializer(
            message, self.message_registry, NestedMessage
        )
        buffer = b'\x03B\r\x00Hello, World!\x02\x03\x00\xff\xff\xff\xff\xfe\xff\xff\xff\xfd\xff\xff\xff*'
        msg, size = deserializer(buffer)
        self.assertEqual(
            msg,
            NestedMessage(
                0x42,
                LogMessage('Hello, World!', Verbosity.HIGH),
                [-1, -2, -3],
                Ping(42),
            ),
        )
        self.assertEqual(size, len(buffer))

    def test_generate_string_lists_deserializer(self):
        message = self.STRING_LISTS
        deserializer = engine.generate_deserializer(
            message, self.message_registry, StringLists
        )
        buffer = b'\x02\x00\x05\x00hello\x05\x00world\x02\x00\x03\x00\x01\x02\x03\x02\x00\x04\x05'
        msg, size = deserializer(buffer)
        self.assertEqual(
            msg,
            StringLists(
                messages=['hello', 'world'],
                buffers=[b'\x01\x02\x03', b'\x04\x05'],
            ),
        )
        self.assertEqual(size, len(buffer))
