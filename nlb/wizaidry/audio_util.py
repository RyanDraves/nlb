"""Audio utilities for handling audio input and output using sounddevice and pyaudio.

Derived from OpenAI's `openai-python` examples for real-time audio processing.
https://github.com/openai/openai-python/blob/f66d2e6fdc51c4528c99bb25a8fbca6f9b9b872d/examples/realtime/audio_util.py
"""

import io
import threading
from typing import Any

import numpy as np
import pyaudio
import pydub
import sounddevice as sd
from numpy import typing as npt

CHUNK_LENGTH_S = 0.05  # 100ms
SAMPLE_RATE = 24000
FORMAT = pyaudio.paInt16
CHANNELS = 1


def audio_to_pcm16_base64(audio_bytes: bytes) -> bytes:
    # Load the audio file from the byte stream
    audio = pydub.AudioSegment.from_file(io.BytesIO(audio_bytes))
    print(
        f'Loaded audio: {audio.frame_rate=} {audio.channels=} {audio.sample_width=} {audio.frame_width=}'
    )
    # Resample to 24kHz mono pcm16
    pcm_audio = (
        audio.set_frame_rate(SAMPLE_RATE)
        .set_channels(CHANNELS)
        .set_sample_width(2)
        .raw_data
    )
    return pcm_audio


class AudioPlayerAsync:
    def __init__(self):
        self.queue = []
        self.lock = threading.Lock()
        self.stream = sd.OutputStream(
            callback=self.callback,
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=np.int16,
            blocksize=int(CHUNK_LENGTH_S * SAMPLE_RATE),
        )
        self.playing = False
        self._frame_count = 0

    def callback(
        self, outdata: npt.NDArray, frames: int, time: Any, status: sd.CallbackFlags
    ):
        with self.lock:
            data = np.empty(0, dtype=np.int16)

            # Get next item from queue if there is still space in the buffer
            while len(data) < frames and len(self.queue) > 0:
                item = self.queue.pop(0)
                frames_needed = frames - len(data)
                data = np.concatenate((data, item[:frames_needed]))
                if len(item) > frames_needed:
                    self.queue.insert(0, item[frames_needed:])

            self._frame_count += len(data)

            # Fill the rest of the frames with zeros if there is no more data
            if len(data) < frames:
                data = np.concatenate(
                    (data, np.zeros(frames - len(data), dtype=np.int16))
                )

        outdata[:] = data.reshape(-1, 1)

    def reset_frame_count(self):
        self._frame_count = 0

    def get_frame_count(self):
        return self._frame_count

    def add_data(self, data: bytes):
        with self.lock:
            # bytes is pcm16 single channel audio data, convert to numpy array
            np_data = np.frombuffer(data, dtype=np.int16)
            self.queue.append(np_data)
            if not self.playing:
                self.start()

    def start(self):
        self.playing = True
        self.stream.start()

    def stop(self):
        self.playing = False
        self.stream.stop()
        with self.lock:
            self.queue = []

    def terminate(self):
        self.stream.close()
