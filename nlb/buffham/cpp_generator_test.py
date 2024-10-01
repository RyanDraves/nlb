import os
import pathlib
import unittest


class TestCppGenerator(unittest.TestCase):
    def setUp(self) -> None:
        self.other_hpp = pathlib.Path(__file__).parent / os.environ['TEST_HPP']
        self.other_cc = pathlib.Path(__file__).parent / os.environ['TEST_CC']

        testdata_dir = pathlib.Path(__file__).parent / 'testdata'

        self.golden_hpp = testdata_dir / 'sample_bh.hpp.golden'
        self.golden_cc = testdata_dir / 'sample_bh.cc.golden'

    def test_generate_hpp(self):
        # Check that the generated file matches the golden file
        golden = self.golden_hpp.read_text()
        generated = self.other_hpp.read_text()
        self.assertEqual(generated, golden)

    def test_generate_cc(self):
        # Check that the generated file matches the golden file
        golden = self.golden_cc.read_text()
        generated = self.other_cc.read_text()
        self.assertEqual(generated, golden)
