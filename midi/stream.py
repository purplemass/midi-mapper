"""Utility functions."""
from typing import Any, Dict

from mido import Message

from utils import send


active_bank = 1


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
        control = midi.control
        level = midi.value
    elif midi.type == 'note_off':
        control = midi.note
        level = midi.velocity
    elif midi.type == 'note_on':
        control = midi.note
        level = midi.velocity
    elif midi.type == 'program_change':
        control = midi.program
        level = None
    elif midi.type == 'aftertouch':
        control = None
        level = midi.value
    elif midi.type == 'pitchwheel':
        control = None
        level = midi.pitch

    data['msg'] = {
        'type': midi.type,
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
            'o-type'] == 'bank_change']
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
    """Translate messages and send."""
    for translate in data['translate']:
        translate['memory'] = data['msg']['level']
        msg = {
            'type': translate['o-type'],
            'channel': int(translate['o-channel']) - 1,
            'control': translate['o-control'],
            'level': data['msg']['level'],
        }
        send(msg, data['outports'])
    return data
