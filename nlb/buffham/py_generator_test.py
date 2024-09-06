import pathlib
import tempfile
import unittest
from importlib import util

from emb.network.node import dataclass_node
from nlb.buffham import engine
from nlb.buffham import parser
from nlb.buffham import py_generator


class TestPyGenerator(unittest.TestCase):
    def setUp(self) -> None:
        testdata_dir = pathlib.Path(__file__).parent / 'testdata'

        self.sample_file = testdata_dir / 'sample.bh'
        self.golden_file = testdata_dir / 'sample_bh.py.golden'
        self.golden_stub_file = testdata_dir / 'sample_bh.pyi.golden'

    def test_generate_python(self):
        bh = parser.Parser().parse_file(self.sample_file)

        with tempfile.TemporaryDirectory() as tempdir:
            outfile = pathlib.Path(tempdir) / 'sample_bh.py'
            py_generator.generate_python(bh, outfile, stub=False)

            spec = util.spec_from_file_location('sample_bh', outfile)
            assert spec is not None
            sample_bh = util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(sample_bh)

            # Assert that our classes are generated
            ping = sample_bh.Ping(42)
            self.assertEqual(ping.ping, 42)

            # Test serialization & deserialization of `Ping`
            ping_message = next(filter(lambda m: m.name == 'Ping', bh.messages))
            serializer = engine.generate_serializer(ping_message)
            self.assertEqual(
                ping.serialize(),
                serializer(ping),
            )
            self.assertEqual(
                ping,
                sample_bh.Ping.deserialize(ping.serialize()),
            )

            # Test serialization & deserialization of `FlashPage`
            flash_page = sample_bh.FlashPage(0x1234, 0x5678, [0x9A, 0xBC])
            flash_page_message = next(
                filter(lambda m: m.name == 'FlashPage', bh.messages)
            )
            serializer = engine.generate_serializer(flash_page_message)
            self.assertEqual(
                flash_page.serialize(),
                serializer(flash_page),
            )
            self.assertEqual(
                flash_page,
                sample_bh.FlashPage.deserialize(flash_page.serialize()),
            )

            # Test serialization & deserialization of `LogMessage`
            log_message = sample_bh.LogMessage('Hello, world!')
            log_message_message = next(
                filter(lambda m: m.name == 'LogMessage', bh.messages)
            )
            serializer = engine.generate_serializer(log_message_message)
            self.assertEqual(
                log_message.serialize(),
                serializer(log_message),
            )
            self.assertEqual(
                log_message,
                sample_bh.LogMessage.deserialize(log_message.serialize()),
            )

            # Test that our transactions are generated
            self.assertEqual(
                sample_bh.PING,
                dataclass_node.Transaction[sample_bh.Ping, sample_bh.LogMessage](0),
            )
            self.assertEqual(
                sample_bh.FLASH_PAGE,
                dataclass_node.Transaction[sample_bh.FlashPage, sample_bh.FlashPage](1),
            )
            self.assertEqual(
                sample_bh.READ_FLASH_PAGE,
                dataclass_node.Transaction[sample_bh.FlashPage, sample_bh.FlashPage](2),
            )

            # Check the our file matches the golden file
            golden = self.golden_file.read_text()
            generated = outfile.read_text()
            self.assertEqual(generated, golden)

    def test_generate_python_stub(self):
        bh = parser.Parser().parse_file(self.sample_file)

        with tempfile.TemporaryDirectory() as tempdir:
            outfile = pathlib.Path(tempdir) / 'sample_bh.pyi'
            py_generator.generate_python(bh, outfile, stub=True)

            # Check that the generated file matches the golden file
            golden = self.golden_stub_file.read_text()
            generated = outfile.read_text()
            self.assertEqual(generated, golden)
