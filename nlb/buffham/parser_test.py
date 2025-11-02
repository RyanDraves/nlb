import pathlib
import unittest

from nlb.buffham import parser
from nlb.buffham import schema_bh


class TestParserSimple(unittest.TestCase):
    def test_parse_field(self):
        ctx = parser.ParseContext({'test': parser.Buffham('test', '')})
        ctx.cur_namespace = 'test'

        field = '    uint8_t foo;'
        parsed = parser.Parser.parse_message_field(field, [], ctx)
        self.assertEqual(parsed, parser.Field('foo', schema_bh.FieldType.UINT8_T, None))

        field = 'float64 bar;  # inline comment'
        parsed = parser.Parser.parse_message_field(field, [], ctx)
        self.assertEqual(
            parsed,
            parser.Field(
                'bar',
                schema_bh.FieldType.FLOAT64,
                None,
                None,
                None,
                [],
                ' inline comment',
            ),
        )

        field = 'list[uint32_t] baz_2;'
        parsed = parser.Parser.parse_message_field(
            field, ['some other', 'read-in comments'], ctx
        )
        self.assertEqual(
            parsed,
            parser.Field(
                'baz_2',
                schema_bh.FieldType.LIST,
                schema_bh.FieldType.UINT32_T,
                None,
                None,
                ['some other', 'read-in comments'],
            ),
        )

        field = 'list[list[uint32_t]] baz_3;'
        with self.assertRaises(ValueError):
            parser.Parser.parse_message_field(field, [], ctx)

        field = 'list[uint32_t baz_4;'
        with self.assertRaises(ValueError):
            parser.Parser.parse_message_field(field, [], ctx)

        field = 'MyMessage baz_5;'
        my_message = parser.Message('MyMessage', [])
        ctx.cur_buffham.messages.append(my_message)
        parsed = parser.Parser.parse_message_field(field, [], ctx)
        self.assertEqual(
            parsed,
            parser.Field(
                'baz_5', schema_bh.FieldType.MESSAGE, None, my_message, 'test'
            ),
        )

        field = 'NonexistantMessage baz_6;'
        with self.assertRaises(ValueError):
            parser.Parser.parse_message_field(field, [], ctx)

    def test_parse_message(self):
        ctx = parser.ParseContext({'test': parser.Buffham('test', '')})
        ctx.cur_namespace = 'test'

        message = [
            'message Ping {',
            '    uint8_t ping;',
            '}',
        ]
        parsed = parser.Parser.parse_message(message, [], ctx)
        self.assertEqual(
            parsed,
            parser.Message(
                'Ping', [parser.Field('ping', schema_bh.FieldType.UINT8_T, None)]
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
        parsed = parser.Parser.parse_message(message, [], ctx)
        self.assertEqual(
            parsed,
            parser.Message(
                'FlashPage',
                [
                    parser.Field('address', schema_bh.FieldType.UINT32_T, None),
                    parser.Field(
                        'read_size',
                        schema_bh.FieldType.UINT32_T,
                        None,
                        None,
                        None,
                        [],
                        ' inline comment',
                    ),
                    parser.Field(
                        'data',
                        schema_bh.FieldType.LIST,
                        schema_bh.FieldType.UINT32_T,
                        None,
                        None,
                        [' out-of-line comment'],
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
            parser.Parser.parse_message(message, [], ctx)

        # Nested message
        message = [
            'message Outer {',
            '    Inner inner;',
            '}',
        ]
        inner = parser.Message('Inner', [])
        ctx.cur_buffham.messages.append(inner)
        parsed = parser.Parser.parse_message(message, [], ctx)
        self.assertEqual(
            parsed,
            parser.Message(
                'Outer',
                [
                    parser.Field(
                        'inner', schema_bh.FieldType.MESSAGE, None, inner, 'test'
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
            parser.Parser.parse_message(message, [], ctx)

    def test_parse_transaction(self):
        p = parser.Parser()
        ctx = parser.ParseContext({'test': parser.Buffham('test', '')})
        ctx.cur_namespace = 'test'

        transaction = 'transaction ping[Ping, LogMessage];'
        receive = parser.Message(
            'Ping', [parser.Field('ping', schema_bh.FieldType.UINT8_T, None)]
        )
        send = parser.Message(
            'LogMessage',
            [parser.Field('message', schema_bh.FieldType.STRING, None)],
        )
        ctx.cur_buffham.messages.extend([receive, send])
        parsed = p.parse_transaction(transaction, ['some other comment'], ctx)
        self.assertEqual(
            parsed,
            parser.Transaction(
                'ping',
                0,
                receive,
                'test',
                send,
                'test',
                ['some other comment'],
            ),
        )

        transaction = 'transaction flash_page[Ping, Ping];  # inline comment'
        parsed = p.parse_transaction(transaction, [], ctx)
        self.assertEqual(
            parsed,
            parser.Transaction(
                'flash_page',
                1,
                receive,
                'test',
                receive,
                'test',
                comments=[],  # In-line transaction comments are ignored
            ),
        )

        transaction = 'transaction flash_page[Ping, InvalidMessage];'
        with self.assertRaises(ValueError):
            p.parse_transaction(transaction, [], ctx)

        transaction = 'transaction flash_page[Ping, Ping'
        with self.assertRaises(ValueError):
            p.parse_transaction(transaction, [], ctx)

    def test_parse_publish(self):
        p = parser.Parser()
        ctx = parser.ParseContext({'test': parser.Buffham('test', '')})
        ctx.cur_namespace = 'test'

        publish = 'publish log[LogMessage];'
        log_msg = parser.Message(
            'LogMessage',
            [parser.Field('message', schema_bh.FieldType.STRING, None)],
        )
        ctx.cur_buffham.messages.append(log_msg)
        parsed = p.parse_publish(publish, ['some other comment'], ctx)
        self.assertEqual(
            parsed,
            parser.Publish(
                'log',
                0,
                log_msg,
                ['some other comment'],
            ),
        )

        publish = 'publish ping_pong[Ping];  # inline comment'
        ping = parser.Message(
            'Ping', [parser.Field('pong', schema_bh.FieldType.UINT8_T, None)]
        )
        ctx.cur_buffham.messages.append(ping)
        parsed = p.parse_publish(publish, [], ctx)
        self.assertEqual(
            parsed,
            parser.Publish(
                'ping_pong',
                1,
                ping,
                comments=[],  # In-line publish comments are ignored
            ),
        )

        publish = 'publish noise[InvalidMessage];'
        with self.assertRaises(ValueError):
            p.parse_publish(publish, [], ctx)

        publish = 'publish noise[Ping'
        with self.assertRaises(ValueError):
            p.parse_publish(publish, [], ctx)

    def test_parse_constant(self):
        p = parser.Parser()
        ctx = parser.ParseContext({'test': parser.Buffham('test', '')})
        ctx.cur_namespace = 'test'

        constant = 'constant uint8_t foo = 0x01;'
        parsed = p.parse_constant(constant, [], ctx)
        self.assertEqual(
            parsed,
            parser.Constant('foo', schema_bh.FieldType.UINT8_T, '0x01'),
        )

        constant = 'constant uint32_t bar = 0x12345678;  # inline comment'
        parsed = p.parse_constant(constant, [], ctx)
        bar = parser.Constant(
            'bar', schema_bh.FieldType.UINT32_T, '0x12345678', [], ' inline comment'
        )
        ctx.cur_buffham.constants.append(bar)
        self.assertEqual(
            parsed,
            bar,
        )

        constant = 'constant uint32_t baz = 0x1 + {bar};'
        parsed = p.parse_constant(constant, ['some other comment'], ctx)
        self.assertEqual(
            parsed,
            parser.Constant(
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
            p.parse_constant(constant, [], ctx)

    def test_parse_enum(self):
        ctx = parser.ParseContext({'test': parser.Buffham('test', '')})
        ctx.cur_namespace = 'test'

        enum_lines = [
            'enum SampleEnum {',
            '    A = 0;  # inline on A',
            '    # Comment on B',
            '    B = 1;',
            '}',
        ]
        comments = [' Enum comment line 1', ' Enum comment line 2']
        parsed = parser.Parser.parse_enum(enum_lines, comments, ctx)
        self.assertEqual(
            parsed,
            parser.Enum(
                'SampleEnum',
                [
                    parser.EnumField('A', 0, [], ' inline on A'),
                    parser.EnumField('B', 1, [' Comment on B']),
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
            parser.Parser.parse_enum(enum_lines, [], ctx)


class TestParserSample(unittest.TestCase):
    def setUp(self) -> None:
        testdata_dir = pathlib.Path(__file__).parent / 'testdata'

        self.sample_file = testdata_dir / 'sample.bh'
        self.other_file = testdata_dir / 'other.bh'

    def test_parse_file(self):
        p = parser.Parser()

        other = p.parse_file(
            self.other_file,
            parser.ParseContext({}),
            parent_namespace='nlb.buffham.testdata',
        )
        # Quickly inspect the parsed `other` object
        self.assertEqual(len(other.constants), 1)
        self.assertEqual(len(other.messages), 1)
        self.assertEqual(len(other.transactions), 1)

        ctx = parser.ParseContext({'nlb.buffham.testdata.other': other})

        sample_enum = parser.Enum(
            'SampleEnum',
            [
                parser.EnumField('A', 0),
                parser.EnumField('B', 1, [' Comment on B'], ' Inline comment on B'),
            ],
            [' Enums can be defined and are treated as uint8_t values'],
        )

        ping = parser.Message(
            'Ping',
            [
                parser.Field(
                    'ping',
                    schema_bh.FieldType.UINT8_T,
                    None,
                    None,
                    None,
                    [' Add some comments here'],
                )
            ],
            [' A message comment'],
        )
        flash_page = parser.Message(
            'FlashPage',
            [
                parser.Field('address', schema_bh.FieldType.UINT32_T, None),
                parser.Field(
                    'data',
                    schema_bh.FieldType.LIST,
                    schema_bh.FieldType.UINT8_T,
                    None,
                    None,
                    [' Another field comment'],
                    ' What about some in-line comments for fields?',
                ),
                parser.Field(
                    'read_size',
                    schema_bh.FieldType.UINT32_T,
                    None,
                    None,
                    None,
                    [' This comment belongs to `read_size`'],
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
            [parser.Field('message', schema_bh.FieldType.STRING, None)],
        )
        nested_message = parser.Message(
            'NestedMessage',
            [
                parser.Field('flag', schema_bh.FieldType.UINT8_T, None),
                parser.Field(
                    'message', schema_bh.FieldType.MESSAGE, None, log_message, 'sample'
                ),
                parser.Field(
                    'numbers', schema_bh.FieldType.LIST, schema_bh.FieldType.INT32_T
                ),
                parser.Field('pong', schema_bh.FieldType.MESSAGE, None, ping, 'sample'),
                parser.Field(
                    'other_pong',
                    schema_bh.FieldType.MESSAGE,
                    None,
                    other.messages[0],
                    'nlb.buffham.testdata.other',
                ),
            ],
        )

        parsed = p.parse_file(self.sample_file, ctx, parent_namespace='')

        self.assertListEqual(
            parsed.messages,
            [
                ping,
                flash_page,
                log_message,
                nested_message,
            ],
        )

        self.assertListEqual(
            parsed.transactions,
            [
                # Request IDs offset by 1 from `other`'s transactions
                parser.Transaction(
                    'ping',
                    1,
                    other.messages[0],
                    'nlb.buffham.testdata.other',
                    log_message,
                    'sample',
                ),
                parser.Transaction(
                    'flash_page',
                    2,
                    flash_page,
                    'sample',
                    flash_page,
                    'sample',
                    [' Transaction comment'],
                ),
                parser.Transaction(
                    'read_flash_page',
                    3,
                    flash_page,
                    'sample',
                    flash_page,
                    'sample',
                ),
            ],
        )

        self.assertListEqual(
            parsed.constants,
            [
                parser.Constant(
                    'my_constant',
                    schema_bh.FieldType.UINT8_T,
                    '4',
                    [' This is a constant in the global scope'],
                ),
                parser.Constant(
                    'constant_string',
                    schema_bh.FieldType.STRING,
                    'Hello, world!',
                    [
                        " Constants can be strings as well; they're interpreted with bare words"
                    ],
                    ' constants can have inline comments',
                ),
                parser.Constant(
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
                sample_enum,
            ],
        )
