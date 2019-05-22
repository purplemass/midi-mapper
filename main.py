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


def main():
    """Main loop where messages are read from inputs and processed."""
    inports, outports = open_ports()
    multi = MultiPort(inports)
    while True:
        time.sleep(0.1)
        for msg in multi.iter_pending():
            control, level = get_msg_details(msg)
            extra = ''
            for key, details in CONTROLS.items():
                if (control == int(key) and
                        msg.channel == int(details['in_channel']) - 1):

                    translate = details['translate']
                    out_channel = int(details['out_channel'])

                    if (isinstance(translate, str) and '>' in translate):
                        send_nrpn(outports, out_channel - 1, translate, level)
                    else:
                        msg = mido.Message(
                            channel=out_channel - 1,
                            control=int(translate),
                            value=level,
                            type=msg.type,
                        )
                        send_out(outports, msg)

                    extra = '==> CH:{:>2} Control:{:>3}'.format(
                        out_channel, translate)
                    break

            # send untranslated messages
            if extra == '':
                send_out(outports, msg)

            print("CH:{:>2} Control:{:>3} Value:{:>3} [{}] {}".format(
                details['in_channel'],
                control,
                level,
                'CC' if msg.type == 'control_change' else 'NT',
                extra,
            ))


def send_nrpn(outports, channel, control, level):
    """Send NRPN message of this format:

        MIDI # 16 CC 99 = control[0]
        MIDI # 16 CC 98 = control[1]
        MIDI # 16 CC 6 = level
        MIDI # 16 CC 38 = 0
    """
    control = control.split('>')
    if len(control) != 2:
        return
    cc = 'control_change'
    msg = mido.Message(
        channel=channel, control=99, value=int(control[0]), type=cc)
    send_out(outports, msg)
    msg = mido.Message(
        channel=channel, control=98, value=int(control[1]), type=cc)
    send_out(outports, msg)
    msg = mido.Message(
        channel=channel, control=6, value=level, type=cc)
    send_out(outports, msg)
    msg = mido.Message(
        channel=channel, control=38, value=0, type=cc)
    send_out(outports, msg)


def send_out(outports, msg):
    """Send to message all outputs."""
    for outport in outports:
        outport.send(msg)


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


if __name__ == "__main__":
    main()
