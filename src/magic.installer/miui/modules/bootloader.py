#!/usr/bin/python
from miui import _
from miui.utils import magicstep

class MIStep_bootloader (magicstep.magicstepgroup):
    def __init__(self, rootobj):
        magicstep.magicstepgroup.__init__(self, rootobj, 'bootloader.xml',
                                          ['choose', 'bootlist'],
                                          'steps')
        self.restore_dos = 'y'
        self.model = None
        self.iter = None

        self.name_map['winpartition_entry'].connect('focus-out-event',
                                                    self.check_winpartition_change, self)

    def get_label(self):
        return  _("Bootloader")

    def btnhelp_clicked(self, widget, data):
        # TO TRANSLATOR: Let helptext/bootloader.help.en.txt to be i18n string,
        # so the language which different with English can use another text
        # file.
        self.default_btnhelp_clicked(widget, data, _('helptext/bootloader.help.en.txt'))

    def check_leave_choose(self):
        global win_probe_status

        if win_probe_status != OP_STATUS_DONE:
            magicpopup.magicmsgbox(None, _('Please wait a while for the search of Windows partition.'),
                                   magicpopup.magicmsgbox.MB_INFO,
                                   magicpopup.magicpopup.MB_OK)
            return 0
        # save bltype
        self.fetch_values(self.rootobj.values,
                          valuename_list = ['bootloader.bltype'])
        # fill ui
        self.fill_values(self.values)
        return 1

    def get_choose_next(self):
        self.fetch_values(self.rootobj.values)
        choice = self.get_data(self.values, 'bootloader.bltype')
        if choice == 'none':
            return  None
        else:
            return 'bootlist'

    def check_enter_bootlist(self):
        global boot_device
        
        if 'b' in get_devinfo(boot_device).flags:
            f_boot_usable = True
        else:
            f_boot_usable = False
        self.name_map['bootpartition'].set_sensitive(f_boot_usable)
        self.name_map['bootpartition_entry'].set_sensitive(False)

        self.fill_values(self.values)
        self.restore_entrylist()
        return 1
        
    def check_leave_bootlist(self):
        global win_probe_result
        
        self.fetch_values(self.rootobj.values)
        instpos = self.get_data(self.values, 'bootloader.instpos')
        win_device = self.get_data(self.values, 'bootloader.win_device')
        if win_device:
            for dev, os_type in win_probe_result:
                if dev == win_device:
                    break
            else:
                magicpopup.magicmsgbox(None,
                                       _('%s is not a Windows partition.') % win_device,
                                       magicpopup.magicmsgbox.MB_ERROR,
                                       magicpopup.magicpopup.MB_OK)
                return 0
            if instpos == 'win' and os_type != 'winnt':
                magicpopup.magicmsgbox(None,
                                       _('Cannot install grldr: %s does not contain ntldr.') % win_device,
                                       magicpopup.magicmsgbox.MB_ERROR,
                                       magicpopup.magicpopup.MB_OK)
                return 0
        elif instpos == 'win':
            magicpopup.magicmsgbox(None,
                                   _('Windows partition is empty.'), 
                                   magicpopup.magicmsgbox.MB_ERROR,
                                   magicpopup.magicpopup.MB_OK)
            return 0            
            
        self.backup_entrylist()
        return  1

    def backup_entrylist(self):
        global  root_device

        self.fetch_values(self.rootobj.values)
        win_device = self.get_data(self.values, 'bootloader.win_device')

        listnode = self.srh_data_node(self.values, 'bootloader.entrylist')
        self.set_data(self.rootobj.values,
                      'bootloader.default', 'other')
        for r in listnode.getElementsByTagName('row'):
            devfn = r.getAttribute('c2')
            if devfn == root_device:
                self.set_data(self.rootobj.values,
                              'bootloader.linuxlabel',
                              r.getAttribute('c1'))
                if r.getAttribute('c3') == 'true':
                    self.set_data(self.rootobj.values,
                                  'bootloader.default',
                                  'linux')
            elif devfn == win_device:
                self.set_data(self.rootobj.values,
                              'bootloader.doslabel',
                              r.getAttribute('c1'))
                if r.getAttribute('c3') == 'true':
                    self.set_data(self.rootobj.values,
                                  'bootloader.default',
                                  'dos')

    def restore_entrylist(self):
        global  all_part_infor

        child_values = []
        has_dos = None

        self.fetch_values(self.rootobj.values)
        win_device = self.get_data(self.values, 'bootloader.win_device')

        default = self.get_data(self.values, 'bootloader.default')
        if self.restore_dos and win_device:
            try:
                devinfo = get_devinfo(win_device)
                if devinfo.fstype in ('ntfs-3g', 'ntfs', 'vfat') \
                       and devinfo.not_touched == 'true':
                    has_dos = 'true'
            except KeyError:
                pass

        if has_dos:
            node = self.rootobj.values.createElement('row')
            doslabel = self.get_data(self.values, 'bootloader.doslabel')
            node.setAttribute('c1', doslabel)
            node.setAttribute('c2', win_device)
            if default == 'dos':
                node.setAttribute('c0', 'images/yes.png')
                node.setAttribute('c3', 'true')
            else:
                node.setAttribute('c0', 'images/blank.png')
                node.setAttribute('c3', 'false')
            child_values.append(node)

        node = self.rootobj.values.createElement('row')
        linuxlabel = self.get_data(self.values, 'bootloader.linuxlabel')
        linuxdevice = root_device
        node.setAttribute('c1', linuxlabel)
        node.setAttribute('c2', linuxdevice)
        if not has_dos or default == 'linux':
            node.setAttribute('c0', 'images/yes.png')
            node.setAttribute('c3', 'true')
        else:
            node.setAttribute('c0', 'images/blank.png')
            node.setAttribute('c3', 'false')
        child_values.append(node)
        self.set_child_data(self.values,
                            'bootloader.entrylist', 'row', child_values)
        self.fill_values(self.values)

    def restore_entry(self, widget, data):
        self.restore_dos = 'y'
        self.restore_entrylist()

    def edit_entry(self, widget, data):
        (self.model, self.iter) = self.name_map['bootlist_treeview'].get_selection().get_selected()
        if not self.iter:
            magicpopup.magicmsgbox(None,
                                   _('Please choose an entry to edit.'),
                                   magicpopup.magicmsgbox.MB_ERROR,
                                   magicpopup.magicpopup.MB_OK)
            return
        label = self.model.get_value(self.iter, 1)
        device = self.model.get_value(self.iter, 2)
        default = self.model.get_value(self.iter, 3)
        self.edit_values = parseString(
            """<?xml version="1.0"?><data>
            <default>%s</default><o_default>%s</o_default>
            <label>%s</label><o_label>%s</o_label>
            <device>%s</device></data>""" % (default, default, label, label, device))
        self.edit_dialog = magicpopup.magicpopup(self, self.uixmldoc,
                                                 _('Edit a boot entry.'),
                                                 magicpopup.magicpopup.MB_OK |
                                                 magicpopup.magicpopup.MB_CANCEL,
                                                 'bootentry.dialog', 'edit_')
        self.edit_dialog.fill_values(self.edit_values.documentElement)
        self.edit_dialog.name_map['root_device'].set_text(device)

    def edit_ok_clicked(self, widget, data):
        self.edit_dialog.fetch_values(self.edit_values)
        dE = self.edit_values.documentElement
        device = self.get_data(dE, 'device')
        default = self.get_data(dE, 'default')
        o_default = self.get_data(dE, 'o_default')
        label = self.get_data(dE, 'label')
        o_label = self.get_data(dE, 'o_label')
        if label != o_label:
            self.model.set_value(self.iter, 1, label)
        if default != o_default:
            if default == 'true':
                iter = self.model.get_iter_first()
                while iter:
                    self.model.set_value(iter, 0,
                                         self.get_pixbuf_map('images/blank.png'))
                    self.model.set_value(iter, 3, 'false')
                    iter = self.model.iter_next(iter)
                self.model.set_value(self.iter, 0,
                                     self.get_pixbuf_map('images/yes.png'))
                self.model.set_value(self.iter, 3, 'true')
            elif self.model.iter_n_children(None) > 1:
                iter = self.model.get_iter_first()
                first_default = self.model.get_value(iter, 3)
                if first_default == 'true':
                    iter = self.model.iter_next(iter)
                self.model.set_value(self.iter, 0,
                                     self.get_pixbuf_map('images/blank.png'))
                self.model.set_value(self.iter, 3, 'false')
                self.model.set_value(iter, 0,
                                     self.get_pixbuf_map('images/yes.png'))
                self.model.set_value(iter, 3, 'true')
        self.edit_dialog.topwin.destroy()

    def remove_entry(self, widget, data):
        global  root_device

        (model, iter) = self.name_map['bootlist_treeview'].get_selection().get_selected()
        if not iter:
            magicpopup.magicmsgbox(None,
                                   _('Please choose an entry to remove.'),
                                   magicpopup.magicmsgbox.MB_ERROR,
                                   magicpopup.magicpopup.MB_OK)
            return
        device = model.get_value(iter, 2)
        if device == root_device:
            magicpopup.magicmsgbox(None,
                                   _('Please do not remove the entry to boot the installed system.'),
                                   magicpopup.magicmsgbox.MB_ERROR,
                                   magicpopup.magicpopup.MB_OK)
            return
        else:
            self.restore_dos = None
        default = model.get_value(iter, 3)
        self.list_remove('bootloader.entrylist', iter)
        iter = model.get_iter_first()
        while iter:
            device = model.get_value(iter, 2)
            if device == root_device:
                model.set_value(iter, 0, self.get_pixbuf_map('images/yes.png'))
                model.set_value(iter, 3, 'true')
                break
            iter = model.iter_next(iter)

    def check_winpartition_change(self, widget, event, data):
        win_device = self.get_data(self.values, 'bootloader.win_device')
        new_win_device = self.name_map['winpartition_entry'].get_text()
        if win_device != new_win_device:
            self.restore_entrylist()
