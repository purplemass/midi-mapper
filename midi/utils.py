"""Utility functions."""

import csv
import sys

import mido
from mido.ports import MultiPort
from mido import Message


active_bank = 1


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
            if '-v' in sys.argv:
                print(f'\t\t\t\t\t\t\t\t -----> {msg}')

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


def process(midi, translations, outports):
    """Process incoming message."""

    if midi.type == 'control_change':
        mtype = 'CC'
        control = midi.control
        level = midi.value
    elif midi.type == 'note_off':
        mtype = 'OFF'
        control = midi.note
        level = midi.velocity
    elif midi.type == 'note_on':
        mtype = 'ON'
        control = midi.note
        level = midi.velocity
    elif midi.type == 'program_change':
        mtype = 'PG'
        control = midi.program
        level = 0

    return {
        'type': mtype,
        'channel': midi.channel + 1,
        'control': control,
        'level': level,
        'midi': midi,
        'translations': translations,
        'outports': outports,
    }


def check(msg):
    """Check incoming message."""

    def check(translation):
        return (
            translation['type'] == msg['type'] and
            int(translation['channel']) == msg['channel'] and
            int(translation['control']) == msg['control'] and
            (int(translation['bank']) == 0 or
                int(translation['bank']) == active_bank)
        )

    return [{
        'translate': translate,
        'msg': msg
    } for translate in msg['translations'] if check(translate)]


def change_bank(data):
    """Check incoming bank change messages."""

    global active_bank

    def reset_banks(data):
        """Turn all bank buttons off and turn on the active bank."""
        midi = data['msg']['midi']
        banks = [translate['control'] for translate in data['msg'][
            'translations'] if translate['output-device'] == 'Bank']
        for bank in banks:
            data['msg']['outports'].send(Message(
                type='note_off',
                channel=midi.channel,
                note=int(bank),
            ))

        data['msg']['outports'].send(Message(
            type='note_on',
            channel=midi.channel,
            note=midi.note,
        ))

    if (int(data['translate']['bank']) == 0 and
            data['translate']['output-device'].lower() == 'bank'):
        active_bank = int(data['translate']['o-channel'])
        reset_banks(data)
        data = None
    return data


def translate(data):
    """Translate message."""

    midi = data['msg']['midi']
    return {
        'type': midi.type,
        'channel': int(data['translate']['o-channel']) - 1,
        'control': data['translate']['o-control'],
        'level': data['msg']['level'],
        'midi': midi,
        'translations': data['msg']['translations'],
        'outports': data['msg']['outports'],
    }


def send(msg):
    """Send MIDI or NRPN message to output ports."""

    control = msg['control'].split(':')
    if len(control) == 2:
        send_nrpn(msg, control, msg['outports'])
    else:
        send_midi(msg, msg['outports'])


def log(msg):
    """Log message to console."""

    print('[{}] {}__{} => {}__{:<25} {}'.format(
        active_bank,
        msg['translate']['input-device'],
        msg['translate']['description'],
        msg['translate']['output-device'],
        msg['translate']['o-description'],
        msg['msg']['level'],
    ))


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
