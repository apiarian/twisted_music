import wave
import time
import itertools
import tempfile
import os

import numpy as np

from signals import sine, time_array, adsr_envelope, add_at


class Sound(object):
    def __init__(self, freq, duration, start, tone=sine):
        self._freq = freq
        self._duration = duration
        self._start = start
        self._tone = tone

    def copy(self):
        return Sound(self._freq, self._duration, self._start, self._tone)

    @property
    def freq(self):
        return self._freq

    @property
    def duration(self):
        return self._duration

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self.start + self.duration

    def delay(self, offset):
        self._start += offset
        return self

    def delayed(self, offset):
        return self.copy().delay(offset)

    def stretch(self, scale):
        self._duration *= scale
        return self

    def stretched(self, scale):
        return self.copy().stretch(scale)

    @property
    def waveform(self):
        return 0.4 * adsr_envelope(
            0.05,
            0.1,
            0.9,
            0.15,
            self._tone(self.freq, time_array(self.duration)),
        )

    def __repr__(self):
        return f"<Sound {self.freq}Hz {self.duration}s at {self.start}s>"

