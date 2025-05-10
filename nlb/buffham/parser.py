import dataclasses
import enum
import pathlib
import re
from typing import Generator

# `[\w|\.]+` used to match namespaced names
COMMENT_REGEX = re.compile(r'^\s*#(.*)$')
INLINE_COMMENT_REGEX = re.compile(r'.*#(.*)')
CONSTANT_REGEX = re.compile(r'^constant (\w+) (\w+) = (.+);')
IMPORT_REGEX = re.compile(r'^import ([\w|\.]+);')
FIELD_REGEX = re.compile(r'^\s*([\w|\[|\]|\.]+)\s+(\w+);')
MESSAGE_START_REGEX = re.compile(r'^message (\w+) {')
MESSAGE_END_REGEX = re.compile(r'^}')
TRANSACTION_REGEX = re.compile(r'^transaction (\w+)\[([\w|\.]+), ([\w|\.]+)\]')
PUBLISH_REGEX = re.compile(r'^publish (\w+)\[([\w|\.]+)\]')


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
    namespace: str
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

    @property
    def full_name(self) -> str:
        if not self.namespace:
            return self.name
        return f'{self.namespace}.{self.name}'

    def get_relative_name(self, namespace: str) -> str:
        if namespace == self.namespace:
            return self.name
        return self.full_name


@dataclasses.dataclass
class Transaction:
    name: str
    namespace: str
    request_id: int
    receive: Message
    send: Message
    comments: list[str] = dataclasses.field(default_factory=list)

    @property
    def full_name(self) -> str:
        if not self.namespace:
            return self.name
        return f'{self.namespace}.{self.name}'

    def get_relative_name(self, namespace: str) -> str:
        if namespace == self.namespace:
            return self.name
        return self.full_name


@dataclasses.dataclass
class Publish:
    name: str
    namespace: str
    request_id: int
    send: Message
    comments: list[str] = dataclasses.field(default_factory=list)

    @property
    def full_name(self) -> str:
        if not self.namespace:
            return self.name
        return f'{self.namespace}.{self.name}'

    def get_relative_name(self, namespace: str) -> str:
        if namespace == self.namespace:
            return self.name
        return self.full_name


@dataclasses.dataclass
class Constant:
    name: str
    namespace: str
    type: FieldType
    value: str
    comments: list[str] = dataclasses.field(default_factory=list)
    inline_comment: str | None = None
    references: list[str] = dataclasses.field(default_factory=list)

    @property
    def full_name(self) -> str:
        if not self.namespace:
            return self.name
        return f'{self.namespace}.{self.name}'

    def get_relative_name(self, namespace: str) -> str:
        if namespace == self.namespace:
            return self.name
        return self.full_name


@dataclasses.dataclass
class Buffham:
    name: str
    parent_namespace: str
    messages: list[Message]
    transactions: list[Transaction]
    publishes: list[Publish]
    constants: list[Constant]

    @property
    def namespace(self) -> str:
        if not self.parent_namespace:
            return self.name
        return f'{self.parent_namespace}.{self.name}'


@dataclasses.dataclass
class ParseContext:
    # Maps `[parent_namespace].[name]` to Buffhams
    buffhams: dict[str, Buffham]

    def iter_messages(
        self, local_messages: list[Message]
    ) -> Generator[Message, None, None]:
        """Iterate over all messages in the context."""
        for message in local_messages:
            yield message
        for buffham in self.buffhams.values():
            for message in buffham.messages:
                yield message

    def iter_constants(
        self, local_constants: list[Constant]
    ) -> Generator[Constant, None, None]:
        """Iterate over all constants in the context."""
        for constant in local_constants:
            yield constant
        for buffham in self.buffhams.values():
            for constant in buffham.constants:
                yield constant


