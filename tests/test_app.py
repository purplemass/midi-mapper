"""Test functions related to main app."""
import pytest

from unittest.mock import patch

from mido.ports import MultiPort

from midi_mapper import app
from midi_mapper.store import Store


@patch('time.sleep', side_effect=InterruptedError)
@patch('midi_mapper.app.io_ports', lambda: [])
@patch('midi_mapper.app.import_mappings', lambda: [])
def test_main_loop(mocked_sleep):
    with pytest.raises(InterruptedError):
        app.run()
        app.store.update('active_bank', 0)


store = Store({
    'active_bank': 0,
    'active_programe': None,
    'mappings': [],
    'inports': MultiPort([]),
    'outports': MultiPort([]),
    'midi_stream': None,
})


@patch('midi_mapper.app.print', lambda _: [])
@patch('midi_mapper.app.store', store)
def test_signal_handler():
    with pytest.raises(SystemExit):
        app.signal_handler(None, None)
