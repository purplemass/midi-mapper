""""""

import pytest

from midi_mapper.app import run


def f():
    raise SystemExit(1)


def test_mytest():
    print(run)
    with pytest.raises(SystemExit):
        f()
