import dataclasses
import enum
import pathlib
import re

COMMENT_REGEX = re.compile(r'^\s*#(.*)$')
CONSTANT_REGEX = re.compile(r'^constant (\w+) (\w+) = (.+);')


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
    MESSAGE = enum.auto()


@dataclasses.dataclass
class Field:
    name: str
    pri_type: FieldType
    # For lists
    sub_type: FieldType | None = None
    # For messages
    message: 'Message | None' = None
    comments: list[str] = dataclasses.field(default_factory=list)
    inline_comment: str | None = None

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


@dataclasses.dataclass
class Message:
    name: str
    fields: list[Field]
    comments: list[str] = dataclasses.field(default_factory=list)

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
    comments: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Constant:
    name: str
    type: FieldType
    value: str
    comments: list[str] = dataclasses.field(default_factory=list)
    inline_comment: str | None = None
    references: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Buffham:
    name: str
    namespace: list[str]
    messages: list[Message]
    transactions: list[Transaction]
    constants: list[Constant]


class Parser:
    def __init__(self) -> None:
        self._request_id = 0

    @staticmethod
    def parse_field(line: str, messages: list[Message], comments: list[str]) -> Field:
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

        if (pri_type_str := pri_type.upper()) in FieldType._member_names_:
            sub_type = None
            pri_type = FieldType[pri_type_str]
            message = None
        elif pri_type.startswith('list['):
            try:
                sub_type = FieldType[pri_type[5:-1].upper()]
            except KeyError:
                raise ValueError(f'Invalid list type {pri_type}')
            pri_type = FieldType.LIST
            message = None
        else:
            if not (
                message := next(filter(lambda m: m.name == pri_type, messages), None)
            ):
                raise ValueError(f'Invalid message name {pri_type}')
            sub_type = None
            pri_type = FieldType.MESSAGE

        # Ensure the sub_type is not iterable
        if sub_type in (FieldType.LIST, FieldType.STRING, FieldType.BYTES):
            raise ValueError('Nested iterables are not supported')

        inline_comment_match = re.compile(r'.*#(.*)').match(line)
        inline_comment = (
            inline_comment_match.groups()[0] if inline_comment_match else None
        )

        return Field(name, pri_type, sub_type, message, comments, inline_comment)

    @staticmethod
    def parse_message(
        lines: list[str], messages: list[Message], comments: list[str]
    ) -> Message:
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
        fields = []
        field_comments = []
        for line in lines[1:-1]:
            if comment_match := COMMENT_REGEX.match(line):
                field_comments.append(comment_match.groups()[0])
            else:
                fields.append(Parser.parse_field(line, messages, field_comments))
                field_comments = []
        return Message(name, fields, comments)

    def parse_transaction(
        self, line: str, messages: list[Message], comments: list[str]
    ) -> Transaction:
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

        return Transaction(name, request_id, receive, send, comments)

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
        comments = []
        comment_index = 0
        for start, end in zip(start_indices, end_indices):
            if start < prev_end:
                raise ValueError('Nested message definitions are not supported')

            while comment_index < start:
                if match := COMMENT_REGEX.match(lines[comment_index]):
                    comments.append(match.groups()[0])
                else:
                    # Clear out comments; no longer matches with the next message
                    comments = []
                comment_index += 1

            messages.append(
                Parser.parse_message(lines[start : end + 1], messages, comments)
            )

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

        transactions = []
        comments = []
        comment_index = 0
        for i in indices:
            while comment_index < i:
                if match := COMMENT_REGEX.match(lines[comment_index]):
                    comments.append(match.groups()[0])
                else:
                    comments = []
                comment_index += 1

            transactions.append(self.parse_transaction(lines[i], messages, comments))

        return transactions

    @staticmethod
    def parse_constant(
        line: str, constants: list[Constant], comments: list[str]
    ) -> Constant:
        """Parse a constant from a line.

        Constants are arranged as:
        - `constant [type] [name] = [value];`
        where `value` may reference other constants

        Examples:
        - `constant uint8_t foo = 0x01;`
        - `constant string bar = "baz";`
        - `constant uint16_t baz = 0x01 + {foo};`
        """
        match = CONSTANT_REGEX.match(line)
        if not match:
            raise ValueError(f'Invalid constant line: {line}')
        type_str, name, value = match.groups()

        try:
            type_ = FieldType[type_str.upper()]
        except KeyError:
            raise ValueError(f'Invalid constant type {type_str}')

        if type_ in (FieldType.LIST, FieldType.MESSAGE, FieldType.BYTES):
            raise ValueError(
                'Constants cannot be messages or have language syntax ambiguity'
            )

        inline_comment_match = re.compile(r'.*#(.*)').match(line)
        inline_comment = (
            inline_comment_match.groups()[0] if inline_comment_match else None
        )

        # Find references to other constants
        references = []
        for constant in constants:
            if '{' + constant.name + '}' in value:
                references.append(constant.name)

        return Constant(name, type_, value, comments, inline_comment, references)

    def parse_constant_lines(self, lines: list[str]) -> list[Constant]:

        indices = [i for i, line in enumerate(lines) if CONSTANT_REGEX.match(line)]

        constants = []
        comments = []
        comment_index = 0
        for i in indices:
            while comment_index < i:
                if match := COMMENT_REGEX.match(lines[comment_index]):
                    comments.append(match.groups()[0])
                else:
                    comments = []
                comment_index += 1

            constants.append(self.parse_constant(lines[i], constants, comments))

        return constants

    def parse_file(self, file: pathlib.Path) -> Buffham:
        self._request_id = 0

        namespace = file.parent.parts

        lines = file.read_text().splitlines()

        messages = self.parse_message_lines(lines)
        transactions = self.parse_transaction_lines(lines, messages)
        constants = self.parse_constant_lines(lines)

        return Buffham(
            file.stem.title(), list(namespace), messages, transactions, constants
        )
