SHELL := /bin/bash

run:
	python3 main.py

put:
	scp main.py config.py pi@192.168.1.17:/home/pi/

get-config:
	scp pi@192.168.1.17:/home/pi/main.py .

get-main:
	scp pi@192.168.1.17:/home/pi/main.py .
