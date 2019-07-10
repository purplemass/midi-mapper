"""Translate midi messages between input/output devices."""

import signal
import sys
import time

from rx.subjects import Subject
from rx import operators as ops

from utils import (
    io_ports,
    check,
    change_bank,
    process,
    translate,
    send,
    log,
)


def main():
    """Main loop of the application."""

    midi_stream = Subject()
    _, outports = io_ports(midi_stream)
    midi_stream.pipe(
        ops.map(lambda x: process(x)),
        ops.map(lambda x: check(x)),
        ops.filter(lambda x: len(x) > 0),
        ops.map(lambda x: x[0]),
        ops.do_action(lambda x: log(x)),
        ops.map(lambda x: change_bank(x, outports)),
        ops.filter(lambda x: x is not None),
        ops.map(lambda x: translate(x)),
        ops.do_action(lambda x: send(x, outports)),
    ).subscribe()

    while True:
        time.sleep(1)


if __name__ == "__main__":
    """Add keyboard interupt handler and run main."""

    def signal_handler(signal, frame):
        print('\033[H\033[J')
        print('Keyboard interupt detected')
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    main()
