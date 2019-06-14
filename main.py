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
import json
import os
import signal
import sys
import time

import mido
from mido.ports import MultiPort

CONFIG_FILE = './config.json'
SPECIAL_COMMANDS = ['RELOAD']


class Device(object):
    """Device class"""

    def __init__(self, name, info):
        print(100 * '-')
        self.name = name
        self.midi_name = info['midi_name']
        self.port = None
        print('Create {} device "{}"'.format(info['type'], self.name))
        self._connect()

    def _connect(self):
        try:
            self.port = self._get_port()
            print('"{}" connected as "{}"'.format(self.name, self.midi_name))
        except OSError:
            print('Error: Could not connect to "{}"'.format(self.name))


class InputDevice(Device):
    """InputDevice class"""

    def __init__(self, name, info):
        super().__init__(name, info)
        self.channel = int(info['channel'] - 1)
        self.controls = info['controls']

    def _get_port(self):
        return mido.open_input(self.midi_name)

    def translate(self, control, level):
        try:
            details = self.controls[str(control)]
            translate = details['translate']
            channel = int(details['channel'] - 1)
        except KeyError:
            return None, None, False

        nrpn = True if (
            isinstance(translate, str) and '>' in translate) else False
        return translate, channel, nrpn


class OutputDevice(Device):
    """OutputDevice class"""

    def __init__(self, name, info):
        super().__init__(name, info)

    def _get_port(self):
        return mido.open_output(self.midi_name)


class DeviceManager(object):
    """DeviceManager class"""

    def __init__(self, midi_config):
        self.midi_config = midi_config
        self._reset()
        self.run()

    def _reset(self):
        self.input_lookup = {}
        self.input_multi = None
        self.output_ports = []
        self._create_devices()

    def _create_devices(self):
        input_devices = []
        input_ports = []
        for my_input in self.midi_config.get_inputs():
            device = InputDevice(
                my_input, self.midi_config.get_device_info(my_input))
            input_devices.append(device)
            self.input_lookup[device.channel] = device
            if device.port is not None:
                input_ports.append(device.port)
        for my_output in self.midi_config.get_outputs():
            device = OutputDevice(
                my_output, self.midi_config.get_device_info(my_output))
            self.output_ports.append(device.port)
        self.input_multi = MultiPort(input_ports)

    def _get_msg_details(self, msg):
        """Get message control and level.
        These are different for notes and CC messages"""
        if msg.type == 'pitchwheel':
            return msg.pitch, msg.pitch
        control = msg.control if hasattr(msg, 'control') else msg.note
        level = msg.value if hasattr(msg, 'value') else msg.velocity
        return control, level

    def _send_midi(self, msg):
        """Send to message to all outputs."""
        for outport in self.output_ports:
            if outport is not None:
                outport.send(msg)

    def _send_nrpn(self, channel, control, level):
        """Send NRPN message of the format below to all ports:

            MIDI # 16 CC 99 = control[0]
            MIDI # 16 CC 98 = control[1]
            MIDI # 16 CC 6 = level
            MIDI # 16 CC 38 = 0

            Note that control is formatted like: '1>9'
        """
        control = control.split('>')
        if len(control) != 2:
            return
        cc = 'control_change'
        msg = mido.Message(
            channel=channel, control=99, value=int(control[0]), type=cc)
        self._send_midi(msg)
        msg = mido.Message(
            channel=channel, control=98, value=int(control[1]), type=cc)
        self._send_midi(msg)
        msg = mido.Message(
            channel=channel, control=6, value=level, type=cc)
        self._send_midi(msg)
        msg = mido.Message(
            channel=channel, control=38, value=0, type=cc)
        self._send_midi(msg)

    def _compose_message(self, channel, translate, level, mtype):

        def note():
            return mido.Message(
                channel=channel,
                note=int(translate),
                velocity=level,
                type=mtype,
            )

        def control_change():
            return mido.Message(
                channel=channel,
                control=int(translate),
                value=level,
                type=mtype,
            )

        def program_change():
            return mido.Message(
                channel=channel,
                program=int(translate),
                type='program_change',
            )

        switcher = {
            'note_on': note,
            'note_off': note,
            'control_change': control_change,
            'program_change': program_change,
        }
        return switcher.get(mtype, None)()

    def _special_commands(self, cmd):

        print(100 * '>')

        if cmd == 'RELOAD':
            self.midi_config.process()
            self._reset()

    def _process_message(self, msg):
        translate = None
        translated_msg = None
        control, level = self._get_msg_details(msg)
        log1 = "CH:{:>2} Control:{:>3} [{:>3} {}]".format(
            msg.channel + 1,
            control,
            level,
            'CC' if msg.type == 'control_change' else 'NT',
        )
        log2 = '==>'
        nrpn = False

        try:
            my_input = self.input_lookup[msg.channel]
            translate, channel, nrpn = my_input.translate(control, level)

            if translate is not None:
                if translate in SPECIAL_COMMANDS:
                    if msg.type == 'note_off':
                        self._special_commands(translate)
                elif nrpn is True:
                    self._send_nrpn(channel, translate, level)
                else:
                    translated_msg = self._compose_message(
                        channel, translate, level, msg.type)
                log2 = '==> CH:{:>2} Control:{:>3}'.format(
                    channel + 1, translate)

        except KeyError:
            pass

        if nrpn is not True:
            self._send_midi(
                translated_msg if translated_msg is not None else msg)

        # send to self
        if msg.type == 'note_off' and translate == control:
            ret_msg = mido.Message(
                channel=msg.channel,
                note=msg.note,
                type='note_on',
            )
            self._send_midi(ret_msg)

        print("{} {}".format(log1, log2))

    def run(self):
        print(100 * '-')
        while True:
            time.sleep(0.1)
            for msg in self.input_multi.iter_pending():
                self._process_message(msg)


class MidiConfig(object):
    """MidiConfig class"""

    def __init__(self, file):
        self._get_connected_devices()
        self.file = file
        self.process()

    def _get_connected_devices(self):
        self.midi_input_names = mido.get_input_names()
        self.midi_output_names = mido.get_output_names()

    def process(self):
        with open(self.file) as handle:
            data = json.loads(handle.read())
        self.inputs = data['inputs']
        self.outputs = data['outputs']

    def get_inputs(self):
        return self.inputs.keys()

    def get_outputs(self):
        return self.outputs.keys()

    def get_device_info(self, device):
        if device in self.inputs.keys():
            info = self.inputs[device]
            info['type'] = 'input'
            info['midi_name'] = next((
                s for s in self.midi_input_names if device in s), device)
        elif device in self.outputs.keys():
            info = self.outputs[device]
            info['type'] = 'output'
            info['midi_name'] = next((
                s for s in self.midi_output_names if device in s), device)
        else:
            return None
        return info


def main():
    """"""

    def signal_handler(signal, frame):
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        midi_config = MidiConfig(CONFIG_FILE)
    except OSError:
        print('JSON file "{}" missing'.format(CONFIG_FILE))
    except Exception as e:
        print(e)
    else:
        DeviceManager(midi_config)


if __name__ == "__main__":
    os.system('clear')
    main()
