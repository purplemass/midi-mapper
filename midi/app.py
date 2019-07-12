"""Translate midi messages between input/output devices."""
import signal
import sys
import time

from rx.subject import Subject
from rx import operators as ops

from stream import (
    check_mappings,
    create_stream_data,
    log,
    process_midi,
    translate_and_send,
)
from store import store
from utils import (
    get_bank_message,
    io_ports,
    reset_banks_and_controls,
)


def main() -> None:
    """Main loop of the application."""

    midi_stream = Subject()
    io_ports(midi_stream)

    translated_stream = midi_stream.pipe(
        ops.map(lambda x: create_stream_data(x)),
        ops.map(lambda x: process_midi(x)),
        ops.map(lambda x: check_mappings(x)),
        ops.filter(lambda x: x['translations']),
    )

    translated_stream.pipe(
        ops.do_action(lambda x: log(x)),
        ops.map(lambda x: translate_and_send(x)),
    ).subscribe()

    store.pipe(
        ops.map(lambda x: x.get('active_bank')),
        ops.filter(lambda x: x is not None),
        ops.with_latest_from(translated_stream.pipe(
            ops.filter(
                lambda x: x['translations'][0]['o-type'] == 'bank_change')
        )),
        ops.do_action(lambda x: reset_banks_and_controls(x)),
    ).subscribe()

    # send initial bank message to reset controller
    reset_bank_message = get_bank_message(8)
    if reset_bank_message is not None:
        midi_stream.on_next(reset_bank_message)

    while True:
        time.sleep(1)


if __name__ == "__main__":
    """Add keyboard interupt handler and run main."""

    def signal_handler(signal, frame) -> None:
        print('\033[H\033[J')
        print('Keyboard interupt detected')
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    main()
