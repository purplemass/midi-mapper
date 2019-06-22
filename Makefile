SHELL := /bin/bash

run:
	clear; python3 main.py

test:
	clear; pytest

put:
	scp main.py config.py pi@192.168.1.17:/home/pi/

get-config:
	scp pi@192.168.1.17:/home/pi/main.py .

get-main:
	scp pi@192.168.1.17:/home/pi/main.py .
