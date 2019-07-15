SHELL := /bin/bash

run:
	clear; python3 -m midi_mapper.app

debug:
	clear; python3 -m midi_mapper.app -v

test:
	clear; mypy -m midi_mapper; python -m pytest -s


put:
	scp main.py config.py pi@192.168.1.17:/home/pi/

get-config:
	scp pi@192.168.1.17:/home/pi/main.py .

get-main:
	scp pi@192.168.1.17:/home/pi/main.py .
