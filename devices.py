""""""
import mido

from logger import Logger

logger = Logger()


class Device(object):
    """Device class"""

    def __init__(self, name, info):
        logger.log(line=True)
        self.name = name
        self.midi_name = info['midi_name']
        self.port = None
        logger.log('Create {} device "{}"'.format(info['type'], self.name))
        self._connect()

    def _connect(self):
        try:
            self.port = self._get_port()
            logger.log(
                '"{}" connected as "{}"'.format(self.name, self.midi_name))
        except OSError:
            logger.log('Error: Could not connect to "{}"'.format(self.name))


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
