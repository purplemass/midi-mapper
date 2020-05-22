"""
Open Midi Out port
"""
from time import sleep

import rtmidi


MIDIOUT_NAME = 'BobOut'

midiout = rtmidi.MidiOut()
midiout.open_virtual_port(MIDIOUT_NAME)

try:
    # Just wait for keyboard interrupt
    while True:
        sleep(1)
except KeyboardInterrupt:
    print('Keyboard interrupt')
finally:
    print("Exit.")
    midiout.close_port()
    del midiout
