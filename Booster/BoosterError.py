class BoosterError(Exception):
    """ Base class of booster exceptions
    """

    def __init__(self, name=None, detail=None, traceback=None):
        self.name = name
        self.detail = detail
        self.traceback = traceback

    def __str__(self):
        return self.error_message()

    def error_message(self):
        message = []
        if self.name:
            message.append("({})".format(self.name))
        if self.detail:
            message.append('detail: {}'.format(self.detail))
        if self.traceback:
            message.append('exception: {}'.format(self.traceback))
        return ' '.join(message)


class BoosterTagError(BoosterError):
    def __init__(self, name, detail=None, traceback=None):
        super(BoosterTagError, self).__init__(name, detail, traceback)

    def __str__(self):
        return "Booster tag error: {message}".format(message=self.error_message())


class FileNotFoundError(BoosterError):
    def __init__(self, name=None, detail=None, traceback=None):
        super(FileNotFoundError, self).__init__(name, detail, traceback)

    def __str__(self):
        return "File not found: {message}".format(message=self.error_message())


class AdditionalFileError(BoosterError):
    def __init__(self, name=None, detail=None, traceback=None):
        super(FileNotFoundError, self).__init__(name, detail, traceback)

    def __str__(self):
        return "Additional File/Folder found: {message}".format(message=self.error_message())


class SkipperError(BoosterError):
    def __init__(self, name, detail=None, traceback=None):
        super(SkipperError, self).__init__(name, detail, traceback)

    def __str__(self):
        return "Skipper Error: {message}".format(message=self.error_message())


class SSHError(BoosterError):
    def __init__(self, name, detail=None, traceback=None):
        super(SSHError, self).__init__(name, detail, traceback)

    def __str__(self):
        return "SSH Error: {message}".format(message=self.error_message())
