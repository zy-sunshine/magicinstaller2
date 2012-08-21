from gettext import gettext as _
import logging, logging.config
logging.config.fileConfig("logging.conf")

#create logger
logger = logging.getLogger("mi_ui")
