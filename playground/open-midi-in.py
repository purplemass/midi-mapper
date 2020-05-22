"""
Open Midi In port and print messages

https://github.com/SpotlightKid/python-rtmidi/blob/master/examples/basic/midiin_callback.py
"""
from time import sleep, time

import rtmidi


MIDIIN_NAME = 'BobIn'


class MidiInputHandler(object):

    def __init__(self, port):
        self.port = port
        self._wallclock = time()

    def __call__(self, event, data=None):
        message, deltatime = event
        self._wallclock += deltatime
        print("[%s] @%0.6f %r" % (self.port, self._wallclock, message))


midiin = rtmidi.MidiIn()
midiin.open_virtual_port(MIDIIN_NAME)
midiin.ignore_types(sysex=True,
                    timing=False,
                    active_sense=True)
midiin.set_callback(MidiInputHandler(MIDIIN_NAME))

try:
    # Just wait for keyboard interrupt,
    # everything else is handled via the input callback.
    while True:
        sleep(1)
except KeyboardInterrupt:
    print('Keyboard interrupt')
finally:
    print("Exit.")
    midiin.close_port()
    del midiin
