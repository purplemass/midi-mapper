"""Test functions related to midi stream."""
from unittest.mock import patch

from mido import Message

from midi_mapper.stream import get_translations
from midi_mapper.stream import calculate_range
from midi_mapper.stream import log
from midi_mapper.stream import process_midi
from midi_mapper.stream import set_bank
from midi_mapper.stream import store
from midi_mapper.stream import translate_and_send


def test_process_midi_notes(midi_notes):
    ret = process_midi(midi_notes)
    assert ret == {
        'type': midi_notes.type,
        'channel': midi_notes.channel + 1,
        'status': midi_notes.note,
        'level': midi_notes.velocity,
    }


def test_process_polytouch(polytouch):
    ret = process_midi(polytouch)
    assert ret == {
        'type': polytouch.type,
        'channel': polytouch.channel + 1,
        'status': polytouch.note,
        'level': polytouch.value,
    }


def test_process_control_change(control_change):
    ret = process_midi(control_change)
    assert ret == {
        'type': control_change.type,
        'channel': control_change.channel + 1,
        'status': control_change.control,
        'level': control_change.value,
    }


def test_process_program_change(program_change):
    ret = process_midi(program_change)
    assert ret == {
        'type': program_change.type,
        'channel': program_change.channel + 1,
        'status': program_change.program,
        'level': None,
    }


def test_process_aftertouch(aftertouch):
    ret = process_midi(aftertouch)
    assert ret == {
        'type': aftertouch.type,
        'channel': aftertouch.channel + 1,
        'status': None,
        'level': aftertouch.value,
    }


def test_process_pitchwheel(pitchwheel):
    ret = process_midi(pitchwheel)
    assert ret == {
        'type': pitchwheel.type,
        'channel': pitchwheel.channel + 1,
        'status': None,
        'level': pitchwheel.pitch,
    }


def test_process_real_time(real_time):
    ret = process_midi(real_time)
    assert ret == {
        'type': real_time.type,
        'channel': None,
        'status': None,
        'level': None,
    }


def test_get_translations_bank0(mappings_bank0):
    # Ensure mappings are set for these tests
    store.update('mappings', mappings_bank0)
    store.update('active_bank', 0)

    midi = Message(type='note_off', channel=0, note=1, velocity=0)
    ret = get_translations(process_midi(midi))
    assert len(ret) == 0

    midi = Message(type='note_on', channel=15, note=1, velocity=0)
    ret = get_translations(process_midi(midi))
    assert len(ret) == 0

    midi = Message(type='note_on', channel=0, note=127, velocity=0)
    ret = get_translations(process_midi(midi))
    assert len(ret) == 0

    midi = Message(type='note_on', channel=0, note=11, velocity=0)
    ret = get_translations(process_midi(midi))
    assert len(ret) == 1

    midi = Message(type='control_change', channel=15, control=2, value=64)
    ret = get_translations(process_midi(midi))
    assert len(ret) == 0

    midi = Message(type='control_change', channel=0, control=127, value=64)
    ret = get_translations(process_midi(midi))
    assert len(ret) == 0

    midi = Message(type='control_change', channel=1, control=22, value=64)
    ret = get_translations(process_midi(midi))
    assert len(ret) == 1

    # bank0 mappings are not affected by setting the bank
    store.update('active_bank', 1)

    ret = get_translations(process_midi(midi))
    assert len(ret) == 1


def test_get_translations_bank1(mappings_bank1):
    # Ensure mappings are set for these tests
    store.update('mappings', mappings_bank1)
    store.update('active_bank', 0)

    midi = Message(type='note_off', channel=0, note=1, velocity=0)
    ret = get_translations(process_midi(midi))
    assert len(ret) == 0

    midi = Message(type='note_on', channel=0, note=1, velocity=0)
    ret = get_translations(process_midi(midi))
    assert len(ret) == 0

    # change bank
    store.update('active_bank', 1)

    midi = Message(type='note_on', channel=2, note=33, velocity=0)
    ret = get_translations(process_midi(midi))
    assert len(ret) == 1


