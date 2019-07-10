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


def process(midi):
    """Process incoming message."""

    if midi.type == 'control_change':
        mtype = 'CC'
        level = midi.value
        control = midi.control
    elif midi.type == 'note_off':
        mtype = 'OFF'
        level = midi.velocity
        control = midi.note
    elif midi.type == 'note_on':
        mtype = 'ON'
        level = midi.velocity
        control = midi.note

    return {
        'type': mtype,
        'channel': midi.channel + 1,
        'control': control,
        'level': level,
        'midi': midi,
    }


def translate(msg):
    """Translate message."""

    return {
        'type': getattr(msg['current']['midi'], 'type'),
        'channel': int(msg['translate']['o-channel']) - 1,
        'control': msg['translate']['o-control'],
        'level': msg['current']['level'],
    }


def send(msg, outports):
    """Send MIDI or NRPN message to output ports."""

    control = msg['control'].split(':')
    if len(control) == 2:
        send_nrpn(msg, control, outports)
    else:
        send_midi(msg, outports)


def send_midi(msg, outports):
    """Send MIDI to output ports."""

    outports.send(Message(
        channel=msg['channel'],
        control=int(msg['control']),
        value=msg['level'],
        type=msg['type']
    ))


def send_nrpn(msg, control, outports):
    """Send NRPN message of the following format:

        MIDI # 16 CC 99 = control[0]
        MIDI # 16 CC 98 = control[1]
        MIDI # 16 CC 6 = level
        MIDI # 16 CC 38 = 0

        Note that control is formatted like: '1:9'
    """
    send_midi({
        'channel': msg['channel'],
        'control': 99,
        'level': int(control[0]),
        'type': msg['type']
    }, outports)
    send_midi({
        'channel': msg['channel'],
        'control': 98,
        'level': int(control[1]),
        'type': msg['type']
    }, outports)
    send_midi({
        'channel': msg['channel'],
        'control': 6,
        'level': msg['level'],
        'type': msg['type']
    }, outports)
    send_midi({
        'channel': msg['channel'],
        'control': 38,
        'level': 0,
        'type': msg['type']
    }, outports)


def log(msg):
    """Log message to console."""

    print('[{}] {}__{} => {}__{:<25} {}'.format(
        msg['translate']['bank'],
        msg['translate']['input-device'],
        msg['translate']['description'],
        msg['translate']['output-device'],
        msg['translate']['o-description'],
        msg['current']['level'],
    ))
