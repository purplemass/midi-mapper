"""Translate midi messages between input/output devices."""

import signal
import sys
import time

import mido
from mido.ports import MultiPort
from rx.subjects import Subject
from rx import operators as ops


def io_ports(midi_stream):
    """Create input/output ports and add incoming messages to the stream."""

    def input_message(msg):
        midi_stream.on_next(msg)

    input_names = mido.get_input_names()
    output_names = mido.get_output_names()
    print(f'input_names: {input_names}')
    print(f'output_names: {output_names}')
    inports = MultiPort(
        [mido.open_input(
            device, callback=input_message) for device in input_names])
    outports = MultiPort(
        [mido.open_output(device) for device in input_names])
    return inports, outports


def process_message(msg):
    """Process incoming message."""
    return msg


def print_message(msg):
    """Print message."""
    print(msg)


def main():
    """Main loop of the application."""

    def signal_handler(signal, frame):
        # print('\n' * 100)
        print('\033[H\033[J')
        print('Keyboard interupt detected')
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    midi_stream = Subject()
    midi_stream.pipe(
        ops.map(lambda x: process_message(x)),
    ).subscribe(print_message)

    io_ports(midi_stream)

    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
