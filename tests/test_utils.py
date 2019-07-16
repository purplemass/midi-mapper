"""Test functions related to the midi stream."""
import pytest

import mido
from mido import Message

from rx.subject import Subject

from midi_mapper.utils import create_midi
from midi_mapper.utils import create_nrpn
from midi_mapper.utils import io_ports
from midi_mapper.utils import send_message
from midi_mapper.store import store


@pytest.fixture()
def no_io(monkeypatch):
    """Return an empty list for mido IO ports."""

    def get_io_names_mock():
        return []

    monkeypatch.setattr(mido, 'get_input_names', get_io_names_mock)
    monkeypatch.setattr(mido, 'get_output_names', get_io_names_mock)


def test_io_ports(no_io):
    assert store.get('inports') is None
    assert store.get('outports') is None
    midi_stream = Subject()
    io_ports(midi_stream)
    assert store.get('inports').ports == []
    assert store.get('outports').ports == []


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
        'status': 1,
        'level': '12:13',
    }
    send_message(msg)
