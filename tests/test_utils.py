"""Test functions related to midi utils."""
import pytest

from unittest.mock import patch

import mido
from mido import Message

from rx.subject import Subject

from midi_mapper.store import store
from midi_mapper.utils import create_midi
from midi_mapper.utils import create_nrpn
from midi_mapper.utils import input_message
from midi_mapper.utils import set_io_ports
from midi_mapper.utils import send_message


@pytest.fixture()
def no_io(monkeypatch):
    """Return an empty list for mido IO ports."""

    def get_io_names_mock():
        return []

    monkeypatch.setattr(mido, 'get_input_names', get_io_names_mock)
    monkeypatch.setattr(mido, 'get_output_names', get_io_names_mock)


@patch('midi_mapper.utils.print', lambda _: [])
def test_set_io_ports(no_io):
    assert store.get('inports') is None
    assert store.get('outports') is None
    set_io_ports(Subject())
    assert store.get('inports').ports == []
    # Virtual port in outports
    assert len(store.get('outports').ports) == 1


def test_input_message():
    result = []

    def on_next(x):
        result.append(x)

    midi_stream = Subject()
    midi_stream.subscribe(on_next=on_next)

    midi = Message(type='control_change', channel=0, control=1, value=64)

    input_message(Message(type='clock'), midi_stream)
    assert result == []
    input_message(midi, midi_stream)
    input_message(Message(type='start'), midi_stream)
    assert result == [midi]
    input_message(Message(type='stop'), midi_stream)
    assert result == [midi]
    input_message(midi, midi_stream)
    assert result == [midi, midi]
    input_message(Message(type='clock'), midi_stream)
    assert result == [midi, midi]
    input_message(Message(type='songpos'), midi_stream)
    assert result == [midi, midi]
    input_message(Message(type='sysex'), midi_stream)
    assert result == [midi, midi]


def test_send_midi():
    midi = create_midi({
        'type': 'control_change',
        'channel': 0,
        'status': 1,
        'level': 64,
    })
    assert midi == Message(
        type='control_change', channel=0, control=1, value=64)

    midi = create_midi({
        'type': 'note_on',
        'channel': 0,
        'status': 1,
        'level': 127,
    })
    assert midi == Message(type='note_on', channel=0, note=1, velocity=127)

    midi = create_midi({
        'type': 'note_off',
        'channel': 0,
        'status': 1,
        'level': 0,
    })
    assert midi == Message(type='note_off', channel=0, note=1, velocity=0)

    midi = create_midi({
        'type': 'program_change',
        'channel': 0,
        'status': 1,
        'level': 0,
    })
    assert midi == Message(type='program_change', channel=0, program=1)

    midi = create_midi({
        'type': 'aftertouch',
        'channel': 0,
        'status': None,
        'level': 0,
    })
    assert midi == Message(type='aftertouch', channel=0, value=0)

    midi = create_midi({
        'type': 'pitchwheel',
        'channel': 0,
        'status': None,
        'level': 0,
    })
    assert midi == Message(type='pitchwheel', channel=0)

    midi = create_midi({
        'type': 'polytouch',
        'channel': 0,
        'status': 100,
        'level': 64,
    })
    assert midi == Message(type='polytouch', channel=0, note=100, value=64)


def test_send_nrpn():
    msg = {
        'type': 'control_change',
        'channel': 0,
        'status': '12:13',
        'level': 127,
    }
    status = msg['status'].split(':')
    midi_notes = create_nrpn(msg)
    assert midi_notes[0] == Message(
        type='control_change', channel=0, control=99, value=int(status[0]))
    assert midi_notes[1] == Message(
        type='control_change', channel=0, control=98, value=int(status[1]))
    assert midi_notes[2] == Message(
        type='control_change', channel=0, control=6, value=msg['level'])
    assert midi_notes[3] == Message(
        type='control_change', channel=0, control=38, value=0)


def test_send_message():
    msg = {
        'type': 'note_on',
        'channel': 0,
        'status': 66,
        'level': 127,
    }
    send_message(msg)
    msg = {
        'type': 'program_change',
        'channel': 0,
        'status': '12:13',
        'level': 0,
    }
    send_message(msg)
