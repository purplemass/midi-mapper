"""
Helpers for devices.
"""
import threading
import time

from mido import Message, open_input
from mido.ports import MultiPort

from .devices import InputDevice, OutputDevice


CLOCK_START_DELAY = 0.005


def send_midi(msg, outputs):
    """Send MIDI to output ports."""
    for port in outputs:
        if port is not None:
            port.send(msg)


class MidiMessage(object):
    """"""

    def get_details(self, msg):
        """Get message control and level.
        These are different for notes and CC messages"""
        if msg.type == 'pitchwheel':
            return msg.pitch, msg.pitch, 'PW'
        control = msg.control if hasattr(msg, 'control') else msg.note
        level = msg.value if hasattr(msg, 'value') else msg.velocity
        mtype = 'CC' if msg.type == 'control_change' else 'NT'
        return control, level, mtype

    def compose(self, channel, translate, level, mtype):

        def note():
            return Message(
                channel=channel,
                note=int(translate),
                velocity=level,
                type=mtype,
            )

        def control_change():
            return Message(
                channel=channel,
                control=int(translate),
                value=level,
                type=mtype,
            )

        def program_change():
            return Message(
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


class MidiInput(object):
    """"""

    def __init__(self, config):
        self.config = config

    def create_ports(self):
        input_lookup = {}
        input_devices = []
        input_ports = []
        output_ports = []
        clock_out_ports = []
        # inputs
        for my_input in self.config.get_inputs():
            device = InputDevice(
                my_input, self.config.get_device_info(my_input))
            input_devices.append(device)
            input_lookup[device.channel] = device
            if device.port is not None:
                input_ports.append(device.port)
        # outputs
        for my_output in self.config.get_outputs():
            device = OutputDevice(
                my_output, self.config.get_device_info(my_output))
            output_ports.append(device.port)
            # clock out ports
            if device.name in self.config.get_clock_outputs():
                clock_out_ports.append(device.port)

        return {
            'input_lookup': input_lookup,
            'input_multi': MultiPort(input_ports),
            'output_ports': output_ports,
            'clock_out_ports': clock_out_ports,
        }


class MidiOutput(object):
    """"""

    def set_outputs(self, outputs):
        """Set output ports."""
        self.outputs = outputs

    def send_midi(self, msg):
        """Send MIDI message to all outputs."""
        send_midi(msg, self.outputs)

    def send_nrpn(self, channel, control, level):
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
        msg = Message(
            channel=channel, control=99, value=int(control[0]), type=cc)
        self.send_midi(msg)
        msg = Message(
            channel=channel, control=98, value=int(control[1]), type=cc)
        self.send_midi(msg)
        msg = Message(
            channel=channel, control=6, value=level, type=cc)
        self.send_midi(msg)
        msg = Message(
            channel=channel, control=38, value=0, type=cc)
        self.send_midi(msg)


class MidiClock(object):
    """Handle clock input/outputs."""

    def __init__(self, config):
        self.keep_running = True
        self.input = None
        clock_input = config.get_clock_input()
        if clock_input is not None:
            self.input = open_input(clock_input)

    def set_outputs(self, outputs):
        """Set output ports."""
        self.outputs = outputs
        send_midi(Message(type='stop'), self.outputs)

    def _get_midi(self):
        while self.keep_running:
            for msg in self.input:
                if (msg.type == 'clock' or
                        msg.type == 'start' or
                        msg.type == 'stop'):
                    # slight delay at start
                    if msg.type == 'start':
                        time.sleep(CLOCK_START_DELAY)
                    send_midi(msg, self.outputs)

    def start(self):
        if self.input is not None:
            threading.Thread(target=self._get_midi, daemon=True).start()

    def stop(self):
        send_midi(Message(type='stop'), self.outputs)
        self.keep_running = False
