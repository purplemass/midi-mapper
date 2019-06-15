"""
Helpers for devices.
"""

import mido


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


class MidiOutput(object):
    """"""

    def set_outputs(self, output_ports, clock_ports):
        """Set output ports."""
        self.output_ports = output_ports
        self.clock_ports = clock_ports

    def send_midi(self, msg):
        """Send MIDI message to all outputs."""
        for port in self.output_ports:
            if port is not None:
                port.send(msg)

    def send_clock(self, msg):
        """Send CLOCK to all outputs."""
        for port in self.clock_ports:
            if port is not None:
                port.send(msg)

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
        msg = mido.Message(
            channel=channel, control=99, value=int(control[0]), type=cc)
        self.send_midi(msg)
        msg = mido.Message(
            channel=channel, control=98, value=int(control[1]), type=cc)
        self.send_midi(msg)
        msg = mido.Message(
            channel=channel, control=6, value=level, type=cc)
        self.send_midi(msg)
        msg = mido.Message(
            channel=channel, control=38, value=0, type=cc)
        self.send_midi(msg)
