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
FIELD_REGEX = re.compile(r'^\s*(optional)?\s*([\w|\[|\]|\.]+)\s+(\w+);')
MESSAGE_START_REGEX = re.compile(r'^message (\w+) {')
MESSAGE_END_REGEX = re.compile(r'^}')
TRANSACTION_REGEX = re.compile(r'^transaction (\w+)\[([\w|\.]+), ([\w|\.]+)\]')
PUBLISH_REGEX = re.compile(r'^publish (\w+)\[([\w|\.]+)\]')
ENUM_START_REGEX = re.compile(r'^enum (\w+) {')
ENUM_END_REGEX = re.compile(r'^}')
ENUM_VALUE_REGEX = re.compile(r'^\s*(\w+)\s*=\s*(\d+);')

# Size map for each field type
#
# Strings and bytes return 1 as the "size" of each "element"
SIZE_MAP = {
    schema_bh.FieldType.BOOL: 1,
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
    schema_bh.FieldType.MESSAGE: -1,  # N/A
}


FORMAT_MAP = {
    schema_bh.FieldType.BOOL: 'B',
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
    schema_bh.FieldType.MESSAGE: 'N/A',
    schema_bh.FieldType.STRING: 'N/A',
    schema_bh.FieldType.BYTES: 'N/A',
}


class NamedEntry(dataclass.DataclassLike, Protocol):
    @property
    def name(self) -> str: ...


def full_name(entry_name: schema_bh.Name) -> str:
    """Get the full name of the entry."""
    if not entry_name.namespace:
        return entry_name.name
    return f'{entry_name.namespace}.{entry_name.name}'


def relative_name(entry_name: schema_bh.Name, cur_namespace: str) -> str:
    """Get the relative name of the entry from the current namespace."""
    if entry_name.namespace == cur_namespace:
        return entry_name.name
    return full_name(entry_name)


def is_field_iterable(field: schema_bh.Field) -> bool:
    """Check if the field is iterable."""
    return field.pri_type in (
        schema_bh.FieldType.LIST,
        schema_bh.FieldType.STRING,
        schema_bh.FieldType.BYTES,
    )


