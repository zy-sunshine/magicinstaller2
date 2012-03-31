#!/usr/bin/python
from miui.utils import _
from miui.utils import magicstep
from miutils.miconfig import MiConfig
CONF = MiConfig.get_instance()

class MIStep_scsi (magicstep.magicstep):
    def __init__(self, rootobj):
        self.first_fill = None
        magicstep.magicstep.__init__(self, rootobj, 'scsi.xml', 'scsi')

    def get_label(self):
        return  _("SCSI Driver")

    def enter(self):
        CONF.RUN.reprobe_all_disks_required
        if not self.first_fill:
            self.do_first_fill()
        CONF.reprobe_all_disks_required = 0
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
        CONF.reprobe_all_disks_required
        success = tdata
        self.waitdlg.topwin.destroy()
        if not success:
            magicpopup.magicmsgbox(None, _('Load module failed.'),
                                   magicpopup.magicmsgbox.MB_ERROR,
                                   magicpopup.magicpopup.MB_OK)
        else:
            CONF.reprobe_all_disks_required = 1
            stepobj = self.rootobj.stepobj_list[self.rootobj.curstep + 1] # reprobe disk
            stepobj.reprobe_all()

            magicpopup.magicmsgbox(None, _('Load module success.'),
                                   magicpopup.magicmsgbox.MB_INFO,
                                   magicpopup.magicpopup.MB_OK)
            self.do_refresh_fill()

    def do_first_fill(self):
        def modcmp(mod0, mod1):
            return  cmp(mod0[2], mod1[2])

        #def load_pciids():
        #    """Load /usr/share/hwdata/pci.ids into a dict."""
        #    # res - {'vendor_id': ('vendor', {'device_id': ('device', [('subvendor_id', 'subdevice_id', 'sub desc')...])})}
        #    res = {}
        #    vendor_id = device_id = subvendor_id = subdevice_id = ''
        #    pciids_f = file('/usr/share/hwdata/pci.ids')
        #    l = pciids_f.readline()
        #    while l:
        #        # vendor  vendor_name
        #        #	device  device_name				<-- single tab
        #        #		subvendor subdevice  subsystem_name	<-- two tabs
        #        if l[0] != '#' and l.strip() != '' and l[0] != 'C':  # Skip comment line and blank line, device classes.
        #            parts = l.split()
        #            if l[0] != '\t':
        #                vendor_id = '0x' + parts[0]
        #                res[vendor_id] = (' '.join(parts[1:]), {})
        #            elif l[0] == '\t' and l[1] != '\t':
        #                device_id = '0x' + parts[0]
        #                res[vendor_id][1][device_id] = (' '.join(parts[1:]), [])
        #            elif l[0] == '\t' and l[1] == '\t':
        #                subvendor_id = '0x' + parts[0]
        #                subdevice_id = '0x' + parts[1]
        #                res[vendor_id][1][device_id][1].append((subvendor_id, subdevice_id, ' '.join(parts[2:])))
        #        l = pciids_f.readline()
        #    pciids_f.close()
        #    return res
        # 
        #def lookup_desc(ids_map, v):
        #    """Look up v in ids_map."""
        #    desc = ''
        #    tup = ids_map.get(v[0], None)       # vendor
        #    if tup:
        #        desc = tup[0]
        #        tup = tup[1].get(v[1], None)    # device
        #        if tup:
        #            desc = ' '.join([desc, tup[0]])
        #            if len(v)==5:
        #                for subvendor_id, subdevice_id, subdesc in tup[1]:
        #                    if subvendor_id==v[2] and subdevice_id==v[3]:
        #                        desc = ' '.join([desc, subdesc])
        #    return desc

        scsi_module_list = self.rootobj.tm.actserver.get_all_scsi_modules()
        loaded_module_list = self.rootobj.tm.actserver.get_all_loaded_modules()

        self.modulelist = []

        ## do not use pcitable now
        #pciids_map = load_pciids()
        #pcitable = file('/usr/share/hwdata/pcitable')
        #l = pcitable.readline()
        #while l:
        #    v = l.split('\t')
        #    if (len(v) == 3 or len(v) == 5) and \
        #           v[-1][0] == '"' and v[-1][-2] == '"' and v[-1][-1] == '\n':
        #       module = v[-1][1:-2]
        #       if module in scsi_module_list:
        #           loaded = module in loaded_module_list
        #           desc = lookup_desc(pciids_map, v)
        #           self.modulelist.append([None, loaded, module, desc])
        #    l = pcitable.readline()
        #pcitable.close()
        #del pciids_map
        ## new pcitable dose not include desc
        ## so use modulelist instead
        ##for mod in scsi_module_list:
        ##    loaded = mod in loaded_module_list
        ##    self.modulelist.append([None, loaded, mod, mod])

        def find_kmod(arg, dirname, fnames):
            for fn in fnames:
                if fn.endswith('.ko') or fn.endswith('.o'):
                    mod = fn[:fn.rfind('.')]
                    loaded = mod in loaded_module_list
                    self.modulelist.append([None, loaded, mod, mod])
        os.path.walk('/lib/modules/%s/kernel/drivers/scsi' % CONF.LOAD.CONF_KERNELVER,
                     find_kmod, None)
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
