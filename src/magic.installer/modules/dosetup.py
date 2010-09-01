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

from gettext import gettext as _

class mistep_dosetup (magicstep.magicstep):
    def __init__(self, rootobj):
        magicstep.magicstep.__init__(self, rootobj, 'dosetup.xml', 'dosetup')
        self.doing = 1

    def get_label(self):
        return  _("Do Setup")

    def enter(self):
        global mount_all_list
        self.rootobj.btnback_sensitive(False)
        self.rootobj.btnnext_sensitive(False)

        dolog('action_accounts\n')
        rootpasswd = self.get_data(self.values, 'accounts.root.password')
        acclist = []
        accnode = self.srh_data_node(self.values, 'accounts.userlist')
        for node in accnode.getElementsByTagName('row'):
            acclist.append((node.getAttribute('c0'), # Username.
                            node.getAttribute('c1'), # Password.
                            node.getAttribute('c2'), # Shell.
                            node.getAttribute('c3'), # Home directory.
                            node.getAttribute('c4'))) # Real UID or 'Auto'.
        dolog('%s\n' % 'setup_accounts') #str(('setup_accounts', rootpasswd, acclist)))

        self.rootobj.tm.add_action(_('Setup accounts'), self.doshort, None,
                                   'setup_accounts', rootpasswd, acclist)
        return  1

    def leave(self):
        if self.doing:
            magicpopup.magicmsgbox(None,
                                   _('We are doing setup, do not leave please.'),
                                   magicpopup.magicmsgbox.MB_ERROR,
                                   magicpopup.magicmsgbox.MB_OK)
            return  0
        return  1

    def doshort(self, operid, data):
        hostname = self.get_data(self.values, 'network.hostname')
        ret = self.rootobj.tm.actserver.config_network_short(hostname)
        ret = self.rootobj.tm.actserver.config_keyboard()
        self.rootobj.tm.add_action(_('Run post install script'), self.do_umount_all, None,
                                   'run_post_install', 0)

    def do_umount_all(self, operid, data):
        self.rootobj.tm.add_action(_('Umount all target partition(s)'), self.done, None,
                                   'umount_all_tgtpart', mount_all_list, 'y')

    def done(self, operid, data):
        self.doing = None
        self.rootobj.btnnext_do()
