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

class mistep_pkgselect (magicstep.magicstepgroup):
    def __init__(self, rootobj):
        magicstep.magicstepgroup.__init__(self, rootobj, 'pkgselect.xml',
                                          ['toplevel', 'pkgchoose'], 'steps')
        self.pa_choose = None

    def get_label(self):
        return  _("Package Select")

    def popup_srcpos_dialog(self):
        global pkgarr_probe_result
        valdoc = Document()
        self.srcpos_value_doc = valdoc
        topele = valdoc.createElement('data')
        valdoc.appendChild(topele)
        valtopele = valdoc.createElement('srcposlist')
        topele.appendChild(valtopele)
        for (pafile, dev, mntpoint, fstype, dir, isofn) in pkgarr_probe_result:
            rowele = valdoc.createElement('row')
            rowele.setAttribute('c0', pafile)
            rowele.setAttribute('c1', dev)
            rowele.setAttribute('c2', fstype)
            rowele.setAttribute('c3', '/' + dir)
            rowele.setAttribute('c4', isofn)
            valtopele.appendChild(rowele)
        self.srcpos_dialog = magicpopup.magicpopup( \
            self, self.uixmldoc, _('You want fetch packages from...'),
            magicpopup.magicpopup.MB_OK, 'srcpos.dialog', 'srcpos_')
        self.srcpos_dialog.topwin.set_size_request(480, 320)
        self.srcpos_dialog.fill_values(topele)

    def tryload_file(self, patuple):
        global path_tftproot
        global choosed_patuple
        global arch_map, arrangement, archsize_map, pkgpos_map, toplevelgrp_map

        (pafile, dev, mntpoint, fstype, dir, isofn) = patuple

        g_map = {}
        l_map = {}
        try:
            execfile(os.path.join(path_tftproot, pafile), g_map, l_map)
            arch_map = l_map['arch_map']
            arrangement = l_map['arrangement']
            archsize_map = l_map['archsize_map']
            pkgpos_map = l_map['pkgpos_map']
            toplevelgrp_map = l_map['toplevelgrp_map']
            del(g_map)
            del(l_map)
        except:
            return None
        valdoc = Document()
        self.groupdoc = valdoc
        topele = valdoc.createElement('data')
        valdoc.appendChild(topele)
        valtopele = valdoc.createElement('grouplist')
        topele.appendChild(valtopele)
        for group in toplevelgrp_map.keys():
            if group == 'lock':
                continue
            rowele = valdoc.createElement('row')
            rowele.setAttribute('c0', group)
            rowele.setAttribute('c1', group)
            valtopele.appendChild(rowele)
        rowele = valdoc.createElement('row')
        rowele.setAttribute('c0', _('All Packages'))
        rowele.setAttribute('c1', 'ALL')
        valtopele.appendChild(rowele)
        self.fill_values(topele)
        self.fill_values(self.values)
        self.pa_choose = pafile
        self.name_map['srcpos_show'].set_text(os.path.join(dev, dir, isofn))
        choosed_patuple = patuple
        return 1

    def srcpos_ok_clicked(self, widget, data):
        global  pkgarr_probe_result

        (model, iter) = \
                self.srcpos_dialog.name_map['srcposlist_treeview'].get_selection().get_selected()
        if iter:
            pafile = model.get_value(iter, 0)
            for patuple in pkgarr_probe_result:
                if patuple[0] == pafile:
                    break
            if self.tryload_file(patuple):
                self.srcpos_dialog.topwin.destroy()
            else:
                magicpopup.magicmsgbox(None,
                                       _('Load the choosed package arrangement failed!'),
                                       magicpopup.magicmsgbox.MB_ERROR,
                                       magicpopup.magicpopup.MB_OK)
        else:
            magicpopup.magicmsgbox(None,
                                   _('Please choose one position.'),
                                   magicpopup.magicmsgbox.MB_ERROR,
                                   magicpopup.magicpopup.MB_OK)


    def change_srcpos(self, widget, data):
        self.popup_srcpos_dialog()

    def enter(self):
        global pkgarr_probe_status
        global pkgarr_probe_result
        if pkgarr_probe_status != OP_STATUS_DONE:
            magicpopup.magicmsgbox(None, _('Please wait a while for the search of package arrangement information.'),
                                   magicpopup.magicmsgbox.MB_INFO,
                                   magicpopup.magicpopup.MB_OK)
            return 0
        if len(pkgarr_probe_result) == 0:
            magicpopup.magicmsgbox(None, _('Not any package arrangement information can be found!\nPlease return to the parted step to check your setup.'),
                                   magicpopup.magicmsgbox.MB_ERROR,
                                   magicpopup.magicpopup.MB_OK)
            return 0
        if len(pkgarr_probe_result) > 1:
            print pkgarr_probe_result
            popup = 'true'
            if self.pa_choose:
                for result in pkgarr_probe_result:
                    if self.pa_choose == result[0]:
                        popup = None
                        break
            if popup:
                self.popup_srcpos_dialog()
        else:
            if not self.tryload_file(pkgarr_probe_result[0]):
                magicpopup.magicmsgbox(None,
                                       _('Load the only package arrangement failed!\nPlease return to the parted step to check your step.'),
                                       magicpopup.magicmsgbox.MB_ERROR,
                                       magicpopup.magicpopup.MB_OK)
                return 0
        return 1

    def leave(self):
        self.fetch_values(self.rootobj.values)
        return 1

    # There is no need to collect the selected group because xmlgtk.py has done it.
    #def each_group(self, model, path, iter, data):
        #self.selected_group_list.append(model.get_value(iter, 1))

    def get_toplevel_next(self):
        # Bypass the individual package selection step.
        return None
        #self.selected_group_list = []
        #selection = self.name_map['grouplist_treeview'].get_selection()
        #selection.selected_foreach(self.each_group, None)
        #print self.selected_group_list

    def select_all(self, widget, data):
        pass

    def select_nothing(self, widget, data):
        pass

    def select_details(self, widget, data):
        pass
