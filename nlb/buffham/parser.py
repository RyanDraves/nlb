import dataclasses
import pathlib
import re
from typing import Callable, Generator, Protocol

from nlb.buffham import schema_bh
from nlb.util import dataclass

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
ENUM_START_REGEX = re.compile(r'^enum (\w+) {')
ENUM_END_REGEX = re.compile(r'^}')
ENUM_VALUE_REGEX = re.compile(r'^\s*(\w+)\s*=\s*(\d+);')


class NamedEntry(dataclass.DataclassLike, Protocol):
    @property
    def name(self) -> str: ...


@dataclasses.dataclass
class Field:
    name: str
    pri_type: schema_bh.FieldType
    # For lists
    sub_type: schema_bh.FieldType | None = None
    # For messages
    message: 'Message | None' = None
    message_ns: str | None = None
    # For enums
    enum: 'Enum | None' = None
    enum_ns: str | None = None
    comments: list[str] = dataclasses.field(default_factory=list)
    inline_comment: str | None = None

    @property
    def iterable(self) -> bool:
        """Check if the field is iterable."""
        return self.pri_type in (
            schema_bh.FieldType.LIST,
            schema_bh.FieldType.STRING,
            schema_bh.FieldType.BYTES,
        )

    @property
    def size(self) -> int:
        """Get the size of the field in bytes.

        Returns the `sub_type` size if the field is a list
        and 1 for iterable fields like strings and bytes.
        """
        return {
            schema_bh.FieldType.UINT8_T: 1,
            schema_bh.FieldType.UINT16_T: 2,
            schema_bh.FieldType.UINT32_T: 4,
            schema_bh.FieldType.UINT64_T: 8,
            schema_bh.FieldType.INT8_T: 1,
            schema_bh.FieldType.INT16_T: 2,
            schema_bh.FieldType.INT32_T: 4,
            schema_bh.FieldType.INT64_T: 8,
            schema_bh.FieldType.FLOAT32: 4,
            schema_bh.FieldType.FLOAT64: 8,
            schema_bh.FieldType.STRING: 1,
            schema_bh.FieldType.BYTES: 1,
            schema_bh.FieldType.ENUM: 1,
        }[self.sub_type or self.pri_type]

    @property
    def format(self) -> str:
        """Get the `struct` format string for the field.

        Returns the `sub_type` format if the field is a list
        and raises KeyError for iterable fields like strings and bytes,
        as `struct` is not used to encode them.
        """
        return {
            schema_bh.FieldType.UINT8_T: 'B',
            schema_bh.FieldType.UINT16_T: 'H',
            schema_bh.FieldType.UINT32_T: 'I',
            schema_bh.FieldType.UINT64_T: 'Q',
            schema_bh.FieldType.INT8_T: 'b',
            schema_bh.FieldType.INT16_T: 'h',
            schema_bh.FieldType.INT32_T: 'i',
            schema_bh.FieldType.INT64_T: 'q',
            schema_bh.FieldType.FLOAT32: 'f',
            schema_bh.FieldType.FLOAT64: 'd',
            schema_bh.FieldType.ENUM: 'B',
        }[self.sub_type or self.pri_type]


@dataclasses.dataclass
class Message:
    name: str
    fields: list[Field]
    comments: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Transaction:
    name: str
    request_id: int
    receive: Message
    receive_ns: str
    send: Message
    send_ns: str
    comments: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Publish:
    name: str
    request_id: int
    send: Message
    comments: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Constant:
    name: str
    type: schema_bh.FieldType
    value: str
    comments: list[str] = dataclasses.field(default_factory=list)
    inline_comment: str | None = None
    references: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class EnumField:
    name: str
    value: int
    comments: list[str] = dataclasses.field(default_factory=list)
    inline_comment: str | None = None


@dataclasses.dataclass
class Enum:
    name: str
    fields: list[EnumField]
    comments: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Buffham:
    name: str
    parent_namespace: str
    messages: list[Message] = dataclasses.field(default_factory=list)
    transactions: list[Transaction] = dataclasses.field(default_factory=list)
    publishes: list[Publish] = dataclasses.field(default_factory=list)
    constants: list[Constant] = dataclasses.field(default_factory=list)
    enums: list[Enum] = dataclasses.field(default_factory=list)

    @property
    def namespace(self) -> str:
        if not self.parent_namespace:
            return self.name
        return f'{self.parent_namespace}.{self.name}'


def full_name(entry: NamedEntry, namespace: str) -> str:
    """Get the full name of the entry."""
    return f'{namespace}.{entry.name}'


def relative_name(entry: NamedEntry, entry_namespace: str, cur_namespace: str) -> str:
    """Get the relative name of the entry from the current namespace."""
    if entry_namespace == cur_namespace:
        return entry.name
    return full_name(entry, entry_namespace)


