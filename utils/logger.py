""""""


class Logger(object):
    """Logger class"""

    def __init__(self):
        self.parts = []

    def add(self, msg=None, line=False, dline=False):
        if line is True:
            self.parts.append(100 * '-')
        if dline is True:
            self.parts.append(100 * '=')
        if msg is not None:
            self.parts.append(msg)

    def log(self, msg=None, line=False, dline=False):
        self.add(msg, line, dline)
        print(' '.join(part for part in self.parts))
        self.parts = []
