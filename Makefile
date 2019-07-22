SHELL := /bin/bash
COVERAGE_FAIL_UNDER = 90

run:
	clear; python3 -m midi_mapper.app

debug:
	clear; python3 -m midi_mapper.app -v

test:
	clear; mypy midi_mapper; python3 -m pytest -s

test-cover:
	clear; mypy midi_mapper; python3 -m pytest -s --cov=midi_mapper --cov-report term-missing --cov-fail-under=${COVERAGE_FAIL_UNDER}

cover:
	clear; coverage report -m ./midi_mapper/*.py


put:
	scp -r ./* pi@192.168.1.11:/home/pi/midi_mapper/
