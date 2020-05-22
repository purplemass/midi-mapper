"""Test functions related to mappings."""
import os

import pytest

from midi_mapper import mappings
from midi_mapper.mappings import import_mappings


def test_import_mappings_success():
    mappings.MAPPINGS_FOLDER = '/tmp'
    data = import_mappings()
    assert data == []


def test_import_mappings_fail():
    with pytest.raises(FileNotFoundError):
        mappings.MAPPINGS_FOLDER = '/some-non-existent-folder'
        import_mappings()


def test_import_mappings_dummy_csv():
    dummy_file_path = '/tmp/test.csv'
    mappings.MAPPINGS_FOLDER = '/tmp'

    with open(dummy_file_path, 'w') as f:
        f.write('input-device,channel,output-device,channel\n')
        f.write('DeviceIn,1,DeviceOut,11\n')
        f.write('DeviceIn,2,DeviceOut,12\n')

    data = import_mappings()
    os.remove(dummy_file_path)
    assert data[0]['input-device'] == 'DeviceIn'
    assert data[0]['channel'] == '1'
    assert data[0]['output-device'] == 'DeviceOut'
    assert data[0]['o-channel'] == '11'
    assert data[0]['memory'] == '0'
    assert data[1]['channel'] == '2'
    assert data[1]['o-channel'] == '12'
    assert data[1]['memory'] == '0'
