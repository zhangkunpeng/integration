
class BException(Exception):
    def __init__(self, msg, *args, **kwargs):
        self.msg = msg % args

    def __str__(self):
        return self.msg


class CriticalException(BException):
    pass


class FileNotExistException(Exception):
    def __init__(self, filepath):
        self.filepath = filepath

    def __str__(self):
        return "File %s not exist" % self.filepath


class DirNotExistException(Exception):
    def __init__(self, dirpath):
        self.dirpath = dirpath

    def __str__(self):
        return "Dir %s not exist" % self.dirpath