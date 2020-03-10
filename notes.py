import math
from collections import OrderedDict


class Note(object):
    def __init__(self, frequency):
        self._frequency = frequency

    @property
    def frequency(self):
        return self._frequency

    @staticmethod
    def from_scientific(note):
        """
        Takes a note in the form of A4 or A4# and creates a Note. The number
        may be in the range [-1, inf), though at some point it becomes too high
        to be interesting.
        
        Based on https://en.wikipedia.org/wiki/Scientific_pitch_notation
        and https://github.com/mienaikoe/nodea/blob/gh-pages/core/Scales.js
        """

        base_note = note[0]
        if base_note not in "ABCDEFG":
            raise ValueError("Base note must be between A and G")

        tail = note[-1]
        if tail == "#":
            sharp = True
            note = note[:-1]
        else:
            sharp = False

        octave = int(note[1:])
        if octave < -1:
            raise ValueError("Octave cannot be less than -1")

        A4 = Note(440.0)
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

        return A4.add_octaves(octave - 4).add_half_steps(target_idx - A_idx)

    def copy(self):
        return Note(self.frequency)

    def add_half_steps(self, half_steps):
        self._frequency *= math.pow(2, (half_steps / 12.0))
        return self

    def add_cents(self, cents):
        self._frequency *= math.pow(2, (cents / 1200.0))
        return self

    def add_whole_steps(self, whole_steps):
        self._frequency *= math.pow(2, (whole_steps / 6.0))
        return self

    def add_octaves(self, octaves):
        self._frequency *= math.pow(2, octaves)
        return self

    def __repr__(self):
        return f"<Note {self.frequency}Hz>"


if __name__ == "__main__":
    for note in ("A4", "A0", "A-1", "A8", "A20"):
        print(f"{note}: {Note.from_scientific(note)}")

    for note in "C4 C4# D4 D4# E4 F4 F4# G4 G4# A4 A4# B4".split(" "):
        print(f"{note}: {Note.from_scientific(note)}")

    for note in "C4 C4# D4 D4# E4 F4 F4# G4 G4# A4 A4# B4".replace(
        "4", "3"
    ).split(" "):
        print(f"{note}: {Note.from_scientific(note)}")

    for note in "C4 C4# D4 D4# E4 F4 F4# G4 G4# A4 A4# B4".replace(
        "4", "8"
    ).split(" "):
        print(f"{note}: {Note.from_scientific(note)}")

    for note in "C4 C4# D4 D4# E4 F4 F4# G4 G4# A4 A4# B4".replace(
        "4", "-1"
    ).split(" "):
        print(f"{note}: {Note.from_scientific(note)}")

