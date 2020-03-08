import wave
import time
import itertools
import tempfile
import os
import random

import numpy as np

from streams import (
    Stream,
    make_loop_and_tap,
    chunk_and_play,
    window_sort,
    log_sounds,
    ensure_positive,
)
from sounds import Sound
from signals import prevent_device_sleep


twinkle_twinkle_little_star_notes = [
    "CCGGAAG",
    "FFEEDDC",
    "GGFFEED",
    "GGFFEED",
    "CCGGAAG",
    "FFEEDDC",
]
twinkle_twinkle_little_star_notes = twinkle_twinkle_little_star_notes[:]
tinkle_twinkle_little_star_timings = [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.5]
note_to_frequency = {
    "B": 493.8833,
    "C": 523.2511,
    "D": 587.3295,
    "E": 659.2551,
    "F": 698.4565,
    "G": 783.9909,
    "A": 880.0000,
}
note_length = 2.5


twinkle_twinkle_little_star = Stream()
current_time = 0
for phrase in twinkle_twinkle_little_star_notes:
    for note, timing in zip(phrase, tinkle_twinkle_little_star_timings):
        duration = note_length * timing
        twinkle_twinkle_little_star.add_sound(
            Sound(note_to_frequency[note], duration, current_time)
        )
        current_time += duration


def fuzzy_start(sounds):
    for sound in sounds:
        yield sound.delayed(
            random.uniform(-note_length / 16.0, note_length / 16.0)
        )


def fuzzy_duration(sounds):
    for sound in sounds:
        yield sound.stretched(random.uniform(0.75, 1.25))


loop, tap = make_loop_and_tap()


with prevent_device_sleep():
    chunk_and_play(
        log_sounds(
            window_sort(
                tap(
                    ensure_positive(
                        fuzzy_duration(
                            fuzzy_start(
                                loop(
                                    twinkle_twinkle_little_star.stream,
                                    loops=float("inf"),
                                    gap=0.1,
                                )
                            )
                        )
                    )
                ),
                3,
            )
        )
    )

