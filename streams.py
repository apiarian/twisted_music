import itertools
import time

from signals import empty, add_at, play_sound_asynchronously
from sounds import Sound


class Stream(object):
    def __init__(self):
        self._sounds = set()

    def add_sound(self, sound):
        self._sounds.add(sound)

    @property
    def sounds(self):
        return self._sounds

    @property
    def is_empty(self):
        return not self.sounds

    @property
    def min_start(self):
        return min(sound.start for sound in self.sounds)

    @property
    def max_start(self):
        return max(sound.start for sound in self.sounds)

    @property
    def max_end(self):
        return max(sound.end for sound in self.sounds)

    @property
    def duration(self):
        return self.max_end - self.min_start

    @property
    def stream(self):
        for sound in sorted(self.sounds, key=lambda sound: sound.start):
            yield sound

    def waveform(self, offset=0):
        chunk_waveform = empty()
        for sound in self.sounds:
            chunk_waveform = add_at(
                chunk_waveform, sound.waveform, sound.start - offset
            )
        return chunk_waveform

    def deplayed(self, offset):
        result = Stream()
        for sound in self.sounds:
            result.add_sound(sound.delayed(offset))
        return result

    @staticmethod
    def chunk_ordered_sounds(sounds, length_break=4):
        chunk = Stream()
        for _, chord in itertools.groupby(
            sounds, key=lambda sound: sound.start
        ):
            for sound in chord:
                chunk.add_sound(sound)

            if chunk.duration >= length_break:
                yield chunk
                chunk = Stream()

        if not chunk.is_empty:
            yield chunk

    @staticmethod
    def play_streams(streams):
        offset = 0

        deadline = None
        audio_cleanup = None
        for stream in streams:
            waveform = stream.waveform(offset)
            max_start = stream.max_start

            if audio_cleanup is not None:
                audio_cleanup()

            if deadline is not None:
                if (deadline - time.monotonic()) < 1:
                    print("less than one second left to wait")
                time.sleep(deadline - time.monotonic())
            # NOTE: we want to do the most we can between starting the playback
            # and sleeping. So there should be a minimum of code right here.
            audio_cleanup = play_sound_asynchronously(waveform, waveform)

            deadline = time.monotonic() + max_start - offset
            offset = max_start


def chunk_and_play(sounds, length_break=4):
    Stream.play_streams(
        Stream.chunk_ordered_sounds(sounds, length_break=length_break)
    )


def make_loop_and_tap():
    class Store(object):
        def __init__(self):
            self._stream = Stream()

        def add_sound(self, sound):
            self._stream.add_sound(sound)

        def return_and_reset(self):
            result = self._stream.deplayed(self._stream.duration)
            self._stream = Stream()
            return result

    store = Store()

    def loop(sounds, loops=float("inf"), gap=0):
        while loops > 0:
            loops -= 1
            yield from sounds
            sounds = store.return_and_reset().deplayed(gap).stream

    def tap(sounds):
        for sound in sounds:
            store.add_sound(sound)
            yield sound

    return loop, tap


def simple_loop(sounds, loops=float("inf"), gap=0):
    loop, tap = make_loop_and_tap()
    yield from tap(loop(sounds, loops, gap))


def window_sort(sounds, window):
    """Ensure that sounds are ordered within a window of seconds"""

    buffer = []
    for sound in sounds:
        buffer.append(sound)
        buffer.sort(key=lambda sound: sound.start)
        while buffer[-1].start - buffer[0].start > window:
            yield buffer.pop(0)

    yield from buffer


def ensure_positive(sounds):
    """
    Makes sure that if a stream of ordered sounds happens to start at a
    negative time, it is shifted forward to start at zero.
    """
    offset = None
    for sound in sounds:
        if offset is None:
            if sound.start < 0:
                offset = -sound.start
            else:
                offset = 0

        yield sound.delayed(offset)


def log_sounds(sounds):
    for sound in sounds:
        print(sound)
        yield sound


if __name__ == "__main__":
    s = Stream()
    s.add_sound(Sound(440, 1, 0))
    s.add_sound(Sound(660, 1, 0.5))
    s.add_sound(Sound(880, 0.5, 2))

    print("just once")
    for snd in log_sounds(s.stream):
        pass

    print("twice")
    for snd in log_sounds(simple_loop(s.stream, loops=2, gap=3)):
        pass

    print("forever")
    for snd in log_sounds(
        itertools.islice(simple_loop(s.stream, loops=float("inf"), gap=3), 10)
    ):
        pass

    print("chunks")
    for chunk in itertools.islice(
        Stream.chunk_ordered_sounds(
            simple_loop(s.stream, loops=float("inf"), gap=3)
        ),
        3,
    ):
        print(list(s for s in chunk.stream))

    chunk_and_play(
        itertools.islice(simple_loop(s.stream, loops=float("inf"), gap=0.5), 20)
    )

