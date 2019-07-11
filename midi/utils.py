"""Utility functions."""
from typing import Any, Dict, Tuple
import sys

import mido  # type: ignore
from mido.ports import MultiPort  # type: ignore
from mido import Message


active_bank = 1


def io_ports(midi_stream: Any) -> Tuple[Any, Any]:
    """Create input/output ports and add incoming messages to the stream."""

    def input_message(msg: Message) -> None:
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


def create_stream_data(midi, mappings, outports) -> Dict[str, Any]:
    return {
        'msg': {},
        'midi': midi,
        'mappings': mappings,
        'outports': outports,
        'translate': [],
    }


def process_midi(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process incoming message."""
    midi = data['midi']
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

    data['msg'] = {
        'type': mtype,
        'channel': midi.channel + 1,
        'control': control,
        'level': level,
    }
    return data


def check_mappings(data: Dict[str, Any]) -> Dict[str, Any]:
    """Check incoming message for matches in mappings."""

    def check(mapping):
        return (
            mapping['type'] == data['msg']['type'] and
            int(mapping['channel']) == data['msg']['channel'] and
            int(mapping['control']) == data['msg']['control'] and
            (int(mapping['bank']) == 0 or
                int(mapping['bank']) == active_bank)
        )

    data['translate'] = [
        translate for translate in data['mappings'] if check(translate)]
    return data


def log(data: Dict[str, Any]) -> None:
    """Log messages to console."""
    for translate in data['translate']:
        print('[{}] {}__{} => {}__{:<25} {}'.format(
            active_bank,
            translate['input-device'],
            translate['description'],
            translate['output-device'],
            translate['o-description'],
            data['msg']['level'],
        ))


def change_bank(data: Dict[str, Any]) -> Dict[str, Any]:
    """Check incoming bank change messages."""

    global active_bank

    def reset_banks_and_controls(data: Dict[str, Any]) -> None:
        """Turn all bank buttons off and turn on the active bank.

        Reset controls to their memory value.
        """
        outports = data['outports']
        mappings = data['mappings']
        midi = data['midi']
        banks = [translate['control'] for translate in mappings if translate[
            'output-device'] == 'Bank']
        for bank in banks:
            outports.send(Message(
                type='note_off',
                channel=midi.channel,
                note=int(bank),
            ))

        resets = [translate for translate in mappings if int(
            translate['bank']) == active_bank]
        for reset in resets:
            outports.send(Message(
                type='control_change',
                channel=int(reset['channel']) - 1,
                control=int(reset['control']),
                value=int(reset['memory']),
            ))

        outports.send(Message(
            type='note_on',
            channel=midi.channel,
            note=midi.note,
        ))

    for translate in data['translate']:
        if (int(translate['bank']) == 0 and
                translate['output-device'].lower() == 'bank'):
            active_bank = int(translate['o-channel'])
            reset_banks_and_controls(data)
            data['translate'] = []
            break
    return data


def translate_and_send(data: Dict[str, Any]) -> Dict[str, Any]:
    """Translate message and send."""
    midi = data['midi']
    for translate in data['translate']:
        translate['memory'] = data['msg']['level']
        msg = {
            'type': midi.type,
            'channel': int(translate['o-channel']) - 1,
            'control': translate['o-control'],
            'level': data['msg']['level'],
        }
        send(msg, data['outports'])
    return data


def send(msg, outports) -> None:
    """Send MIDI or NRPN message to output ports."""
    if len(msg['control'].split(':')) == 2:
        send_nrpn(msg, outports)
    else:
        send_midi(msg, outports)


def send_midi(msg, outports) -> None:
    """Send MIDI to output ports."""
    outports.send(Message(
        type=msg['type'],
        channel=msg['channel'],
        control=int(msg['control']),
        value=msg['level'],
    ))


def send_nrpn(msg, outports) -> None:
    """Send NRPN message of the following format:

        MIDI # 16 CC 99 = control[0]
        MIDI # 16 CC 98 = control[1]
        MIDI # 16 CC 6 = level
        MIDI # 16 CC 38 = 0

        Note that control is formatted like: '1:9'
    """
    control = msg['control'].split(':')
    send_midi({
        'type': msg['type'],
        'channel': msg['channel'],
        'control': 99,
        'level': int(control[0]),
    }, outports)
    send_midi({
        'type': msg['type'],
        'channel': msg['channel'],
        'control': 98,
        'level': int(control[1]),
    }, outports)
    send_midi({
        'type': msg['type'],
        'channel': msg['channel'],
        'control': 6,
        'level': msg['level'],
    }, outports)
    send_midi({
        'type': msg['type'],
        'channel': msg['channel'],
        'control': 38,
        'level': 0,
    }, outports)


def get_bank_message(mappings):
    """Get Midi message bank 1."""
    bank_one = [m for m in mappings if (
        m['output-device'] == 'Bank' and
        m['o-channel'] == '1') and
        m['type'] == 'OFF']
    if len(bank_one) > 0:
        return Message(
            type='note_on',
            channel=int(bank_one[0]['channel']) - 1,
            note=int(bank_one[0]['control']),
            velocity=127,
        )
    return None
