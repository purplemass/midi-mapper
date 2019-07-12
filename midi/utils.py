"""Utility functions."""
from typing import Any
import sys

import mido  # type: ignore
from mido.ports import MultiPort  # type: ignore
from mido import Message

from store import store


def io_ports(midi_stream: Any) -> None:
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
    store.update('inports', inports)
    store.update('outports', outports)


def send_message(msg) -> None:
    """Send MIDI or NRPN message to output ports."""
    if type(msg['status']) == str and len(msg['status'].split(':')) == 2:
        send_nrpn(msg)
    else:
        send_midi(msg)


def send_midi(msg) -> None:
    """Send MIDI to output ports."""

    # Handle our own special types first - don't send message
    if msg['type'] == 'bank_change':
        store.update('active_bank', int(msg['status']))
        return
    # Handle generic Midi types and send message
    if msg['type'] == 'control_change':
        midi = Message(
            type=msg['type'],
            channel=msg['channel'],
            control=int(msg['status']),
            value=msg['level'],
        )
    elif msg['type'] == 'note_off':
        midi = Message(
            type=msg['type'],
            channel=msg['channel'],
            note=int(msg['status']),
            velocity=0,
        )
    elif msg['type'] == 'note_on':
        midi = Message(
            type=msg['type'],
            channel=msg['channel'],
            note=int(msg['status']),
            velocity=127,
        )
    elif msg['type'] == 'program_change':
        midi = Message(
            type=msg['type'],
            channel=msg['channel'],
            program=int(msg['status']),
        )
    elif msg['type'] == 'aftertouch':
        midi = Message(
            type=msg['type'],
            value=msg['level'],
        )
    elif msg['type'] == 'pitchwheel':
        midi = Message(
            type=msg['type'],
            pitch=msg['level'],
        )

    store.value['outports'].send(midi)


def send_nrpn(msg) -> None:
    """Send NRPN message of the following format:

        MIDI # 16 CC 99 = control[0]
        MIDI # 16 CC 98 = control[1]
        MIDI # 16 CC 6 = level
        MIDI # 16 CC 38 = 0

        Note that control is formatted like: '1:9'
    """
    status = msg['status'].split(':')
    send_midi({
        'type': msg['type'],
        'channel': msg['channel'],
        'status': 99,
        'level': int(status[0]),
    })
    send_midi({
        'type': msg['type'],
        'channel': msg['channel'],
        'status': 98,
        'level': int(status[1]),
    })
    send_midi({
        'type': msg['type'],
        'channel': msg['channel'],
        'status': 6,
        'level': msg['level'],
    })
    send_midi({
        'type': msg['type'],
        'channel': msg['channel'],
        'status': 38,
        'level': 0,
    })


def reset_banks_and_controls(combined) -> None:
    """Turn all bank buttons off and turn on the active bank.

    Reset controls to their memory value.
    """
    # new_bank = combined[0]
    midi = combined[1]['midi']
    mappings = store.get('mappings')
    banks = [mapping['control'] for mapping in mappings if (
        mapping['o-type'] == 'bank_change')]
    for bank in banks:
        send_message({
            'type': 'note_off',
            'channel': midi.channel,
            'status': midi.note,
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


def get_bank_message(select_bank):
    """Get Midi message bank 1."""
    bank_one = [m for m in store.get('mappings') if (
        m['o-type'] == 'bank_change' and
        m['o-control'] == str(select_bank))]
    if len(bank_one) > 0:
        send_message({
            'type': 'note_on',
            'channel': int(bank_one[0]['channel']) - 1,
            'status': int(bank_one[0]['control']),
        })
        return Message(
            type='note_on',
            channel=int(bank_one[0]['channel']) - 1,
            note=int(bank_one[0]['control']),
            velocity=127,
        )
    return None
