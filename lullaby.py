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
from notes import Note


twinkle_twinkle_little_star_notes = [
    "C5 C5 G5 G5 A5 A5 G5",
    "F5 F5 E5 E5 D5 D5 C5",
    "G5 G5 F5 F5 E5 E5 D5",
    "G5 G5 F5 F5 E5 E5 D5",
    "C5 C5 G5 G5 A5 A5 G5",
    "F5 F5 E5 E5 D5 D5 C5",
]
twinkle_twinkle_little_star_notes = twinkle_twinkle_little_star_notes[:]
tinkle_twinkle_little_star_timings = [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.5]
note_length = 2.5


twinkle_twinkle_little_star = Stream()
current_time = 0
for phrase in twinkle_twinkle_little_star_notes:
    for note, timing in zip(
        phrase.split(" "), tinkle_twinkle_little_star_timings
    ):
        duration = note_length * timing
        twinkle_twinkle_little_star.add_sound(
            Sound(Note.from_scientific(note), duration, current_time)
        )
        current_time += duration


def fuzzy_start(sounds):
    for sound in sounds:
        yield sound.delayed(
            random.uniform(-note_length / 32.0, note_length / 32.0)
        )


def fuzzy_duration(sounds):
    for sound in sounds:
        yield sound.stretched(random.uniform(0.9, 1.1))


def dedune(sounds):
    for sound in sounds:
        detuned = sound.copy()
        detuned._frequency_source.add_cents(-50)
        yield detuned


loop, tap = make_loop_and_tap()


with prevent_device_sleep():
    chunk_and_play(
        log_sounds(
            window_sort(
                ensure_positive(
                    dedune(
                        fuzzy_duration(
                            fuzzy_start(
                                tap(
                                    loop(
                                        twinkle_twinkle_little_star.stream,
                                        loops=float("inf"),
                                        gap=0.1,
                                    )
                                )
                            )
                        )
                    )
                ),
                3,
            )
        )
    )

