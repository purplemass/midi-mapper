"""Functions used in the main appplication streams."""
from typing import Any, Dict, List

from mido import Message  # type: ignore

from .constants import STANDARD_MESSAGES
from .store import store
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
        'type': midi.type,
        'channel': channel,
        'status': status,
        'level': level,
    }


def get_translations(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Check incoming message for matches in mappings."""

    def set_memory(mapping):
        mapping['memory'] = data['level']
        return mapping

    def check(mapping):
        return (
            mapping['type'] == data['type']
            and int(mapping['channel']) == data['channel']
            and int(mapping['control']) == data['status']
            and (
                int(mapping['bank']) == 0
                or int(mapping['bank']) == store.get('active_bank')
            )
        )

    mappings = store.get('mappings')
    return [set_memory(m) for m in mappings if check(m)]


def translate_and_send(translation: Dict[str, Any]) -> Dict[str, Any]:
    """Translate messages and send."""
    if translation['o-type'].startswith('mm_'):
        process_mapper_types(translation)
    else:
        process_standard_types(translation)
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


def process_standard_types(translation: Dict[str, Any]) -> None:
    """Process standard type messages."""
    level = calculate_range(translation['o-range'], translation['memory'])
    send_message({
        'type': translation['o-type'],
        'channel': int(translation['o-channel']) - 1,
        'status': translation['o-control'],
        'level': level,
    })
    translation['o-level'] = level


def process_mapper_types(translation: Dict[str, Any]) -> None:
    """Process midi mapper special type messages.

    These are:
        mm_bank_change    : where o-control is set to the bank number
        mm_program_change : where o-channel/o-control are set appropriately
    """
    if translation['o-type'] == 'mm_bank_change':
        set_bank(int(translation['o-control']))
    elif translation['o-type'] == 'mm_program_change':
        set_program(int(translation['o-control']))


def set_bank(active_bank: int, initial=False) -> None:
    """Set active bank, turn all bank buttons off and turn on the active bank.

    Reset controls to their memory value.
    """
    mappings = store.get('mappings')
    controls = [m for m in mappings if 'mm_bank_change' in m['o-type']]
    # Check if passed bank is valid
    if not [c for c in controls if (int(c['o-control']) == active_bank)]:
        return

    store.update('active_bank', active_bank)

    for control in controls:
        channel, status = int(control['channel']) - 1, int(control['control'])
        if int(control['o-control']) != active_bank:
            send_message({'type': 'note_off', 'channel': channel,
                          'status': status, 'level': 0})
        elif initial:
            send_message({'type': 'note_on', 'channel': channel,
                          'status': status, 'level': 127})

    resets = [m for m in mappings if int(m['bank']) == active_bank]
    for reset in resets:
        send_message({
            'type': 'control_change',
            'channel': int(reset['channel']) - 1,
            'status': int(reset['control']),
            'level': int(reset['memory']),
        })


def set_program(active_program: int) -> None:
    """Send program_change messaage along with resets and light on."""
    mappings = store.get('mappings')
    controls = [m for m in mappings if 'mm_program_change' in m['o-type']]
    for control in controls:
        channel, status = int(control['channel']) - 1, int(control['control'])
        if int(control['o-control']) != active_program:
            send_message({'type': 'note_off', 'channel': channel,
                          'status': status, 'level': 0})
        else:
            send_message({'type': 'note_on', 'channel': channel,
                          'status': status, 'level': 127})
            # Send program_change
            send_message({'type': 'program_change',
                          'channel': int(control['o-channel']) - 1,
                          'status': int(control['o-control']), 'level': None})


def calculate_range(range_: str, level: int) -> int:
    """Calculate range and apply to level."""
    if (range_ is not None and type(range_) == str
            and len(range_.split('-')) == 2):
        low, high = range_.split('-')
        new_level = level * ((int(high) - int(low)) / 127) + int(low)
        return int(new_level)
    return level
