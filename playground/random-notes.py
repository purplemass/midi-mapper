"""
Play Random Music

Now in the Major scale :-)

Lots more to do:
http://www.guitarland.com/Music10/FGA/LectureMIDIscales.html
"""
import random
import signal
import sys

from threading import Thread
from time import sleep

import rtmidi

# COA Resonant Pad
# COA Lofi Soft Pad 2
# SF Brass CC2 A
CONCURRENT_NOTES = 3

MIDIOUT_NAME = 'BobOut'

compositions = []

midiout = rtmidi.MidiOut()
midiout.open_virtual_port(MIDIOUT_NAME)

# https://syntheway.com/MIDI_Keyboards_Middle_C_MIDI_Note_Number_60_C4.htm
MAJOR = [
    # 24, 26, 28, 29, 31, 33, 35,
    36, 38, 40, 41, 43, 45, 47,
    48, 50, 52, 53, 55, 57, 59,
    60, 62, 64, 65, 67, 69, 71,
    72, 74, 76, 77, 79, 81, 83,
    # 84, 86, 88, 89, 91, 93, 95,
]

SCALE = MAJOR


def compose() -> object:
    # note = random.randint(20, 100)
    note = SCALE[random.randint(0, len(SCALE) - 1)]
    # note = 64
    velocity = random.randint(20, 100)
    delay = random.randint(
        1, CONCURRENT_NOTES) / 10.0 / CONCURRENT_NOTES
    return {
        'delay1': delay,
        'on': [0x90, note, velocity],
        'delay2': random.randint(50, 200) / 50.0,
        'off': [0x80, note, 0],
        'delay3': delay + random.random(),
    }


def play_note(midiout, composition, index) -> None:
    # sleep(composition['delay1'] + index / 10.0)
    print(composition['on'])
    midiout.send_message(composition['on'])
    # sleep(composition['delay2'])
    sleep(1)
    midiout.send_message(composition['off'])
    # sleep(composition['delay3'])


def create_compositions():
    compositions = []
    for i in range(CONCURRENT_NOTES):
        compositions.append(compose())
    delays = []
    for comp in compositions:
        delay = comp['delay1'] + comp['delay2']
        delays.append(delay)
    delays.sort()
    compositions[CONCURRENT_NOTES - 2] = compositions[0]
    return compositions, delays


def run(midiout) -> None:
    global compositions

    compositions, delays = create_compositions()
    main_delay = int(delays[-1]) - (CONCURRENT_NOTES / 10)
    main_delay = int(delays[-1]) - 0.5 - random.random() * 3

    with midiout:
        for i in range(1, 1000):
            print(50 * '-')
            for index in range(len(compositions)):
                comp = compositions[index]
                player = Thread(
                    target=play_note,
                    args=(midiout, comp, index),
                    daemon=True,
                )
                player.start()
                # player.join()
            sleep(main_delay)
            if i % CONCURRENT_NOTES / 2 == 0:
                print(50 * '=')
                random.shuffle(compositions)
            if i % CONCURRENT_NOTES == 0:
                print(50 * '>')
                compositions, delays = create_compositions()
            compositions, delays = create_compositions()

    del midiout


def signal_handler(*args) -> None:
    """Handle keyboard interupt and close all ports."""
    global compositions, midiout
    print('\033[H\033[J')
    print('Keyboard interupt detected\n')
    for composition in compositions:
        print(composition['off'])
        midiout.send_message(composition['off'])
    sys.exit(0)


if __name__ == "__main__":  # pragma: no cover
    """Add keyboard interupt handler and run application."""
    signal.signal(signal.SIGINT, signal_handler)
    run(midiout)
