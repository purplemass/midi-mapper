"""Translate midi messages between input/output devices."""
import signal
import sys
import time

from rx.subject import Subject
from rx import operators as ops

from mappings import import_mappings
from utils import (
    change_bank,
    check_mappings,
    create_stream_data,
    io_ports,
    log,
    process_midi,
    translate_and_send,
)

MAPPINGS_FOLDER = './mappings/'


def main():
    """Main loop of the application."""

    mappings = import_mappings(MAPPINGS_FOLDER)

    midi_stream = Subject()
    _, outports = io_ports(midi_stream)
    midi_stream.pipe(
        ops.map(lambda x: create_stream_data(x, mappings, outports)),
        ops.map(lambda x: process_midi(x)),
        ops.map(lambda x: check_mappings(x)),
        ops.map(lambda x: change_bank(x)),
        ops.map(lambda x: translate_and_send(x)),
        ops.do_action(lambda x: log(x)),
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
