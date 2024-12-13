import os
import pathlib
import unittest


class TestTemplateGenerator(unittest.TestCase):
    def setUp(self) -> None:
        self.test_file = pathlib.Path(__file__).parent / os.environ['TEST_FILE']

        testdata_dir = pathlib.Path(__file__).parent / 'testdata'

        self.golden_file = testdata_dir / 'sample.md.golden'

    def test_generate_cpp(self):
        # Check that the generated file matches the golden file
        golden = self.golden_file.read_text()
        generated = self.test_file.read_text()
        self.assertEqual(generated, golden)
