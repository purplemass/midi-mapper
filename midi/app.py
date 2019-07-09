"""Translate midi messages between input/output devices."""

import signal
import sys
import time

import mido
from mido import Message
from mido.ports import MultiPort

from rx.subjects import Subject
from rx import operators as ops

from utils import csv_dict_list


TRANSLATIONS_FILE = './mappings/mappings.csv'
translations = csv_dict_list(TRANSLATIONS_FILE)


def io_ports(midi_stream):
    """Create input/output ports and add incoming messages to the stream."""

    def input_message(msg):
        if (
            msg.type != 'clock' and
            msg.type != 'start' and
            msg.type != 'stop'
        ):
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


def process(msg):
    """Process incoming message."""

    if msg.type == 'control_change':
        mtype = 'CC'
        value = msg.value
        control = msg.control
    elif msg.type == 'note_off':
        mtype = 'OFF'
        value = msg.velocity
        control = msg.note
    elif msg.type == 'note_on':
        mtype = 'ON'
        value = msg.velocity
        control = msg.note

    return {
        'type': mtype,
        'channel': msg.channel + 1,
        'control': control,
        'value': value,
        'midi': msg,
    }


def check(msg):
    """Check incoming message."""

    def check(translation):
        return (
            translation['type'] == msg['type'] and
            int(translation['channel']) == msg['channel'] and
            int(translation['control']) == msg['control']
        )

    return [{
        'translate': t,
        'current': msg
    } for t in translations if check(t)]


def translate(msg):
    """Translate message."""

    channel = int(msg['translate']['o-channel']) - 1
    translated = Message(
        type=getattr(msg['current']['midi'], 'type'),
        channel=channel,
        control=int(msg['translate']['o-control']),
        value=msg['current']['value'],
    )
    return translated


def log(msg):
    """Log message to console."""

    print('[{}] {}__{} => {}__{:<25} {}'.format(
        msg['translate']['bank'],
        msg['translate']['input-device'],
        msg['translate']['description'],
        msg['translate']['output-device'],
        msg['translate']['o-description'],
        msg['current']['value'],
    ))


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
        ops.map(lambda x: translate(x)),
        ops.do_action(lambda x: outports.send(x)),
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
