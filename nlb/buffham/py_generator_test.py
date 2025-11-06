import pathlib
import tempfile
import unittest
from importlib import util

from nlb.buffham import bh
from nlb.buffham import engine
from nlb.buffham import parser
from nlb.buffham import py_generator
from nlb.buffham import schema_bh

# Test generation by Bazel rules by importing this module
from nlb.buffham.testdata import other_bh
from nlb.util import test_utils

# Transitive dependency of our generated code
# gazelle:include_dep //emb/network/serialize:bh_cobs


class TestPyGenerator(unittest.TestCase):
    def setUp(self) -> None:
        testdata_dir = pathlib.Path(__file__).parent / 'testdata'

        self.other_file = testdata_dir / 'other.bh'
        self.sample_file = testdata_dir / 'sample.bh'
        self.golden_file = testdata_dir / 'sample_bh.py.golden'
        self.golden_stub_file = testdata_dir / 'sample_bh.pyi.golden'

        self.ctx = parser.Parser()
        self.other_bh = self.ctx.parse_file(
            self.other_file,
            parent_namespace='nlb.buffham.testdata',
        )
        self.sample_bh = self.ctx.parse_file(
            self.sample_file, parent_namespace='nlb.buffham.testdata'
        )

    def test_schema_serialization(self):
        buffham = self.sample_bh

        # Verify that serializing and deserializing the schema works
        serialized_schema = buffham.serialize()
        deserialized_bh, _ = schema_bh.Buffham.deserialize(serialized_schema)
        self.assertEqual(buffham, deserialized_bh)

    def test_generate_python(self):
        buffham = self.sample_bh

        with tempfile.TemporaryDirectory() as tempdir:
            message_registry = {
                ('nlb.buffham.testdata.sample', m.name): m for m in buffham.messages
            }
            for m in self.other_bh.messages:
                message_registry[('nlb.buffham.testdata.other', m.name)] = m

            outfile = pathlib.Path(tempdir) / 'sample_bh.py'
            py_generator.generate_python(
                self.ctx, parser.full_name(buffham.name), outfile, stub=False
            )

            spec = util.spec_from_file_location('sample_bh', outfile)
            assert spec is not None
            sample_bh = util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(sample_bh)

            # Assert that our classes are generated
            ping = sample_bh.Ping(42)
            self.assertEqual(ping.ping, 42)

            # Test serialization & deserialization of `Ping`
            ping_message = next(filter(lambda m: m.name == 'Ping', buffham.messages))
            serializer = engine.generate_serializer(ping_message, message_registry)
            buffer = ping.serialize()
            msg, size = sample_bh.Ping.deserialize(buffer)
            self.assertEqual(buffer, serializer(ping))
            self.assertEqual(msg, ping)
            self.assertEqual(size, len(buffer))

            # Test serialization & deserialization of `FlashPage`
            flash_page = sample_bh.FlashPage(0x1234, [0x9A, 0xBC], 0x5678)
            flash_page_message = next(
                filter(lambda m: m.name == 'FlashPage', buffham.messages)
            )
            serializer = engine.generate_serializer(
                flash_page_message, message_registry
            )
            buffer = flash_page.serialize()
            msg, size = sample_bh.FlashPage.deserialize(buffer)
            self.assertEqual(buffer, serializer(flash_page))
            self.assertEqual(msg, flash_page)
            self.assertEqual(size, len(buffer))

            # Test serialization & deserialization of `LogMessage`
            log_message = sample_bh.LogMessage(
                'Hello, world!', sample_bh.Verbosity.MEDIUM, other_bh.MyEnum.B
            )
            log_message_message = next(
                filter(lambda m: m.name == 'LogMessage', buffham.messages)
            )
            serializer = engine.generate_serializer(
                log_message_message, message_registry
            )
            buffer = log_message.serialize()
            msg, size = sample_bh.LogMessage.deserialize(buffer)
            self.assertEqual(buffer, serializer(log_message))
            self.assertEqual(msg, log_message)
            self.assertEqual(size, len(buffer))

            # Test serialization & deserialization of `NestedMessage`
            nested_message = sample_bh.NestedMessage(
                False,
                log_message,
                [log_message, log_message],
                [-0x1, -0x2],
                ping,
                other_bh.Pong(0x43),
            )
            nested_message_message = next(
                filter(lambda m: m.name == 'NestedMessage', buffham.messages)
            )
            serializer = engine.generate_serializer(
                nested_message_message, message_registry
            )
            buffer = nested_message.serialize()
            msg, size = sample_bh.NestedMessage.deserialize(buffer)
            self.assertEqual(buffer, serializer(nested_message))
            self.assertEqual(msg, nested_message)
            self.assertEqual(size, len(buffer))

            # Test serialization & deserialization of `StringLists`
            string_lists = sample_bh.StringLists(
                ['hello', 'world'], [b'\x01\x02\x03', b'\x04\x05']
            )
            string_lists_message = next(
                filter(lambda m: m.name == 'StringLists', buffham.messages)
            )
            serializer = engine.generate_serializer(
                string_lists_message, message_registry
            )
            buffer = string_lists.serialize()
            msg, size = sample_bh.StringLists.deserialize(buffer)
            self.assertEqual(buffer, serializer(string_lists))
            self.assertEqual(msg, string_lists)
            self.assertEqual(size, len(buffer))

            # Test that our transactions are generated
            self.assertEqual(
                sample_bh.PING,
                # Request IDs offset by 1 from `other_bh`
                bh.Transaction[sample_bh.Ping, sample_bh.LogMessage](1),
            )
            self.assertEqual(
                sample_bh.FLASH_PAGE,
                bh.Transaction[sample_bh.FlashPage, sample_bh.FlashPage](2),
            )
            self.assertEqual(
                sample_bh.READ_FLASH_PAGE,
                bh.Transaction[sample_bh.FlashPage, sample_bh.FlashPage](3),
            )

            # Test that our publishes are generated
            self.assertEqual(sample_bh.PublishIds.LOG_MESSAGE.value, 4)

            # Test that our constants are generated
            self.assertEqual(sample_bh.MY_CONSTANT, 4)
            self.assertEqual(sample_bh.CONSTANT_STRING, 'Hello, world!')
            self.assertEqual(
                sample_bh.COMPOSED_CONSTANT,
                2 + sample_bh.MY_CONSTANT + other_bh.OTHER_CONSTANT,
            )

            # Check the our file matches the golden file
            golden = self.golden_file.read_text()
            generated = outfile.read_text()
            test_utils.assertTextEqual(self, generated, golden)

    def test_generate_python_stub(self):
        buffham = self.sample_bh

        with tempfile.TemporaryDirectory() as tempdir:
            outfile = pathlib.Path(tempdir) / 'sample_bh.pyi'
            py_generator.generate_python(
                self.ctx, parser.full_name(buffham.name), outfile, stub=True
            )

            # Check that the generated file matches the golden file
            golden = self.golden_stub_file.read_text()
            generated = outfile.read_text()
            test_utils.assertTextEqual(self, generated, golden)
