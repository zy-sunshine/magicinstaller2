#!/usr/bin/python
import os, gtk, string, parted
from mi.client.utils import _
from mi.client.utils import magicstep, magicpopup, xmlgtk
from xml.dom.minidom import parse, parseString
from mi.utils.common import search_file, get_devinfo, convert_str_size

from mi.utils.miconfig import MiConfig
from mi.utils.exception import MiNotSatisfied
CF = MiConfig.get_instance()

from mi.server.utils import logger
dolog = logger.info

from mi.utils.common import STAT

class MIStep_Partition (magicstep.magicstep):
    NAME = 'partition'
    LABEL = _("Partition")
### mistep_parted
    def __init__(self, rootobj):
        self.warn_show = 1
        self.warn_dir_size = True
        self.tmpvalues = None
        self.nb_harddisk = None
        magicstep.magicstep.__init__(self, rootobj, 'parted.xml', 'step')
        self.probeall_status = STAT.OP_STATUS_DOING
        self.hdobj_list = []

        # hide the frame if not autopart profile is defined
        if not self.optionmenu_map[self.name_map["autopart_om"]][1]:
            self.name_map["autopart_frame"].hide()
            
        self.sself = rootobj
        
    def xgc_miparted_notebook(self, node):
        widget = gtk.Notebook()
        widget.set_tab_pos(gtk.POS_TOP)
        widget.set_scrollable(True)
        self.nb_harddisk = widget
        return  widget

    def startup_action(self):
        self.rootobj.tm.add_action(_('Probe all harddisk'),
                                   self.probe_all_ok, None,
                                   'device_probe_all', 0)
        boxnode = self.search_hook(self.uixmldoc, 'vbox', 'DISKTYPEBOX')
        if boxnode:
            all_disk_type = self.rootobj.tm.actserver.all_disk_type()
            for dt in all_disk_type:
                newnode = self.uixmldoc.createElement('radiobutton')
                newnode.setAttribute('label', dt)
                newnode.setAttribute('value', 'disktype')
                newnode.setAttribute('valuedata', dt)
                newnode.setAttribute('expand', 'true')
                newnode.setAttribute('fill', 'true')
                boxnode.appendChild(newnode)
        fsnode1 = self.search_hook(self.uixmldoc, 'optionmenu', 'FILESYSTEM_HOOK1')
        fsnode2 = self.search_hook(self.uixmldoc, 'optionmenu', 'FILESYSTEM_HOOK2')
        if fsnode1 or fsnode2:
            all_fs_type = self.rootobj.tm.actserver.all_file_system_type()
            fst_index = 0
            for fst in all_fs_type:
                if not CF.D.FSTYPE_MAP.has_key(fst):
                    continue
                
                if CF.D.FSTYPE_MAP[fst][1] == '':
                        continue

                if fst == 'linux-swap':
                    CF.G.fstype_swap_index = fst_index
                newnode = self.uixmldoc.createElement('value')
                newsubnode = self.uixmldoc.createTextNode(fst)
                newnode.appendChild(newsubnode)
                if fsnode1:
                    fsnode1.appendChild(newnode)
                if fsnode2:
                    if fsnode1:
                        fsnode2.appendChild(newnode.cloneNode(2))
                    else:
                        fsnode2.appendChild(newnode)
                fst_index = fst_index + 1

    def get_label(self):
        return self.LABEL

    def probe_all_ok(self, tdata, data):
        def check_tdata(tdata):
            if not tdata:
                return False
            if type(tdata) not in (list, tuple):
                return False
            for t in tdata:
                if len(t) != 3:
                    return False
            return True
        if not check_tdata(tdata):
            self.sself.warn_dialog('Can not probe all disk RESULT: %s' % repr(tdata))
        # remove pages in harddisk notebook first
        for i in range(self.nb_harddisk.get_n_pages()):
            self.nb_harddisk.remove_page(-1)
        for (devfn, length, model) in tdata:
            hdobj = Harddisk(self.rootobj.tm, self.uixmldoc,
                                  devfn, length, model)
            label = gtk.Label(hdobj.devfn)
            self.nb_harddisk.append_page(hdobj.widget, label)
            self.hdobj_list.append(hdobj)
        self.probeall_status = STAT.OP_STATUS_DONE

    def reprobe_all(self):
        if CF.G.reprobe_all_disks_required:
            self.probeall_status = STAT.OP_STATUS_DOING
            for hdobj in self.hdobj_list:
                del hdobj
            self.hdobj_list = []
            self.rootobj.tm.add_action(_('Probe all harddisk'),
                                       self.probe_all_ok, None,
                                       'device_probe_all', 0)
            CF.G.reprobe_all_disks_required = 0

