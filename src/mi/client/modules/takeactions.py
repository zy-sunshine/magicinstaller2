#!/usr/bin/python
import os, gtk, time
from mi.client.utils import _
from mi.client.utils import magicstep, magicpopup, xmlgtk
from mi.utils.common import get_devinfo
from mi.games.xglines import xglines
from xml.dom.minidom import parse, parseString
from mi.utils.miconfig import MiConfig
CF = MiConfig.get_instance()

from mi.client.utils import logger
dolog = logger.info

class TaDialog(xmlgtk.xmlgtk):
    def __init__(self, upobj, uixml, uirootname=None):
        self.upobj = upobj
        xmlgtk.xmlgtk.__init__(self, uixml, uirootname)
        #self.topwin = gtk.Window(gtk.WINDOW_TOPLEVEL)
        #self.topwin.set_size_request(CF.D.FULL_WIDTH, CF.D.FULL_HEIGHT)
        #self.topwin.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        #self.topwin.add(self.widget)
        #self.topwin.show()
        #self.topwin.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.LEFT_PTR))
        
    def btntheme_clicked(self, widget, data):
        self.upobj.rootobj.btntheme_clicked(widget, data)

    def btnlogger_clicked(self, widget, data):
        self.upobj.rootobj.btnlogger_clicked(widget, data)

    def popup_xglines(self, widget, data):
        framexml = parseString('<?xml version="1.0"?><frame type="in"><frame name="slot" type="out"/></frame>')
        self.gamebox = magicpopup.magicpopup(None, framexml, _('XGlines'), 0)
        self.gameobj = xglines('games', self.help_gamebox, self.close_gamebox)
        self.gameobj.widget.show()
        self.gamebox.name_map['slot'].add(self.gameobj.widget)

    def help_gamebox(self, name):
        if name == 'xglines':
            magicpopup.magichelp_popup(_('helptext/games.xglines.en.txt'))

    def close_gamebox(self):
        self.gamebox.topwin.destroy()
        del self.gameobj
        
class MIStep_takeactions(magicstep.magicstepgroup):
    NAME = 'takeactions'
    LABEL = _('Take Actions')
    def __init__(self, rootobj):
        magicstep.magicstepgroup.__init__(self, rootobj, 'takeactions.xml',
                                  ['notes', 'ensure', 'doactions'], 'step')
        
        self.tadlg = TaDialog(self, self.uixmldoc, 'actions.dialog')
        self.statusarr = []
        width = 3
        height = (len(self.actlist) + width - 1) / width
        table = self.tadlg.name_map['stepsshow']
        for i in range(len(self.actlist)):
            image = gtk.Image()
            image.set_from_file('images/applet-blank.png')
            image.show()
            self.statusarr.append(image)
            table.attach(image, 0, 1, i, i + 1, 0, 0, 0, 0)
            label = gtk.Label(_(self.actlist[i][0]))
            label.set_alignment(0.0, 0.5)
            label.show()
            table.attach(label, 1, 2, i, i + 1,
                         gtk.EXPAND | gtk.FILL, gtk.EXPAND | gtk.FILL,
                         0, 0)
                         
        self.left_panel = self.tadlg.name_map['leftpanel']
        # remove leftpanel from its parent
        parent = self.left_panel.parent
        parent.remove(self.left_panel)
        self.right_panel = self.tadlg.name_map['rightpanel']
        # remove leftpanel from its parent
        parent = self.right_panel.parent
        parent.remove(self.right_panel)

    def start_install(self):
        if CF.D.PKGTYPE == 'rpm':     # In the mipublic.py
            # install rpm
        elif CF.D.PKGTYPE == 'tar':
            # install tar
            
    def check_enter_doactions(self):
        #### TODO: set the next back button sensitive
        # self.rootobj.btnback_sensitive(False)
        # self.rootobj.btnnext_sensitive(False)
        
        self.rootobj.cb_push_leftpanel(self.get_left_panel())
        self.rootobj.cb_push_rightpanel(self.get_right_panel())
        
        self.act_enter()
        return 1
        
    def check_leave_doactions(self):
        logger.d('check_leave_doactions')
        self.rootobj.cb_pop_leftpanel()
        self.rootobj.cb_pop_rightpanel()
        return 1
    
    def act_enter(self):
        self.statusarr[self.actpos].set_from_file('images/applet-busy.png')
        self.actlist[self.actpos][1]()

    def act_leave(self):
        if self.actlist[self.actpos][2]:
            self.actlist[self.actpos][2]()
        self.statusarr[self.actpos].set_from_file('images/applet-okay.png')
        self.actpos = self.actpos + 1
        if self.actpos < len(self.actlist):
            self.act_enter()
        else:
            self.add_action(None, self.act_finish, None, 'sleep', 0)

    def act_finish(self, tdata, data):
        self.rootobj.tm.pop_progress()
        self.tadlg.name_map['otname'].set_text('')
        self.tadlg.name_map['otprog'].set_fraction(1)
        self.tadlg.name_map['frame_other'].set_sensitive(False)
        # self.tadlg.topwin.destroy()

    def get_label(self):
        return self.LABEL
        
    def get_left_panel(self):
        return self.left_panel
        
    def get_right_panel(self):
        return self.right_panel
    
#def TestTaDialog():
#    import gtk
#    from mi.utils.common import search_file
#    uixml_file = 'takeactions.xml'
#    uixml_path = search_file( uixml_file,
#                              [CF.D.HOTFIXDIR, '.'],
#                              postfix = 'UIxml')
#    uixmldoc = parse(uixml_path)
#    tadlg = TaDialog(None, uixmldoc, 'actions.dialog')
#    tadlg.name_map['otname'].set_text('')
#    tadlg.name_map['otprog'].set_fraction(1)
#    tadlg.name_map['frame_other'].set_sensitive(False)
#    #import pdb; pdb.set_trace()
#    #tadlg.topwin.destroy()
#    gtk.main()
#        
#def TestMIStep_takeactions():
#    import gtk
#    from mi.test import TestMIStep
#    win = TestMIStep(gtk.WINDOW_TOPLEVEL)
#    h = MIStep_takeactions(win)
#    win.add_mistep(h)
#    win.show_all()
#    gtk.main()
#    
#if __name__ == '__main__':
#    TestMIStep_takeactions()
    