@patch('midi_mapper.stream.print', lambda _: [])
def test_check_log(mappings_bank1):
    store.update('mappings', mappings_bank1)
    store.update('active_bank', 1)

    midi = Message(type='note_on', channel=2, note=33, velocity=0)
    ret = get_translations(process_midi(midi))
    assert len(ret) == 1
    log(translate_and_send(ret[0]))


def test_translate_and_send0(mappings_bank0):
    store.update('mappings', mappings_bank0)
    store.update('active_bank', 0)

    midi = Message(type='note_on', channel=0, note=11, velocity=0)
    ret = get_translations(process_midi(midi))
    assert len(ret) == 1

    ret = translate_and_send(ret[0])
    assert ret['type'] == midi.type
    assert int(ret['channel']) == midi.channel + 1
    assert int(ret['control']) == midi.note

    store.update('active_bank', 1)

    midi = Message(type='note_on', channel=0, note=11, velocity=0)
    ret = get_translations(process_midi(midi))
    assert len(ret) == 1

    ret = translate_and_send(ret[0])
    assert ret['type'] == midi.type
    assert int(ret['channel']) == midi.channel + 1
    assert int(ret['control']) == midi.note


def test_translate_and_send1(mappings_bank1):
    store.update('mappings', mappings_bank1)
    store.update('active_bank', 0)

    midi = Message(type='note_on', channel=0, note=11, velocity=0)
    ret = get_translations(process_midi(midi))
    assert len(ret) == 0

    store.update('active_bank', 1)

    midi = Message(type='note_on', channel=2, note=33, velocity=0)
    ret = get_translations(process_midi(midi))
    assert len(ret) == 1

    ret = translate_and_send(ret[0])
    assert ret['type'] == midi.type
    assert int(ret['channel']) == midi.channel + 1
    assert int(ret['control']) == midi.note


def send_midi_through_the_stream(midi):
    ret = get_translations(process_midi(midi))
    if ret:
        return translate_and_send(ret[0])
    return None


def test_get_translations_bank_set(mappings_bank_set):
    store.update('mappings', mappings_bank_set)
    store.update('active_bank', 0)

    midi = Message(type='note_on', channel=15, note=1, velocity=0)
    send_midi_through_the_stream(midi)
    assert store.get('active_bank') == 0

    midi = Message(type='note_on', channel=4, note=55, velocity=0)
    send_midi_through_the_stream(midi)
    assert store.get('active_bank') == 1

    midi = Message(type='note_on', channel=5, note=66, velocity=0)
    send_midi_through_the_stream(midi)
    assert store.get('active_bank') == 2


def test_check_memory(mappings_bank_set):
    store.update('mappings', mappings_bank_set)
    store.update('active_bank', 0)

    bank1_element = 2
    bank2_element = 3
    assert store.get('mappings')[bank1_element]['memory'] == 0
    assert store.get('mappings')[bank2_element]['memory'] == 0

    # no bank selected the next messages should be ignored
    midi = Message(type='control_change', channel=6, control=77, value=64)
    send_midi_through_the_stream(midi)
    midi = Message(type='control_change', channel=7, control=88, value=89)
    send_midi_through_the_stream(midi)
    assert store.get('active_bank') == 0
    assert store.get('mappings')[bank1_element]['memory'] == 0
    assert store.get('mappings')[bank2_element]['memory'] == 0

    # change to bank 1
    midi = Message(type='note_on', channel=4, note=55, velocity=0)
    send_midi_through_the_stream(midi)
    assert store.get('active_bank') == 1
    # bank1_element should change, bank2_element unchanged
    midi = Message(type='control_change', channel=6, control=77, value=78)
    send_midi_through_the_stream(midi)
    midi = Message(type='control_change', channel=7, control=88, value=89)
    send_midi_through_the_stream(midi)
    assert store.get('mappings')[bank1_element]['memory'] == 78
    assert store.get('mappings')[bank2_element]['memory'] == 0

    # change to bank 2
    midi = Message(type='note_on', channel=5, note=66, velocity=0)
    send_midi_through_the_stream(midi)
    assert store.get('active_bank') == 2
    # bank2_element should change, bank1_element unchanged
    midi = Message(type='control_change', channel=6, control=77, value=127)
    send_midi_through_the_stream(midi)
    midi = Message(type='control_change', channel=7, control=88, value=89)
    send_midi_through_the_stream(midi)
    assert store.get('mappings')[bank1_element]['memory'] == 78
    assert store.get('mappings')[bank2_element]['memory'] == 89

    # change to bank 1
    midi = Message(type='note_on', channel=4, note=55, velocity=0)
    send_midi_through_the_stream(midi)
    assert store.get('active_bank') == 1
    # bank1_element should change, bank2_element unchanged
    midi = Message(type='control_change', channel=6, control=77, value=127)
    send_midi_through_the_stream(midi)
    midi = Message(type='control_change', channel=7, control=88, value=89)
    send_midi_through_the_stream(midi)
    assert store.get('mappings')[bank1_element]['memory'] == 127
    assert store.get('mappings')[bank2_element]['memory'] == 89


