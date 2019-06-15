""""""

import threading
import time

import mido
from mido.ports import MultiPort

from utils.logger import Logger

from .devices import InputDevice, OutputDevice
from .helpers import MidiMessage, MidiOutput

SPECIAL_COMMANDS = ['RELOAD']

logger = Logger()


class DeviceManager(object):
    """DeviceManager class"""

    def __init__(self, config):
        self.config = config
        self.message = MidiMessage()
        self.output = MidiOutput()
        self._reset()
        self._run()

    def _reset(self):
        self.input_lookup = {}
        self.input_multi = None
        self._create_devices()

    def _run(self):

        def get_midi():
            while True:
                for msg in self.input_multi.iter_pending():
                    self._process_message(msg)

        logger.log(line=True)
        threading.Thread(target=get_midi).start()
        while True:
            time.sleep(1)

    def _create_devices(self):
        input_devices = []
        input_ports = []
        output_ports = []
        clock_ports = []
        for my_input in self.config.get_inputs():
            device = InputDevice(
                my_input, self.config.get_device_info(my_input))
            input_devices.append(device)
            self.input_lookup[device.channel] = device
            if device.port is not None:
                input_ports.append(device.port)
        for my_output in self.config.get_outputs():
            device = OutputDevice(
                my_output, self.config.get_device_info(my_output))
            output_ports.append(device.port)
            # clock ports
            if device.port is not None and 'Deluge' in device.port.name:
                clock_ports.append(device.port)

        self.input_multi = MultiPort(input_ports)
        self.output.set_outputs(output_ports, clock_ports)

    def _special_commands(self, cmd):

        logger.log()
        logger.log(dline=True)

        if cmd == 'RELOAD':
            self.config.process()
            self._reset()

    def _process_message(self, msg):
        if msg.type == 'clock':
            self.output.send_clock(msg)
            return
        if msg.type == 'program_change':
            return
        if msg.type == 'start' or msg.type == 'stop':
            self.output.send_midi(msg)
            return

        translate = None
        translated_msg = None
        control, level, mtype = self.message.get_details(msg)
        logger.add('CH:{:>2} Control:{:>3} [{:>3} {}]'.format(
            msg.channel + 1, control, level, mtype))
        logger.add('==>')
        nrpn = False

        try:
            my_input = self.input_lookup[msg.channel]
            translate, channel, nrpn = my_input.translate(control, level)

            if translate is not None:
                if translate in SPECIAL_COMMANDS:
                    if msg.type == 'note_off':
                        self._special_commands(translate)
                elif nrpn is True:
                    self.output.send_nrpn(channel, translate, level)
                else:
                    translated_msg = self.message.compose(
                        channel, translate, level, msg.type)
                logger.add('CH:{:>2} Control:{:>3}'.format(
                    channel + 1, translate))

        except KeyError:
            pass

        if nrpn is not True:
            self.output.send_midi(
                translated_msg if translated_msg is not None else msg)

        # send to self
        if msg.type == 'note_off' and translate == control:
            ret_msg = mido.Message(
                channel=msg.channel,
                note=msg.note,
                type='note_on',
            )
            self.output.send_midi(ret_msg)

        logger.log()
