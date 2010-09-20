# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------
#
#  logging.py
#
#  Created by Martin J. Laubach on 07.10.09.
#
# ------------------------------------------------------------------------

from feincms import settings
from feincms.utils import get_object

# ------------------------------------------------------------------------
class LogBase(object):
    """
    Base logging class. This just defines the infrastructure but does
    not log anything. To implement something more useful, subclass it
    and implement the do_log() method.
    """
    # Log categories
    ANY   = 0
    DB    = 1
    CACHE = 2
    AUTH  = 3

    # Log levels
    TRACE = 9
    DEBUG = 7
    INFO  = 5
    WARN  = 3
    ERR   = 1

    _name_dict = { }
    _k = 0
    for _k in locals():
        if _k[0] != '_':
            _name_dict[_k] = eval(_k)

    # Default log levels
    levels = { ANY: 10,  DB: 10,  CACHE: 10,  AUTH: 10  }

    def log(self, *args, **kwargs):
        level  = kwargs.get('level', self.ERR)
        subsys = kwargs.get('subsys', self.ANY)

        if level > self.levels[subsys]:
            return

        self.do_log(subsys, level, *args)

    def set_levels(self, **kwargs):
        """
        Set log levels.
        
        logger.set_levels(CACHE=logger.ERR, AUTH=logger.INFO)
        """

        for k in kwargs.keys():
            self.levels[self._name_dict[k]] = kwargs[k]

    def trace(self, *args, **kwargs):
        self.log(level=self.TRACE, *args, **kwargs)

    def debug(self, *args, **kwargs):
        self.log(level=self.DEBUG, *args, **kwargs)
    
    def info(self, *args, **kwargs):
        self.log(level=self.INFO, *args, **kwargs)
    
    def warn(self, *args, **kwargs):
        self.log(level=self.WARN, *args, **kwargs)
        
    def err(self, *args, **kwargs):
        self.log(level=self.ERR, *args, **kwargs)

    def do_log(self, subsys, level, *args):
        # Don't actually log anything. Override this in subclasses
        pass

# ------------------------------------------------------------------------
class LogFile(LogBase):
    """
    Example logging class, logs to a file.
    """
    from sys import stderr
    def __init__(self, file = stderr):
        self.log_file = file

    subsys = { LogBase.ANY: '*', LogBase.DB: '#', LogBase.CACHE: '@', LogBase.AUTH: '!' }

    def make_log_string(self, subsys, *args):
        s = u'%s %s' % (self.subsys[subsys], u', '.join(args))
        return s

    def do_log(self, subsys, level, *args):
        print >>self.log_file, self.make_log_string(subsys, *args).encode('utf-8')

# ------------------------------------------------------------------------
class LogStderr(LogFile):
    """
    Compat class
    """
    pass

# ------------------------------------------------------------------------
class LogDatedStderr(LogFile):
    """
    Another simple logging class, prefixes log output with current time.
    """
    def make_log_string(self, subsys, *args):
        from datetime import datetime

        now = datetime.now().isoformat()
        return u"%s %s" % ( now, super(LogDatedStderr, self).make_log_string(subsys, *args) )

# ------------------------------------------------------------------------
class LogStdout(LogDatedStderr):
    """
    Compat class.
    """
    def __init__(self):
        from sys import stdout
        super(LogStdout, self).__init__(file=stdout)

# ------------------------------------------------------------------------
# Finally instanciate the logger, yeah!

logger = get_object(settings.FEINCMS_LOGGING_CLASS)()

# ------------------------------------------------------------------------
