import pathlib
import tempfile
import unittest

import numpy as np
from scipy.io import wavfile

from nlb.wav import wav2cc


class TestConvertSamples(unittest.TestCase):
    def test_mono_duplicated_to_stereo(self):
        data = np.array([0, 16384, -16384, -32768], dtype=np.int16)
        samples = wav2cc.convert_samples(
            data, input_rate=22050, sample_rate=22050, gain_db=0.0, pad_ms=0
        )

        self.assertEqual(samples.shape, (4, 2))
        self.assertEqual(samples.dtype, np.int16)
        np.testing.assert_array_equal(samples[:, 0], samples[:, 1])
        # int16 -32768 normalizes to -1.0 and back to -32768
        self.assertEqual(samples[3, 0], -32768)
        self.assertAlmostEqual(samples[1, 0], 16384, delta=1)

    def test_stereo_passthrough(self):
        data = np.array([[100, -100], [200, -200]], dtype=np.int16)
        samples = wav2cc.convert_samples(
            data, input_rate=22050, sample_rate=22050, gain_db=0.0, pad_ms=0
        )

        self.assertEqual(samples.shape, (2, 2))
        np.testing.assert_allclose(samples, data, atol=1)

    def test_too_many_channels_raises(self):
        data = np.zeros((8, 3), dtype=np.int16)
        with self.assertRaises(ValueError):
            wav2cc.convert_samples(
                data, input_rate=22050, sample_rate=22050, gain_db=0.0, pad_ms=0
            )

    def test_resample_halves_length(self):
        data = np.zeros(441, dtype=np.int16)
        samples = wav2cc.convert_samples(
            data, input_rate=44100, sample_rate=22050, gain_db=0.0, pad_ms=0
        )

        self.assertEqual(samples.shape, (221, 2))

    def test_padding_appends_silence(self):
        data = np.full(10, 1000, dtype=np.int16)
        samples = wav2cc.convert_samples(
            data, input_rate=22050, sample_rate=22050, gain_db=0.0, pad_ms=50
        )

        pad_frames = 22050 * 50 // 1000
        self.assertEqual(samples.shape, (10 + pad_frames, 2))
        np.testing.assert_array_equal(samples[10:], 0)

    def test_gain_clips_to_int16(self):
        data = np.array([16384, -16384], dtype=np.int16)
        samples = wav2cc.convert_samples(
            data, input_rate=22050, sample_rate=22050, gain_db=12.0, pad_ms=0
        )

        self.assertEqual(samples[0, 0], 32767)
        self.assertEqual(samples[1, 0], -32768)

    def test_float_input(self):
        data = np.array([0.0, 0.5, -1.0], dtype=np.float32)
        samples = wav2cc.convert_samples(
            data, input_rate=22050, sample_rate=22050, gain_db=0.0, pad_ms=0
        )

        self.assertEqual(samples[0, 0], 0)
        self.assertAlmostEqual(samples[1, 0], 16384, delta=1)
        self.assertEqual(samples[2, 0], -32768)


class TestGenerate(unittest.TestCase):
    def test_generate_hpp(self):
        hpp = wav2cc.generate_hpp('rimshot.wav', 'emb::project::punbox', 'rimshot')

        self.assertIn('#include "emb/yaal/audio_clip.hpp"', hpp)
        self.assertIn('namespace emb::project::punbox {', hpp)
        self.assertIn('extern const emb::yaal::AudioClip rimshot;', hpp)

    def test_generate_cc(self):
        samples = np.array([[1, 2], [3, 4]], dtype=np.int16)
        cc = wav2cc.generate_cc(
            'rimshot.wav',
            'emb/project/punbox/rimshot.hpp',
            'emb::project::punbox',
            'rimshot',
            22050,
            samples,
        )

        self.assertIn('#include "emb/project/punbox/rimshot.hpp"', cc)
        self.assertIn('alignas(4) const int16_t rimshot_samples[4] = {', cc)
        self.assertIn('    1, 2, 3, 4,', cc)
        self.assertIn('.sample_rate = 22050,', cc)
        self.assertIn('.num_frames = 2,', cc)
        self.assertIn('.samples = rimshot_samples,', cc)


class TestMain(unittest.TestCase):
    def test_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = pathlib.Path(tmpdir)
            wav = tmp / 'clip.wav'
            hpp = tmp / 'clip.hpp'
            cc = tmp / 'clip.cc'

            # 100ms 440Hz mono tone at 44.1kHz
            t = np.linspace(0, 0.1, 4410, endpoint=False)
            tone = (np.sin(2 * np.pi * 440 * t) * 16384).astype(np.int16)
            wavfile.write(wav, 44100, tone)

            wav2cc.main(
                [
                    '-i',
                    str(wav),
                    '--output-hpp',
                    str(hpp),
                    '--output-cc',
                    str(cc),
                    '--header-include',
                    'nlb/wav/clip.hpp',
                    '--symbol',
                    'clip',
                ],
                standalone_mode=False,
            )

            self.assertIn('extern const emb::yaal::AudioClip clip;', hpp.read_text())
            contents = cc.read_text()
            # 100ms at 22.05kHz + 50ms default padding
            expected_frames = 2205 + 1102
            self.assertIn(f'.num_frames = {expected_frames},', contents)


if __name__ == '__main__':
    unittest.main()
