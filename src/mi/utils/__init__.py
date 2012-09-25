from milogger import MiLogger
#logger = MiLogger('mi')
import logging, logging.config
logging.config.fileConfig('logging.conf')
logger = logging.getLogger('mi')
logger.i = logger.info
logger.e = logger.error
logger.w = logger.warn
logger.d = logger.debug

from gettext import gettext as _