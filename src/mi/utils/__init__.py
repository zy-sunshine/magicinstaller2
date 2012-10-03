from milogger import MiLogger
#logger = MiLogger('mi')
import logging, logging.config
import os, sys
CUR_DIR = os.path.dirname(os.path.dirname(__file__))
logconf = os.path.join(CUR_DIR, 'logging.conf')
print logconf
logging.config.fileConfig(logconf)

logger = logging.getLogger('mi')
logger.i = logger.info
logger.e = logger.error
logger.w = logger.warn
logger.d = logger.debug

from mi.utils.miconfig import MiConfig
CF = MiConfig.get_instance()


from gettext import gettext as _