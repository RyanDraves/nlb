import pathlib
import unittest

from nlb.buffham import parser
from nlb.buffham import schema_bh


class TestParserSimple(unittest.TestCase):
    def setUp(self) -> None:
        self.ctx = parser.Parser(
            {'test': parser.Buffham('test', '')}, cur_namespace='test'
        )

    def test_parse_field(self):
        # Simple field
        field = '    uint8_t foo;'
        parsed = self.ctx.parse_message_field(field, [])
        self.assertEqual(
            parsed,
            schema_bh.Field(
                'foo',
                schema_bh.FieldType.UINT8_T,
                None,
                False,
                None,
                [],
                None,
            ),
        )

        # Field with inline comment
        field = 'float64 bar;  # inline comment'
        parsed = self.ctx.parse_message_field(field, [])
        self.assertEqual(
            parsed,
            schema_bh.Field(
                'bar',
                schema_bh.FieldType.FLOAT64,
                None,
                False,
                None,
                [],
                ' inline comment',
            ),
        )

        # List field
        field = 'list[uint32_t] baz_2;'
        parsed = self.ctx.parse_message_field(field, ['some other', 'read-in comments'])
        self.assertEqual(
            parsed,
            schema_bh.Field(
                'baz_2',
                schema_bh.FieldType.LIST,
                schema_bh.FieldType.UINT32_T,
                False,
                None,
                ['some other', 'read-in comments'],
                None,
            ),
        )

        # List of strings
        field = 'list[string] string_list;'
        parsed = self.ctx.parse_message_field(field, [])
        self.assertEqual(
            parsed,
            schema_bh.Field(
                'string_list',
                schema_bh.FieldType.LIST,
                schema_bh.FieldType.STRING,
                False,
                None,
                [],
                None,
            ),
        )

        # List of messages
        message = parser.Message('MyMessage', [])
        self.ctx.cur_buffham.messages.append(message)
        field = 'list[MyMessage] message_list;'
        parsed = self.ctx.parse_message_field(field, [])
        self.assertEqual(
            parsed,
            schema_bh.Field(
                'message_list',
                schema_bh.FieldType.LIST,
                schema_bh.FieldType.MESSAGE,
                False,
                schema_bh.Name(message.name, 'test'),
                [],
                None,
            ),
        )

        # Optional field
        field = 'optional list[uint8_t] optional_field;  # optional field'
        parsed = self.ctx.parse_message_field(field, [])
        self.assertEqual(
            parsed,
            schema_bh.Field(
                'optional_field',
                schema_bh.FieldType.LIST,
                schema_bh.FieldType.UINT8_T,
                True,
                None,
                [],
                ' optional field',
            ),
        )

        # Invalid list-of-lists
        field = 'list[list[uint32_t]] baz_3;'
        with self.assertRaises(ValueError):
            self.ctx.parse_message_field(field, [])

        # Malformed list
        field = 'list[uint32_t baz_4;'
        with self.assertRaises(ValueError):
            self.ctx.parse_message_field(field, [])

        # Message field
        field = 'MyMessage baz_5;'
        my_message = parser.Message('MyMessage', [])
        self.ctx.cur_buffham.messages.append(my_message)
        parsed = self.ctx.parse_message_field(field, [])
        self.assertEqual(
            parsed,
            schema_bh.Field(
                'baz_5',
                schema_bh.FieldType.MESSAGE,
                None,
                False,
                schema_bh.Name(my_message.name, 'test'),
                [],
                None,
            ),
        )

        # Non-existent message field
        field = 'NonexistantMessage baz_6;'
        with self.assertRaises(ValueError):
            self.ctx.parse_message_field(field, [])

    def test_parse_message(self):
        message = [
            'message Ping {',
            '    uint8_t ping;',
            '}',
        ]
        parsed = self.ctx.parse_message(message, [])
        self.assertEqual(
            parsed,
            parser.Message(
                'Ping',
                [
                    schema_bh.Field(
                        'ping',
                        schema_bh.FieldType.UINT8_T,
                        None,
                        False,
                        None,
                        [],
                        None,
                    )
                ],
            ),
        )

        message = [
            'message FlashPage {  ',
            '    uint32_t address;',
            '    uint32_t read_size;  # inline comment',
            '    # out-of-line comment',
            '    list[uint32_t] data;',
            '}  # inline comment',
        ]
        parsed = self.ctx.parse_message(message, [])
        self.assertEqual(
            parsed,
            parser.Message(
                'FlashPage',
                [
                    schema_bh.Field(
                        'address',
                        schema_bh.FieldType.UINT32_T,
                        None,
                        False,
                        None,
                        [],
                        None,
                    ),
                    schema_bh.Field(
                        'read_size',
                        schema_bh.FieldType.UINT32_T,
                        None,
                        False,
                        None,
                        [],
                        ' inline comment',
                    ),
                    schema_bh.Field(
                        'data',
                        schema_bh.FieldType.LIST,
                        schema_bh.FieldType.UINT32_T,
                        False,
                        None,
                        [' out-of-line comment'],
                        None,
                    ),
                ],
            ),
        )

        message = [
            'message LogMessage {',
            'we do a little mischief',
            '}',
        ]
        with self.assertRaises(ValueError):
            self.ctx.parse_message(message, [])

        # Nested message
        message = [
            'message Outer {',
            '    Inner inner;',
            '}',
        ]
        inner = parser.Message('Inner', [])
        self.ctx.cur_buffham.messages.append(inner)
        parsed = self.ctx.parse_message(message, [])
        self.assertEqual(
            parsed,
            parser.Message(
                'Outer',
                [
                    schema_bh.Field(
                        'inner',
                        schema_bh.FieldType.MESSAGE,
                        None,
                        False,
                        schema_bh.Name(inner.name, 'test'),
                        [],
                        None,
                    )
                ],
            ),
        )

        message = [
            'message Outer {',
            '    DoesNotExist inner;',
            '}',
        ]
        with self.assertRaises(ValueError):
            self.ctx.parse_message(message, [])

    def test_parse_transaction(self):
        transaction = 'transaction ping[Ping, LogMessage];'
        receive = parser.Message(
            'Ping',
            [
                schema_bh.Field(
                    'ping',
                    schema_bh.FieldType.UINT8_T,
                    None,
                    False,
                    None,
                    [],
                    None,
                )
            ],
        )
        send = parser.Message(
            'LogMessage',
            [
                schema_bh.Field(
                    'message',
                    schema_bh.FieldType.STRING,
                    None,
                    False,
                    None,
                    [],
                    None,
                )
            ],
        )
        self.ctx.cur_buffham.messages.extend([receive, send])
        parsed = self.ctx.parse_transaction(transaction, ['some other comment'])
        self.assertEqual(
            parsed,
            schema_bh.Transaction(
                'ping',
                0,
                schema_bh.Name(receive.name, 'test'),
                schema_bh.Name(send.name, 'test'),
                ['some other comment'],
                None,
            ),
        )

        transaction = 'transaction flash_page[Ping, Ping];  # inline comment'
        parsed = self.ctx.parse_transaction(transaction, [])
        self.assertEqual(
            parsed,
            schema_bh.Transaction(
                'flash_page',
                1,
                schema_bh.Name(receive.name, 'test'),
                schema_bh.Name(receive.name, 'test'),
                comments=[],
                inline_comment=' inline comment',
            ),
        )

        transaction = 'transaction flash_page[Ping, InvalidMessage];'
        with self.assertRaises(ValueError):
            self.ctx.parse_transaction(transaction, [])

        transaction = 'transaction flash_page[Ping, Ping'
        with self.assertRaises(ValueError):
            self.ctx.parse_transaction(transaction, [])

    def test_parse_publish(self):
        publish = 'publish log[LogMessage];'
        log_msg = parser.Message(
            'LogMessage',
            [
                schema_bh.Field(
                    'message',
                    schema_bh.FieldType.STRING,
                    None,
                    False,
                    None,
                    [],
                    None,
                )
            ],
        )
        self.ctx.cur_buffham.messages.append(log_msg)
        parsed = self.ctx.parse_publish(publish, ['some other comment'])
        self.assertEqual(
            parsed,
            schema_bh.Publish(
                'log',
                0,
                schema_bh.Name(log_msg.name, 'test'),
                ['some other comment'],
                None,
            ),
        )

        publish = 'publish ping_pong[Ping];  # inline comment'
        ping = parser.Message(
            'Ping',
            [
                schema_bh.Field(
                    'pong',
                    schema_bh.FieldType.UINT8_T,
                    None,
                    False,
                    None,
                    [],
                    None,
                )
            ],
        )
        self.ctx.cur_buffham.messages.append(ping)
        parsed = self.ctx.parse_publish(publish, [])
        self.assertEqual(
            parsed,
            schema_bh.Publish(
                'ping_pong',
                1,
                schema_bh.Name(ping.name, 'test'),
                comments=[],
                inline_comment=' inline comment',
            ),
        )

        publish = 'publish noise[InvalidMessage];'
        with self.assertRaises(ValueError):
            self.ctx.parse_publish(publish, [])

        publish = 'publish noise[Ping'
        with self.assertRaises(ValueError):
            self.ctx.parse_publish(publish, [])

    def test_parse_constant(self):
        constant = 'constant uint8_t foo = 0x01;'
        parsed = self.ctx.parse_constant(constant, [])
        self.assertEqual(
            parsed,
            schema_bh.Constant(
                'foo',
                schema_bh.FieldType.UINT8_T,
                '0x01',
                [],
                None,
                [],
            ),
        )

        constant = 'constant uint32_t bar = 0x12345678;  # inline comment'
        parsed = self.ctx.parse_constant(constant, [])
        bar = schema_bh.Constant(
            'bar',
            schema_bh.FieldType.UINT32_T,
            '0x12345678',
            [],
            ' inline comment',
            [],
        )
        self.ctx.cur_buffham.constants.append(bar)
        self.assertEqual(
            parsed,
            bar,
        )

        constant = 'constant uint32_t baz = 0x1 + {bar};'
        parsed = self.ctx.parse_constant(constant, ['some other comment'])
        self.assertEqual(
            parsed,
            schema_bh.Constant(
                'baz',
                schema_bh.FieldType.UINT32_T,
                '0x1 + {bar}',
                ['some other comment'],
                None,
                ['bar'],
            ),
        )

        constant = 'constant uint32_t baz = 0x12345678  # missing semicolon'
        with self.assertRaises(ValueError):
            self.ctx.parse_constant(constant, [])

    def test_parse_enum(self):
        enum_lines = [
            'enum SampleEnum {',
            '    A = 0;  # inline on A',
            '    # Comment on B',
            '    B = 1;',
            '}',
        ]
        comments = [' Enum comment line 1', ' Enum comment line 2']
        parsed = self.ctx.parse_enum(enum_lines, comments)
        self.assertEqual(
            parsed,
            parser.Enum(
                'SampleEnum',
                [
                    schema_bh.EnumField('A', 0, [], ' inline on A'),
                    schema_bh.EnumField('B', 1, [' Comment on B'], None),
                ],
                comments,
            ),
        )

        enum_lines = [
            'enum InvalidEnum {',
            '    A 0;',  # Missing '='
            '    B = 1;',
            '}',
        ]
        with self.assertRaises(ValueError):
            self.ctx.parse_enum(enum_lines, [])


