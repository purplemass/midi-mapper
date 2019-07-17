"""Test functions related to midi stream."""
from mido import Message

from midi_mapper.stream import check_mappings
from midi_mapper.stream import create_stream_data
from midi_mapper.stream import log
from midi_mapper.stream import process_midi
from midi_mapper.stream import store
from midi_mapper.stream import translate_and_send


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


def test_check_mappings_bank0(mappings_bank0):
    # Ensure mappings are set for these tests
    store.update('mappings', mappings_bank0)
    store.update('active_bank', 0)

    midi = Message(type='note_off', channel=0, note=1, velocity=0)
    ret = check_mappings(process_midi(create_stream_data(midi)))
    assert len(ret['translations']) == 0

    midi = Message(type='note_on', channel=15, note=1, velocity=0)
    ret = check_mappings(process_midi(create_stream_data(midi)))
    assert len(ret['translations']) == 0

    midi = Message(type='note_on', channel=0, note=127, velocity=0)
    ret = check_mappings(process_midi(create_stream_data(midi)))
    assert len(ret['translations']) == 0

    midi = Message(type='note_on', channel=0, note=11, velocity=0)
    ret = check_mappings(process_midi(create_stream_data(midi)))
    assert len(ret['translations']) == 1

    midi = Message(type='control_change', channel=15, control=2, value=64)
    ret = check_mappings(process_midi(create_stream_data(midi)))
    assert len(ret['translations']) == 0

    midi = Message(type='control_change', channel=0, control=127, value=64)
    ret = check_mappings(process_midi(create_stream_data(midi)))
    assert len(ret['translations']) == 0

    midi = Message(type='control_change', channel=1, control=22, value=64)
    ret = check_mappings(process_midi(create_stream_data(midi)))
    assert len(ret['translations']) == 1

    # bank0 mappings are not affected by setting the bank
    store.update('active_bank', 1)

    ret = check_mappings(process_midi(create_stream_data(midi)))
    assert len(ret['translations']) == 1


def test_check_mappings_bank1(mappings_bank1):
    # Ensure mappings are set for these tests
    store.update('mappings', mappings_bank1)
    store.update('active_bank', 0)

    midi = Message(type='note_off', channel=0, note=1, velocity=0)
    ret = check_mappings(process_midi(create_stream_data(midi)))
    assert len(ret['translations']) == 0

    midi = Message(type='note_on', channel=0, note=1, velocity=0)
    ret = check_mappings(process_midi(create_stream_data(midi)))
    assert len(ret['translations']) == 0

    # change bank
    store.update('active_bank', 1)

    midi = Message(type='note_on', channel=2, note=33, velocity=0)
    ret = check_mappings(process_midi(create_stream_data(midi)))
    assert len(ret['translations']) == 1


def test_check_log(mappings_bank1):
    store.update('active_bank', 1)

    midi = Message(type='note_on', channel=2, note=33, velocity=0)
    ret = check_mappings(process_midi(create_stream_data(midi)))
    assert len(ret['translations']) == 1
    log(ret)


def test_translate_and_send0(mappings_bank0):
    store.update('mappings', mappings_bank0)
    store.update('active_bank', 0)

    midi = Message(type='note_on', channel=0, note=11, velocity=0)
    ret = translate_and_send(
        check_mappings(process_midi(create_stream_data(midi))))
    assert len(ret['translations']) == 1

    store.update('active_bank', 1)

    midi = Message(type='note_on', channel=0, note=11, velocity=0)
    ret = translate_and_send(
        check_mappings(process_midi(create_stream_data(midi))))
    assert len(ret['translations']) == 1


def test_translate_and_send1(mappings_bank1):
    store.update('mappings', mappings_bank1)
    store.update('active_bank', 0)

    midi = Message(type='note_on', channel=0, note=11, velocity=0)
    ret = translate_and_send(
        check_mappings(process_midi(create_stream_data(midi))))
    assert len(ret['translations']) == 0

    store.update('active_bank', 1)

    midi = Message(type='note_on', channel=2, note=33, velocity=0)
    ret = translate_and_send(
        check_mappings(process_midi(create_stream_data(midi))))
    assert len(ret['translations']) == 1


def test_check_mappings_bank_set(mappings_bank_set):
    store.update('mappings', mappings_bank_set)
    store.update('active_bank', 0)

    midi = Message(type='note_on', channel=15, note=1, velocity=0)
    translate_and_send(check_mappings(process_midi(create_stream_data(midi))))
    assert store.get('active_bank') == 0

    midi = Message(type='note_on', channel=4, note=55, velocity=0)
    translate_and_send(check_mappings(process_midi(create_stream_data(midi))))
    assert store.get('active_bank') == 1

    midi = Message(type='note_on', channel=5, note=66, velocity=0)
    translate_and_send(check_mappings(process_midi(create_stream_data(midi))))
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
    translate_and_send(check_mappings(process_midi(create_stream_data(midi))))
    midi = Message(type='control_change', channel=7, control=88, value=89)
    translate_and_send(check_mappings(process_midi(create_stream_data(midi))))
    assert store.get('active_bank') == 0
    assert store.get('mappings')[bank1_element]['memory'] == 0
    assert store.get('mappings')[bank2_element]['memory'] == 0

    # change to bank 1
    midi = Message(type='note_on', channel=4, note=55, velocity=0)
    translate_and_send(check_mappings(process_midi(create_stream_data(midi))))
    assert store.get('active_bank') == 1
    # bank1_element should change, bank2_element unchanged
    midi = Message(type='control_change', channel=6, control=77, value=78)
    translate_and_send(check_mappings(process_midi(create_stream_data(midi))))
    midi = Message(type='control_change', channel=7, control=88, value=89)
    translate_and_send(check_mappings(process_midi(create_stream_data(midi))))
    assert store.get('mappings')[bank1_element]['memory'] == 78
    assert store.get('mappings')[bank2_element]['memory'] == 0

    # change to bank 2
    midi = Message(type='note_on', channel=5, note=66, velocity=0)
    translate_and_send(check_mappings(process_midi(create_stream_data(midi))))
    assert store.get('active_bank') == 2
    # bank2_element should change, bank1_element unchanged
    midi = Message(type='control_change', channel=6, control=77, value=127)
    translate_and_send(check_mappings(process_midi(create_stream_data(midi))))
    midi = Message(type='control_change', channel=7, control=88, value=89)
    translate_and_send(check_mappings(process_midi(create_stream_data(midi))))
    assert store.get('mappings')[bank1_element]['memory'] == 78
    assert store.get('mappings')[bank2_element]['memory'] == 89

    # change to bank 1
    midi = Message(type='note_on', channel=4, note=55, velocity=0)
    translate_and_send(check_mappings(process_midi(create_stream_data(midi))))
    assert store.get('active_bank') == 1
    # bank1_element should change, bank2_element unchanged
    midi = Message(type='control_change', channel=6, control=77, value=127)
    translate_and_send(check_mappings(process_midi(create_stream_data(midi))))
    midi = Message(type='control_change', channel=7, control=88, value=89)
    translate_and_send(check_mappings(process_midi(create_stream_data(midi))))
    assert store.get('mappings')[bank1_element]['memory'] == 127
    assert store.get('mappings')[bank2_element]['memory'] == 89
