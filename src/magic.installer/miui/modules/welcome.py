#!/usr/bin/python
from gettext import gettext as _
from miui.utils import magicstep, magicpopup

class MIStep_welcome (magicstep.magicstep):
    def __init__(self, rootobj):
        self.substeps = [('welcome', False, ''),
                         ('license', True, 'license'),
                         ('nowarranty', True, 'nowarranty')]
        self.substep = self.substeps[0][0]
        self.msgbox = None
        magicstep.magicstep.__init__(self, rootobj, 'welcome.xml')
        self.cancel_widget = None
        self.cancel_data = None

    def get_label(self):
        return  _("Welcome")

    def subswitch(self, substep):
        self.substep = substep
        for ss in self.substeps:
            if ss[0] != substep:
                self.name_map[ss[0]].hide()
        for ss in self.substeps:
            if ss[0] == substep:
                self.name_map[substep].show()
                self.rootobj.btnback_sensitive(ss[1])
                if ss[2] == '':
                    self.rootobj.btnnext_sensitive(True)
                else:
                    agree_or_not = self.get_data(self.values, 'welcome.' + ss[2])
                    if agree_or_not == 'agree':
                        self.name_map[ss[2] + '_query'].hide()
                        self.name_map[ss[2] + '_agreed'].show()
                        self.rootobj.btnnext_sensitive(True)
                    else:
                        self.rootobj.btnnext_sensitive(False)

    def enter(self):
        self.subswitch(self.substeps[0][0])
        return  1

    def leave(self):
        self.rootobj.btnback_sensitive(True)
        self.rootobj.btnnext_sensitive(True)
        return  1

    def yes_clicked(self, widget, data):
        self.default_btncancel_clicked(self.cancel_widget, self.cancel_data)
        self.msgbox.topwin.destroy()
        del self.msgbox
        self.msgbox = None

    def no_clicked(self, widget, data):
        self.msgbox.topwin.destroy()
        del self.msgbox
        self.msgbox = None

    def btncancel_clicked(self, widget, data):
        self.msgbox = magicpopup.magicmsgbox(self,
                                             _('Do you realy want to cancel the installation?'),
                                             magicpopup.magicmsgbox.MB_QUESTION,
                                             magicpopup.magicmsgbox.MB_YES |
                                             magicpopup.magicmsgbox.MB_NO)
        self.cancel_widget = widget
        self.cancel_data = data

    def btnback_clicked(self, widget, data):
        prevstep = ''
        for step in self.substeps:
            if step[0] == self.substep:
                break
            prevstep = step[0]
        if prevstep != '':
            self.subswitch(prevstep)
        return  0

    def btnnext_clicked(self, widget, data):
        self.fetch_values(self.rootobj.values)
        if self.substep == self.substeps[-1][0]:
            self.rootobj.btnback_sensitive(True)
            return  1
        step = ''
        for nextstep in self.substeps:
            if step == self.substep:
                break
            step = nextstep[0]
        self.subswitch(nextstep[0])
        return  0

    def agree(self, widget, data):
        self.rootobj.btnnext_sensitive(True)

    def disagree(self, widget, data):
        self.rootobj.btnnext_sensitive(False)
