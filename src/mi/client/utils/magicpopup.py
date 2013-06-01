#!/usr/bin/python
import gtk
from gettext import gettext as _
from xml.dom.minidom import parse

import xmlgtk

class magicpopup (xmlgtk.xmlgtk):
    MB_APPLY    = 1
    MB_CANCEL   = 2
    MB_NO       = 4
    MB_OK       = 8
    MB_YES      = 16
    MB_IGNORE   = 32
    MB_REBOOT   = 64
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
                                (self.MB_IGNORE, 'ignore'),
                                (self.MB_REBOOT, 'reboot')]:
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
        #self.topwin.set_position(gtk.WIN_POS_CENTER)
        self.topwin.add(self.dialogframe.widget)
        self.topwin.show()

    def closedialog(self, widget=None):
        self.topwin.destroy()

class magicmsgbox(magicpopup):
    MB_ERROR    = 0
    MB_INFO     = 1
    MB_QUESTION = 2
    MB_WARNING  = 3
    def __init__(self, upobj, message, msgtype=MB_INFO, buttons=magicpopup.MB_YES, prefix=''):
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
    def __init__(self, helpfile=None):
        from mi.utils.miconfig import MiConfig
        CF = MiConfig.get_instance()
        
        uixml = parse('UIxml/mi_dialog.xml')
        textnodes = uixml.getElementsByTagName('text')
        if helpfile:
            for tn in textnodes:
                tn.setAttribute('filename', helpfile)
        magicpopup.__init__(self, self, uixml, _('Help'), magicpopup.MB_OK, 'helpdialog')
        self.topwin.set_size_request(CF.D.HELP_WIDTH, CF.D.HELP_HEIGHT)
        self.topwin.set_resizable(False)

    def ok_clicked(self, widget, data):
        self.topwin.destroy()

