"""Common fixtures for all tests are created here."""
import pytest

from mido import Message

from midi_mapper import mappings


@pytest.fixture(autouse=True)
def no_mappings(monkeypatch):
    """Do not import mappings for these tests."""

    def import_mappings_mock():
        return []

    monkeypatch.setattr(mappings, 'import_mappings', import_mappings_mock)


@pytest.fixture()
def control_change():
    return Message(type='control_change', channel=0, control=64, value=64)


@pytest.fixture(params=['note_on', 'note_off'])
def midi_notes(request):
    if request.param == 'note_on':
        return Message(type=request.param, channel=0, note=101, velocity=127)
    elif request.param == 'note_off':
        return Message(type=request.param, channel=0, note=102, velocity=0)


@pytest.fixture()
def polytouch():
    return Message(type='polytouch', channel=0, note=101, value=64)


@pytest.fixture()
def program_change():
    return Message(type='program_change', channel=0, program=64)


@pytest.fixture()
def aftertouch():
    return Message(type='aftertouch', value=64)


@pytest.fixture()
def pitchwheel():
    return Message(type='pitchwheel', pitch=64)


@pytest.fixture(params=[
    'clock', 'start', 'continue', 'stop', 'active_sensing', 'reset'])
def real_time(request):
    return Message(type=request.param)