def test_calculate_range(mappings_bank_set):
    store.update('mappings', mappings_bank_set)
    store.update('active_bank', 1)

    midi = Message(type='control_change', channel=6, control=77, value=17)
    ret = send_midi_through_the_stream(midi)
    expected = calculate_range(ret['o-range'], 17)
    assert ret['o-level'] == expected

    midi = Message(type='control_change', channel=6, control=77, value=101)
    ret = send_midi_through_the_stream(midi)
    expected = calculate_range(ret['o-range'], 101)
    assert ret['o-level'] == expected

    store.update('active_bank', 2)
    midi = Message(type='control_change', channel=7, control=88, value=89)
    ret = send_midi_through_the_stream(midi)
    expected = calculate_range(ret['o-range'], 89)
    assert ret['o-level'] == expected


def test_set_bank(mappings_bank_set):
    store.update('mappings', mappings_bank_set)
    store.update('active_bank', 0)
    assert store.get('active_bank') == 0

    set_bank(6)
    assert store.get('active_bank') == 0
    set_bank(12)
    assert store.get('active_bank') == 0
    set_bank(121)
    assert store.get('active_bank') == 0

    set_bank(1)
    assert store.get('active_bank') == 1
    set_bank(2)
    assert store.get('active_bank') == 2

    set_bank(1, initial=True)
    assert store.get('active_bank') == 1


@patch('midi_mapper.stream.program_change')
def test_program_change1(program_change_mock, mappings_program_change):
    store.update('mappings', mappings_program_change)
    store.update('active_bank', 0)

    assert program_change_mock.called is False
    assert program_change_mock.call_count == 0

    # Program change 1
    midi = Message(type='note_on', channel=8, note=99, velocity=127)
    send_midi_through_the_stream(midi)
    assert program_change_mock.called is True
    assert program_change_mock.call_count == 1
    expected = int(mappings_program_change[0]['o-control'])
    program_change_mock.assert_called_with(expected)
    # Program change 2
    midi = Message(type='note_on', channel=9, note=111, velocity=127)
    send_midi_through_the_stream(midi)
    expected = int(mappings_program_change[1]['o-control'])
    program_change_mock.assert_called_with(expected)
    assert program_change_mock.call_count == 2


@patch('midi_mapper.stream.send_message')
def test_program_change2(send_message_mock, mappings_program_change):
    store.update('mappings', mappings_program_change)
    store.update('active_bank', 0)

    assert send_message_mock.called is False
    assert send_message_mock.call_count == 0

    # Program change 1
    midi = Message(type='note_on', channel=8, note=99, velocity=127)
    send_midi_through_the_stream(midi)
    assert send_message_mock.called is True
    assert send_message_mock.call_count == 3
    calls = send_message_mock.call_args_list
    assert calls[0][0][0]['type'] == 'note_on'
    assert calls[1][0][0]['type'] == 'program_change'
    assert calls[2][0][0]['type'] == 'note_off'
    # Program change 2
    midi = Message(type='note_on', channel=9, note=111, velocity=127)
    send_midi_through_the_stream(midi)
    assert send_message_mock.call_count == 6
    calls = send_message_mock.call_args_list
    assert calls[3][0][0]['type'] == 'note_off'
    assert calls[4][0][0]['type'] == 'note_on'
    assert calls[5][0][0]['type'] == 'program_change'
