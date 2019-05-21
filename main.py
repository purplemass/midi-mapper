"""
Translate midi messages between input/output devices.

References:
    https://mido.readthedocs.io/en/latest/ports.html
    https://www.bome.com/forums/viewtopic.php?t=2832
    https://www.dataquest.io/blog/python-dictionary-tutorial/
"""
import time

import mido
from mido.ports import MultiPort

from config import INPUT_DEVICES, OUTPUT_DEVICES, CONTROLS


def main_loop():
    inports, outports = open_ports()
    multi = MultiPort(inports)
    while True:
        time.sleep(0.1)
        for msg in multi.iter_pending():
            control, level = get_msg_details(msg)
            extra = ''
            midi_msg = msg
            for key, details in CONTROLS.items():
                if control == key and msg.channel == details['in_channel']:
                    extra = '==> CH:{:>2} Control:{:>3}'.format(
                        details['out_channel'], details['control'])
                    midi_msg = mido.Message(
                        channel=details['out_channel'],
                        control=details['control'],
                        value=level,
                        type=msg.type,
                    )
                    break
            for outport in outports:
                outport.send(midi_msg)

            print("CH:{:>2} Control:{:>3} Value:{:>3} [{}] {}".format(
                msg.channel,
                control,
                level,
                'CC' if msg.type == 'control_change' else 'NT',
                extra,
            ))


def open_ports():
    """"""
    inports = []
    outports = []

    def open_port(type, port):
        try:
            if type == 'input':
                opened_port = mido.open_input(port)
            else:
                opened_port = mido.open_output(port)
            print('Connected to {} as {}'.format(port, type))
        except OSError:
            opened_port = None
            print('Could not connect to {} as {}'.format(port, type))
        return opened_port

    print(100 * '-')

    input_devices = [
        j for i in INPUT_DEVICES for j in mido.get_input_names() if i in j]
    for input_device in input_devices:
        port = open_port('input', input_device)
        if port is not None:
            inports.append(port)

    output_devices = [
        j for i in OUTPUT_DEVICES for j in mido.get_output_names() if i in j]
    for output_device in output_devices:
        port = open_port('output', output_device)
        if port is not None:
            outports.append(port)

    print(100 * '-')
    return inports, outports


def get_msg_details(msg):
    """"""
    control = msg.control if hasattr(msg, 'control') else msg.note
    level = msg.value if hasattr(msg, 'value') else msg.velocity
    return control, level


def main():
    """"""
    main_loop()


if __name__ == "__main__":
    main()
