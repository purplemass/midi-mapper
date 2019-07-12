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
        'translations': [],
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
        'channel': midi.channel + 1,
        'status': status,
        'level': level,
    }
    return data


def check_mappings(data: Dict[str, Any]) -> Dict[str, Any]:
    """Check incoming message for matches in mappings."""

    def check(mapping):
        return (
            mapping['type'] == getattr(data['midi'], 'type') and
            int(mapping['channel']) == data['msg']['channel'] and
            int(mapping['control']) == data['msg']['status'] and
            (int(mapping['bank']) == 0 or
                int(mapping['bank']) == active_bank)
        )

    data['translations'] = [m for m in data['mappings'] if check(m)]
    return data


def log(data: Dict[str, Any]) -> None:
    """Log messages to console."""
    for translation in data['translations']:
        print('[{}] {}__{} => {}__{:<25} {}'.format(
            active_bank,
            translation['input-device'],
            translation['description'],
            translation['output-device'],
            translation['o-description'],
            data['msg']['level'],
        ))


def change_bank(data: Dict[str, Any]) -> Dict[str, Any]:
    """Check incoming bank_change messages."""

    global active_bank

    def reset_banks_and_controls() -> None:
        """Turn all bank buttons off and turn on the active bank.

        Reset controls to their memory value.
        """
        midi = data['midi']
        banks = [mapping['control'] for mapping in data['mappings'] if (
            mapping['o-type'] == 'bank_change')]
        for bank in banks:
            if midi.note != int(bank):
                send_message({
                    'type': 'note_off',
                    'channel': midi.channel,
                    'status': int(bank),
                }, data['outports'])

        resets = [mapping for mapping in data['mappings'] if (
            int(mapping['bank']) == active_bank)]
        for reset in resets:
            send_message({
                'type': 'control_change',
                'channel': int(reset['channel']) - 1,
                'status': int(reset['control']),
                'level': int(reset['memory']),
            }, data['outports'])

    for translation in data['translations']:
        if (int(translation['bank']) == 0 and
                translation['o-type'] == 'bank_change'):
            active_bank = int(translation['o-control'])
            reset_banks_and_controls()
            data['translations'] = []
            break
    return data


def translate_and_send(data: Dict[str, Any]) -> Dict[str, Any]:
    """Translate messages and send."""
    for translation in data['translations']:
        translation['memory'] = data['msg']['level']
        send_message({
            'type': translation['o-type'],
            'channel': int(translation['o-channel']) - 1,
            'status': translation['o-control'],
            'level': data['msg']['level'],
        }, data['outports'])
    return data