##### Enter & Leave Check
    
    def set_no_edit_device(self, dev_list):
        for hdobj in self.hdobj_list:
            rows = hdobj.name_map['partitions_treeview'].get_model()
            for row in rows:
                devfn = row.model.get_value(row.iter, hdobj.COLUMN_DEVICE)
                if devfn and devfn in dev_list:
                    pixbuf = gtk.gdk.pixbuf_new_from_file('images/no.png') #@UndefinedVariable
                    row.model.set_value(row.iter, hdobj.COLUMN_FORMAT, pixbuf)

    def enter(self):
        if not CF.G.choosed_patuple:
            magicpopup.magicmsgbox(None, _('Please choose a package resource.'),
                   magicpopup.magicmsgbox.MB_INFO,
                   magicpopup.magicpopup.MB_OK)
            return
        
        pkgarr_dev = CF.G.choosed_patuple[1]

        logger.d('enter partition step: pkgarr_dev is %s'% pkgarr_dev)
        self.set_no_edit_device([pkgarr_dev, ]) 

        if self.probeall_status != STAT.OP_STATUS_DONE:
            magicpopup.magicmsgbox(None, _('Please wait until the harddisk probe finished.'),
                                   magicpopup.magicmsgbox.MB_INFO,
                                   magicpopup.magicpopup.MB_OK)
            return 0
        if self.hdobj_list == []:
            magicpopup.magicmsgbox(None, _('Not any harddisk is detected, you might need to load driver for your SCSI harddisk...'),
                                   magicpopup.magicmsgbox.MB_ERROR,
                                   magicpopup.magicpopup.MB_OK)
            return 0
        if self.warn_show:
            magicpopup.magicmsgbox(None,
                                   _('Please read the help carefully if it is the first time that you use this partition code.'),
                                   magicpopup.magicmsgbox.MB_WARNING,
                                   magicpopup.magicpopup.MB_OK)
            self.warn_show = None
        return  1

    def leave(self):
        # Clean global settings and fill them below in every device fill_global_and_check method
        CF.G.all_part_infor = {}
        CF.G.all_orig_part = []
        CF.G.root_device = None
        CF.G.boot_device = None
        CF.G.swap_device = None
        # Set mbr_device
        devfn_list = [hdobj.devfn for hdobj in self.hdobj_list]
        mbr_device = self.get_data(self.values, 'bootloader.mbr_device')
        if mbr_device not in devfn_list:
            mbrlist = map(lambda x: '/dev/sd' + chr(x), range(ord('a'), ord('z') + 1)) # ['/dev/sda', '/dev/sdb', ..., '/dev/sdz']
            mbrlist.extend(map(lambda x: '/dev/hd' + chr(x), range(ord('a'), ord('z') + 1))) # + ['/dev/hda', '/dev/hdb', ..., '/dev/hdz']
            for mbrpos in mbrlist:
                if mbrpos in devfn_list:
                    mbr_device = mbrpos
                    break
        if not mbr_device:
            magicpopup.magicmsgbox(None,
                                   _('Not any usable MBR is found.'),
                                   magicpopup.magicmsgbox.MB_ERROR,
                                   magicpopup.magicpopup.MB_OK)
            return 0

        # Fill parts and check
        for hdobj in self.hdobj_list:
            errmsg = hdobj.fill_global_and_check()
            if errmsg:
                magicpopup.magicmsgbox(None,
                                       errmsg,
                                       magicpopup.magicmsgbox.MB_ERROR,
                                       magicpopup.magicpopup.MB_OK)
                return 0
        logger.i('fill_global_and check complete for each device:\n%s\n%s\n' % (
                'CF.G.all_part_infor = %s' % (CF.G.all_part_infor, ),
                'CF.G.all_orig_part = %s' % (CF.G.all_orig_part, )
            )
        )

        # The mount point '/' must exists.
        if not CF.G.root_device:
            magicpopup.magicmsgbox(None,
                                   _('No partition is mounted on /.'),
                                   magicpopup.magicmsgbox.MB_ERROR,
                                   magicpopup.magicpopup.MB_OK)
            return 0

        if not CF.G.boot_device:
            CF.G.boot_device = CF.G.root_device

        dir_size = {} # { '/usr': ('hda', part_no, size), ... }, for partition size check
        mountpoints = {}
        for api in CF.G.all_part_infor.keys():
            for p in CF.G.all_part_infor[api]:
                if p[7] == '' or p[7] == 'USE':
                    continue
                # Mount point must be different.
                if mountpoints.has_key(p[7]):
                    errstr = _('More than one partitions are mounted on %s.')
                    errstr = errstr % p[7]
                    magicpopup.magicmsgbox(None, errstr,
                                           magicpopup.magicmsgbox.MB_ERROR,
                                           magicpopup.magicpopup.MB_OK)
                    return 0
                # Do not mount on the subdirectory of /boot.
                if p[7][:6] == '/boot/':
                    errstr = _('Mount %s%d(%s) on %s might corrupt bootloader. Please do not mount any partition in the subdirectory of /boot.')
                    errstr = errstr % (api, p[0], p[6], p[7])
                    magicpopup.magicmsgbox(None, errstr,
                                           magicpopup.magicmsgbox.MB_ERROR,
                                           magicpopup.magicpopup.MB_OK)
                    return 0
                # DOS partition must be mounted on the subdirectory of /mnt.
                if p[7][:5] != '/mnt/' and \
                   (p[6] == 'fat16' or p[6] == 'fat32' or p[6] == 'ntfs'):
                    errstr = _('fat16, fat32 or ntfs must be mounted in the subdirectory of /mnt.\nBut one %s%d(%s) is mounted on %s.')
                    errstr = errstr % (api, p[0], p[6], p[7])
                    magicpopup.magicmsgbox(None, errstr,
                                           magicpopup.magicmsgbox.MB_ERROR,
                                           magicpopup.magicpopup.MB_OK)
                    CF.G.root_device = ''
                    return 0

                # set mount point
                mountpoints[p[7]] = (api, p[0])

                # collect dir size
                dir_size[p[7]] = (api, p[0], (p[4] - p[3] + 1) * 512)

        # check partition size
        if self.warn_dir_size:
            # check /usr
            dir_chk_pt = '/usr'
            try:
                dir_chk_size = dir_size[dir_chk_pt]
            except KeyError:
                dir_chk_pt = '/'
                dir_chk_size = dir_size[dir_chk_pt]
            if not self.check_dir_size(dir_chk_pt, dir_chk_size, 4 * 1024 ** 3): # 4G
                return 0

            # check /boot
            dir_chk_pt = '/boot'
            try:
                dir_chk_size = dir_size[dir_chk_pt]
            except KeyError:
                pass
            else:
                if not self.check_dir_size(dir_chk_pt, dir_chk_size, 20 * 1024 ** 2): # 20M
                    return 0

        CF.G.win_probe_status = STAT.OP_STATUS_DOING
        self.rootobj.tm.add_action(_('Search for Windows partitions'),
                                   self.got_win_probe_result, None,
                                   'win_probe', CF.G.all_orig_part)
        bt_instpos = self.get_data(self.values, 'bootloader.instpos')
        if bt_instpos == 'boot' and \
               string.find(get_devinfo(CF.G.boot_device, CF.G.all_part_infor).flags, 'b') < 0:
            warnmsg = _('Could not install the bootloader into %s as you will because it contain %s which will prevent the bootloader boot your system. Reset to MBR forcely.')
            warnmsg = warnmsg % (CF.G.boot_device, get_devinfo(CF.G.boot_device, CF.G.all_part_infor).fstype)
            magicpopup.magicmsgbox(None, warnmsg,
                                   magicpopup.magicmsgbox.MB_WARNING,
                                   magicpopup.magicpopup.MB_OK)
            self.set_data(self.rootobj.values, 'bootloader.instpos', 'mbr')

        self.set_data(self.rootobj.values, 'bootloader.CF.G.boot_device', CF.G.boot_device)
        self.set_data(self.rootobj.values, 'bootloader.mbr_device', mbr_device)

        return  1

##### Check Dir Size
    def check_dir_size(self, dir_name, dir_info, min_size):
        if dir_info[2] >= min_size:
            return True
        else:
            if min_size > 1024 ** 3:
                disp_size = '%.2fGB' % (min_size * 1.0 / 1024 ** 3)
            else:
                disp_size = '%.2MB' % (min_size * 1.0 / 1024 ** 2)

            infostr = _('The capacity of %s should >= %s. \nPlease increase the size of partition %s%d.') \
                      % (dir_name, disp_size, dir_info[0], dir_info[1])
            # popup and warn
            magicpopup.magicmsgbox(self, infostr,
                                   magicpopup.magicmsgbox.MB_WARNING,
                                   magicpopup.magicpopup.MB_OK | magicpopup.magicpopup.MB_IGNORE,
                                   'check_dir_size_')
            return False

    def check_dir_size_ok_clicked(self, widget, dlg):
        dlg.topwin.destroy()

    def check_dir_size_ignore_clicked(self, widget, dlg):
        dlg.topwin.destroy()
        #### TODO: remove this dirty code.
        self.warn_dir_size = False
        CF.G.root_device = ''
        # invoke next button again
        self.rootobj.buttonbar.next.clicked()

