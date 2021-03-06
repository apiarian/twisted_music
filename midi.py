import mido
from collections import defaultdict
import functools

from numpy import pi

from streams import Stream, chunk_and_play
from sounds import Tone, Overtone
from notes import midi_note_frequency


def build_stream_from_midi(filename):
    mid = mido.MidiFile(filename)
    merged_tracks = mido.merge_tracks(mid.tracks)

    bpm = None
    current_time = 0

    active_notes = {
        channel: defaultdict(list)
        for channel in set(
            msg.channel for msg in merged_tracks if "channel" in msg.dict()
        )
    }

    stream = Stream()

    for msg in merged_tracks:
        if msg.type == "note_on" and msg.velocity == 0:
            # turn a zero velocity note on into an equivalent note off
            data = msg.dict()
            data["type"] = "note_off"
            msg = msg.from_dict(data)

        if bpm is not None:
            current_time += msg.time / mid.ticks_per_beat / bpm * 60

        if msg.type == "set_tempo":
            bpm = mido.tempo2bpm(msg.tempo)

        elif msg.type == "note_on":
            if bpm is None:
                raise Exception(f"no tempo found before the first note")

            active_notes[msg.channel][msg.note].append(
                (current_time, msg.velocity)
            )

        elif msg.type == "note_off":
            if not active_notes[msg.channel][msg.note]:
                raise Exception(f"notes: {active_notes}, disabling note: {msg}")

            if current_time is None:
                raise Exception(f"no tempo found before the first note")

            if msg.velocity != 0:
                raise Exception(
                    f"do not konw how to work with non-zero note_off velocity: {msg}"
                )

            started, initial_velocity = active_notes[msg.channel][
                msg.note
            ].pop()

            if msg.channel == 2:
                continue

            duration = current_time - started
            if duration > 5:
                raise Exception(f"would have created a very long note: {msg}")
            stream.add_sound(
                Tone(
                    start=started,
                    duration=duration,
                    frequency=midi_note_frequency(msg.note),
                    overtones=[
                        Overtone(2, 0.5 * pi, 0.5),
                        Overtone(3, 0, 0.3),
                        Overtone(4, 0.25 * pi, 0.2),
                        Overtone(5, 0, 0.2),
                    ],
                    volume=0.4 * initial_velocity / 127,
                    attack_seconds=0.1,
                    decay_seconds=0.1,
                    sustain_level=0.75,
                    release_seconds=0.1,
                )
            )

        elif msg.type in (
            "time_signature",
            "key_signature",
            "program_change",
            "control_change",
            "track_name",
            "smpte_offset",
            "midi_port",
            "end_of_track",
        ):
            continue

        else:
            raise Exception(f"unkown message: {msg}")

    return stream


if __name__ == "__main__":
    mid = mido.MidiFile("gnossiennes_1.mid")
    for track_num, track in enumerate(mid.tracks):
        # print(f"{track_num}: {track}")
        for msg in track:
            if msg.type in ("note_on", "note_off"):
                pass
            # print(msg)

    print("all together")
    for msg in mido.merge_tracks(mid.tracks):
        d = msg.dict()
        if "note" not in d or d["note"] != 61:
            pass
        print(msg)

    stream = build_stream_from_midi("satie_gnoissienne1.midi")
    stream = build_stream_from_midi("cs1-1pre.mid")
    #stream = build_stream_from_midi("gnossiennes_1.mid")
    chunk_and_play(stream.stream, length_break=10)

