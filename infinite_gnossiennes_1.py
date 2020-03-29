from itertools import groupby, islice
from collections import namedtuple
import random

import console
import sound

from midi import build_stream_from_midi
from streams import chunk_and_play, Stream
from signals import prevent_device_sleep


KeySound = namedtuple("KeySound", "frequency, duration, volume")
Node = namedtuple("Node", "stream, edges")
Edge = namedtuple("Edge", "delta_t, key")


def sounds_to_key_and_stream(sounds):
    key = set()
    stream = Stream()
    for sound in sounds:
        stream.add_sound(sound)

        key.add(
            KeySound(
                frequency=sound.frequency,
                duration=sound.duration,
                volume=sound.volume,
            )
        )
    return frozenset(key), stream


def build_graph(sounds):
    graph = {}

    previous_key, previous_stream = None, None
    for _, group in groupby(sounds, key=lambda sound: sound.start):
        key, stream = sounds_to_key_and_stream(group)

        if key not in graph.keys():
            graph[key] = Node(
                stream=stream.delayed(-stream.min_start), edges=[]
            )

        if previous_key is not None:
            graph[previous_key].edges.append(
                Edge(
                    delta_t=stream.min_start - previous_stream.min_start,
                    key=key,
                )
            )

        previous_key, previous_stream = key, stream

    return graph


def walk_graph(graph):
    offset = 0
    key = random.choice(list(graph.keys()))

    while True:
        yield from graph[key].stream.delayed(offset).stream

        if graph[key].edges:
            edge = random.choice(graph[key].edges)
            offset += edge.delta_t
            key = edge.key
        else:
            print("hit a dead end, starting from a random start")
            offset += 5
            key = random.choice(list(graph.keys()))


if __name__ == "__main__":
    console.clear()
    sound.stop_all_effects()

    gnossiennes = build_stream_from_midi("gnossiennes_1.mid")

    graph = build_graph(gnossiennes.stream)
    print(len(graph))
    for key, node in graph.items():
        print(key)
        for sound in node.stream.stream:
            print(sound)
        print(node.edges)
        print()

    with prevent_device_sleep():
        chunk_and_play(walk_graph(graph))

