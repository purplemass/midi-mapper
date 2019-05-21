"""
References:
    https://mido.readthedocs.io/en/latest/ports.html
    https://www.bome.com/forums/viewtopic.php?t=2832
    https://www.dataquest.io/blog/python-dictionary-tutorial/
"""
import time

import mido
from mido.ports import MultiPort

INPUT_DEVICES = ['Faderfox UC4', 'XONE:K2', ]
OUTPUT_DEVICES = ['Circuit', ]

CONTROLS = {
    16: {
        'control': 12,
        'description': 'Synth1 Volume',
        'in_channel': 14,
        'out_channel': 15,
    },
    17: {
        'control': 14,
        'description': 'Synth2 Volume',
        'in_channel': 14,
        'out_channel': 15,
    },
}


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
                if control == key:
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
    for input_port in INPUT_DEVICES:
        port = open_port('input', input_port)
        if port is not None:
            inports.append(port)
    for output_port in OUTPUT_DEVICES:
        port = open_port('output', output_port)
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
