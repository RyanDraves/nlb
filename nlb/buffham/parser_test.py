import pathlib
import unittest

from nlb.buffham import parser


class TestParserSimple(unittest.TestCase):
    def test_parse_field(self):
        ctx = parser.ParseContext({})

        field = '    uint8_t foo;'
        parsed = parser.Parser.parse_field(field, [], [], ctx)
        self.assertEqual(parsed, parser.Field('foo', parser.FieldType.UINT8_T, None))

        field = 'float64 bar;  # inline comment'
        parsed = parser.Parser.parse_field(field, [], [], ctx)
        self.assertEqual(
            parsed,
            parser.Field(
                'bar', parser.FieldType.FLOAT64, None, None, [], ' inline comment'
            ),
        )

        field = 'list[uint32_t] baz_2;'
        parsed = parser.Parser.parse_field(
            field, [], ['some other', 'read-in comments'], ctx
        )
        self.assertEqual(
            parsed,
            parser.Field(
                'baz_2',
                parser.FieldType.LIST,
                parser.FieldType.UINT32_T,
                None,
                ['some other', 'read-in comments'],
            ),
        )

        field = 'list[list[uint32_t]] baz_3;'
        with self.assertRaises(ValueError):
            parser.Parser.parse_field(field, [], [], ctx)

        field = 'list[uint32_t baz_4;'
        with self.assertRaises(ValueError):
            parser.Parser.parse_field(field, [], [], ctx)

        field = 'MyMessage baz_5;'
        my_message = parser.Message('MyMessage', '', [])
        parsed = parser.Parser.parse_field(field, [my_message], [], ctx)
        self.assertEqual(
            parsed,
            parser.Field('baz_5', parser.FieldType.MESSAGE, None, my_message),
        )

        field = 'NonexistantMessage baz_6;'
        with self.assertRaises(ValueError):
            parser.Parser.parse_field(field, [my_message], [], ctx)

    def test_parse_message(self):
        ctx = parser.ParseContext({})

        message = [
            'message Ping {',
            '    uint8_t ping;',
            '}',
        ]
        parsed = parser.Parser.parse_message(message, [], [], ctx)
        self.assertEqual(
            parsed,
            parser.Message(
                'Ping', '', [parser.Field('ping', parser.FieldType.UINT8_T, None)]
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
        parsed = parser.Parser.parse_message(message, [], [], ctx)
        self.assertEqual(
            parsed,
            parser.Message(
                'FlashPage',
                '',
                [
                    parser.Field('address', parser.FieldType.UINT32_T, None),
                    parser.Field(
                        'read_size',
                        parser.FieldType.UINT32_T,
                        None,
                        None,
                        [],
                        ' inline comment',
                    ),
                    parser.Field(
                        'data',
                        parser.FieldType.LIST,
                        parser.FieldType.UINT32_T,
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
            parser.Parser.parse_message(message, [], [], ctx)

        # Nested message
        message = [
            'message Outer {',
            '    Inner inner;',
            '}',
        ]
        inner = parser.Message('Inner', '', [])
        parsed = parser.Parser.parse_message(message, [inner], [], ctx)
        self.assertEqual(
            parsed,
            parser.Message(
                'Outer',
                '',
                [parser.Field('inner', parser.FieldType.MESSAGE, None, inner)],
            ),
        )

        message = [
            'message Outer {',
            '    DoesNotExist inner;',
            '}',
        ]
        with self.assertRaises(ValueError):
            parser.Parser.parse_message(message, [inner], [], ctx)

    def test_parse_transaction(self):
        p = parser.Parser()
        ctx = parser.ParseContext({})

        transaction = 'transaction ping[Ping, LogMessage];'
        receive = parser.Message(
            'Ping', '', [parser.Field('ping', parser.FieldType.UINT8_T, None)]
        )
        send = parser.Message(
            'LogMessage', '', [parser.Field('message', parser.FieldType.STRING, None)]
        )
        messages = [receive, send]
        parsed = p.parse_transaction(transaction, messages, ['some other comment'], ctx)
        self.assertEqual(
            parsed,
            parser.Transaction(
                'ping',
                '',
                0,
                receive,
                send,
                ['some other comment'],
            ),
        )

        transaction = 'transaction flash_page[Ping, Ping];  # inline comment'
        messages = [receive, receive]
        parsed = p.parse_transaction(transaction, messages, [], ctx)
        self.assertEqual(
            parsed,
            parser.Transaction(
                'flash_page',
                '',
                1,
                receive,
                receive,
            ),
        )

        transaction = 'transaction flash_page[Ping, InvalidMessage];'
        with self.assertRaises(ValueError):
            p.parse_transaction(transaction, messages, [], ctx)

        transaction = 'transaction flash_page[Ping, Ping'
        with self.assertRaises(ValueError):
            p.parse_transaction(transaction, messages, [], ctx)

    def test_parse_constant(self):
        p = parser.Parser()
        ctx = parser.ParseContext({})

        constant = 'constant uint8_t foo = 0x01;'
        parsed = p.parse_constant(constant, [], [], ctx)
        self.assertEqual(
            parsed,
            parser.Constant('foo', '', parser.FieldType.UINT8_T, '0x01'),
        )

        constant = 'constant uint32_t bar = 0x12345678;  # inline comment'
        parsed = p.parse_constant(constant, [], [], ctx)
        bar = parser.Constant(
            'bar', '', parser.FieldType.UINT32_T, '0x12345678', [], ' inline comment'
        )
        self.assertEqual(
            parsed,
            bar,
        )

        constant = 'constant uint32_t baz = 0x1 + {bar};'
        parsed = p.parse_constant(constant, [bar], ['some other comment'], ctx)
        self.assertEqual(
            parsed,
            parser.Constant(
                'baz',
                '',
                parser.FieldType.UINT32_T,
                '0x1 + {bar}',
                ['some other comment'],
                None,
                ['bar'],
            ),
        )

        constant = 'constant uint32_t baz = 0x12345678  # missing semicolon'
        with self.assertRaises(ValueError):
            p.parse_constant(constant, [], [], ctx)


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

        ping = parser.Message(
            'Ping',
            'sample',
            [
                parser.Field(
                    'ping',
                    parser.FieldType.UINT8_T,
                    None,
                    None,
                    [' Add some comments here'],
                )
            ],
            [' A message comment'],
        )
        flash_page = parser.Message(
            'FlashPage',
            'sample',
            [
                parser.Field('address', parser.FieldType.UINT32_T, None),
                parser.Field(
                    'data',
                    parser.FieldType.LIST,
                    parser.FieldType.UINT8_T,
                    None,
                    [' Another field comment'],
                    ' What about some in-line comments for fields?',
                ),
                parser.Field(
                    'read_size',
                    parser.FieldType.UINT32_T,
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
            'sample',
            [parser.Field('message', parser.FieldType.STRING, None)],
        )
        nested_message = parser.Message(
            'NestedMessage',
            'sample',
            [
                parser.Field('flag', parser.FieldType.UINT8_T, None),
                parser.Field('message', parser.FieldType.MESSAGE, None, log_message),
                parser.Field(
                    'numbers', parser.FieldType.LIST, parser.FieldType.INT32_T
                ),
                parser.Field('pong', parser.FieldType.MESSAGE, None, ping),
                parser.Field(
                    'other_pong', parser.FieldType.MESSAGE, None, other.messages[0]
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
                parser.Transaction('ping', 'sample', 0, other.messages[0], log_message),
                parser.Transaction(
                    'flash_page',
                    'sample',
                    1,
                    flash_page,
                    flash_page,
                    [' Transaction comment'],
                ),
                parser.Transaction(
                    'read_flash_page', 'sample', 2, flash_page, flash_page
                ),
            ],
        )

        self.assertListEqual(
            parsed.constants,
            [
                parser.Constant(
                    'my_constant',
                    'sample',
                    parser.FieldType.UINT8_T,
                    '4',
                    [' This is a constant in the global scope'],
                ),
                parser.Constant(
                    'constant_string',
                    'sample',
                    parser.FieldType.STRING,
                    '"Hello, world!"',
                    [],
                    ' constants can have inline comments',
                ),
                parser.Constant(
                    'composed_constant',
                    'sample',
                    parser.FieldType.UINT16_T,
                    '2 + {my_constant} + {nlb.buffham.testdata.other.other_constant}',
                    [' Constants may reference other constants with {brackets}'],
                    None,
                    ['my_constant', 'nlb.buffham.testdata.other.other_constant'],
                ),
            ],
        )
