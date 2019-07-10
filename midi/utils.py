"""Utility functions."""

import csv

import mido
from mido.ports import MultiPort
from mido import Message


TRANSLATIONS_FILE = './mappings/mappings.csv'


def csv_dict_list(filename):
    """Read translations CSV file and convert to a dictionary.

    Ensure output fieldnames are not the same as input fieldnames.
    """

    with open(filename, 'r') as fd:
        reader = csv.reader(fd, delimiter=',')
        fieldnames = next(reader)
        fieldnames = [f.lower().replace(' ', '-') for f in fieldnames]
        prefix_output_fieldname = False
        for idx, name in enumerate(fieldnames):
            if prefix_output_fieldname is True:
                fieldnames[idx] = f'o-{fieldnames[idx]}'
            if 'output' in name:
                prefix_output_fieldname = True
        data = list(csv.DictReader(fd, fieldnames))
    return data


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


def check(msg):
    """Check incoming message."""

    def check(translation):
        return (
            translation['type'] == msg['type'] and
            int(translation['channel']) == msg['channel'] and
            int(translation['control']) == msg['control']
        )

    translations = csv_dict_list(TRANSLATIONS_FILE)

    return [{
        'translate': t,
        'current': msg
    } for t in translations if check(t)]


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