##### Probe Result
    def got_pkgarr_probe_result(self, tdata, data):
        def check_data(tdata):
            for d in tdata:
                if (type(d) is not list or type(d) is not tuple):
                    return False
            return True
        CF.G.pkgarr_probe_result = tdata
        CF.G.pkgarr_probe_status = STAT.OP_STATUS_DONE
        dolog('CF.G.pkgarr_probe_result: %s\n' % str(CF.G.pkgarr_probe_result))
        if not check_data(CF.G.pkgarr_probe_result):
            raise MiNotSatisfied('''Can not get pkgarr (pkgarr_probe) CF.G.pkgarr_probe_result 
             TYPE %s VALUE: %s''' % (type(CF.G.pkgarr_probe_result), CF.G.pkgarr_probe_result))

            
        

    def got_win_probe_result(self, tdata, data):
        CF.G.win_probe_result = tdata
        CF.G.win_probe_status = STAT.OP_STATUS_DONE
        dolog('CF.G.win_probe_result: %s\n' % str(CF.G.win_probe_result))

        if CF.G.win_probe_result:
            def win_part_cmp(e1, e2):
                # priority sort
                d = {'vista/7': 1, 'winnt': 2, 'win98': 3, 'win': 4 }
                r = d[e1[1]] - d[e2[1]]
                if r != 0:
                    return r
                else:
                    return cmp(e1[0], e2[0])
            CF.G.win_probe_result.sort(win_part_cmp)
            win_device = CF.G.win_probe_result[0][0]
        else:
            win_device = ''
        self.set_data(self.rootobj.values, 'bootloader.win_device', win_device)

##### Misc
    def get_help(self):
        # TO TRANSLATOR: Let helptext/parted.help.en.txt to be i18n string,
        # so the language which different with English can use another text
        # file.
        return _('helptext/parted.help.en.txt')
        
    def btnback_clicked(self, widget, data):
        return  1

    def btnnext_clicked(self, widget, data):
        return  1

##### Autopart
    def auto1_clicked(self, widget, data):
        errtxt = _("Auto-partition will erase all existing partitions.\nContinue?")
        magicpopup.magicmsgbox(self, errtxt,
                               magicpopup.magicmsgbox.MB_QUESTION,
                               magicpopup.magicpopup.MB_YES | magicpopup.magicpopup.MB_NO,
                               'autopart_')

    def autopart_yes_clicked(self, widget, dlg):
        dlg.topwin.destroy()
        self.fetch_values(self.rootobj.values)
        sel_profile = self.get_data(self.values, 'parted.profile')
        if not sel_profile:
            errtxt = _("No auto-partition profile is defined or selected.")
            magicpopup.magicmsgbox(None, errtxt,
                                   magicpopup.magicmsgbox.MB_ERROR,
                                   magicpopup.magicpopup.MB_OK)
            return
        err = True
        profile_file = search_file('magic.autopart.xml', [CF.D.HOTFIXDIR, '.'], exit_if_not_found = False)
        dolog('fname2: %s\n' % profile_file)
        if profile_file:
            dE = parse(profile_file).documentElement
            partprofile_node = self.srh_data_node(dE, "autopart." + sel_profile)
            dolog('sel_profile=%s,  node=%s\n' % (sel_profile, partprofile_node))
            if partprofile_node:
                err = False
        if err:
            errtxt = _("Read auto-partition profile failed.")
            magicpopup.magicmsgbox(None, errtxt,
                                   magicpopup.magicmsgbox.MB_ERROR,
                                   magicpopup.magicpopup.MB_OK)
            return

        class AutoPart:
            def __init__(self, mountpoint, filesystem, size):
                self.mountpoint = mountpoint
                self.filesystem = filesystem
                self.size = size
            def __str__(self):
                return '(%s, %s, %s)' % (self.mountpoint,
                                         self.filesystem,
                                         self.size)

        autoparts = []
        for part_node in partprofile_node.childNodes:
            if part_node.nodeType != part_node.ELEMENT_NODE:
                continue
            mntpnt = self.get_data(part_node, 'mountpoint')
            fs = self.get_data(part_node, 'filesystem')
            if fs.lower() == 'swap':
                fs = 'linux-swap'
            elif fs == 'ext2fs':
                fs = 'ext2'
            elif fs == 'ext3fs':
                fs = 'ext3'
            elif fs == 'vfat':
                fs = 'fat32'
            if not fs in CF.D.FSTYPE_MAP:
                errtxt = _("Filesystem type '%s' not supported.") % fs
                magicpopup.magicmsgbox(None, errtxt,
                                       magicpopup.magicmsgbox.MB_INFO,
                                       magicpopup.magicpopup.MB_OK)
                return
            size = self.get_data(part_node, 'size')
            if size[-1] == '%':
                size = - convert_str_size(size[:-1])
            else:
                size = convert_str_size(size)
            autoparts.append(AutoPart(mntpnt, fs, size))
        dolog('autoparts: %s\n' % (autoparts, ))

        # Check for sanity
        if not autoparts:
            errtxt = _("Read auto-partition profile failed.")
            magicpopup.magicmsgbox(None, errtxt,
                                   magicpopup.magicmsgbox.MB_ERROR,
                                   magicpopup.magicpopup.MB_OK)
            return
        n = self.nb_harddisk.get_current_page()
        if n < 0 or n >= len(self.hdobj_list):
            n = 0
        hdobj = self.hdobj_list[n]       # default to the first harddisk
        remain_size = hdobj.length * 512 # convert sector to byte
        proportion_sum = 0
        cleaned_autoparts = []
        for part in autoparts:
            if part.size == 0:          # skip zero-sized part
                continue
            if part.size > 0:
                remain_size -= part.size
            else:
                proportion_sum += part.size
            cleaned_autoparts.append(part)
        autoparts = cleaned_autoparts
        if remain_size < 0 or \
               (remain_size == 0 and proportion_sum < 0):
            errtxt = _("Insufficient disk space for this auto-partition profile.")
            magicpopup.magicmsgbox(None, errtxt,
                                   magicpopup.magicmsgbox.MB_ERROR,
                                   magicpopup.magicpopup.MB_OK)
            return
        # allocate the free space here
        for part in autoparts:
            if part.size <= 0:
                part.size = part.size * remain_size / proportion_sum
            if part.size <= 0:
                errtxt = _("Insufficient disk space for this auto-partition profile.")
                magicpopup.magicmsgbox(None, errtxt,
                                       magicpopup.magicmsgbox.MB_ERROR,
                                       magicpopup.magicpopup.MB_OK)
                return

        # start to do part
        class autopart_coroutine:
            def __init__(self, autoparts, tm, hdobj):
                self.autoparts = autoparts
                self.tm = tm
                self.hdobj = hdobj
                self.tdata = None
                self.generator = self.action()

            def action(self):
                yield self.tm.add_action(None, self, None,
                                         'disk_new_fresh', self.hdobj.devfn, 'msdos')
                self.hdobj.part_addon_infor = {}
                self.hdobj.added_part_start = {}
                start_sect = 0
                for (i, part) in enumerate(self.autoparts):
                    if i < 3:
                        parttype = 'primary'
                    elif i == 3:
                        # create a 'extended' partition first
                        parttype = 'extended'
                        yield self.tm.add_action(None, self, None,
                                                 'add_partition', self.hdobj.devfn,
                                                 parttype, 'N/A', start_sect, self.hdobj.length - 1)
                        (rc, errmsg) = self.tdata
                        if rc < 0:
                            errtxt = _(errmsg)
                            magicpopup.magicmsgbox(None, errtxt,
                                                   magicpopup.magicmsgbox.MB_INFO,
                                                   magicpopup.magicpopup.MB_OK)
                            break
                        parttype = 'logical'
                    else:
                        parttype = 'logical'
                    end_sect = start_sect + part.size / 512
                    if end_sect > self.hdobj.length - 1:
                        end_sect = self.hdobj.length - 1
                    dolog("\nCreate %s part on [%d, %d].\n" % (part.mountpoint, start_sect, end_sect))
                    yield self.tm.add_action(None, self, None,
                                             'add_partition', self.hdobj.devfn,
                                             parttype, part.filesystem,
                                             start_sect, end_sect)
                    (real_start_sect, errmsg) = self.tdata
                    if real_start_sect < 0:
                        errtxt = _(errmsg)
                        magicpopup.magicmsgbox(None, errtxt,
                                               magicpopup.magicmsgbox.MB_ERROR,
                                               magicpopup.magicpopup.MB_OK)
                        break
                    if part.filesystem == 'linux-swap':
                        addon_info = ('true', 'linux-swap', 'USE')
                    else:
                        addon_info = ('true', part.filesystem, part.mountpoint)
                    self.hdobj.part_addon_infor[real_start_sect] = addon_info
                    self.hdobj.added_part_start[real_start_sect] = 'y'
                    start_sect = end_sect + 1
                self.tm.add_action(None, self.hdobj.got_all_partitions, None,
                                   'get_all_partitions', self.hdobj.devfn)

            def __call__(self, tdata, data):
                try:
                    self.tdata = tdata
                    self.generator.next()
                except StopIteration:
                    pass

        part_co = autopart_coroutine(autoparts, self.rootobj.tm, hdobj)
        part_co(None, None)

    def xgc_autopart_optionmenu(self, node):
        # Fill up auto part profile option menu
        fname = search_file('magic.autopart.xml', [CF.D.HOTFIXDIR, '.'],
                            exit_if_not_found = False)
        is_empty = True
        if fname:
            dolog('fname: %s' % fname)
            dE = parse(fname).documentElement
            profile_node = self.srh_data_node(dE, 'autopart')
            if profile_node is None:
                chnode_list = []
            else:
                chnode_list = profile_node.childNodes
            # Fill values
            for chnode in chnode_list:
                if chnode.nodeType != chnode.ELEMENT_NODE:
                    continue
                # create node and add
                newnode = self.uixmldoc.createElement('value')
                newnode.setAttribute('valstr', chnode.tagName)
                dispval = chnode.getAttribute('desc')
                if dispval:
                    dispval = _(dispval)
                else:
                    dispval = chnode.tagName
                newsubnode = self.uixmldoc.createTextNode(dispval)
                newnode.appendChild(newsubnode)
                node.appendChild(newnode)
                is_empty = False

        if is_empty:
            dolog("magic.autopart.xml not found or invalid.\n")
        return self.xgc_optionmenu(node)


