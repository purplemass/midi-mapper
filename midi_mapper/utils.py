"""Utility functions."""
from typing import Any
import sys

import mido  # type: ignore
from mido.ports import MultiPort  # type: ignore
from mido import Message

from .store import store


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
    print('ports ready\n\tin: {}\n\tout: {}'.format(
        len(inports.ports), len(outports.ports)))
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

    if store.get('outports') is not None:
        store.get('outports').send(midi)


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


def reset_banks_and_controls(data) -> None:
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


def set_initial_bank(active_bank: int, midi_stream) -> None:
    """Set  bank and reset controller."""
    bank_controls = [m for m in store.get('mappings') if (
        m['o-type'] == 'bank_change' and
        int(m['o-control']) == active_bank)]
    for bank_control in bank_controls:
        send_message({
            'type': 'note_on',
            'channel': int(bank_control['channel']) - 1,
            'status': int(bank_control['control']),
        })
        midi_stream.on_next(Message(
            type='note_on',
            channel=int(bank_control['channel']) - 1,
            note=int(bank_control['control']),
            velocity=127,
        ))
