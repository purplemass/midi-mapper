"""Test functions related to midi utils."""
import pytest

import mido
from mido import Message

from rx.subject import Subject

from midi_mapper.utils import create_midi
from midi_mapper.utils import create_nrpn
from midi_mapper.utils import input_message
from midi_mapper.utils import io_ports
from midi_mapper.utils import send_message
from midi_mapper.utils import set_initial_bank

from midi_mapper.stream import check_mappings
from midi_mapper.stream import create_stream_data
from midi_mapper.stream import process_midi
from midi_mapper.stream import translate_and_send

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
    store.update('midi_stream', Subject())
    io_ports()
    assert store.get('inports').ports == []
    assert store.get('outports').ports == []


def test_input_message():
    result = []

    def on_next(x):
        result.append(x)

    midi_stream = store.get('midi_stream')
    midi_stream.subscribe(on_next=on_next)

    midi = Message(type='control_change', channel=0, control=1, value=64)

    input_message(Message(type='clock'))
    assert result == []
    input_message(midi)
    input_message(Message(type='start'))
    assert result == [midi]
    input_message(Message(type='stop'))
    assert result == [midi]
    input_message(midi)
    assert result == [midi, midi]
    input_message(Message(type='clock'))
    assert result == [midi, midi]
    input_message(Message(type='songpos'))
    assert result == [midi, midi]
    input_message(Message(type='sysex'))
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


def test_set_initial_bank(mappings_bank_set):
    store.update('mappings', mappings_bank_set)
    store.update('active_bank', 0)
    assert store.get('active_bank') == 0

    result = []

    def on_next(x):
        result.append(x)

    midi_stream = store.get('midi_stream')
    midi_stream.subscribe(on_next=on_next)

    assert result == []

    set_initial_bank(0)
    assert len(result) == 0
    set_initial_bank(6)
    assert len(result) == 0

    set_initial_bank(1)
    assert len(result) == 1
    assert store.get('active_bank') == 0

    midi = result[0]
    translate_and_send(check_mappings(process_midi(create_stream_data(midi))))
    assert store.get('active_bank') == 1