### Harddisk Class
class  Harddisk(xmlgtk.xmlgtk):
    COLUMN_NUM        = 0
    COLUMN_DEVICE     = 1
    COLUMN_FORMAT     = 2
    COLUMN_FLAGS      = 3
    COLUMN_TYPE       = 4
    COLUMN_CAPACITY   = 5
    COLUMN_FILESYSTEM = 6
    COLUMN_MOUNTPOINT = 7
    COLUMN_LABEL      = 8
    COLUMN_START      = 9
    COLUMN_END        = 10
    COLUMN_FON_VAL    = 11
    COLUMN_AVA_FLAGS  = 12
    COLUMN_ORIGFS     = 13

    aeval_xml = """<?xml version="1.0"?>
    <partition>
      <parttype>%s</parttype>
      <ppos>ppbegin</ppos>
      <size>%d</size>
      <format_or_not>%s</format_or_not>
      <filesystem>%s</filesystem>
      <mountpoint>%s</mountpoint>
      <swap>%s</swap>
      <label>%s</label><o_label>%s</o_label>
      <avaflags>%s</avaflags>
      %s
    </partition>"""

    def __init__(self, tm, uixmldoc,
                 devfn, length, model='N/A'):
        xmlgtk.xmlgtk.__init__(self, uixmldoc, 'diskpage')
        
        # harddisk info
        self.devfn = devfn
        self.length = length
        self.model = model
        self.disklabel = None

        # partition info
        self.partlist = []          # partition list
        # part_addon_infor is indexed by start sector because it can be used to
        # identify an partition even if the partition number is changed.
        # The value of the part_addon_infor is
        #     (format_or_not, format_to_filesystem, mount_point)
        self.part_addon_infor = {}
        # added_part_start is indexed by start sector. All value is 'y'.
        # It distinguish the user added partition from the original exist partition.
        self.added_part_start = {}
        # 'true' | 'false', support parition name or not
        self.support_partition_name = None

        self.orig_partitions = None # { start_sect: 'part devfn' }, original partitions

        # Values for Create/Edit partition.
        self.aeval_xmldoc = None
        self.ae_start = None
        self.ae_end = None
        self.ae_model = None
        self.ae_iter = None

        # Values for disk type choice.
        self.tmpdtval_xmldoc = None
        self.disktype = None

        # fill ui
        self.set_widget_value('model', model)
        self.set_widget_value('capacity', self.sector2str(length))
        
        # get all partitions
        self.tm = tm                # task manager
        tm.add_action(None, self.got_all_partitions, None, 'get_all_partitions', devfn)

##### Utility
    def partdevfn(self, partnum):
        if partnum < 1:
            return ''
        return  '%s%d' % (self.devfn, partnum)

    def waitdlg(self):
        return magicpopup.magicmsgbox(None, _('Please wait......'),
                                      magicpopup.magicmsgbox.MB_INFO, 0)

    def close_dialog(self, tdata, data):
        data.topwin.destroy()

