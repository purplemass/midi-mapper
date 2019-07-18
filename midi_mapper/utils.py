"""Utility functions."""
from typing import Any, Dict, List

import sys

import mido  # type: ignore
from mido.ports import MultiPort  # type: ignore
from mido import Message

from .constants import REAL_TIME_MESSAGES
from .constants import SYSTEM_COMMON_MESSAGES
from .store import store


def input_message(midi: Message) -> None:
    """Emit valid messages onto midi_stream."""
    if midi.type in SYSTEM_COMMON_MESSAGES:
        return
    if midi.type in REAL_TIME_MESSAGES:
        return

    store.get('midi_stream').on_next(midi)
    if '-v' in sys.argv:  # pragma: no cover
        print(f'[-] {midi}')


def set_io_ports() -> None:
    """Create input/output ports and add incoming messages to the stream."""
    input_names = mido.get_input_names()
    output_names = mido.get_output_names()
    print(f'input_names: {input_names}')
    print(f'output_names: {output_names}')
    inports = MultiPort(
        [mido.open_input(
            device, callback=input_message) for device in input_names])
    outports = MultiPort(
        [mido.open_output(device) for device in output_names])
    print('ports ready\n\tin: {}\n\tout: {}'.format(
        len(inports.ports), len(outports.ports)))
    store.update('inports', inports)
    store.update('outports', outports)


def send_message(msg: Dict[str, Any]) -> None:
    """Send MIDI or NRPN message to output ports."""
    if store.get('outports') is None:
        return

    if type(msg['status']) == str and len(msg['status'].split(':')) == 2:
        midi_notes = create_nrpn(msg)
        for midi in midi_notes:
            store.get('outports').send(midi)
    else:
        store.get('outports').send(create_midi(msg))


def create_midi(msg: Dict[str, Any]) -> Message:
    """Send MIDI to output ports."""
    if msg['type'] == 'control_change':
        return Message(
            type=msg['type'],
            channel=msg['channel'],
            control=int(msg['status']),
            value=msg['level'],
        )
    elif msg['type'] == 'note_off':
        return Message(
            type=msg['type'],
            channel=msg['channel'],
            note=int(msg['status']),
            velocity=0,
        )
    elif msg['type'] == 'note_on':
        return Message(
            type=msg['type'],
            channel=msg['channel'],
            note=int(msg['status']),
            velocity=127,
        )
    elif msg['type'] == 'program_change':
        return Message(
            type=msg['type'],
            channel=msg['channel'],
            program=int(msg['status']),
        )
    elif msg['type'] == 'aftertouch':
        return Message(
            type=msg['type'],
            value=msg['level'],
        )
    elif msg['type'] == 'pitchwheel':
        return Message(
            type=msg['type'],
            pitch=msg['level'],
        )
    elif msg['type'] == 'polytouch':
        return Message(
            type=msg['type'],
            channel=msg['channel'],
            note=int(msg['status']),
            value=msg['level'],
        )


def create_nrpn(msg: Dict[str, Any]) -> List[Message]:
    """Send NRPN message of the following format:

        MIDI # 16 CC 99 = control[0]
        MIDI # 16 CC 98 = control[1]
        MIDI # 16 CC 6 = level
        MIDI # 16 CC 38 = 0

        Note that control is formatted like: '1:9'
    """
    status = msg['status'].split(':')
    return [
        create_midi({
            'type': msg['type'],
            'channel': msg['channel'],
            'status': 99,
            'level': int(status[0]),
        }),
        create_midi({
            'type': msg['type'],
            'channel': msg['channel'],
            'status': 98,
            'level': int(status[1]),
        }),
        create_midi({
            'type': msg['type'],
            'channel': msg['channel'],
            'status': 6,
            'level': msg['level'],
        }),
        create_midi({
            'type': msg['type'],
            'channel': msg['channel'],
            'status': 38,
            'level': 0,
        }),
    ]


def reset_banks_and_controls(data: Dict[str, Any]) -> None:
    """Turn all bank buttons off and turn on the active bank.

    Reset controls to their memory value.
    """
    mappings = store.get('mappings')
    bank_controls = [mapping['control'] for mapping in mappings if (
        mapping['o-type'] == 'bank_change')]
    for bank_control in bank_controls:
        if int(bank_control) != data['msg']['status']:
            send_message({
                'type': 'note_off',
                'channel': getattr(data['midi'], 'channel'),
                'status': int(bank_control),
                'level': 0,
            })

    resets = [mapping for mapping in mappings if (
        int(mapping['bank']) == store.get('active_bank'))]
    for reset in resets:
        send_message({
            'type': 'control_change',
            'channel': int(reset['channel']) - 1,
            'status': int(reset['control']),
            'level': int(reset['memory']),
        })


def set_initial_bank(active_bank: int) -> None:
    """Set  bank and reset controller."""
    bank_controls = [m for m in store.get('mappings') if (
        m['o-type'] == 'bank_change' and
        int(m['o-control']) == active_bank)]
    for bank_control in bank_controls:
        send_message({
            'type': 'note_on',
            'channel': int(bank_control['channel']) - 1,
            'status': int(bank_control['control']),
            'level': 127,
        })
        store.get('midi_stream').on_next(Message(
            type='note_on',
            channel=int(bank_control['channel']) - 1,
            note=int(bank_control['control']),
            velocity=127,
        ))
