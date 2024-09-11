import dataclasses
import enum
import pathlib
import re


class FieldType(enum.Enum):
    UINT8_T = enum.auto()
    UINT16_T = enum.auto()
    UINT32_T = enum.auto()
    UINT64_T = enum.auto()
    INT8_T = enum.auto()
    INT16_T = enum.auto()
    INT32_T = enum.auto()
    INT64_T = enum.auto()
    FLOAT32 = enum.auto()
    FLOAT64 = enum.auto()
    STRING = enum.auto()
    BYTES = enum.auto()
    # Some Haskell nerd is going to come along and present a beatiful argument
    # on how terrible my design is, but alas, I do not care.
    LIST = enum.auto()


@dataclasses.dataclass
class Field:
    name: str
    pri_type: FieldType
    # For lists
    sub_type: FieldType | None = None

    @property
    def iterable(self) -> bool:
        """Check if the field is iterable."""
        return self.pri_type in (FieldType.LIST, FieldType.STRING, FieldType.BYTES)

    @property
    def size(self) -> int:
        """Get the size of the field in bytes.

        Returns the `sub_type` size if the field is a list
        and 1 for iterable fields like strings and bytes.
        """
        return {
            FieldType.UINT8_T: 1,
            FieldType.UINT16_T: 2,
            FieldType.UINT32_T: 4,
            FieldType.UINT64_T: 8,
            FieldType.INT8_T: 1,
            FieldType.INT16_T: 2,
            FieldType.INT32_T: 4,
            FieldType.INT64_T: 8,
            FieldType.FLOAT32: 4,
            FieldType.FLOAT64: 8,
            FieldType.STRING: 1,
            FieldType.BYTES: 1,
        }[self.sub_type or self.pri_type]

    @property
    def format(self) -> str:
        """Get the `struct` format string for the field.

        Returns the `sub_type` format if the field is a list
        and raises KeyError for iterable fields like strings and bytes,
        as `struct` is not used to encode them.
        """
        return {
            FieldType.UINT8_T: 'B',
            FieldType.UINT16_T: 'H',
            FieldType.UINT32_T: 'I',
            FieldType.UINT64_T: 'Q',
            FieldType.INT8_T: 'b',
            FieldType.INT16_T: 'h',
            FieldType.INT32_T: 'i',
            FieldType.INT64_T: 'q',
            FieldType.FLOAT32: 'f',
            FieldType.FLOAT64: 'd',
        }[self.sub_type or self.pri_type]

    @property
    def py_type(self) -> str:
        """Get the Python type hint for the field."""
        type_map = {
            FieldType.UINT8_T: 'int',
            FieldType.UINT16_T: 'int',
            FieldType.UINT32_T: 'int',
            FieldType.UINT64_T: 'int',
            FieldType.INT8_T: 'int',
            FieldType.INT16_T: 'int',
            FieldType.INT32_T: 'int',
            FieldType.INT64_T: 'int',
            FieldType.FLOAT32: 'float',
            FieldType.FLOAT64: 'float',
            FieldType.STRING: 'str',
            FieldType.BYTES: 'bytes',
        }

        if self.pri_type is FieldType.LIST:
            assert self.sub_type is not None
            return f'list[{type_map[self.sub_type]}]'

        return type_map[self.pri_type]

    @property
    def cpp_type(self) -> str:
        """Get the C++ type for the field."""
        type_map = {
            FieldType.UINT8_T: 'uint8_t',
            FieldType.UINT16_T: 'uint16_t',
            FieldType.UINT32_T: 'uint32_t',
            FieldType.UINT64_T: 'uint64_t',
            FieldType.INT8_T: 'int8_t',
            FieldType.INT16_T: 'int16_t',
            FieldType.INT32_T: 'int32_t',
            FieldType.INT64_T: 'int64_t',
            FieldType.FLOAT32: 'float',
            FieldType.FLOAT64: 'double',
            FieldType.STRING: 'std::string',
            FieldType.BYTES: 'std::vector<uint8_t>',
        }

        if self.pri_type is FieldType.LIST:
            assert self.sub_type is not None
            return f'std::vector<{type_map[self.sub_type]}>'

        return type_map[self.pri_type]


@dataclasses.dataclass
class Message:
    name: str
    fields: list[Field]

    @property
    def size(self) -> int | None:
        # XXX: Unused
        size = 0
        for f in self.fields:
            if f.size is None:
                return None

            size += f.size

        return size


