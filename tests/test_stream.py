"""Test functions related to the midi stream."""

from midi_mapper.stream import create_stream_data
from midi_mapper.stream import process_midi
from midi_mapper.stream import store


def test_create_stream_data(midi_notes):
    stream_data = create_stream_data(midi_notes)
    assert stream_data['msg'] == dict()
    assert stream_data['midi'] == midi_notes
    assert stream_data['translations'] == []
    assert stream_data['store'] == store


def partial_test_process_midi(data, midi):
    assert data['midi'] == midi
    assert data['translations'] == []
    assert data['store'] == store


def test_process_midi_notes(midi_notes):
    ret = process_midi(create_stream_data(midi_notes))
    assert ret['msg'] == {
        'channel': midi_notes.channel + 1,
        'status': midi_notes.note,
        'level': midi_notes.velocity,
    }
    partial_test_process_midi(ret, midi_notes)


def test_process_polytouch(polytouch):
    ret = process_midi(create_stream_data(polytouch))
    assert ret['msg'] == {
        'channel': polytouch.channel + 1,
        'status': polytouch.note,
        'level': polytouch.value,
    }
    partial_test_process_midi(ret, polytouch)


def test_process_control_change(control_change):
    ret = process_midi(create_stream_data(control_change))
    assert ret['msg'] == {
        'channel': control_change.channel + 1,
        'status': control_change.control,
        'level': control_change.value,
    }
    partial_test_process_midi(ret, control_change)


def test_process_program_change(program_change):
    ret = process_midi(create_stream_data(program_change))
    assert ret['msg'] == {
        'channel': program_change.channel + 1,
        'status': program_change.program,
        'level': None,
    }
    partial_test_process_midi(ret, program_change)


def test_process_aftertouch(aftertouch):
    ret = process_midi(create_stream_data(aftertouch))
    assert ret['msg'] == {
        'channel': aftertouch.channel + 1,
        'status': None,
        'level': aftertouch.value,
    }
    partial_test_process_midi(ret, aftertouch)


def test_process_pitchwheel(pitchwheel):
    ret = process_midi(create_stream_data(pitchwheel))
    assert ret['msg'] == {
        'channel': pitchwheel.channel + 1,
        'status': None,
        'level': pitchwheel.pitch,
    }
    partial_test_process_midi(ret, pitchwheel)


def test_process_real_time(real_time):
    ret = process_midi(create_stream_data(real_time))
    assert ret['msg'] == {
        'channel': None,
        'status': None,
        'level': None,
    }
    partial_test_process_midi(ret, real_time)