@dataclasses.dataclass
class Parser:
    # Maps `[parent_namespace].[name]` to Buffhams
    buffhams: dict[str, schema_bh.Buffham] = dataclasses.field(default_factory=dict)
    # Internal request ID counter
    request_id: int = dataclasses.field(default=0)
    # Current full namespace
    cur_namespace: schema_bh.Name = dataclasses.field(
        default_factory=lambda: schema_bh.Name('', '')
    )

    @property
    def cur_buffham(self) -> schema_bh.Buffham:
        """Get the current Buffham being parsed."""
        return self.buffhams[full_name(self.cur_namespace)]

    @property
    def cur_namespace_str(self) -> str:
        """Get the current namespace as a string."""
        return full_name(self.cur_namespace)

    def iter_messages(
        self,
    ) -> Generator[tuple[schema_bh.Message, schema_bh.Name], None, None]:
        """Iterate over all messages in the context."""
        for buffham in self.buffhams.values():
            for message in buffham.messages:
                yield message, schema_bh.Name(message.name, full_name(buffham.name))

    def iter_enums(
        self,
    ) -> Generator[tuple[schema_bh.Enum, schema_bh.Name], None, None]:
        """Iterate over all enums in the context."""
        for buffham in self.buffhams.values():
            for enum in buffham.enums:
                yield enum, schema_bh.Name(enum.name, full_name(buffham.name))

    def iter_constants(
        self,
    ) -> Generator[tuple[schema_bh.Constant, schema_bh.Name], None, None]:
        """Iterate over all constants in the context."""
        for buffham in self.buffhams.values():
            for constant in buffham.constants:
                yield constant, schema_bh.Name(constant.name, full_name(buffham.name))

    def parse_message_field(self, line: str, comments: list[str]) -> schema_bh.Field:
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

        optional = parts[0] is not None
        pri_type = parts[1]
        name = parts[2]

        if (pri_type_str := pri_type.upper()) in schema_bh.FieldType._member_names_:
            sub_type = None
            pri_type = schema_bh.FieldType[pri_type_str]
            obj_name = None
        elif pri_type.startswith('list['):
            sub_type_str = pri_type[5:-1]
            message, message_name = next(
                filter(
                    lambda x: relative_name(x[1], self.cur_namespace_str)
                    == sub_type_str,
                    self.iter_messages(),
                ),
                (None, None),
            )
            if message is not None:
                sub_type = schema_bh.FieldType.MESSAGE
                obj_name = message_name
            elif sub_type_str.upper() in schema_bh.FieldType._member_names_:
                sub_type = schema_bh.FieldType[sub_type_str.upper()]
                obj_name = None
            else:
                raise ValueError(f'Invalid sub-field type {sub_type_str}')
            pri_type = schema_bh.FieldType.LIST
        else:
            message, message_name = next(
                filter(
                    lambda x: relative_name(x[1], self.cur_namespace_str) == pri_type,
                    self.iter_messages(),
                ),
                (None, None),
            )
            enum, enum_name = next(
                filter(
                    lambda x: relative_name(x[1], self.cur_namespace_str) == pri_type,
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
                obj_name = message_name
                pri_type = schema_bh.FieldType.MESSAGE
            else:
                obj_name = enum_name
                pri_type = schema_bh.FieldType.ENUM

        # Ensure the sub_type is not a list
        if sub_type is schema_bh.FieldType.LIST:
            raise ValueError('Nested iterables are not supported')

        inline_comment_match = INLINE_COMMENT_REGEX.match(line)
        inline_comment = (
            inline_comment_match.groups()[0] if inline_comment_match else None
        )

        return schema_bh.Field(
            name,
            pri_type,
            sub_type,
            optional,
            obj_name,
            comments,
            inline_comment,
        )

    def parse_message(
        self,
        lines: list[str],
        comments: list[str],
    ) -> schema_bh.Message:
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
        return schema_bh.Message(name, fields, comments)

    def parse_transaction(
        self, line: str, comments: list[str]
    ) -> schema_bh.Transaction:
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
            receive, receive_name = next(
                filter(
                    lambda x: relative_name(x[1], self.cur_namespace_str) == receive,
                    self.iter_messages(),
                )
            )
            send, send_name = next(
                filter(
                    lambda x: relative_name(x[1], self.cur_namespace_str) == send,
                    self.iter_messages(),
                )
            )
        except StopIteration:
            raise ValueError(
                f'Invalid message name(s) {receive=} {send=} in transaction'
            )

        request_id = self.request_id
        self.request_id += 1

        inline_comment_match = INLINE_COMMENT_REGEX.match(line)
        inline_comment = (
            inline_comment_match.groups()[0] if inline_comment_match else None
        )

        return schema_bh.Transaction(
            name,
            request_id,
            receive_name,
            send_name,
            comments,
            inline_comment,
        )

    def parse_publish(self, line: str, comments: list[str]) -> schema_bh.Publish:
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
            send, send_name = next(
                filter(
                    lambda x: relative_name(x[1], self.cur_namespace_str) == send,
                    self.iter_messages(),
                )
            )
        except StopIteration:
            raise ValueError(f'Invalid message name(s) {send=} in transaction')

        request_id = self.request_id
        self.request_id += 1

        inline_comment_match = INLINE_COMMENT_REGEX.match(line)
        inline_comment = (
            inline_comment_match.groups()[0] if inline_comment_match else None
        )

        return schema_bh.Publish(name, request_id, send_name, comments, inline_comment)

    def parse_constant(self, line: str, comments: list[str]) -> schema_bh.Constant:
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

        # Expand references to other constants
        expanded_value = value
        references = []
        for constant, constant_name in self.iter_constants():
            if re.match(
                rf'.*{{({relative_name(constant_name, self.cur_namespace_str)})}}',
                value,
            ):
                references.append(relative_name(constant_name, self.cur_namespace_str))
                expanded_value = expanded_value.replace(
                    f'{{{relative_name(constant_name, self.cur_namespace_str)}}}',
                    constant.expanded_value,
                )

        return schema_bh.Constant(
            name, type_, value, expanded_value, comments, inline_comment, references
        )

    def parse_enum_field(self, line: str, comments: list[str]) -> schema_bh.EnumField:
        """Parse a single enum field from a line."""
        match = ENUM_VALUE_REGEX.match(line)
        if not match:
            raise ValueError(f'Invalid enum value line: {line}')

        value_name, value_num = match.groups()

        inline_comment_match = INLINE_COMMENT_REGEX.match(line)
        inline_comment = (
            inline_comment_match.groups()[0] if inline_comment_match else None
        )

        return schema_bh.EnumField(value_name, int(value_num), comments, inline_comment)

    def parse_enum(
        self,
        lines: list[str],
        comments: list[str],
    ) -> schema_bh.Enum:
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

        return schema_bh.Enum(name, fields, comments)

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
    ) -> schema_bh.Buffham:
        # Handle binary Buffham files
        if file.suffix == '.bhb':
            bh, _ = schema_bh.Buffham.deserialize(file.read_bytes())
            self.buffhams[full_name(bh.name)] = bh
            self.cur_namespace = bh.name
            self.request_id = (
                max(
                    self.request_id - 1,
                    *(t.request_id for t in bh.transactions),
                    *(p.request_id for p in bh.publishes),
                )
                + 1
            )
            return bh

        # Determine the namespace
        if parent_namespace is None:
            parent_namespace = '.'.join(file.parent.parts)
        name = schema_bh.Name(file.stem, parent_namespace)
        self.cur_namespace = name

        # Insert a new Buffham into the context
        bh = schema_bh.Buffham(name, [], [], [], [], [])
        if full_name(bh.name) in self.buffhams:
            raise ValueError(f'Duplicate Buffham namespace: {bh.name}')
        self.buffhams[full_name(bh.name)] = bh

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
