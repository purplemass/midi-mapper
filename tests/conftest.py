"""Common fixtures for all tests are created here."""
import pytest

from mido import Message

from midi_mapper.utils import REAL_TIME_MESSAGES


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


@pytest.fixture(params=REAL_TIME_MESSAGES)
def real_time(request):
    return Message(type=request.param)


@pytest.fixture()
def mappings_bank0():
    e1 = dict([
        ('input-device', 'TestControllerIn'),
        ('description', 'Button1'),
        ('type', 'note_on'),
        ('bank', '0'),
        ('channel', '1'),
        ('control', '11'),
        ('=>', '=>'),
        ('output-device', 'TestControllerOut'),
        ('o-description', 'NoteOn Test'),
        ('o-type', 'note_on'),
        ('o-channel', '2'),
        ('o-control', '12'),
        ('memory', 0)])
    e2 = dict([
        ('input-device', 'TestControllerIn'),
        ('description', 'Wheel 1'),
        ('type', 'control_change'),
        ('bank', '0'),
        ('channel', '2'),
        ('control', '22'),
        ('=>', '=>'),
        ('output-device', 'TestControllerOut'),
        ('o-description', 'CC Test'),
        ('o-type', 'control_change'),
        ('o-channel', '3'),
        ('o-control', '23'),
        ('memory', 0)])
    return [e1, e2]


@pytest.fixture()
def mappings_bank1():
    e1 = dict([
        ('input-device', 'TestControllerIn'),
        ('description', 'Button1'),
        ('type', 'note_on'),
        ('bank', '1'),
        ('channel', '3'),
        ('control', '33'),
        ('=>', '=>'),
        ('output-device', 'TestControllerOut'),
        ('o-description', 'NoteOn Test'),
        ('o-type', 'note_on'),
        ('o-channel', '4'),
        ('o-control', '34'),
        ('memory', 0)])
    e2 = dict([
        ('input-device', 'TestControllerIn'),
        ('description', 'Wheel 1'),
        ('type', 'control_change'),
        ('bank', '1'),
        ('channel', '4'),
        ('control', '44'),
        ('=>', '=>'),
        ('output-device', 'TestControllerOut'),
        ('o-description', 'CC Test'),
        ('o-type', 'control_change'),
        ('o-channel', '5'),
        ('o-control', '45'),
        ('memory', 0)])
    return [e1, e2]


@pytest.fixture()
def mappings_bank_set():
    e1 = dict([
        ('input-device', 'TestControllerIn'),
        ('description', 'Button1'),
        ('type', 'note_on'),
        ('bank', '0'),
        ('channel', '5'),
        ('control', '55'),
        ('=>', '=>'),
        ('output-device', 'Bank'),
        ('o-description', 'Change bank 1'),
        ('o-type', 'bank_change'),
        ('o-channel', '-'),
        ('o-control', '1'),
        ('memory', 0)])
    e2 = dict([
        ('input-device', 'TestControllerIn'),
        ('description', 'Button2'),
        ('type', 'note_on'),
        ('bank', '0'),
        ('channel', '6'),
        ('control', '66'),
        ('=>', '=>'),
        ('output-device', 'Bank'),
        ('o-description', 'Change bank 2'),
        ('o-type', 'bank_change'),
        ('o-channel', '-'),
        ('o-control', '2'),
        ('memory', 0)])
    e3 = dict([
        ('input-device', 'TestControllerIn'),
        ('description', 'Wheel 1'),
        ('type', 'control_change'),
        ('bank', '1'),
        ('channel', '7'),
        ('control', '77'),
        ('=>', '=>'),
        ('output-device', 'TestControllerOut'),
        ('o-description', 'CC Test'),
        ('o-type', 'control_change'),
        ('o-channel', '8'),
        ('o-control', '78'),
        ('memory', 0)])
    e4 = dict([
        ('input-device', 'TestControllerIn'),
        ('description', 'Wheel 1'),
        ('type', 'control_change'),
        ('bank', '2'),
        ('channel', '8'),
        ('control', '88'),
        ('=>', '=>'),
        ('output-device', 'TestControllerOut'),
        ('o-description', 'CC Test'),
        ('o-type', 'control_change'),
        ('o-channel', '9'),
        ('o-control', '89'),
        ('memory', 0)])
    return [e1, e2, e3, e4]
