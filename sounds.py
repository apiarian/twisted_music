import wave
import time
import itertools
import tempfile
import os
import functools
from abc import ABC, abstractmethod
import math
from collections import namedtuple

import numpy as np

from signals import (
    sine,
    time_array,
    add_at,
    n_samples,
    play_sound_asynchronously,
)


class Sound(ABC):
    def __init__(self, start, duration):
        self._start = start
        self._duration = duration

    @abstractmethod
    def copy(self):
        pass

    @property
    def start(self):
        return self._start

    @property
    def duration(self):
        return self._duration

    @property
    def end(self):
        return self.start + self.duration

    @property
    @abstractmethod
    def waveform_source(self):
        pass

    @property
    def waveform(self):
        return self.waveform_source(time_array(self.duration))

    def delayed(self, offset):
        c = self.copy()
        c._start += offset
        return c

    def stretched(self, scale):
        c = self.copy()
        c._duration *= scale
        return c


Overtone = namedtuple(
    "Overtone", "frequency_multiplier, phase_shift, amplitude"
)


class Tone(Sound):
    def __init__(
        self,
        start,
        duration,
        frequency,
        overtones,
        volume,
        attack_seconds,
        decay_seconds,
        sustain_level,
        release_seconds,
    ):
        super().__init__(start, duration)
        self._frequency = frequency
        self._overtones = overtones
        self._volume = volume
        self._attack_seconds = attack_seconds
        self._decay_seconds = decay_seconds
        self._sustain_level = sustain_level
        self._release_seconds = release_seconds

    def copy(self):
        return Tone(
            self.start,
            self.duration,
            self.frequency,
            self.overtones,
            self.volume,
            self.attack_seconds,
            self.decay_seconds,
            self.sustain_level,
            self.release_seconds,
        )

    @property
    def frequency(self):
        return self._frequency

    @property
    def overtones(self):
        return self._overtones.copy()

    @property
    def volume(self):
        return self._volume

    @property
    def attack_seconds(self):
        return self._attack_seconds

    @property
    def decay_seconds(self):
        return self._decay_seconds

    @property
    def sustain_level(self):
        return self._sustain_level

    @property
    def release_seconds(self):
        return self._release_seconds

    @property
    def waveform_source(self):
        def ws(t):
            result = sine(self.frequency, 0, t)
            for frequency_multiplier, phase_shift, amplitude in self.overtones:
                result += amplitude * sine(
                    frequency_multiplier * self.frequency, phase_shift, t
                )

            total_samples = len(t)
            ATTACK, DECAY, RELEASE = 0, 1, 2
            phase_samples = [
                n_samples(t)
                for t in (
                    self.attack_seconds,
                    self.decay_seconds,
                    self.release_seconds,
                )
            ]
            i = 0
            while sum(phase_samples) > total_samples:
                phase_samples[i] = math.floor(phase_samples[i] * 0.9)
                i = (i + 1) % 3
            sustain_samples = total_samples - sum(phase_samples)
            result *= np.concatenate(
                (
                    np.linspace(0, self.volume, phase_samples[ATTACK]),
                    np.linspace(
                        self.volume,
                        self.volume * self.sustain_level,
                        phase_samples[DECAY],
                    ),
                    self.volume
                    * self.sustain_level
                    * np.ones((sustain_samples,)),
                    np.linspace(
                        self.volume * self.sustain_level,
                        0,
                        phase_samples[RELEASE],
                    ),
                )
            )

            return result

        return ws
        
    def detuned(self, mutator):
        c = self.copy()
        c._frequency = mutator(c.frequency)
        return c
        
    def __repr__(self):
        return f"<Tone {self.duration}s at {self.start}s, {self.frequency}Hz with {self.overtones} overtones, {self.volume} volume, ADSR({self.attack_seconds}, {self.decay_seconds}, {self.sustain_level}, {self.release_seconds})>"


if __name__ == "__main__":
    cleanup = play_sound_asynchronously(
        Tone(0, 1, 440, [], 0.5, 0.1, 0.1, 0.1, 0.1).waveform,
        Tone(0, 2, 445, [], 0.5, 0.1, 0.1, 0.1, 0.1).waveform,
    )
    cleanup()

