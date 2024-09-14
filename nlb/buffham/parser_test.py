import pathlib
import unittest

from nlb.buffham import parser


class TestParserSimple(unittest.TestCase):
    def test_parse_field(self):
        field = '    uint8_t foo;'
        parsed = parser.Parser.parse_field(field)
        self.assertEqual(parsed, parser.Field('foo', parser.FieldType.UINT8_T, None))

        field = 'float64 bar;  # inline comment'
        parsed = parser.Parser.parse_field(field)
        self.assertEqual(parsed, parser.Field('bar', parser.FieldType.FLOAT64, None))

        field = 'list[uint32_t] baz_2;'
        parsed = parser.Parser.parse_field(field)
        self.assertEqual(
            parsed,
            parser.Field('baz_2', parser.FieldType.LIST, parser.FieldType.UINT32_T),
        )

        field = 'list[list[uint32_t]] baz_3;'
        with self.assertRaises(ValueError):
            parser.Parser.parse_field(field)

        field = 'list[uint32_t baz_4;'
        with self.assertRaises(ValueError):
            parser.Parser.parse_field(field)

    def test_parse_message(self):
        message = [
            'message Ping {',
            '    uint8_t ping;',
            '}',
        ]
        parsed = parser.Parser.parse_message(message)
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
            '    list[uint32_t] data;',
            '}  # inline comment',
        ]
        parsed = parser.Parser.parse_message(message)
        self.assertEqual(
            parsed,
            parser.Message(
                'FlashPage',
                [
                    parser.Field('address', parser.FieldType.UINT32_T, None),
                    parser.Field('read_size', parser.FieldType.UINT32_T, None),
                    parser.Field(
                        'data', parser.FieldType.LIST, parser.FieldType.UINT32_T
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
            parser.Parser.parse_message(message)

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
        parsed = p.parse_transaction(transaction, messages)
        self.assertEqual(
            parsed,
            parser.Transaction(
                'ping',
                0,
                receive,
                send,
            ),
        )

        transaction = 'transaction flash_page[Ping, Ping];  # inline comment'
        messages = [receive, receive]
        parsed = p.parse_transaction(transaction, messages)
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
            p.parse_transaction(transaction, messages)

        transaction = 'transaction flash_page[Ping, Ping'
        with self.assertRaises(ValueError):
            p.parse_transaction(transaction, messages)


class TestParserSample(unittest.TestCase):
    def setUp(self) -> None:
        testdata_dir = pathlib.Path(__file__).parent / 'testdata'

        self.sample_file = testdata_dir / 'sample.bh'

    def test_parse_file(self):
        p = parser.Parser()

        ping = parser.Message(
            'Ping', [parser.Field('ping', parser.FieldType.UINT8_T, None)]
        )
        flash_page = parser.Message(
            'FlashPage',
            [
                parser.Field('address', parser.FieldType.UINT32_T, None),
                parser.Field('data', parser.FieldType.LIST, parser.FieldType.UINT8_T),
                parser.Field('read_size', parser.FieldType.UINT32_T, None),
            ],
        )
        log_message = parser.Message(
            'LogMessage', [parser.Field('message', parser.FieldType.STRING, None)]
        )

        # No comment lines in the middle of the message, so this is valid
        parsed = p.parse_file(self.sample_file)
        self.assertListEqual(
            parsed.messages,
            [
                ping,
                flash_page,
                log_message,
            ],
        )

        self.assertListEqual(
            parsed.transactions,
            [
                parser.Transaction('ping', 0, ping, log_message),
                parser.Transaction('flash_page', 1, flash_page, flash_page),
                parser.Transaction('read_flash_page', 2, flash_page, flash_page),
            ],
        )
