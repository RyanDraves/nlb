import pathlib
import unittest

from nlb.buffham import parser


class TestParserSimple(unittest.TestCase):
    def test_parse_field(self):
        field = '    uint8_t foo;'
        parsed = parser.Parser.parse_field(field, [], [])
        self.assertEqual(parsed, parser.Field('foo', parser.FieldType.UINT8_T, None))

        field = 'float64 bar;  # inline comment'
        parsed = parser.Parser.parse_field(field, [], [])
        self.assertEqual(
            parsed,
            parser.Field(
                'bar', parser.FieldType.FLOAT64, None, None, [], ' inline comment'
            ),
        )

        field = 'list[uint32_t] baz_2;'
        parsed = parser.Parser.parse_field(
            field, [], ['some other', 'read-in comments']
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
            parser.Parser.parse_field(field, [], [])

        field = 'list[uint32_t baz_4;'
        with self.assertRaises(ValueError):
            parser.Parser.parse_field(field, [], [])

        field = 'MyMessage baz_5;'
        my_message = parser.Message('MyMessage', [])
        parsed = parser.Parser.parse_field(field, [my_message], [])
        self.assertEqual(
            parsed,
            parser.Field('baz_5', parser.FieldType.MESSAGE, None, my_message),
        )

        field = 'NonexistantMessage baz_6;'
        with self.assertRaises(ValueError):
            parser.Parser.parse_field(field, [my_message], [])

    def test_parse_message(self):
        message = [
            'message Ping {',
            '    uint8_t ping;',
            '}',
        ]
        parsed = parser.Parser.parse_message(message, [], [])
        self.assertEqual(
            parsed,
            parser.Message(
                'Ping', [parser.Field('ping', parser.FieldType.UINT8_T, None)]
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
        parsed = parser.Parser.parse_message(message, [], [])
        self.assertEqual(
            parsed,
            parser.Message(
                'FlashPage',
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
            parser.Parser.parse_message(message, [], [])

        # Nested message
        message = [
            'message Outer {',
            '    Inner inner;',
            '}',
        ]
        inner = parser.Message('Inner', [])
        parsed = parser.Parser.parse_message(message, [inner], [])
        self.assertEqual(
            parsed,
            parser.Message(
                'Outer', [parser.Field('inner', parser.FieldType.MESSAGE, None, inner)]
            ),
        )

        message = [
            'message Outer {',
            '    DoesNotExist inner;',
            '}',
        ]
        with self.assertRaises(ValueError):
            parser.Parser.parse_message(message, [inner], [])

    def test_parse_transaction(self):
        p = parser.Parser()

        transaction = 'transaction ping[Ping, LogMessage];'
        receive = parser.Message(
            'Ping', [parser.Field('ping', parser.FieldType.UINT8_T, None)]
        )
        send = parser.Message(
            'LogMessage', [parser.Field('message', parser.FieldType.STRING, None)]
        )
        messages = [receive, send]
        parsed = p.parse_transaction(transaction, messages, ['some other comment'])
        self.assertEqual(
            parsed,
            parser.Transaction(
                'ping',
                0,
                receive,
                send,
                ['some other comment'],
            ),
        )

        transaction = 'transaction flash_page[Ping, Ping];  # inline comment'
        messages = [receive, receive]
        parsed = p.parse_transaction(transaction, messages, [])
        self.assertEqual(
            parsed,
            parser.Transaction(
                'flash_page',
                1,
                receive,
                receive,
            ),
        )

        transaction = 'transaction flash_page[Ping, InvalidMessage];'
        with self.assertRaises(ValueError):
            p.parse_transaction(transaction, messages, [])

        transaction = 'transaction flash_page[Ping, Ping'
        with self.assertRaises(ValueError):
            p.parse_transaction(transaction, messages, [])


class TestParserSample(unittest.TestCase):
    def setUp(self) -> None:
        testdata_dir = pathlib.Path(__file__).parent / 'testdata'

        self.sample_file = testdata_dir / 'sample.bh'

    def test_parse_file(self):
        p = parser.Parser()

        ping = parser.Message(
            'Ping',
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
            'LogMessage', [parser.Field('message', parser.FieldType.STRING, None)]
        )
        nested_message = parser.Message(
            'NestedMessage',
            [
                parser.Field('flag', parser.FieldType.UINT8_T, None),
                parser.Field('message', parser.FieldType.MESSAGE, None, log_message),
                parser.Field(
                    'numbers', parser.FieldType.LIST, parser.FieldType.INT32_T
                ),
                parser.Field('pong', parser.FieldType.MESSAGE, None, ping),
            ],
        )

        parsed = p.parse_file(self.sample_file)
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
                parser.Transaction('ping', 0, ping, log_message),
                parser.Transaction(
                    'flash_page', 1, flash_page, flash_page, [' Transaction comment']
                ),
                parser.Transaction('read_flash_page', 2, flash_page, flash_page),
            ],
        )
