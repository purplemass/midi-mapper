""""""

import json

import mido


class MidiConfig(object):
    """MidiConfig class"""

    def __init__(self, file):
        self.file = file
        self.process()

    def _get_connected_devices(self):
        self.midi_input_names = mido.get_input_names()
        self.midi_output_names = mido.get_output_names()

    def _load_file(self):
        with open(self.file) as handle:
            data = json.loads(handle.read())
        self.inputs = data['inputs']
        self.outputs = data['outputs']

    def process(self):
        self._get_connected_devices()
        self._load_file()

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