##### Value conversion
    def sector2str(self, sector):
        if sector > 2 * 1024 * 1024:
            return '%6.2fGB' % (sector / 2.0 / 1024 / 1024)
        else:
            return '%7.2fMB' % (sector / 2.0 / 1024)

    def parttype2str(self, parttype):
        result = ''
        if parttype & parted.PARTITION_LOGICAL:
            result = result + 'L'
        if parttype & parted.PARTITION_EXTENDED:
            result = result + 'E'
        if parttype & parted.PARTITION_FREESPACE:
            result = result + 'F'
        if result == '':
            return  'P'
        return  result

    def str2parttype(self, str):
        result = 0
        if string.find(str, 'L') >= 0:
            result = result | parted.PARTITION_LOGICAL
        if string.find(str, 'E') >= 0:
            result = result | parted.PARTITION_EXTENDED
        if string.find(str, 'F') >= 0:
            result = result | parted.PARTITION_FREESPACE
        return  result

    def partflags2str(self, partflags):
        result = ''
        for f in partflags:
            if f == parted.PARTITION_BOOT:
                result = result + 'B'
            elif f == parted.PARTITION_ROOT:
                result = result + 'R'
            elif f == parted.PARTITION_SWAP:
                result = result + 'S'
            elif f == parted.PARTITION_HIDDEN:
                result = result + 'H'
            elif f == parted.PARTITION_RAID:
                result = result + 'A'
            elif f == parted.PARTITION_LVM:
                result = result + 'V'
            elif f == parted.PARTITION_LBA:
                result = result + 'L'
        return  result

    def str2partflags(self, str):
        result = []
        for c in str:
            if c == 'B':
                result.append(parted.PARTITION_BOOT)
            elif c == 'R':
                result.append(parted.PARTITION_ROOT)
            elif c == 'S':
                result.append(parted.PARTITION_SWAP)
            elif c == 'H':
                result.append(parted.PARTITION_HIDDEN)
            elif c == 'A':
                result.append(parted.PARTITION_RAID)
            elif c == 'V':
                result.append(parted.PARTITION_LVM)
            elif c == 'L':
                result.append(parted.PARTITION_LBA)
        return  result


##### Gather info
    def refresh_disklabel_label(self, tdata, data):
        "Callback of op 'get_disk_type'"
        (self.disklabel, self.support_partition_name) = tdata
        self.set_widget_value('disklabel', self.disklabel)

    def fill_global_and_check(self):
        CF.G.all_part_infor[self.devfn] = []
        models = self.list_map.keys()
        model = models[0]
        iter = model.get_iter_first()
        while iter:
            partnum = int(model.get_value(iter, self.COLUMN_NUM))
            parttype = self.str2parttype(model.get_value(iter, self.COLUMN_TYPE))
            partflags = self.str2partflags(model.get_value(iter, self.COLUMN_FLAGS))
            start = int(model.get_value(iter, self.COLUMN_START))
            end = int(model.get_value(iter, self.COLUMN_END))
            format_or_not = model.get_value(iter, self.COLUMN_FON_VAL)
            filesystem = model.get_value(iter, self.COLUMN_FILESYSTEM)
            mountpoint = model.get_value(iter, self.COLUMN_MOUNTPOINT)
            not_touched = 'true'
            if format_or_not == 'true':
                not_touched = 'false'
            elif self.added_part_start.has_key(start):
                not_touched = 'false'
            CF.G.all_part_infor[self.devfn].append((partnum,
                                               parttype,
                                               partflags,
                                               start,
                                               end,
                                               format_or_not,
                                               filesystem,
                                               mountpoint,
                                               not_touched))
            if not_touched == 'true' and \
                   filesystem != 'N/A' and \
                   filesystem not in ('linux-swap', 'linux-swap(v1)'):
                CF.G.all_orig_part.append((self.orig_partitions[start],
                                      filesystem,
                                      self.partdevfn(partnum)))
            
            if mountpoint == '/':
                if CF.G.root_device:
                    return  _('More than one partition is mounted on /')
                CF.G.root_device = '%s%d' % (self.devfn, partnum)
            if mountpoint == '/boot':
                CF.G.boot_device = '%s%d' % (self.devfn, partnum)
            if CF.D.FSTYPE_MAP.has_key(filesystem):
                minsize = CF.D.FSTYPE_MAP[filesystem][2]
                if minsize != -1:
                    if end - start + 1 < minsize * 2048:
                        errmsg = _('%0.2fM is too small for %s, %dM at least.')
                        errmsg = errmsg % ((end - start + 1.0) / 2048, filesystem, minsize)
                        return  errmsg
                maxsize = CF.D.FSTYPE_MAP[filesystem][3]
                if maxsize != -1:
                    if end - start + 1 > maxsize * 2048:
                        errmsg = _('%0.2fM is too big for %s, %dM at most.')
                        errmsg = errmsg % ((end - start + 1.0) / 2048, filesystem, maxsize)
                        return  errmsg
            if filesystem == 'linux-swap' and mountpoint == 'USE':
                # Choose the maximum swap.
                if not CF.G.swap_device or CF.G.swap_device[2] < end - start + 1:
                    CF.G.swap_device = [self.devfn, partnum, end - start + 1]
            iter = model.iter_next(iter)
        return  None

    def got_all_partitions(self, tdata, data):
        "Callback of op 'get_all_partitions'"
        self.tm.add_action(None, self.refresh_disklabel_label, None,
                           'get_disk_type', self.devfn)
        self.partlist = tdata
        if self.orig_partitions is None:  # save original partitions
            self.orig_partitions = {}
            for p in self.partlist:
                self.orig_partitions[p[6]] = self.partdevfn(p[0])

        for p in self.partlist:
            if not self.part_addon_infor.has_key(p[6]):
                if p[4] == 'linux-swap':
                    self.part_addon_infor[p[6]] = ('false', p[4], 'USE')
                else:
                    self.part_addon_infor[p[6]] = ('false', p[4], '')
        self.fill_parts_view()
        if data:
            data.topwin.destroy()
        else:
            self.name_map['restore'].set_sensitive(True)
            self.name_map['newlabel'].set_sensitive(True)

    def reload_all_partitions(self, tdata, data):
        self.tm.add_action(None, self.got_all_partitions, data,
                           'get_all_partitions', self.devfn)

    def fill_parts_view(self):
        tmpval_xmldoc = parseString('<?xml version="1.0"?><data><partitions/></data>')
        tmpval_root = tmpval_xmldoc.getElementsByTagName('partitions')[0]
        for part in self.partlist:
            if part[2] & parted.PARTITION_FREESPACE:
                if part[7] - part[6] + 1 < 2048:
                    continue
                addon_infor = ('false', '', '')
            else:
                addon_infor = self.part_addon_infor[part[6]]
            newnode = tmpval_xmldoc.createElement('row')
            newnode.setAttribute('c0', str(part[0]))
            newnode.setAttribute('c1', self.partdevfn(part[0]))
            if addon_infor[0] == 'true':
                newnode.setAttribute('c2', 'images/yes.png')
            elif self.added_part_start.has_key(part[6]) or \
                 part[2] & parted.PARTITION_FREESPACE or \
                 part[2] & parted.PARTITION_EXTENDED:
                newnode.setAttribute('c2', 'images/blank.png')
            else:
                newnode.setAttribute('c2', 'images/apple-green.png')
            newnode.setAttribute('c3', self.partflags2str(part[1]))
            newnode.setAttribute('c4', self.parttype2str(part[2]))
            newnode.setAttribute('c5', self.sector2str(part[3]))
            if addon_infor[0] == 'true':
                newnode.setAttribute('c6', addon_infor[1])
            else:
                newnode.setAttribute('c6', part[4])
            newnode.setAttribute('c7', addon_infor[2])
            newnode.setAttribute('c8', part[5])
            newnode.setAttribute('c9', str(part[6]))
            newnode.setAttribute('c10', str(part[7]))
            newnode.setAttribute('c11', addon_infor[0]) # Format or not.
            newnode.setAttribute('c12', self.partflags2str(part[8])) # avaflags
            newnode.setAttribute('c13', part[4]) # Original filesystem.
            tmpval_root.appendChild(newnode)
        self.fill_values(tmpval_xmldoc.documentElement)


    def part_sel_changed(self, treesel, data):
        (model, iter) = treesel.get_selected()
        if not iter: # iter is None
            for btnname in ['create', 'edit', 'remove']:
                self.name_map[btnname].set_sensitive(False)
        else:
            # Get the part type.
            parttypestr = model.get_value(iter, self.COLUMN_TYPE)
            if string.find(parttypestr, 'F') >= 0:
                # This is a free space.
                self.name_map['create'].set_sensitive(True)
                self.name_map['edit'].set_sensitive(False)
                self.name_map['remove'].set_sensitive(False)
            else:
                self.name_map['create'].set_sensitive(False)
                self.name_map['edit'].set_sensitive(True)
                self.name_map['remove'].set_sensitive(True)

