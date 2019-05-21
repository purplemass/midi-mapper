SHELL := /bin/bash

run:
	python main.py

put:
	scp main.py pi@192.168.1.17:/home/pi/

get:
	scp pi@192.168.1.17:/home/pi/main.py .
