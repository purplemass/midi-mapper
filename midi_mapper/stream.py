"""Functions used in the main appplication streams."""
from typing import Any, Dict

from mido import Message  # type: ignore

from .constants import STANDARD_MESSAGES
from .store import store
from .utils import reset_banks_and_controls
from .utils import send_message


def process_midi(midi: Message) -> Dict[str, Any]:
    """Process incoming message."""
    try:
        channel = midi.channel + 1
    except AttributeError:
        channel = None
    try:
        status, level = STANDARD_MESSAGES[midi.type](midi)
    except KeyError:
        status, level = None, None
    return {
        'msg': {
            'type': midi.type,
            'channel': channel,
            'status': status,
            'level': level,
        },
        'translations': [],
    }


def check_mappings(data: Dict[str, Any]) -> Dict[str, Any]:
    """Check incoming message for matches in mappings."""

    def set_memory(mapping):
        mapping['memory'] = data['msg']['level']
        return mapping

    def check(mapping):
        return (
            mapping['type'] == data['msg']['type'] and
            int(mapping['channel']) == data['msg']['channel'] and
            int(mapping['control']) == data['msg']['status'] and
            (int(mapping['bank']) == 0 or
                int(mapping['bank']) == store.get('active_bank'))
        )

    mappings = store.get('mappings')
    data['translations'] = [set_memory(m) for m in mappings if check(m)]
    return data


def calculate_range(range_: str, level: int) -> int:
    """Calculate range and apply to level."""
    if (range_ is not None and type(range_) == str and
            len(range_.split('-')) == 2):
        low, high = range_.split('-')
        new_level = level * ((int(high) - int(low)) / 127) + int(low)
        return int(new_level)
    return level


def translate_and_send(translation: Dict[str, Any]) -> Dict[str, Any]:
    """Translate messages and send."""
    level = translation['memory']

    if translation['o-type'] == 'bank_change':
        store.update('active_bank', int(translation['o-control']))
        reset_banks_and_controls()
    else:
        level = calculate_range(translation['o-range'], level)
        send_message({
            'type': translation['o-type'],
            'channel': int(translation['o-channel']) - 1,
            'status': translation['o-control'],
            'level': level,
        })
    translation['o-level'] = level
    return translation


def log(translation: Dict[str, Any]) -> None:
    """Log messages to console."""
    formatter = '[{}] | {:12.12} | {:10.10} | => | {:12.12} | {:25.25} | {:>3}'
    print(formatter.format(
        store.get('active_bank'),
        translation['input-device'],
        translation['description'],
        translation['output-device'],
        translation['o-description'],
        translation['o-level'],
    ))