@dataclasses.dataclass
class Transaction:
    name: str
    request_id: int
    receive: Message
    send: Message


@dataclasses.dataclass
class Buffham:
    name: str
    namespace: list[str]
    messages: list[Message]
    transactions: list[Transaction]


class Parser:
    def __init__(self) -> None:
        self._request_id = 0

    @staticmethod
    def parse_field(line: str) -> Field:
        """Parse a field from a line.

        Fields are arranged as `[type] [name];`. Examples:
        - `uint8_t foo;`
        - `string bar;`
        - `list[float32] baz_2;`
        """
        match = re.compile(r'\s*([\w|\[|\]]+)\s+(\w+);').match(line)
        if not match:
            raise ValueError(f'Invalid field line: {line}')
        parts = match.groups()

        pri_type = parts[0]
        name = parts[1]

        try:
            pri_type.startswith('list[')
            if pri_type.startswith('list['):
                sub_type = FieldType[pri_type[5:-1].upper()]
                pri_type = FieldType.LIST
            else:
                sub_type = None
                pri_type = FieldType[pri_type.upper()]
        except KeyError:
            raise ValueError(f'Invalid field type: {pri_type}')

        # Ensure the sub_type is not iterable
        if sub_type in (FieldType.LIST, FieldType.STRING, FieldType.BYTES):
            raise ValueError('Nested iterables are not supported')

        return Field(name, pri_type, sub_type)

    @staticmethod
    def parse_message(lines: list[str]) -> Message:
        """Parse a message from a list of lines.

        Messages are arranged as:
        ```
        message [name] {
        [field] (repeated)
        }
        ```
        """
        match = re.compile(r'^message (\w+) {').match(lines[0])
        if not match:
            raise ValueError(f'Invalid message line: {lines[0]}')

        name = match.groups()[0]
        fields = [Parser.parse_field(line) for line in lines[1:-1]]
        return Message(name, fields)

    def parse_transaction(self, line: str, messages: list[Message]) -> Transaction:
        """Parse a transaction from a line.

        Transactions are arranged as:
        - `transaction [name][[receive], [send]]`

        (Note the double brackets)
        """
        match = re.compile(r'^transaction (\w+)\[(\w+), (\w+)\]').match(line)

        if not match:
            raise ValueError(f'Invalid transaction line: {line}')

        name, receive, send = match.groups()
        try:
            receive = next(filter(lambda m: m.name == receive, messages))
            send = next(filter(lambda m: m.name == send, messages))
        except StopIteration:
            raise ValueError(
                f'Invalid message name(s) {receive=} {send=} in transaction'
            )

        request_id = self._request_id
        self._request_id += 1

        return Transaction(name, request_id, receive, send)

    @staticmethod
    def parse_message_lines(lines: list[str]) -> list[Message]:
        # Use regex to find all starting indices of messages
        # (i.e. `message [name] {`)
        start_indices = [
            i
            for i, line in enumerate(lines)
            if re.compile(r'^message \w+ {').match(line)
        ]

        # Find the end of each message
        # (i.e. `}`)
        end_indices = [
            i for i, line in enumerate(lines) if re.compile(r'^}').match(line)
        ]

        assert len(start_indices) == len(end_indices), 'Mismatched message brackets'

        # Pair the start and end indices and parse the message
        prev_end = -1
        messages = []
        for start, end in zip(start_indices, end_indices):
            if start < prev_end:
                raise ValueError('Nested messages are not supported')

            messages.append(Parser.parse_message(lines[start : end + 1]))

            prev_end = end

        return messages

    def parse_transaction_lines(
        self, lines: list[str], messages: list[Message]
    ) -> list[Transaction]:
        # Use regex to find all starting indices of transactions
        # (i.e. `transaction [name][[receive], [send]]`)
        indices = [
            i
            for i, line in enumerate(lines)
            if re.compile(r'^transaction \w+\[\w+, \w+\]').match(line)
        ]

        return [self.parse_transaction(lines[i], messages) for i in indices]

    def parse_file(self, file: pathlib.Path) -> Buffham:
        self._request_id = 0

        namespace = file.parent.parts

        lines = file.read_text().split('\n')
        # Remove comment lines; in-line comments are valid per the regex
        # patterns, but block comments are not.
        lines = [line for line in lines if not re.compile(r'^\s*#').match(line)]

        messages = self.parse_message_lines(lines)
        transactions = self.parse_transaction_lines(lines, messages)

        return Buffham(file.stem.title(), list(namespace), messages, transactions)
