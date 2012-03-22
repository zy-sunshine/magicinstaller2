#!/usr/bin/python
import os.path
#from locale import getdefaultlocale
#from gettext import GNUTranslations
#
#deflocale = getdefaultlocale()
#mopath = os.path.join(os.path.dirname(__file__), 'locale', deflocale[0] + '.mo')
#gnutrans = GNUTranslations(open(mopath, 'rb'))
#
#def _(text):
#    return gnutrans.gettext(text).decode(gnutrans.charset())
from gettext import gettext as _
