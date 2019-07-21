"""Translate midi messages between input/output devices."""
import signal
import sys
import time

from rx.subject import Subject
from rx import operators as ops

from .mappings import import_mappings
from .store import store
from .stream import get_translations
from .stream import log
from .stream import process_midi
from .stream import translate_and_send
from .stream import set_bank
from .utils import set_io_ports


def signal_handler(*args) -> None:
    """Handle keyboard interupt and close all ports."""
    print('\033[H\033[J')
    print('Keyboard interupt detected\n')
    for port in store.get('inports').ports + store.get('outports').ports:
        if port.closed is False:  # pragma: no cover
            print(f'Closing {port}')
            port.close()
    sys.exit(0)


def run() -> None:
    """Update store, create streams and run the main loop."""

    midi_stream = Subject()
    store.update('mappings', import_mappings())
    set_io_ports(midi_stream)

    translations_stream = midi_stream.pipe(
        ops.map(lambda x: process_midi(x)),
        ops.map(lambda x: get_translations(x)),
        ops.flat_map(lambda x: x),
    )

    translations_stream.pipe(
        ops.map(lambda x: translate_and_send(x)),
        ops.do_action(lambda x: log(x)),
    ).subscribe(on_error=lambda x: print(f'ERROR: {x}'))

    # send initial bank to reset controller
    set_bank(1, initial=True)

    while True:
        time.sleep(1)


if __name__ == "__main__":  # pragma: no cover
    """Add keyboard interupt handler and run application."""
    signal.signal(signal.SIGINT, signal_handler)
    run()
