"""Utility functions."""
from typing import Any, Dict

from utils import send_message


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
        status = midi.control
        level = midi.value
    elif midi.type == 'note_off':
        status = midi.note
        level = midi.velocity
    elif midi.type == 'note_on':
        status = midi.note
        level = midi.velocity
    elif midi.type == 'program_change':
        status = midi.program
        level = None
    elif midi.type == 'aftertouch':
        status = None
        level = midi.value
    elif midi.type == 'pitchwheel':
        status = None
        level = midi.pitch

    data['msg'] = {
        'type': midi.type,
        'channel': midi.channel + 1,
        'status': status,
        'level': level,
    }
    return data


def check_mappings(data: Dict[str, Any]) -> Dict[str, Any]:
    """Check incoming message for matches in mappings."""

    def check(mapping):
        return (
            mapping['type'] == data['msg']['type'] and
            int(mapping['channel']) == data['msg']['channel'] and
            int(mapping['control']) == data['msg']['status'] and
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
            send_message({
                'type': 'note_off',
                'channel': midi.channel,
                'status': int(bank),
            }, outports)

        resets = [translate for translate in mappings if int(
            translate['bank']) == active_bank]
        for reset in resets:
            send_message({
                'type': 'control_change',
                'channel': int(reset['channel']) - 1,
                'status': int(reset['control']),
                'level': int(reset['memory']),
            }, outports)

        send_message({
            'type': 'note_on',
            'channel': midi.channel,
            'status': midi.note,
        }, outports)

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
        send_message({
            'type': translate['o-type'],
            'channel': int(translate['o-channel']) - 1,
            'status': translate['o-control'],
            'level': data['msg']['level'],
        }, data['outports'])
    return data
