#!/usr/bin/python
# Copyright (C) 2003, Charles Wang.
# Author:  Charles Wang <charles@linux.net.cn>
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANT; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public LIcense for more
# details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.

import gtk
from gettext import gettext as _
from xml.dom.minidom import parse

from mipublic import *
import xmlgtk

class magicpopup (xmlgtk.xmlgtk):
    MB_APPLY    = 1
    MB_CANCEL   = 2
    MB_NO       = 4
    MB_OK       = 8
    MB_YES      = 16
    MB_IGNORE   = 32
    def __init__(self, upobj, uixml, title, buttons, uirootname=None, prefix=''):
        if not upobj:
            upobj = self
        framedoc = parse('UIxml/mi_dialog.xml')
        self.dialogframe = xmlgtk.xmlgtk(framedoc, 'dialogframe')
        self.dialogframe.name_map['dialog_title'].set_text(title)

        xmlgtk.xmlgtk.__init__(self, uixml, uirootname)
        self.dialogframe.name_map['dialog_area'].pack_start(self.widget, True, True)

        if buttons == 0:
            self.dialogframe.name_map['buttonframe'].hide()
        else:
            for (bit, name) in [(self.MB_APPLY,  'apply'),
                                (self.MB_CANCEL, 'cancel'),
                                (self.MB_NO,     'no'),
                                (self.MB_OK,     'ok'),
                                (self.MB_YES,    'yes'),
                                (self.MB_IGNORE, 'ignore')]:
                if buttons & bit:
                    self.dialogframe.name_map[name].show()
                    self.dialogframe.name_map[name + '_space'].show()
                    if hasattr(upobj, prefix + name + '_clicked'):
                        self.dialogframe.name_map[name].connect('clicked', getattr(upobj, prefix + name + '_clicked'), self)
                    else:
                        self.dialogframe.name_map[name].connect('clicked', self.closedialog)

        self.topwin = gtk.Window(gtk.WINDOW_POPUP)
        self.topwin.set_modal(True)
        self.topwin.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.topwin.add(self.dialogframe.widget)
        self.topwin.show()

    def closedialog(self, widget):
        self.topwin.destroy()

class magicmsgbox (magicpopup):
    MB_ERROR    = 0
    MB_INFO     = 1
    MB_QUESTION = 2
    MB_WARNING  = 3
    def __init__(self, upobj, message, msgtype, buttons, prefix=''):
        uixml = parse('UIxml/mi_dialog.xml')
        labelnode = self.search_hook(uixml, 'label', 'LABEL')
        labelnode.setAttribute('text', message)
        iconnode = self.search_hook(uixml, 'image', 'ICON')
        if msgtype == self.MB_ERROR:
            iconnode.setAttribute('file', 'images/stock_dialog_error_48.png')
            magicpopup.__init__(self, upobj, uixml, _('Error'),
                                buttons, 'messagedialog', prefix)
        elif msgtype == self.MB_INFO:
            iconnode.setAttribute('file', 'images/stock_dialog_info_48.png')
            magicpopup.__init__(self, upobj, uixml, _('Info'),
                                buttons, 'messagedialog', prefix)
        elif msgtype == self.MB_QUESTION:
            iconnode.setAttribute('file', 'images/stock_dialog_question_48.png')
            magicpopup.__init__(self, upobj, uixml, _('Question'),
                                buttons, 'messagedialog', prefix)
        elif msgtype == self.MB_WARNING:
            iconnode.setAttribute('file', 'images/stock_dialog_warning_48.png')
            magicpopup.__init__(self, upobj, uixml, _('Warning'),
                                buttons, 'messagedialog', prefix)
        else:
            magicpopup.__init__(self, upobj, uixml, '',
                                buttons, 'messagedialog', prefix)

class magichelp_popup(magicpopup):
    def __init__(self, helpfile):
        uixml = parse('UIxml/mi_dialog.xml')
        textnodes = uixml.getElementsByTagName('text')
        for tn in textnodes:
            tn.setAttribute('filename', helpfile)
        magicpopup.__init__(self, self, uixml, _('Help'), magicpopup.MB_OK, 'helpdialog')
        self.topwin.set_size_request(HELP_WIDTH, HELP_HEIGHT)
        self.topwin.set_resizable(False)

    def ok_clicked(self, widget, data):
        self.topwin.destroy()
