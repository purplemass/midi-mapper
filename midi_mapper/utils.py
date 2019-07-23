"""Utility functions."""
from typing import Any, Dict, List

import sys

import mido  # type: ignore
from mido.ports import MultiPort  # type: ignore
from mido import Message

from rx.subject import Subject

from .constants import REAL_TIME_MESSAGES
from .constants import SYSTEM_COMMON_MESSAGES
from .store import store


def input_message(midi: Message, midi_stream: Subject) -> None:
    """Emit valid messages onto midi_stream."""
    if midi.type in SYSTEM_COMMON_MESSAGES:
        return
    if midi.type in REAL_TIME_MESSAGES:
        return

    midi_stream.on_next(midi)

    if '-v' in sys.argv:  # pragma: no cover
        print('{:35.35}> | {}'.format(100 * '=', midi))


def set_io_ports(midi_stream: Subject) -> None:
    """Create input/output ports and add incoming messages to the stream.

    Ignore Raspberyy Pi's 'Midi Through' port."""
    BAD_PORT = 'Midi Through'

    def input_message_passer(midi: Message):  # pragma: no cover
        """Pass midi_stream to input_message."""
        input_message(midi, midi_stream)

    input_names = [n for n in mido.get_input_names() if BAD_PORT not in n]
    output_names = [n for n in mido.get_output_names() if BAD_PORT not in n]
    print(f'input_names: {input_names}')
    print(f'output_names: {output_names}')
    inports = MultiPort(
        [mido.open_input(
            device, callback=input_message_passer) for device in input_names])
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
        for midi in create_nrpn(msg):
            store.get('outports').send(midi)
    else:
        store.get('outports').send(create_midi(msg))


def create_midi(msg: Dict[str, Any]) -> Message:
    """Create MIDI message."""
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
    """Create NRPN message of the following format:

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
