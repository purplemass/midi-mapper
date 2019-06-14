"""
Translate midi messages between input/output devices.

References:
    https://mido.readthedocs.io/en/latest/ports.html
    https://www.bome.com/forums/viewtopic.php?t=2832
    https://www.dataquest.io/blog/python-dictionary-tutorial/

X-Touch Rx Data:
        # change mode
        msg = mido.Message(
            channel=0,
            control=127,
            value=0,  # 0=MC or 1=Standard
            type='control_change',
        )
        # change layer
        msg = mido.Message(
            channel=0,
            program=1,  # 0=LayerA 1=LayerB
            type='program_change',
        )
        # change LED ring
        msg = mido.Message(
            channel=0,
            control=2,
            value=2,
            type='control_change',
        )
        # change button LED
        msg = mido.Message(
            channel=0,
            note=0,
            type='note_on',
        )
"""
import os
import signal
import sys

from devices.device_manager import DeviceManager
from utils.logger import Logger
from config import Config

CONFIG_FILE = './mappings/all.json'

logger = Logger()


def main():
    """"""

    def signal_handler(signal, frame):
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        midi_config = Config(CONFIG_FILE)
    except OSError:
        logger.log('JSON file "{}" missing'.format(CONFIG_FILE))
    except Exception as e:
        logger.log(e)
    else:
        DeviceManager(midi_config)


if __name__ == "__main__":
    os.system('clear')
    main()
