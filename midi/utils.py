"""Utility functions."""
from typing import Any, Tuple
import sys

import mido  # type: ignore
from mido.ports import MultiPort  # type: ignore
from mido import Message


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


def send(msg, outports) -> None:
    """Send MIDI or NRPN message to output ports."""
    if len(msg['control'].split(':')) == 2:
        send_nrpn(msg, outports)
    else:
        send_midi(msg, outports)


def send_midi(msg, outports) -> None:
    """Send MIDI to output ports."""
    if msg['type'] == 'control_change':
        midi = Message(
            type=msg['type'],
            channel=msg['channel'],
            control=int(msg['control']),
            value=msg['level'],
        )
    elif msg['type'] == 'note_off':
        midi = Message(
            type=msg['type'],
            channel=msg['channel'],
            note=int(msg['control']),
            velocity=0,
        )
    elif msg['type'] == 'note_on':
        midi = Message(
            type=msg['type'],
            channel=msg['channel'],
            note=int(msg['control']),
            velocity=127,
        )
    elif msg['type'] == 'program_change':
        midi = Message(
            type=msg['type'],
            channel=msg['channel'],
            program=int(msg['control']),
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

    outports.send(midi)


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