@dataclasses.dataclass
class Parser:
    # Maps `[parent_namespace].[name]` to Buffhams
    buffhams: dict[str, Buffham] = dataclasses.field(default_factory=dict)
    # Internal request ID counter
    request_id: int = dataclasses.field(default=0)
    # Current full namespace
    cur_namespace: str = dataclasses.field(default='')

    @property
    def cur_buffham(self) -> Buffham:
        """Get the current Buffham being parsed."""
        return self.buffhams[self.cur_namespace]

    def iter_messages(self) -> Generator[tuple[Message, str], None, None]:
        """Iterate over all messages in the context."""
        for buffham in self.buffhams.values():
            for message in buffham.messages:
                yield message, buffham.namespace

    def iter_enums(self) -> Generator[tuple[Enum, str], None, None]:
        """Iterate over all enums in the context."""
        for buffham in self.buffhams.values():
            for enum in buffham.enums:
                yield enum, buffham.namespace

    def iter_constants(self) -> Generator[tuple[Constant, str], None, None]:
        """Iterate over all constants in the context."""
        for buffham in self.buffhams.values():
            for constant in buffham.constants:
                yield constant, buffham.namespace

    def parse_message_field(self, line: str, comments: list[str]) -> Field:
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

        if (pri_type_str := pri_type.upper()) in schema_bh.FieldType._member_names_:
            sub_type = None
            pri_type = schema_bh.FieldType[pri_type_str]
            message = None
            message_ns = None
            enum = None
            enum_ns = None
        elif pri_type.startswith('list['):
            try:
                sub_type = schema_bh.FieldType[pri_type[5:-1].upper()]
            except KeyError:
                raise ValueError(f'Invalid list type {pri_type}')
            pri_type = schema_bh.FieldType.LIST
            message = None
            message_ns = None
            enum = None
            enum_ns = None
        else:
            message, message_ns = next(
                filter(
                    lambda x: relative_name(x[0], x[1], self.cur_namespace) == pri_type,
                    self.iter_messages(),
                ),
                (None, None),
            )
            enum, enum_ns = next(
                filter(
                    lambda x: relative_name(x[0], x[1], self.cur_namespace) == pri_type,
                    self.iter_enums(),
                ),
                (None, None),
            )
            if message is None and enum is None:
                raise ValueError(f'Invalid field type {pri_type}')
            if message is not None and enum is not None:
                raise ValueError(f'Field type {pri_type} is both a message and an enum')
            sub_type = None
            if message is not None:
                pri_type = schema_bh.FieldType.MESSAGE
            else:
                pri_type = schema_bh.FieldType.ENUM

        # Ensure the sub_type is not iterable
        if sub_type in (
            schema_bh.FieldType.LIST,
            schema_bh.FieldType.STRING,
            schema_bh.FieldType.BYTES,
        ):
            raise ValueError('Nested iterables are not supported')

        inline_comment_match = INLINE_COMMENT_REGEX.match(line)
        inline_comment = (
            inline_comment_match.groups()[0] if inline_comment_match else None
        )

        return Field(
            name,
            pri_type,
            sub_type,
            message,
            message_ns,
            enum,
            enum_ns,
            comments,
            inline_comment,
        )

    def parse_message(
        self,
        lines: list[str],
        comments: list[str],
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
                fields.append(self.parse_message_field(line, field_comments))
                field_comments = []
        return Message(name, fields, comments)

    def parse_transaction(self, line: str, comments: list[str]) -> Transaction:
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
            receive, receive_ns = next(
                filter(
                    lambda x: relative_name(x[0], x[1], self.cur_namespace) == receive,
                    self.iter_messages(),
                )
            )
            send, send_ns = next(
                filter(
                    lambda x: relative_name(x[0], x[1], self.cur_namespace) == send,
                    self.iter_messages(),
                )
            )
        except StopIteration:
            raise ValueError(
                f'Invalid message name(s) {receive=} {send=} in transaction'
            )

        request_id = self.request_id
        self.request_id += 1

        return Transaction(
            name, request_id, receive, receive_ns, send, send_ns, comments
        )

    def parse_publish(self, line: str, comments: list[str]) -> Publish:
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
            send, _ = next(
                filter(
                    lambda x: relative_name(x[0], x[1], self.cur_namespace) == send,
                    self.iter_messages(),
                )
            )
        except StopIteration:
            raise ValueError(f'Invalid message name(s) {send=} in transaction')

        request_id = self.request_id
        self.request_id += 1

        return Publish(name, request_id, send, comments)

    def parse_constant(self, line: str, comments: list[str]) -> Constant:
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
            type_ = schema_bh.FieldType[type_str.upper()]
        except KeyError:
            raise ValueError(f'Invalid constant type {type_str}')

        if type_ in (
            schema_bh.FieldType.LIST,
            schema_bh.FieldType.MESSAGE,
            schema_bh.FieldType.BYTES,
        ):
            raise ValueError(
                'Constants cannot be messages or have language syntax ambiguity'
            )

        inline_comment_match = INLINE_COMMENT_REGEX.match(line)
        inline_comment = (
            inline_comment_match.groups()[0] if inline_comment_match else None
        )

        # Find references to other constants
        references = []
        for constant, ns in self.iter_constants():
            if re.match(
                rf'.*{{{relative_name(constant, ns, self.cur_namespace)}}}', value
            ):
                references.append(relative_name(constant, ns, self.cur_namespace))

        return Constant(name, type_, value, comments, inline_comment, references)

    def parse_enum_field(self, line: str, comments: list[str]) -> EnumField:
        """Parse a single enum field from a line."""
        match = ENUM_VALUE_REGEX.match(line)
        if not match:
            raise ValueError(f'Invalid enum value line: {line}')

        value_name, value_num = match.groups()

        inline_comment_match = INLINE_COMMENT_REGEX.match(line)
        inline_comment = (
            inline_comment_match.groups()[0] if inline_comment_match else None
        )

        return EnumField(value_name, int(value_num), comments, inline_comment)

    def parse_enum(
        self,
        lines: list[str],
        comments: list[str],
    ) -> Enum:
        """Parse an enum from a list of lines.

        Enums are arranged as:
        ```
        enum [name] {
        [value] (repeated)
        }
        ```
        """
        match = ENUM_START_REGEX.match(lines[0])
        if not match:
            raise ValueError(f'Invalid enum start line: {lines[0]}')

        name = match.groups()[0]
        fields = []
        field_comments = []
        for line in lines[1:-1]:
            if comment_match := COMMENT_REGEX.match(line):
                field_comments.append(comment_match.groups()[0])
            else:
                fields.append(self.parse_enum_field(line, field_comments))
                field_comments = []

        return Enum(name, fields, comments)

    def parse_singleline_definition[T: NamedEntry](
        self,
        lines: list[str],
        regex: re.Pattern,
        parse_fn: Callable[[str, list[str]], T],
        bh_entry: list[T],
    ) -> None:
        # Use regex to find all starting indices of definitions
        # (i.e. `message [name] {`)
        indices = [i for i, line in enumerate(lines) if regex.match(line)]

        comments = []
        comment_index = 0
        for i in indices:
            while comment_index < i:
                if match := COMMENT_REGEX.match(lines[comment_index]):
                    comments.append(match.groups()[0])
                else:
                    comments = []
                comment_index += 1

            bh_entry.append(parse_fn(lines[i], comments))

    def parse_multiline_definition[T: NamedEntry](
        self,
        lines: list[str],
        start_regex: re.Pattern,
        end_regex: re.Pattern,
        parse_fn: Callable[[list[str], list[str]], T],
        bh_entry: list[T],
    ) -> None:
        # Use regex to find all starting indices of definitions
        # (i.e. `message [name] {`)
        start_indices = [i for i, line in enumerate(lines) if start_regex.match(line)]

        # Find the end of each definition
        # (i.e. `}`)
        end_indices = [i for i, line in enumerate(lines) if end_regex.match(line)]

        prev_end = -1
        comments = []
        comment_index = 0
        for start in start_indices:
            if start < prev_end:
                raise ValueError('Nested definitions are not supported')

            end = next((e for e in end_indices if e > start), None)
            if end is None:
                raise ValueError('Mismatched brackets')

            while comment_index < start:
                if match := COMMENT_REGEX.match(lines[comment_index]):
                    comments.append(match.groups()[0])
                else:
                    # Clear out comments; no longer matches with the next definition
                    comments = []
                comment_index += 1

            bh_entry.append(parse_fn(lines[start : end + 1], comments))

            prev_end = end

    def parse_imports(self, lines: list[str]) -> None:
        for line in lines:
            if match := IMPORT_REGEX.match(line):
                full_name = match.groups()[0]
                if full_name not in self.buffhams:
                    raise ValueError(f'Unknown import {full_name}')

        # Do nothing with the imports, including imports in our context that are not used.

    def parse_file(
        self, file: pathlib.Path, parent_namespace: str | None = None
    ) -> Buffham:
        # Determine the namespace
        if parent_namespace is None:
            parent_namespace = '.'.join(file.parent.parts)
        name = file.stem
        namespace = f'{parent_namespace}.{name}' if parent_namespace else name
        self.cur_namespace = namespace

        # Insert a new Buffham into the context
        bh = Buffham(name=file.stem, parent_namespace=parent_namespace)
        if bh.namespace in self.buffhams:
            raise ValueError(f'Duplicate Buffham namespace: {bh.namespace}')
        self.buffhams[bh.namespace] = bh

        lines = file.read_text().splitlines()

        self.parse_imports(lines)
        # Enums must be parsed before messages
        self.parse_multiline_definition(
            lines,
            ENUM_START_REGEX,
            ENUM_END_REGEX,
            self.parse_enum,
            bh.enums,
        )
        self.parse_multiline_definition(
            lines,
            MESSAGE_START_REGEX,
            MESSAGE_END_REGEX,
            self.parse_message,
            bh.messages,
        )
        self.parse_singleline_definition(
            lines,
            TRANSACTION_REGEX,
            self.parse_transaction,
            bh.transactions,
        )
        self.parse_singleline_definition(
            lines,
            PUBLISH_REGEX,
            self.parse_publish,
            bh.publishes,
        )
        self.parse_singleline_definition(
            lines,
            CONSTANT_REGEX,
            self.parse_constant,
            bh.constants,
        )

        return bh
