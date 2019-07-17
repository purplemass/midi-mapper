"""Constants used in the application."""

STANDARD_MESSAGES = {
    'note_off': lambda x: (x.note, x.velocity),
    'note_on': lambda x: (x.note, x.velocity),
    'polytouch': lambda x: (x.note, x.value),
    'control_change': lambda x: (x.control, x.value),
    'program_change': lambda x: (x.program, None),
    'aftertouch': lambda x: (None, x.value,),
    'pitchwheel': lambda x: (None, x.pitch,),
}

REAL_TIME_MESSAGES = [
    'clock', 'start', 'continue', 'active_sensing', 'stop', 'reset']

SYSTEM_COMMON_MESSAGES = [
    'sysex', 'quarter_frame', 'songpos', 'song_select', 'tune_request']
