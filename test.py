import wave
import time
import numpy as np
import itertools
import tempfile
import os

Fs = 44100


def join_channels(left, right):
    target_length = max(len(left), len(right))
    if len(left) < target_length:
        left = np.concatenate((left, np.zeros(target_length - len(left))))
    if len(right) < target_length:
        right = np.concatenate((right, np.zeros(target_length - len(right))))
    return np.vstack((left, right))


def time_array(duration, Fs=Fs):
    return np.linspace(0, duration, round(duration * Fs))


def sine(freq, t):
    return np.sin(2.0 * np.pi * freq * t)


def add_at(base, extra, t, Fs=Fs):
    start_index = round(t * Fs)
    end_index = start_index + len(extra)

    if end_index > len(base):
        base = np.concatenate((base, np.zeros(end_index - len(base))))

    base[start_index:end_index] += extra
    return base


def envelope(attack, drop, sustain, sustain_level, fall, data):
    total_length = data.shape[0]
    attack_length, drop_length, sustain_length, fall_length = (
        round(section * total_length)
        for section in (attack, drop, sustain, fall)
    )
    resulting_length = (
        attack_length + drop_length + sustain_length + fall_length
    )
    if resulting_length < total_length:
        sustain_length += total_length - resulting_length

    shape = np.concatenate(
        (
            np.linspace(0, 1, attack_length),
            np.linspace(1, sustain_level, drop_length),
            sustain_level * np.ones((sustain_length,)),
            np.linspace(sustain_level, 0, fall_length),
        )
    )
    return data * shape[:total_length]


def create_note(freq, duration):
    return 0.5 * envelope(
        0.1, 0.1, 0.7, 0.9, 0.1, sine(freq, time_array(duration))
    )


def write_sound(data, filename, Fs=Fs, bits_per_sample=32):
    CHANNELS = 2

    if data.shape[0] != CHANNELS:
        raise Exception(f"need a {CHANNELS}xN array of data: {data.shape}")

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


output_file = "test.wav"

import sound

twinkle_twinkle_little_star_notes = [
    "CCGGAAG",
    "FFEEDDC",
    "GGFFEED",
    "GGFFEED",
    "CCGGAAG",
    "FFEEDDC",
]
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
note_length = 3.5


class Note(object):
    def __init__(self, freq, duration, start):
        self._freq = freq
        self._duration = duration
        self._start = start

    @property
    def freq(self):
        return self._freq

    @property
    def duration(self):
        return self._duration

    @property
    def start(self):
        return self._start

    def shifted(self, offset):
        return Note(self.freq, self.duration, self.start + offset)

    def add_to(self, base):
        return add_at(base, create_note(self.freq, self.duration), self.start)

    def __repr__(self):
        return f"<Note {self.freq}Hz {self.duration}s at {self.start}s>"


class Piece(object):
    def __init__(self, *notes):
        self._notes = set(notes) if notes else set()

    @property
    def notes(self):
        return self._notes

    @property
    def notes_in_order(self):
        yield from sorted(self.notes, key=lambda note: note.start)

    @property
    def chords_in_order(self):
        def note_start(note):
            return note.start

        for _, g in itertools.groupby(
            sorted(self.notes, key=note_start), key=note_start
        ):
            yield set(g)

    @property
    def first_start(self):
        if not self.notes:
            return 0

        return next(self.chords_in_order).pop().start

    @property
    def last_start(self):
        if not self.notes:
            return 0

        return list(self.chords_in_order)[-1].pop().start

    @property
    def total_length(self):
        if not self.notes:
            return 0

        last_group = list(self.chords_in_order)[-1]
        return (
            max(note.duration for note in last_group) + last_group.pop().start
        )

    def add_note(self, note):
        self._notes.add(note)

    def subpieces(self, length_break=7, forever=False):
        group = None
        while True:
            if group is not None:
                offset = group.total_length - group.last_start
            else:
                offset = 0

            group = Piece()

            for chord in self.chords_in_order:
                if group.last_start > length_break:
                    yield group
                    offset -= group.last_start
                    group = Piece()

                for note in chord:
                    group.add_note(note.shifted(offset))

            if group.last_start > 0:
                yield group

            if not forever:
                break

    def waveform(self):
        w = np.array([])
        for note in self.notes:
            w = note.add_to(w)
        return w


def play_audio_asynchronously(data):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        filename = f.name

    write_sound(data, filename)
    sound.play_effect(filename)
    return filename


twinkle_twinkle_little_star = Piece()
current_time = 0
for phrase in twinkle_twinkle_little_star_notes:
    for note, timing in zip(phrase, tinkle_twinkle_little_star_timings):
        duration = note_length * timing
        twinkle_twinkle_little_star.add_note(
            Note(note_to_frequency[note], duration * 0.8, current_time)
        )
        twinkle_twinkle_little_star.add_note(
            Note(
                note_to_frequency[note] * 2,
                duration * 1.2,
                current_time + (0.125 * note_length),
            )
        )
        current_time += duration

print("original")
print(twinkle_twinkle_little_star.notes)


def play_stream(sections):
    deadline = None
    filename = None
    try:
        for section in sections:
            if filename is not None:
                os.remove(filename)
            if deadline is not None:
                time.sleep(deadline - time.monotonic())
            w = section.waveform()
            deadline = time.monotonic() + section.last_start
            filename = play_audio_asynchronously(join_channels(w, w))
    finally:
        if filename is not None:
            try:
                os.remove(filename)
            except:
                pass


play_stream(twinkle_twinkle_little_star.subpieces(length_break=3, forever=True))

