"""Test functions related to main app."""
import pytest

from unittest.mock import patch

from midi_mapper import app


@patch('time.sleep', side_effect=InterruptedError)
@patch('midi_mapper.app.io_ports', lambda: [])
@patch('midi_mapper.app.import_mappings', lambda: [])
def test_main_loop(mocked_sleep):
    with pytest.raises(InterruptedError):
        app.run()
        app.store.update('active_bank', 0)
