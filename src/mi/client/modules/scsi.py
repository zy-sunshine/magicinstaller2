#!/usr/bin/python
from mi.client.utils import _, magicpopup
from mi.client.utils import magicstep
from mi.utils.miconfig import MiConfig
import os
CF = MiConfig.get_instance()

class MIStep_scsi (magicstep.magicstep):
    NAME = 'scsi'
    LABEL = _("SCSI Driver")
    def __init__(self, rootobj):
        self.first_fill = None
        magicstep.magicstep.__init__(self, rootobj, 'scsi.xml', 'scsi')

    def get_label(self):
        return self.LABEL

    def enter(self):
        CF.G.reprobe_all_disks_required
        if not self.first_fill:
            self.do_first_fill()
        CF.G.reprobe_all_disks_required = 0
        return  1

    def leave(self):
        loaded_scsi_modules = []
        for mod in self.modulelist:
            if mod[1] and mod[2] not in loaded_scsi_modules:
                loaded_scsi_modules.append(mod[2])
        self.set_data(self.rootobj.values, "scsi.modules", '/'.join(loaded_scsi_modules))
        return  1

    def btnback_clicked(self, widget, data):
        return  1

    def btnnext_clicked(self, widget, data):
        return  1

    def do_modprobe(self, widget, data):
        (model, iter) = self.name_map['scsilist_treeview'].get_selection().get_selected()
        if not iter:
            magicpopup.magicmsgbox(None, _('Not any driver is selected.'),
                                   magicpopup.magicmsgbox.MB_INFO,
                                   magicpopup.magicpopup.MB_OK)
            return
        loaded = model.get_value(iter, 0)
        if loaded == self.get_pixbuf_map('images/yes.png'):
            magicpopup.magicmsgbox(None, _('The selected module has been loaded already.'),
                                   magicpopup.magicmsgbox.MB_INFO,
                                   magicpopup.magicpopup.MB_OK)
            return
        module = model.get_value(iter, 1)
        self.rootobj.tm.add_action(None, self.get_modprobe_result, module,
                           'do_modprobe', module)
        self.waitdlg = magicpopup.magicmsgbox(None, _('Please wait......'),
                                              magicpopup.magicmsgbox.MB_INFO, 0)

    def get_modprobe_result(self, tdata, data):
        CF.G.reprobe_all_disks_required
        success = tdata
        self.waitdlg.topwin.destroy()
        if not success:
            magicpopup.magicmsgbox(None, _('Load module failed.'),
                                   magicpopup.magicmsgbox.MB_ERROR,
                                   magicpopup.magicpopup.MB_OK)
        else:
            CF.G.reprobe_all_disks_required = 1
            stepobj = self.rootobj.stepobj_list[self.rootobj.curstep + 1] # reprobe disk
            stepobj.reprobe_all()

            magicpopup.magicmsgbox(None, _('Load module success.'),
                                   magicpopup.magicmsgbox.MB_INFO,
                                   magicpopup.magicpopup.MB_OK)
            self.do_refresh_fill()

    def do_first_fill(self):
        def modcmp(mod0, mod1):
            return  cmp(mod0[2], mod1[2])

        all_scsi_modules = self.rootobj.tm.actserver.get_all_scsi_modules()
        loaded_module_list = self.rootobj.tm.actserver.get_all_loaded_modules()
        
        self.modulelist = []
        for mod in all_scsi_modules:
            loaded = mod in loaded_module_list
            self.modulelist.append([None, loaded, mod, mod])
            
        self.modulelist.sort(modcmp)

        tv = self.name_map['scsilist_treeview']
        model = tv.get_model()
        model.clear()
        for mod in self.modulelist:
            iter = model.append()
            if mod[1]:
                pixbuf = self.get_pixbuf_map('images/yes.png')
            else:
                pixbuf = self.get_pixbuf_map('images/blank.png')
            model.set(iter, 0, pixbuf, 1, mod[2], 2, mod[3])
            mod[0] = iter

        self.first_fill = 1

    def do_refresh_fill(self):
        tv = self.name_map['scsilist_treeview']
        model = tv.get_model()

        loaded_module_list = self.rootobj.tm.actserver.get_all_loaded_modules()
        for mod in self.modulelist:
            loaded = mod[2] in loaded_module_list
            if loaded != mod[1]:
                mod[1] = loaded
                if loaded:
                    pixbuf = self.get_pixbuf_map('images/yes.png')
                else:
                    pixbuf = self.get_pixbuf_map('images/blank.png')
                model.set(mod[0], 0, pixbuf)