class Parser:
    def __init__(self) -> None:
        self._request_id = 0

    @staticmethod
    def parse_field(
        line: str, messages: list[Message], comments: list[str], ctx: ParseContext
    ) -> Field:
        """Parse a field from a line.

        Fields are arranged as `[type] [name];`. Examples:
        - `uint8_t foo;`
        - `string bar;`
        - `list[float32] baz_2;`
        """
        match = FIELD_REGEX.match(line)
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
                message := next(
                    filter(
                        lambda m: m.full_name == pri_type, ctx.iter_messages(messages)
                    ),
                    None,
                )
            ):
                raise ValueError(f'Invalid message name {pri_type}')
            sub_type = None
            pri_type = FieldType.MESSAGE

        # Ensure the sub_type is not iterable
        if sub_type in (FieldType.LIST, FieldType.STRING, FieldType.BYTES):
            raise ValueError('Nested iterables are not supported')

        inline_comment_match = INLINE_COMMENT_REGEX.match(line)
        inline_comment = (
            inline_comment_match.groups()[0] if inline_comment_match else None
        )

        return Field(name, pri_type, sub_type, message, comments, inline_comment)

    @staticmethod
    def parse_message(
        lines: list[str],
        messages: list[Message],
        comments: list[str],
        ctx: ParseContext,
    ) -> Message:
        """Parse a message from a list of lines.

        Messages are arranged as:
        ```
        message [name] {
        [field] (repeated)
        }
        ```
        """
        match = MESSAGE_START_REGEX.match(lines[0])
        if not match:
            raise ValueError(f'Invalid message line: {lines[0]}')

        name = match.groups()[0]
        fields = []
        field_comments = []
        for line in lines[1:-1]:
            if comment_match := COMMENT_REGEX.match(line):
                field_comments.append(comment_match.groups()[0])
            else:
                fields.append(Parser.parse_field(line, messages, field_comments, ctx))
                field_comments = []
        return Message(name, '', fields, comments)

    def parse_transaction(
        self, line: str, messages: list[Message], comments: list[str], ctx: ParseContext
    ) -> Transaction:
        """Parse a transaction from a line.

        Transactions are arranged as:
        - `transaction [name][[receive], [send]]`

        (Note the double brackets)
        """
        match = TRANSACTION_REGEX.match(line)

        if not match:
            raise ValueError(f'Invalid transaction line: {line}')

        name, receive, send = match.groups()
        try:
            receive = next(
                filter(lambda m: m.full_name == receive, ctx.iter_messages(messages))
            )
            send = next(
                filter(lambda m: m.full_name == send, ctx.iter_messages(messages))
            )
        except StopIteration:
            raise ValueError(
                f'Invalid message name(s) {receive=} {send=} in transaction'
            )

        request_id = self._request_id
        self._request_id += 1

        return Transaction(name, '', request_id, receive, send, comments)

    def parse_publish(
        self, line: str, messages: list[Message], comments: list[str], ctx: ParseContext
    ) -> Publish:
        """Parse a publish from a line.

        Publishes are arranged as:
        - `publish [name][[send]]`

        (Note the double brackets)
        """
        match = PUBLISH_REGEX.match(line)

        if not match:
            raise ValueError(f'Invalid publish line: {line}')

        name, send = match.groups()
        try:
            send = next(
                filter(lambda m: m.full_name == send, ctx.iter_messages(messages))
            )
        except StopIteration:
            raise ValueError(f'Invalid message name(s) {send=} in transaction')

        request_id = self._request_id
        self._request_id += 1

        return Publish(name, '', request_id, send, comments)

    @staticmethod
    def parse_message_lines(lines: list[str], ctx: ParseContext) -> list[Message]:
        # Use regex to find all starting indices of messages
        # (i.e. `message [name] {`)
        start_indices = [
            i for i, line in enumerate(lines) if MESSAGE_START_REGEX.match(line)
        ]

        # Find the end of each message
        # (i.e. `}`)
        end_indices = [
            i for i, line in enumerate(lines) if MESSAGE_END_REGEX.match(line)
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
                Parser.parse_message(lines[start : end + 1], messages, comments, ctx)
            )

            prev_end = end

        return messages

    def parse_transaction_lines(
        self, lines: list[str], messages: list[Message], ctx: ParseContext
    ) -> list[Transaction]:
        # Use regex to find all starting indices of transactions
        # (i.e. `transaction [name][[receive], [send]]`)
        indices = [i for i, line in enumerate(lines) if TRANSACTION_REGEX.match(line)]

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

            transactions.append(
                self.parse_transaction(lines[i], messages, comments, ctx)
            )

        return transactions

    def parse_publish_lines(
        self, lines: list[str], messages: list[Message], ctx: ParseContext
    ) -> list[Publish]:
        # Use regex to find all starting indices of publishes
        # (i.e. `transaction [name][[receive], [send]]`)
        indices = [i for i, line in enumerate(lines) if PUBLISH_REGEX.match(line)]

        publishes = []
        comments = []
        comment_index = 0
        for i in indices:
            while comment_index < i:
                if match := COMMENT_REGEX.match(lines[comment_index]):
                    comments.append(match.groups()[0])
                else:
                    comments = []
                comment_index += 1

            publishes.append(self.parse_publish(lines[i], messages, comments, ctx))

        return publishes

    @staticmethod
    def parse_constant(
        line: str, constants: list[Constant], comments: list[str], ctx: ParseContext
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

        inline_comment_match = INLINE_COMMENT_REGEX.match(line)
        inline_comment = (
            inline_comment_match.groups()[0] if inline_comment_match else None
        )

        # Find references to other constants
        references = []
        for constant in ctx.iter_constants(constants):
            if re.match(rf'.*{{{constant.full_name}}}', value):
                references.append(constant.full_name)

        return Constant(name, '', type_, value, comments, inline_comment, references)

    def parse_constant_lines(
        self, lines: list[str], ctx: ParseContext
    ) -> list[Constant]:
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

            constants.append(self.parse_constant(lines[i], constants, comments, ctx))

        return constants

    def parse_imports(self, lines: list[str], ctx: ParseContext) -> None:
        for line in lines:
            if match := IMPORT_REGEX.match(line):
                full_name = match.groups()[0]
                if full_name not in ctx.buffhams:
                    raise ValueError(f'Unknown import {full_name}')

        # Do nothing with the imports, including imports in our context that are not used.

    def parse_file(
        self, file: pathlib.Path, ctx: ParseContext, parent_namespace: str | None = None
    ) -> Buffham:
        # Ensure the request ID is properly set
        self._request_id = max(
            self._request_id,
            max(
                (
                    t.request_id
                    for buffham in ctx.buffhams.values()
                    for t in buffham.transactions + buffham.publishes
                ),
                default=-1,
            )
            + 1,
        )

        if parent_namespace is None:
            parent_namespace = '.'.join(file.parent.parts)

        lines = file.read_text().splitlines()

        self.parse_imports(lines, ctx)
        messages = self.parse_message_lines(lines, ctx)
        transactions = self.parse_transaction_lines(lines, messages, ctx)
        publishes = self.parse_publish_lines(lines, messages, ctx)
        constants = self.parse_constant_lines(lines, ctx)

        bh = Buffham(
            file.stem, parent_namespace, messages, transactions, publishes, constants
        )

        # Insert namespace into messages, transactions, and constants.
        # Deferring this allows not specifying the namespace in the Buffham file for
        # local references.
        for message in messages:
            message.namespace = bh.namespace
        for transaction in transactions:
            transaction.namespace = bh.namespace
        for constant in constants:
            constant.namespace = bh.namespace

        if bh.namespace in ctx.buffhams:
            raise ValueError(f'Duplicate Buffham namespace: {bh.namespace}')
        ctx.buffhams[bh.namespace] = bh

        return bh