##### Partition create and edit
    def aevalue_create(self):
        (model, iter) = \
                self.name_map['partitions_treeview'].get_selection().get_selected()
        self.ae_model = model
        self.ae_iter = iter
        if iter:
            extended_or_not = None
            t = model.get_value(iter, self.COLUMN_TYPE)
            if string.find(t, 'L') >= 0:
                t = 'logical'
            elif string.find(t, 'E') >= 0:
                t = 'extended'
                extended_or_not = 1
            else:
                t = 'primary'
            fon = model.get_value(iter, self.COLUMN_FON_VAL)
            fs = model.get_value(iter, self.COLUMN_FILESYSTEM)
            must_format_or_not = (fs == 'N/A')
            mp = model.get_value(iter, self.COLUMN_MOUNTPOINT)
            swap = 'USE'  # default to use swap
            if fs == 'linux-swap':
                #swap = mp
                mp = ''
            #else:
            #    swap = ''
            l = model.get_value(iter, self.COLUMN_LABEL)
            flags = model.get_value(iter, self.COLUMN_FLAGS)
            avaflags = model.get_value(iter, self.COLUMN_AVA_FLAGS)
            self.ae_start = int(model.get_value(iter, self.COLUMN_START))
            self.ae_end = int(model.get_value(iter, self.COLUMN_END))
        else:  # It shouldn't come here.....
            t = 'primary'
            fon = 'false'
            fs = 'reiserfs'
            must_format_or_not = 1
            mp = '/'
            swap = ''
            l = 'N/A'
            flags = ''
            avaflags = ''
            self.ae_start = 0
            self.ae_end = 0
            exnteded_or_not = None
        self.orig_fs = fs
        if l == 'N/A':
            l = ''
        flagsxml = ''
        for f in 'BRSHAVL':
            if string.find(flags, f) >= 0:
                val = 'true'
            else:
                val = 'false'
            flagsxml = flagsxml + \
                       '<flag_%s>%s</flag_%s><o_flag_%s>%s</o_flag_%s>' % (f, val, f, f, val, f)
        self.aeval_xmldoc = parseString(self.aeval_xml % \
                                        (t, self.ae_end - self.ae_start + 1,
                                         fon, fs, mp, swap,
                                         l, l, avaflags, flagsxml))
        return  (avaflags,
                 extended_or_not, must_format_or_not, fs == 'linux-swap')

    def aedialog_setup(self,
                       extended_or_not, must_format_or_not, swap_or_not):
        if must_format_or_not:
            self.aedialog.name_map['mountpoint_label'].hide()
            self.aedialog.name_map['mountpoint_combo'].hide()
            #self.aedialog.name_map['swapbox'].hide()
        elif swap_or_not:
            self.aedialog.name_map['mountpoint_label'].hide()
            self.aedialog.name_map['mountpoint_combo'].hide()
            self.aedialog.name_map['swapbox'].show()
        self.aedialog.fill_values(self.aeval_xmldoc.documentElement)
        if self.support_partition_name == 'false':
            self.aedialog.name_map['label_label'].set_sensitive(False)
            self.aedialog.name_map['label_entry'].set_sensitive(False)
        if extended_or_not:
            for widget in self.aedialog.group_map['noextend']:
                widget.set_sensitive(False)

    def aevalue_fetch_addon_infor(self, dE):
        fon = self.aedialog.get_data(dE, 'format_or_not')
        self.ae_model.set_value(self.ae_iter, self.COLUMN_FON_VAL, fon)
        if fon == 'true':
            self.ae_model.set_value(self.ae_iter, self.COLUMN_FORMAT,
                                    self.get_pixbuf_map('images/yes.png'))
            fs = self.aedialog.get_data(dE, 'filesystem')
            self.ae_model.set_value(self.ae_iter, self.COLUMN_FILESYSTEM, fs)
        else:
            start = int(self.ae_model.get_value(self.ae_iter, self.COLUMN_START))
            typestr = self.ae_model.get_value(self.ae_iter, self.COLUMN_TYPE)
            if self.added_part_start.has_key(start) or \
               string.find(typestr, 'F') >= 0 or \
               string.find(typestr, 'E') >= 0:
                self.ae_model.set_value(self.ae_iter, self.COLUMN_FORMAT,
                                        self.get_pixbuf_map('images/blank.png'))
            else:
                self.ae_model.set_value(self.ae_iter, self.COLUMN_FORMAT,
                                        self.get_pixbuf_map('images/apple-green.png'))
            fs = self.ae_model.get_value(self.ae_iter, self.COLUMN_ORIGFS)
            self.ae_model.set_value(self.ae_iter, self.COLUMN_FILESYSTEM, fs)
        if fs == 'linux-swap':
            mp = self.aedialog.get_data(dE, 'swap')
        else:
            mp = self.aedialog.get_data(dE, 'mountpoint')
            # Trim the mount point.
            if mp != '' and mp[0] != '/':
                mp = '/' + mp
            while len(mp) > 1 and mp[-1] == '/':
                mp = mp[:-1]
        self.ae_model.set_value(self.ae_iter, self.COLUMN_MOUNTPOINT, mp)
        avaflags = self.aedialog.get_data(dE, 'avaflags')
        return (fon, fs, mp)

    def update_create_labels(self):
        size = int(float(self.aedialog.name_map['size_hscale'].get_value()))
        self.aedialog.name_map['size_entry'].set_text(str(size))
        self.aedialog.fetch_values(self.aeval_xmldoc)
        dE = self.aeval_xmldoc.documentElement
        ppos = self.aedialog.get_data(dE, 'ppos')
        if ppos == 'ppbegin':
            self.aedialog.name_map['start_sec'].set_text(str(self.ae_start))
            self.aedialog.name_map['start_mega'].set_text(self.sector2str(self.ae_start))
            self.aedialog.name_map['end_sec'].set_text(str(self.ae_start + size - 1))
            self.aedialog.name_map['end_mega'].set_text(self.sector2str(self.ae_start + size - 1))
        else:
            self.aedialog.name_map['start_sec'].set_text(str(self.ae_end - size + 1))
            self.aedialog.name_map['start_mega'].set_text(self.sector2str(self.ae_end - size + 1))
            self.aedialog.name_map['end_sec'].set_text(str(self.ae_end))
            self.aedialog.name_map['end_mega'].set_text(self.sector2str(self.ae_end))
        self.aedialog.name_map['size_sec'].set_text(str(size))
        self.aedialog.name_map['size_mega'].set_text(self.sector2str(size))

    class  partcreate (magicpopup.magicpopup):
        def __init__(self, upobj, uixml, title, buttons,
                     uirootname=None, prefix=''):
            self.upobj = upobj
            magicpopup.magicpopup.__init__(self, upobj, uixml, title,
                                           buttons, uirootname, prefix)

        def label_change(self, range, data):
            self.upobj.update_create_labels()

        def parttype_changed(self, optmenu, data):
            if optmenu.get_active() == 1:
                # This means the user choose to create an Extended Partition.
                for widget in self.group_map['noextend']:
                    widget.set_sensitive(False)
                self.name_map['filesystem_om'].set_sensitive(False)
            else:
                # This means the user choose to create an Primary/Logical Partition.
                for widget in self.group_map['noextend']:
                    widget.set_sensitive(True)
                if self.name_map['format'].get_active():
                    self.name_map['filesystem_om'].set_sensitive(True)
                else:
                    self.name_map['filesystem_om'].set_sensitive(False)

        def format_changed(self, togglebutton, data):
            self.upobj.format_fstype_changed(togglebutton,
                                             self.name_map['filesystem_om'],
                                             data)

        def fstype_changed(self, optmenu, data):
            self.upobj.format_fstype_changed(self.name_map['format'],
                                             optmenu,
                                             data)

    class  partedit (magicpopup.magicpopup):
        def __init__(self, upobj, uixml, title, buttons,
                     uirootname=None, prefix=''):
            self.upobj = upobj
            magicpopup.magicpopup.__init__(self, upobj, uixml, title,
                                           buttons, uirootname, prefix)

        def format_changed(self, togglebutton, data):
            self.upobj.format_fstype_changed(togglebutton,
                                             self.name_map['filesystem_om'],
                                             data)

        def fstype_changed(self, optmenu, data):
            self.upobj.format_fstype_changed(self.name_map['format'],
                                             optmenu,
                                             data)

    def format_fstype_changed(self, togglebutton, optmenu, data):
        if not togglebutton.get_active() and self.must_format_or_not:
            self.aedialog.name_map['mountpoint_label'].hide()
            self.aedialog.name_map['mountpoint_combo'].hide()
            self.aedialog.name_map['swapbox'].hide()
        else:
            if optmenu.get_active() == CF.G.fstype_swap_index:
                self.aedialog.name_map['mountpoint_label'].hide()
                self.aedialog.name_map['mountpoint_combo'].hide()
                self.aedialog.name_map['swapbox'].show()
            else:
                self.aedialog.name_map['swapbox'].hide()
                self.aedialog.name_map['mountpoint_label'].show()
                self.aedialog.name_map['mountpoint_combo'].show()
        if not togglebutton.get_active():
            omval = self.aedialog.optionmenu_map[optmenu][1]
            for i in range(len(omval)):
                if omval[i] == self.orig_fs:
                    optmenu.set_active(i)
                    break

    def create_clicked(self, widget, data):
        (avaflags, extended_or_not, must_format_or_not, swap_or_not) = \
                   self.aevalue_create()
        self.must_format_or_not = must_format_or_not
        hsnode = self.search_hook(self.uixmldoc, 'hscale', 'size_hscale')
        if hsnode:
            hsnode.setAttribute('upper', self.ae_end - self.ae_start)
        self.aedialog = self.partcreate( \
            self, self.uixmldoc, _('Create a new partition'),
            magicpopup.magicpopup.MB_OK |
            magicpopup.magicpopup.MB_CANCEL,
            'newpart-dlg', 'add_')
        self.aedialog.name_map['device_label'].set_text(self.model)
        self.aedialog_setup(extended_or_not, must_format_or_not, swap_or_not)
        self.aedialog.name_map['size_hscale'].set_value(self.ae_end - self.ae_start + 1)

    def add_ok_clicked(self, widget, data):
        self.aedialog.fetch_values(self.aeval_xmldoc)
        self.aedialog.topwin.destroy()
        dE = self.aeval_xmldoc.documentElement
        parttype = self.aedialog.get_data(dE, 'parttype')
        format_or_not = self.aedialog.get_data(dE, 'format_or_not')
        if parttype == 'extended':
            fstype = 'N/A'
            addon_infor = ('false', 'N/A' , '')
        elif format_or_not == 'false' and self.must_format_or_not:
            fstype = 'N/A'
            addon_infor = ('false', 'N/A' , '')
        else:
            fstype = self.aedialog.get_data(dE, 'filesystem')
            addon_infor = self.aevalue_fetch_addon_infor(dE)
        ppos = self.aedialog.get_data(dE, 'ppos')
        # Trim size.
        size = self.aedialog.get_data(dE, 'size')
        maxsize = self.ae_end - self.ae_start + 1
        if len(size) > 0:
            if size[-1] in 'kKmMgG':
                size = convert_str_size(size)
                if size is not None:
                    size /= 512 # to sector num
            else:
                size = convert_str_size(size)
            if size is None:
                size = maxsize
        if size <= 0:
            size = 1
        if size > maxsize:
            size = maxsize
        if ppos == 'ppbegin':
            start = self.ae_start
            end = self.ae_start + size - 1
        else:
            start = self.ae_end - size + 1
            end = self.ae_end
        self.tm.add_action(None, self.partition_added, (self.waitdlg(), addon_infor),
                           'add_partition', self.devfn, parttype, fstype, start, end)

    def partition_added(self, tdata, data):
        (start, errstr) = tdata
        (waitdlg, addon_infor) = data
        if start >= 0:
            self.part_addon_infor[start] = addon_infor
            self.added_part_start[start] = 'y'
            self.tm.add_action(None, self.got_all_partitions, waitdlg,
                               'get_all_partitions', self.devfn)
        else:
            magicpopup.magicmsgbox(None, errstr,
                                   magicpopup.magicmsgbox.MB_ERROR,
                                   magicpopup.magicpopup.MB_OK)
            waitdlg.topwin.destroy()

    def edit_clicked(self, widget, data):
        (avaflags, extended_or_not, must_format_or_not, swap_or_not) = \
                   self.aevalue_create()        
        # Check whether the partition is the one choosed pkgarr in.
        if CF.G.choosed_patuple:
            pkgarr_dev = CF.G.choosed_patuple[1]
        else:
            pkgarr_dev = None
            
        (model, iter) = \
                self.name_map['partitions_treeview'].get_selection().get_selected()
        if iter:
            devfn = model.get_value(iter, self.COLUMN_DEVICE)
        else:
            devfn = None
        logger.d('devfn is %s pkgarr_dev is %s'% (devfn, pkgarr_dev))
        if pkgarr_dev and devfn == pkgarr_dev:
            magicpopup.magicmsgbox(None,
                   _('Sorry, you can not edit this deivce.\nBecause the setup package is in it.'),
                   magicpopup.magicmsgbox.MB_INFO,
                   magicpopup.magicpopup.MB_OK)
            return
        
        # Make a dialog to edit partition.
        self.must_format_or_not = must_format_or_not
        self.aedialog = self.partedit( \
            self, self.uixmldoc, _('Edit an exist partition'),
            magicpopup.magicpopup.MB_OK |
            magicpopup.magicpopup.MB_CANCEL,
            'editpart-dlg', 'edit_')
        self.aedialog_setup(extended_or_not, must_format_or_not, swap_or_not)
        for f in 'BRSHAVL':
            if string.find(avaflags, f) < 0:
                self.aedialog.name_map['flag_%s' % f].set_sensitive(False)

    def edit_fstype_changed(self, optmenu, data):
        self.fstype_changed(optmenu, data)

    def edit_ok_clicked(self, widget, data):
        self.aedialog.fetch_values(self.aeval_xmldoc)
        self.aedialog.topwin.destroy()
        dE = self.aeval_xmldoc.documentElement
        self.part_addon_infor[self.ae_start] = self.aevalue_fetch_addon_infor(dE)
        true_flags = ''
        false_flags = ''
        cur_flags = ''
        avaflags = self.aedialog.get_data(dE, 'avaflags')
        for f in avaflags:
            flag_orig = self.aedialog.get_data(dE, 'o_flag_%s' % f)
            flag_cur = self.aedialog.get_data(dE, 'flag_%s' % f)
            if flag_cur == 'true':
                cur_flags = cur_flags + f
            if flag_orig != flag_cur:
                if flag_cur == 'true':
                    true_flags = true_flags + f
                else:
                    false_flags = false_flags + f
        if true_flags != '' or false_flags != '':
            self.ae_model.set_value(self.ae_iter, self.COLUMN_FLAGS, cur_flags)
        set_label = 'false'
        if self.support_partition_name:
            o_label = self.aedialog.get_data(dE, 'o_label')
            label = self.aedialog.get_data(dE, 'label')
            if o_label != label:
                set_label = 'true'
                self.ae_model.set_value(self.ae_iter, self.COLUMN_LABEL, label)
        if true_flags != '' or false_flags != '' or set_label:
            self.tm.add_action(None, self.close_dialog, self.waitdlg(),
                               'set_flags_and_label', self.devfn, self.ae_start,
                               self.str2partflags(true_flags),
                               self.str2partflags(false_flags), set_label, label)