class TestParserSample(unittest.TestCase):
    def setUp(self) -> None:
        testdata_dir = pathlib.Path(__file__).parent / 'testdata'

        self.sample_file = testdata_dir / 'sample.bh'
        self.other_file = testdata_dir / 'other.bh'

        self.ctx = parser.Parser()

    def test_parse_file(self):
        other = self.ctx.parse_file(
            self.other_file,
            parent_namespace='nlb.buffham.testdata',
        )
        # Quickly inspect the parsed `other` object
        self.assertEqual(len(other.constants), 1)
        self.assertEqual(len(other.messages), 1)
        self.assertEqual(len(other.transactions), 1)

        verbosity_enum = parser.Enum(
            'Verbosity',
            [
                schema_bh.EnumField('LOW', 0, [], None),
                schema_bh.EnumField(
                    'MEDIUM', 1, [' Comment on MEDIUM'], ' Inline comment on MEDIUM'
                ),
                schema_bh.EnumField('HIGH', 2, [], None),
            ],
            [' Enums can be defined and are treated as uint8_t values'],
        )

        ping = parser.Message(
            'Ping',
            [
                schema_bh.Field(
                    'ping',
                    schema_bh.FieldType.UINT8_T,
                    None,
                    False,
                    None,
                    [' Add some comments here'],
                    None,
                )
            ],
            [' A message comment'],
        )
        flash_page = parser.Message(
            'FlashPage',
            [
                schema_bh.Field(
                    'address',
                    schema_bh.FieldType.UINT32_T,
                    None,
                    False,
                    None,
                    [],
                    None,
                ),
                schema_bh.Field(
                    'data',
                    schema_bh.FieldType.LIST,
                    schema_bh.FieldType.UINT8_T,
                    False,
                    None,
                    [' Another field comment'],
                    ' What about some in-line comments for fields?',
                ),
                schema_bh.Field(
                    'read_size',
                    schema_bh.FieldType.UINT32_T,
                    None,
                    True,
                    None,
                    [' This comment belongs to `read_size`'],
                    ' Fields can be marked optional',
                ),
            ],
            [
                '',
                ' A bunch of message comments,',
                ' in a block-like pattern.',
                '',
                ' All of these belong to `FlashPage`',
                '',
            ],
        )
        log_message = parser.Message(
            'LogMessage',
            [
                schema_bh.Field(
                    'message',
                    schema_bh.FieldType.STRING,
                    None,
                    False,
                    None,
                    [],
                    None,
                ),
                schema_bh.Field(
                    'verbosity',
                    schema_bh.FieldType.ENUM,
                    None,
                    False,
                    schema_bh.Name(verbosity_enum.name, 'sample'),
                    [],
                    None,
                ),
                schema_bh.Field(
                    'my_enum',
                    schema_bh.FieldType.ENUM,
                    None,
                    False,
                    schema_bh.Name(other.enums[0].name, 'nlb.buffham.testdata.other'),
                    [],
                    None,
                ),
            ],
        )
        nested_message = parser.Message(
            'NestedMessage',
            [
                schema_bh.Field(
                    'flag',
                    schema_bh.FieldType.BOOL,
                    None,
                    True,
                    None,
                    [],
                    None,
                ),
                schema_bh.Field(
                    'message',
                    schema_bh.FieldType.MESSAGE,
                    None,
                    False,
                    schema_bh.Name(log_message.name, 'sample'),
                    [],
                    None,
                ),
                schema_bh.Field(
                    'messages',
                    schema_bh.FieldType.LIST,
                    schema_bh.FieldType.MESSAGE,
                    False,
                    schema_bh.Name(log_message.name, 'sample'),
                    [],
                    None,
                ),
                schema_bh.Field(
                    'numbers',
                    schema_bh.FieldType.LIST,
                    schema_bh.FieldType.INT32_T,
                    False,
                    None,
                    [],
                    None,
                ),
                schema_bh.Field(
                    'pong',
                    schema_bh.FieldType.MESSAGE,
                    None,
                    False,
                    schema_bh.Name(ping.name, 'sample'),
                    [],
                    None,
                ),
                schema_bh.Field(
                    'other_pong',
                    schema_bh.FieldType.MESSAGE,
                    None,
                    False,
                    schema_bh.Name(
                        other.messages[0].name, 'nlb.buffham.testdata.other'
                    ),
                    [],
                    None,
                ),
            ],
        )
        string_lists = parser.Message(
            'StringLists',
            [
                schema_bh.Field(
                    'messages',
                    schema_bh.FieldType.LIST,
                    schema_bh.FieldType.STRING,
                    False,
                    None,
                    [],
                    None,
                ),
                schema_bh.Field(
                    'buffers',
                    schema_bh.FieldType.LIST,
                    schema_bh.FieldType.BYTES,
                    False,
                    None,
                    [],
                    None,
                ),
            ],
            comments=[' Lists can be composed of variable-length strings and bytes'],
        )

        parsed = self.ctx.parse_file(self.sample_file, parent_namespace='')

        self.assertListEqual(
            parsed.messages,
            [
                ping,
                flash_page,
                log_message,
                nested_message,
                string_lists,
            ],
        )

        self.assertListEqual(
            parsed.transactions,
            [
                # Request IDs offset by 1 from `other`'s transactions
                schema_bh.Transaction(
                    'ping',
                    1,
                    schema_bh.Name(
                        other.messages[0].name, 'nlb.buffham.testdata.other'
                    ),
                    schema_bh.Name(log_message.name, 'sample'),
                    [],
                    None,
                ),
                schema_bh.Transaction(
                    'flash_page',
                    2,
                    schema_bh.Name(flash_page.name, 'sample'),
                    schema_bh.Name(flash_page.name, 'sample'),
                    [' Transaction comment'],
                    None,
                ),
                schema_bh.Transaction(
                    'read_flash_page',
                    3,
                    schema_bh.Name(flash_page.name, 'sample'),
                    schema_bh.Name(flash_page.name, 'sample'),
                    [],
                    ' In-line transaction comment',
                ),
            ],
        )

        self.assertListEqual(
            parsed.publishes,
            [
                schema_bh.Publish(
                    'log_message',
                    4,
                    schema_bh.Name(log_message.name, 'sample'),
                    [' Publish comment'],
                    ' In-line publish comment',
                ),
            ],
        )

        self.assertListEqual(
            parsed.constants,
            [
                schema_bh.Constant(
                    'my_constant',
                    schema_bh.FieldType.UINT8_T,
                    '4',
                    [' This is a constant in the global scope'],
                    None,
                    [],
                ),
                schema_bh.Constant(
                    'constant_string',
                    schema_bh.FieldType.STRING,
                    'Hello, world!',
                    [
                        " Constants can be strings as well; they're interpreted with bare words"
                    ],
                    ' constants can have inline comments',
                    [],
                ),
                schema_bh.Constant(
                    'composed_constant',
                    schema_bh.FieldType.UINT16_T,
                    '2 + {my_constant} + {nlb.buffham.testdata.other.other_constant}',
                    [' Constants may reference other constants with {brackets}'],
                    None,
                    ['nlb.buffham.testdata.other.other_constant', 'my_constant'],
                ),
            ],
        )

        self.assertListEqual(
            parsed.enums,
            [
                verbosity_enum,
            ],
        )
