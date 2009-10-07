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
    not log anything. To implement something more usefule, subclass it
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
class LogStdout(LogBase):
    """
    Example logging class, logs to stdout.
    """
    subsys = { LogBase.ANY: '*', LogBase.DB: '#', LogBase.CACHE: '@', LogBase.AUTH: '!' }

    def do_log(self, subsys, level, *args):
        from datetime import datetime

        now = datetime.now().isoformat()
        print 'LOG:', now, self.subsys[subsys], ', '.join(args)

# ------------------------------------------------------------------------
# Instanciate the logger, yeah!

logger = get_object(settings.FEINCMS_LOGGING_CLASS)()

# ------------------------------------------------------------------------