##### Partition Remoe
    def remove_clicked(self, widget, data):
        (model, iter) = \
                self.name_map['partitions_treeview'].get_selection().get_selected()
        if iter:
            part_start = model.get_value(iter, self.COLUMN_START)
            part_start = int(part_start)
            self.tm.add_action(None, self.reload_all_partitions, self.waitdlg(),
                               'delete_partition', self.devfn, part_start)

##### Partition Restore
    def restore_clicked(self, widget, data):
        magicpopup.magicmsgbox( \
            self,
            _('This operation will reload partition table from harddisk. All your custom information will be lost.'),
            magicpopup.magicmsgbox.MB_WARNING,
            magicpopup.magicpopup.MB_OK | magicpopup.magicpopup.MB_CANCEL,
            'restore_confirm_')

    def restore_confirm_ok_clicked(self, button, dlg):
        self.part_addon_infor = {}
        self.added_part_start = {}
        dlg.topwin.destroy()
        self.orig_partitions = None
        self.tm.add_action(None, self.reload_all_partitions, self.waitdlg(),
                           'reload_partition_table', self.devfn)

##### Disk Label 
    def newlabel_clicked(self, widget, data):
        cur_disktype = self.disklabel
        if cur_disktype == 'N/A':
            default_disktype = 'msdos'
        else:
            default_disktype = cur_disktype
        self.tmpdtval_xmldoc = parseString( \
            '<?xml version="1.0"?><nld><origdt>%s</origdt><disktype>%s</disktype></nld>' % \
            (cur_disktype, default_disktype))
        self.newlabel_dlg_topwin = magicpopup.magicpopup( \
            self, self.uixmldoc,
            _('Create an empty new disk label'),
            magicpopup.magicpopup.MB_OK |
            magicpopup.magicpopup.MB_CANCEL,
            'newdisklabel-dlg', 'newlabel_')
        self.newlabel_dlg_topwin.fill_values(self.tmpdtval_xmldoc.documentElement)

    def newlabel_ok_clicked(self, widget, data):
        dE = self.tmpdtval_xmldoc.documentElement
        self.newlabel_dlg_topwin.fetch_values(self.tmpdtval_xmldoc)
        self.disktype = self.newlabel_dlg_topwin.get_data(dE, 'disktype')
        self.newlabel_dlg_topwin.topwin.destroy()
        origdt = self.newlabel_dlg_topwin.get_data(dE, 'origdt')
        if origdt != self.disktype:
            if origdt != 'N/A':
                magicpopup.magicmsgbox( \
                    self,
                    _('This operation will erase the whole partition table when apply.'),
                    magicpopup.magicmsgbox.MB_WARNING,
                    magicpopup.magicpopup.MB_OK | magicpopup.magicpopup.MB_CANCEL,
                    'newlabel_confirm_')
            else:
                self.newlabel_confirm_ok_clicked(widget, data)

    def newlabel_confirm_ok_clicked(self, widget, dlg):
        dlg.topwin.destroy()
        self.part_addon_infor = {} # Clear the addon infor.
        self.added_part_start = {}
        self.orig_partitions = None
        self.tm.add_action(None, self.reload_all_partitions, self.waitdlg(),
                           'disk_new_fresh', self.devfn, self.disktype)

if __name__ == '__main__':
    MIStep_Partition()
