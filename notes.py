import math
from collections import OrderedDict


def add_half_steps(half_steps, frequency):
    return frequency * math.pow(2, (half_steps / 12.0))


def add_cents(cents, frequency):
    return frequency * math.pow(2, (cents / 1200.0))


def add_whole_steps(whole_steps, frequency):
    return frequency * math.pow(2, (whole_steps / 6.0))


def add_octaves(octaves, frequency):
    return frequency * math.pow(2, octaves)


def scientific_note_frequency(note_name):
    """
    Takes a note in the form of A4 or A4# and creates a Note. The number
    may be in the range [-1, inf), though at some point it becomes too high
    to be interesting.
        
    Based on https://en.wikipedia.org/wiki/Scientific_pitch_notation
    and https://github.com/mienaikoe/nodea/blob/gh-pages/core/Scales.js
    """

    base_note = note_name[0]
    if base_note not in "ABCDEFG":
        raise ValueError("Base note must be between A and G")

    tail = note_name[-1]
    if tail == "#":
        sharp = True
        note_name = note_name[:-1]
    else:
        sharp = False

    octave = int(note_name[1:])
    if octave < -1:
        raise ValueError("Octave cannot be less than -1")

    A4 = 440.0
    note_order = [
        "C",
        "C#",
        "D",
        "D#",
        "E",
        "F",
        "F#",
        "G",
        "G#",
        "A",
        "A#",
        "B",
    ]
    A_idx = note_order.index("A")
    target_idx = note_order.index(base_note + "#" if sharp else base_note)

    return add_half_steps(target_idx - A_idx, add_octaves(octave - 4, A4))


def midi_note_frequency(note):
    return 440.0 * pow(2, (note - 69) / 12)


if __name__ == "__main__":
    for note in ("A4", "A0", "A-1", "A8", "A20"):
        print(f"{note}: {scientific_note_frequency(note)}")

    for note in "C4 C4# D4 D4# E4 F4 F4# G4 G4# A4 A4# B4".split(" "):
        print(f"{note}: {scientific_note_frequency(note)}")

    for note in "C4 C4# D4 D4# E4 F4 F4# G4 G4# A4 A4# B4".replace(
        "4", "3"
    ).split(" "):
        print(f"{note}: {scientific_note_frequency(note)}")

    for note in "C4 C4# D4 D4# E4 F4 F4# G4 G4# A4 A4# B4".replace(
        "4", "8"
    ).split(" "):
        print(f"{note}: {scientific_note_frequency(note)}")

    for note in "C4 C4# D4 D4# E4 F4 F4# G4 G4# A4 A4# B4".replace(
        "4", "-1"
    ).split(" "):
        print(f"{note}: {scientific_note_frequency(note)}")

