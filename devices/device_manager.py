"""
Device manager.
"""
import threading
import time

import mido

from utils.logger import Logger

from .helpers import MidiMessage, MidiInput, MidiOutput, MidiClock

SPECIAL_COMMANDS = ['RELOAD']
IGNORE_MESSAGE_TYPES = ['clock', 'program_change', 'start', 'stop']

logger = Logger()


class DeviceManager(object):
    """DeviceManager class"""

    def __init__(self):
        self.keep_running = True

    def start(self, config):
        self.config = config
        self.message = MidiMessage()
        self.input = MidiInput(config)
        self.output = MidiOutput()
        self.clock = MidiClock(config)
        self._reset()
        self._run()

    def stop(self):
        self.clock.stop()
        self.keep_running = False

    def _reset(self):
        ports = self.input.create_ports()
        self.input_lookup = ports['input_lookup']
        self.input_multi = ports['input_multi']
        self.output.set_outputs(ports['output_ports'])
        self.clock.set_outputs(ports['clock_out_ports'])
        self.clock.start()

    def _get_midi(self):
        while self.keep_running:
            for msg in self.input_multi.iter_pending():
                self._process_message(msg)
            time.sleep(0.1)

    def _run(self):
        logger.log(line=True)
        threading.Thread(target=self._get_midi, daemon=True).start()
        while self.keep_running:
            time.sleep(1)

    def _special_commands(self, cmd):

        logger.log()
        logger.log(dline=True)

        if cmd == 'RELOAD':
            self.config.process()
            self._reset()

    def _process_message(self, msg):
        if msg.type in IGNORE_MESSAGE_TYPES:
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
