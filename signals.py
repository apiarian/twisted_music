import wave
import time
import itertools
import tempfile
import os

from contextlib import contextmanager

import console
import sound
import numpy as np

Fs = 44100


def time_array(duration):
    return np.linspace(0, duration, n_samples(duration))
    

def n_samples(duration):
    return int(round(duration * Fs))


def sine(freq, phase, t):
    return np.sin(2.0 * np.pi * freq * t + phase)
    

def square(freq, phase, t):
    return np.sign(sine(freq, phase, t))
    
    
def empty():
    return np.array([])


def add_at(base, extra, t):
    if t < 0:
        raise Exception("negative times are not supported")

    start_index = round(t * Fs)
    end_index = start_index + len(extra)

    if end_index > len(base):
        base = np.concatenate((base, np.zeros(end_index - len(base))))

    base[start_index:end_index] += extra
    return base


def _join_channels(left, right):
    target_length = max(len(left), len(right))
    if len(left) < target_length:
        left = np.concatenate((left, np.zeros(target_length - len(left))))
    if len(right) < target_length:
        right = np.concatenate((right, np.zeros(target_length - len(right))))
    return np.vstack((left, right))


def write_sound(left, right, filename, bits_per_sample=32):
    CHANNELS = 2

    data = _join_channels(left, right)

    # need the data to be in a samples x channels layout
    data = data.T

    if bits_per_sample == 8:
        data = data + abs(min(data))
        data = np.array(
            np.round((data / max(data)) * 255), dtype=np.dtype("<u1")
        )
    else:
        data = np.array(
            np.round(data * ((2 ** (bits_per_sample - 1)) - 1)),
            dtype=np.dtype(f"<i{bits_per_sample//8}"),
        )

    with wave.open(filename, mode="wb") as f:
        f.setparams(
            (CHANNELS, bits_per_sample // 8, Fs, 0, "NONE", "not compressed")
        )
        f.writeframes(data.tostring())


def play_sound_asynchronously(left, right):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        filename = f.name

    write_sound(left, right, filename)
    sound.play_effect(filename)

    def cleanup():
        try:
            os.remove(filename)
        except:
            pass

    return cleanup

@contextmanager
def prevent_device_sleep():
    def fix_set_idle_timer_disabled(flag=True):
        from objc_util import on_main_thread

        on_main_thread(console.set_idle_timer_disabled)(flag)
        
    fix_set_idle_timer_disabled(True)
    try:
        yield
    finally:
        fix_set_idle_timer_disabled(False)
