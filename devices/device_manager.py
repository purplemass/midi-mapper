""""""
import time

import mido
from mido.ports import MultiPort

from .devices import InputDevice, OutputDevice
from utils.logger import Logger

SPECIAL_COMMANDS = ['RELOAD']

logger = Logger()


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

        logger.log(dline=True)

        if cmd == 'RELOAD':
            self.midi_config.process()
            self._reset()

    def _process_message(self, msg):
        translate = None
        translated_msg = None
        control, level = self._get_msg_details(msg)
        logger.add('CH:{:>2} Control:{:>3} [{:>3} {}]'.format(
            msg.channel + 1,
            control,
            level,
            'CC' if msg.type == 'control_change' else 'NT',
        ))
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
                    self._send_nrpn(channel, translate, level)
                else:
                    translated_msg = self._compose_message(
                        channel, translate, level, msg.type)
                logger.add('CH:{:>2} Control:{:>3}'.format(
                    channel + 1, translate))

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

        logger.log()

    def run(self):
        logger.log(line=True)
        while True:
            time.sleep(0.1)
            for msg in self.input_multi.iter_pending():
                self._process_message(msg)
