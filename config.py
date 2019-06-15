""""""
import json

import mido


class Config(object):
    """Config class"""

    def __init__(self, file):
        self.file = file
        self.process()

    def _get_connected_devices(self):
        self.input_names = mido.get_input_names()
        self.output_names = mido.get_output_names()

    def _process_file(self):
        with open(self.file) as handle:
            data = json.loads(handle.read())
        self.inputs = data['inputs']
        self.outputs = data['outputs']
        try:
            self.clock_input = data['clock']['input']
            if self.clock_input not in self.input_names:
                self.clock_input = None
        except KeyError:
            self.clock_input = None
        try:
            self.clock_outputs = []
            for clock_out in data['clock']['outputs']:
                if clock_out in self.output_names:
                    self.clock_outputs.append(clock_out)
        except KeyError:
            pass

    def process(self):
        self._get_connected_devices()
        self._process_file()

    def get_inputs(self):
        return self.inputs.keys()

    def get_outputs(self):
        return self.outputs.keys()

    def get_clock_input(self):
        return self.clock_input

    def get_clock_outputs(self):
        return self.clock_outputs

    def get_device_info(self, device):
        if device in self.inputs.keys():
            info = self.inputs[device]
            info['type'] = 'input'
            info['midi_name'] = next((
                s for s in self.input_names if device in s), device)
        elif device in self.outputs.keys():
            info = self.outputs[device]
            info['type'] = 'output'
            info['midi_name'] = next((
                s for s in self.output_names if device in s), device)
        else:
            return None
        return info
