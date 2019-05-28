"""
Translate midi messages between input/output devices.

References:
    https://mido.readthedocs.io/en/latest/ports.html
    https://www.bome.com/forums/viewtopic.php?t=2832
    https://www.dataquest.io/blog/python-dictionary-tutorial/
"""
import json
import os
import time

import mido
from mido.ports import MultiPort

CONFIG_FILE = './config.json'


class Device(object):
    """Device class"""

    def __init__(self, name, props):
        print(100 * '-')
        self.name = name
        self.midi_name = props['midi_name']
        self.type = props['type']
        self.port = None
        print('Create {} device "{}"'.format(self.type, self.name))
        self._connect()

    def _connect(self):
        try:
            self.port = self._get_port()
            print('"{}" connected as "{}"'.format(self.name, self.midi_name))
        except OSError:
            print('Could not connect to "{}"'.format(self.name))

    def translate(self, msg, control, level):
        try:
            details = self.controls[str(control)]
            translate = details['translate']
            out_channel = int(details['channel'] - 1)
        except KeyError:
            return None, None, False

        if (isinstance(translate, str) and '>' in translate):
            return translate, out_channel, True
        else:
            return translate, out_channel, False


class InputDevice(Device):
    """InputDevice class"""

    def __init__(self, name, props):
        super().__init__(name, props)
        self.channel = int(props['channel'] - 1)
        self.controls = props['controls']

    def _get_port(self):
        return mido.open_input(self.midi_name)


class OutputDevice(Device):
    """OutputDevice class"""

    def __init__(self, name, props):
        super().__init__(name, props)

    def _get_port(self):
        return mido.open_output(self.midi_name)


class DeviceManager(object):
    """DeviceManager class"""

    def __init__(self, config):
        self.input_devices = []
        self.input_ports = []
        self.input_lookup = {}
        self.input_multi = None
        self.output_devices = []
        self.output_ports = []
        self._create_devices(config)
        self.run()

    def _create_devices(self, config):
        for my_input in config.get_inputs():
            device = InputDevice(my_input, config.get_props(my_input))
            self.input_devices.append(device)
        for my_output in config.get_outputs():
            device = OutputDevice(my_output, config.get_props(my_output))
            self.output_devices.append(device)

        self.input_ports = [i.port for i in self.input_devices]
        self.output_ports = [i.port for i in self.output_devices]
        self.input_multi = MultiPort(self.input_ports)

        for input_device in self.input_devices:
            self.input_lookup[input_device.channel] = input_device

    def _get_msg_details(self, msg):
        """Get message conrtol and level.
        These are different for notes and CC messages"""
        control = msg.control if hasattr(msg, 'control') else msg.note
        level = msg.value if hasattr(msg, 'value') else msg.velocity
        return control, level

    def _send_midi(self, msg):
        """Send to message to all outputs."""
        for outport in self.output_ports:
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

    def run(self):
        print(100 * '-')
        while True:
            time.sleep(0.1)
            for msg in self.input_multi.iter_pending():
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
                    translate, out_channel, nrpn = my_input.translate(
                        msg, control, level)

                    if translate is not None:
                        if nrpn is True:
                            self._send_nrpn(out_channel, translate, level)
                        else:
                            msg = mido.Message(
                                channel=out_channel,
                                control=int(translate),
                                value=level,
                                type=msg.type,
                            )
                        log2 = '==> CH:{:>2} Control:{:>3}'.format(
                            out_channel + 1, translate)

                except KeyError:
                    pass

                if nrpn is not True:
                    self._send_midi(msg)

                print("{} {}".format(log1, log2))


class MidiConfig(object):
    """MidiConfig class"""

    def __init__(self):
        self._get_connected_devices()

    def _get_connected_devices(self):
        self.input_names = mido.get_input_names()
        self.outputs_names = mido.get_output_names()

    def _parse(self, data):
        self.data = data
        self.inputs = data['inputs']
        self.outputs = data['outputs']

    def process(self, file):
        with open(file) as handle:
            data = json.loads(handle.read())
        self._parse(data)
        self._get_connected_devices()

    def get_inputs(self):
        return self.inputs.keys()

    def get_outputs(self):
        return self.outputs.keys()

    def get_props(self, device):
        if device in self.inputs.keys():
            props = self.inputs[device]
            props['type'] = 'input'
        elif device in self.outputs.keys():
            props = self.outputs[device]
            props['type'] = 'output'
        else:
            return None
        props['midi_name'] = next((
            s for s in self.input_names if device in s), device)
        return props


if __name__ == "__main__":
    os.system('clear')
    try:
        config = MidiConfig()
        config.process(CONFIG_FILE)
    except OSError:
        print('JSON file "{}" missing'.format(CONFIG_FILE))
    except Exception as e:
        print(e)
    else:
        DeviceManager(config)
