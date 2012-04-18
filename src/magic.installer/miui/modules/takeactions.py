#!/usr/bin/python
import os, gtk, time
from miui.utils import _, Logger
from miui.utils import magicstep, magicpopup, xmlgtk
from miutils.miconfig import MiConfig
from miutils.common import get_devinfo
from games.xglines import xglines
from xml.dom.minidom import parse, parseString
CONF = MiConfig.get_instance()
CONF_DEBUG_MODE = CONF.LOAD.CONF_DEBUG_MODE
CONF_FULL_WIDTH = CONF.LOAD.CONF_FULL_WIDTH
CONF_FULL_HEIGHT = CONF.LOAD.CONF_FULL_HEIGHT

Log = Logger.get_instance(__name__)
dolog = Log.i

class TaDialog(xmlgtk.xmlgtk):
    def __init__(self, upobj, uixml, uirootname=None):
        self.upobj = upobj
        xmlgtk.xmlgtk.__init__(self, uixml, uirootname)
        #self.topwin = gtk.Window(gtk.WINDOW_TOPLEVEL)
        #self.topwin.set_size_request(CONF_FULL_WIDTH, CONF_FULL_HEIGHT)
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
        
class DiscDialog(magicpopup.magicpopup):
    def __init__(self, upobj, uixml, msg, uirootname=None):
        if upobj:
            self.upobj = upobj
        else:
            self.upobj = self
        magicpopup.magicpopup.__init__(self, upobj, uixml,
                                        _('Package not found'), 0,
                                        uirootname)
        self.name_map['msg'].set_text(msg)

    def retry_clicked(self, widget, data):
        ####??? data from whrere
        self.upobj.retry_clicked(widget, data)
        self.topwin.destroy()

    def abort_clicked(self, widget, data):
        self.upobj.abort_clicked(widget, data)
        self.topwin.destroy()

    def reboot_clicked(self, widget, data):
        self.upobj.reboot_clicked(widget, data)
        self.topwin.destroy()

class RpmErrDialog(magicpopup.magicpopup):
    """Rpm install error dialog."""
    def __init__(self, upobj, uixml, msg, uirootname, data):
        if upobj:
            self.upobj = upobj
        else:
            self.upobj = self
        magicpopup.magicpopup.__init__(self, upobj, uixml,
                                        _('Package install error'), 0,
                                        uirootname)
        self.name_map['msg'].set_text(msg)
        self.data = data

    def retry_clicked(self, widget, data):
        (disc_no, pkg_no, asize, is_skip) = self.data
        self.upobj.act_instpkg_pkg_start(-1, (disc_no, pkg_no))
        self.topwin.destroy()

    def skip_clicked(self, widget, data):
        (disc_no, pkg_no, asize, is_skip) = self.data
        self.upobj.act_instpkg_pkg_end(-1, (disc_no, pkg_no, asize, True))
        self.topwin.destroy()

    def reboot_clicked(self, widget, data):
        self.upobj.reboot_clicked(widget, data)
        self.topwin.destroy()

class MIStep_takeactions(magicstep.magicstepgroup):
    def __init__(self, rootobj):
        self.rootobj = rootobj
        magicstep.magicstepgroup.__init__(self, rootobj, 'takeactions.xml',
                                          ['notes', 'ensure', 'doactions'], 'step')
        self.actlist = []
        
        if not CONF_DEBUG_MODE:
            # skip format and mount partition
            self.actlist.append( (_('Partition/Format'), self.act_start_parted, self.act_end_parted) )

        self.actlist.append( (_('Install Package'), self.act_start_instpkg, self.act_end_instpkg) )
        if not CONF_DEBUG_MODE:
            self.actlist.append( (_('Make initrd'), self.act_start_mkinitrd, None) )
            self.actlist.append( (_('Install Bootloader'), self.act_start_bootloader, None) )
        #(_('Setup Keyboard'), self.act_start_keyboard, None)]
        self.actpos = 0
        self.discdlg_open_time = -1
        self.installmode = 'rpminstallmode'   # Default
        self.minorarch_pkgs = []
        self.minorarch_later = False     # push back minor arch packages ### current close this feature.
        self.add_action = self.rootobj.tm.add_action
        
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
        parent = self.left_panel.parent
        parent.remove(self.left_panel)
        self.right_panel = self.tadlg.name_map['rightpanel']
        parent = self.right_panel.parent
        parent.remove(self.right_panel)
        
    def get_label(self):
        return  _('Take Actions')
        
    def get_left_panel(self):
        return self.left_panel
        
    def get_right_panel(self):
        return self.right_panel
        
    def check_enter_doactions(self):
        #### TODO: set the next back button sensitive
        # self.rootobj.btnback_sensitive(False)
        # self.rootobj.btnnext_sensitive(False)
        # Get the Install Mode
        self.fetch_values(self.rootobj.values,
                    valuename_list = ['takeactions.installmode']) 
        instmode = self.get_data(self.values, 'takeactions.installmode')
        
        if instmode == 'copyinstallmode':
            # Copy Install Mode
            self.installmode = 'copyinstallmode'
        elif instmode == 'rpminstallmode':
            # Rpm Install Mode
            self.installmode = 'rpminstallmode'
        
        self.rootobj.cb_push_leftpanel(self.get_left_panel())
        self.rootobj.cb_push_rightpanel(self.get_right_panel())
        
        self.act_enter()
        return 1
        
    def check_leave_doactions(self):
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
        self.tadlg.topwin.destroy()


    def act_start_parted(self):
        self.tadlg.name_map['pfprog'].set_fraction(0)
        self.tadlg.name_map['pkgprog'].set_fraction(0)
        self.tadlg.name_map['otprog'].set_fraction(0)

        self.tadlg.name_map['frame_parted'].set_sensitive(True)
        self.rootobj.tm.push_progress(self.tadlg.name_map['pfprog'],
                                      self.tadlg.name_map['pfname'])
        self.add_action(_('Get all dirty disk'),
                        self.act_parted_get_dirty_result, None,
                        'get_all_dirty_disk', 0)

    def act_parted_get_dirty_result(self, tdata, data):
        self.dirty_disks = tdata
        self.format_list = []
        for devpath in CONF.RUN.g_all_part_infor.keys():
            for part_tuple in CONF.RUN.g_all_part_infor[devpath]:
                if part_tuple[5] == 'true':
                    self.format_list.append((devpath,
                                             part_tuple[3],
                                             part_tuple[6],
                                             part_tuple[0]))
        dolog('self.dirty_disks: %s\n' % str(self.dirty_disks))
        dolog('self.format_list: %s\n' % str(self.format_list))
        self.act_parted_commit_start(0)

    def act_parted_commit_start(self, pos):
        if pos < len(self.dirty_disks):
            actinfor = _('Write the partition table of %s.')
            actinfor = actinfor % self.dirty_disks[pos]
            self.add_action(actinfor, self.act_parted_commit_result, pos,
                            'commit_devpath', self.dirty_disks[pos])
        else:
            self.act_parted_format_start(0)

    def act_parted_commit_result(self, tdata, data):
        result = tdata
        if result:
            # Error occurred. Stop it?
            dolog('commit_result ERROR: %s\n' % str(result))
        self.act_parted_commit_start(data + 1)

    def malcmp(self, c0, c1):
        if c0[0] < c1[0]:    return -1
        elif c0[0] > c1[0]:  return 1
        return 0

    def act_parted_format_start(self, pos):
        if pos < len(self.format_list):
            actinfor = 'Formating %s on %s%d.'
            actinfor = actinfor % (self.format_list[pos][2],
                                   self.format_list[pos][0],
                                   self.format_list[pos][3])
            dolog('format_start: %s\n' % str(actinfor))
            self.add_action(actinfor, self.act_parted_format_result, pos,
                            'format_partition',
                            self.format_list[pos][0], # devpath.
                            self.format_list[pos][1], # part_start.
                            self.format_list[pos][2]) # fstype
        else:
            CONF.RUN.g_mount_all_list = []
            for devpath in CONF.RUN.g_all_part_infor.keys():
                for part_tuple in CONF.RUN.g_all_part_infor[devpath]:
                    if part_tuple[7] == '':  # mountpoint ### TODO
                        continue
                    mntpoint = part_tuple[7]
                    devfn = '%s%d' % (devpath, part_tuple[0])
                    fstype = part_tuple[6]
                    CONF.RUN.g_mount_all_list.append((mntpoint, devfn, fstype))
            CONF.RUN.g_mount_all_list.sort(self.malcmp)
            dolog('CONF.RUN.g_mount_all_list: %s\n' % str(CONF.RUN.g_mount_all_list))
            #self.add_action(_('Mount all target partitions.'),
                            #self.nextop, None,
                            #'mount_all_tgtpart', CONF.RUN.g_mount_all_list, 'y')
            self.nextop(None, None)
                            
            #### Because we can mount device many times, so we not check below
            ## Check whether the packages are stored in mounted partitions.
            #pkgmntpoint = 0
            #(pafile, dev, fstype, dir, isofn) = CONF.RUN.g_choosed_patuple
            #for (mntpoint, devfn, fstype) in CONF.RUN.g_mount_all_list:
                #if dev == devfn:
                    #pkgmntpoint = mntpoint
                    #if len(pkgmntpoint) > 0 and pkgmntpoint[0] == '/':
                        #pkgmntpoint = pkgmntpoint[1:]
                    #CONF.RUN.g_choosed_patuple = (pafile, dev, pkgmntpoint,
                                       #fstype, dir, isofn)
                    #dolog('The packages is placed in the mounted partition(%s)\n' %\
                          #pkgmntpoint)
                    #break

    def act_parted_format_result(self, tdata, data):
        result = tdata
        if result:
            # Error occurred. Stop it?
            # Yes, we should stop it, and we should stop at mount failed place too.
            dolog('format_result ERROR: %s\n' % str(result))
            magicpopup.magicmsgbox(None, _('Format Partition Error: %s' % result),
                       magicpopup.magicmsgbox.MB_ERROR,
                       magicpopup.magicpopup.MB_OK)
            #self.rootobj.btnback_do()
        self.act_parted_format_start(data + 1)

    def act_end_parted(self):
        self.rootobj.tm.pop_progress()
        self.tadlg.name_map['pfname'].set_text('')
        self.tadlg.name_map['pfprog'].set_fraction(1)
        self.tadlg.name_map['frame_parted'].set_sensitive(False)

    def pkg2archpkg(self, pkg):
        (disc_no, pkg_no) = CONF.RUN.g_pkgpos_map[pkg]
        pkgarchmap = {}
        pkgpathes = CONF.RUN.g_arrangement[disc_no][pkg_no][4] # pkgpublic.pathes == 4.
        for (apkg, aarch, asize) in pkgpathes:
            if aarch == 'noarch':
                return (apkg, aarch, asize)
            pkgarchmap[aarch] = (apkg, aarch, asize)
        for a in self.archcompat_list:
            if pkgarchmap.has_key(a):
                return pkgarchmap[a]
        # It is an error to reach here!!!
        dolog('Unresolved package: pkg = %s, pkgarchmap = %s, archcompat_list = %s\n' % (pkg, str(pkgarchmap), str(self.archcompat_list)))

    def calc_instpkg_map(self):
        datanode = self.srh_data_node(self.values, 'package.choosedgroup')
        choosed_list = []
        self.totalsize = 0
        self.install_allpkg = None
        self.disc_map = {}
        self.instpkg_map = {}
        for selnode in datanode.getElementsByTagName('select'):
            thisid = selnode.getAttribute('id')
            if thisid == 'ALL':
                self.install_allpkg = 1
                self.totalsize = CONF.RUN.g_archsize_map[self.arch]
                break
            choosed_list.append(thisid)
        if self.install_allpkg:
            self.totalpkg = len(CONF.RUN.g_pkgpos_map.keys())
            return
        for grp in ['lock'] + choosed_list:
            if not CONF.RUN.g_toplevelgrp_map.has_key(grp):
                # Omit the invalid group name.
                continue
            for pkg in CONF.RUN.g_toplevelgrp_map[grp].keys():
                if not self.instpkg_map.has_key(pkg):
                    (apkg, aarch, asize) = self.pkg2archpkg(pkg)
                    self.disc_map[CONF.RUN.g_pkgpos_map[pkg][0]] = 'y'
                    self.instpkg_map[pkg] = 'y'
                    self.totalsize = self.totalsize + asize
        self.totalpkg = len(self.instpkg_map.keys())
        
############################ install package ###################################
##### Start install package
    def act_start_instpkg(self):
        self.tadlg.name_map['frame_packages'].set_sensitive(True)
        self.rootobj.tm.push_progress(self.tadlg.name_map['pkgprog'],
                                      self.tadlg.name_map['pkgname'])
        self.arch = self.rootobj.tm.actserver.get_arch()
        self.archcompat_list = CONF.RUN.g_arch_map[self.arch]
        dolog('Detected Arch: %s\n' % str(self.arch))
        self.calc_instpkg_map()
        dolog('install_allpkg = %s\n' % str(self.install_allpkg))
        self.disc_first_pkgs = []
        for disc_no in range(len(CONF.RUN.g_arrangement)):
            self.disc_first_pkgs.append(CONF.RUN.g_arrangement[disc_no][0][1])
        (pafile, dev, fstype, reldir, bootiso_relpath) = CONF.RUN.g_choosed_patuple
        dolog('disc_first_pkgs: %s\n' % str(self.disc_first_pkgs))
        self.add_action(_('Search packages'),
                        self.act_instpkg_prepare, None,
                        'probe_all_disc', dev, fstype, bootiso_relpath, reldir, self.disc_first_pkgs)

    def szfmt(self, sz):
        return '%0.2fM' % (sz / 1024.0 / 1024.0)

    def tmfmt(self, tmdiff):
        h = int(tmdiff / 3600)
        m = int(tmdiff / 60) % 60
        s = int(tmdiff) % 60
        return '%02d:%02d:%02d' % (h, m, s)

    def act_instpkg_prepare(self, tdata, data):
        self.probe_all_disc_result = tdata
        dolog('probe_all_disc_result: %s\n' % str(self.probe_all_disc_result))
        (pafile, dev, fstype, reldir, bootiso_relpath) = CONF.RUN.g_choosed_patuple
        self.donepkg = 0
        self.cursize = 0
        self.starttime = time.time()

        self.tadlg.name_map['totalpkg'].set_text(str(self.totalpkg))
        self.tadlg.name_map['donepkg'].set_text(str(self.donepkg))
        self.tadlg.name_map['remainpkg'].set_text(str(self.totalpkg))
        self.tadlg.name_map['totalsize'].set_text(self.szfmt(self.totalsize))
        self.tadlg.name_map['donesize'].set_text(self.szfmt(0))
        self.tadlg.name_map['remainsize'].set_text(self.szfmt(self.totalsize))
        self.tadlg.name_map['totaltime'].set_text('--:--:--')
        self.tadlg.name_map['elapsed'].set_text('--:--:--')
        self.tadlg.name_map['remaintime'].set_text('--:--:--')

        self.add_action(None,
                        self.act_instpkg_disc_start, 0,
                        'instpkg_prep', (dev, fstype, bootiso_relpath, reldir), 
                                        self.installmode, 
                                        { '/': (CONF.RUN.g_root_device, get_devinfo(CONF.RUN.g_root_device, CONF.RUN.g_all_part_infor).fstype),
                                          '/boot': (CONF.RUN.g_boot_device, get_devinfo(CONF.RUN.g_boot_device, CONF.RUN.g_all_part_infor).fstype),
                                          'swap': (CONF.RUN.g_swap_device, get_devinfo(CONF.RUN.g_swap_device, CONF.RUN.g_all_part_infor).fstype),
                                          },
                        )

    def act_instpkg_disc_start(self, tdata, disc_no):
        if tdata != 0:
            pass #### occur error, tdata is the error msg
        if self.discdlg_open_time > 0:
            # Do adjustment to omit the influence of replace disc.
            self.starttime = self.starttime + \
                             (time.time() - self.discdlg_open_time)
            self.discdlg_open_time = -1
        (pafile, dev, fstype, reldir, bootiso_relpath) =  CONF.RUN.g_choosed_patuple
        while disc_no < len(CONF.RUN.g_arrangement):
            if not self.install_allpkg and not self.disk_map.has_key(disc_no):
                # Skip the disc which is not needed.
                disc_no = disc_no + 1
                continue
            dolog("probe_all_disc_result: %s" % self.probe_all_disc_result)
            if disc_no >= len(self.probe_all_disc_result) \
                   or not self.probe_all_disc_result[disc_no]:
                #### multi disc, whether it can get here???
                self.cur_disc_no = disc_no
                msgtxt = _("Can't find packages in disc %d.\nIf you are using CDROM to install system, it is the chance to eject the original disc and insert the %d disc.")
                msgtxt = msgtxt % (disc_no + 1, disc_no + 1)
                self.discdlg_open_time = time.time()
                DiscDialog(self, self.uixmldoc, msgtxt, 'disc.dialog')
                return
            bootiso_relpath = self.probe_all_disc_result[disc_no][0]
            self.add_action(None,
                            self.act_instpkg_pkg_start, (disc_no, 0),
                            'instpkg_disc_prep', dev, reldir, fstype, bootiso_relpath)
            return
        self.add_action(_('Last operations for package installation'),
                        self.nextop, None,
                        'instpkg_post', dev, reldir, fstype)
                        
    def act_instpkg_pkg_start(self, tdata, data):
        if tdata != 0:
            pass #### TODO: handle the result error msg.
        (disc_no, pkg_no) = data
        while pkg_no < len(CONF.RUN.g_arrangement[disc_no]):
            pkgtuple = CONF.RUN.g_arrangement[disc_no][pkg_no]
            #noscripts = pkgtuple[6]     # pkgpublic.noscripts == 6.
            noscripts = False   #### noscripts get out of range
            #-> noscripts = pkgtuple[6]     # pkgpublic.noscripts == 6.
            #(Pdb) print pkgtuple
            #[118253L, 'nss-softokn-freebl-3.13.3-1mgc30.i686.rpm', ['System Environment', 'Base'], ['glibc-2.15-1mgc30.i686.rpm'], [['./nss-softokn-freebl-3.13.3-1mgc30.i686.rpm', 'i686', 118253L]]]
            #(Pdb) print len(pkgtuple)
            #5

            if self.install_allpkg or self.instpkg_map.has_key(pkgtuple[1]):
                archpkg = self.pkg2archpkg(pkgtuple[1])
                if not archpkg:
                    data = (disc_no, pkg_no, 0, False)
                    msg = _("Target System Arch %s is not Compatible with package arch %s" % (self.arch, pkgtuple[1]))
                    RpmErrDialog(self, self.uixmldoc, msg, 'rpmerr.dialog', data)
                    return
                (apkg, aarch, asize) = archpkg
                if self.minorarch_later and aarch != "noarch" and aarch != self.arch:
                    self.minorarch_pkgs.append((apkg, aarch, asize))
                    pkg_no = pkg_no + 1
                    continue
                apkg = os.path.basename(apkg)
                self.add_action(apkg,
                                self.act_instpkg_pkg_end, (disc_no, pkg_no, asize, False),
                                'package_install', apkg, self.probe_all_disc_result[disc_no][1],
                                noscripts)
                return
            pkg_no = pkg_no + 1
        if self.minorarch_later and self.minorarch_pkgs:
            (apkg, aarch, asize) = self.minorarch_pkgs.pop(0)
            self.add_action(apkg,
                            self.act_instpkg_pkg_end, (disc_no, pkg_no, asize, False),
                            'package_install', apkg, self.probe_all_disc_result[disc_no][1],
                            noscripts)
            return
        (pafile, dev, fstype, reldir, bootiso_relpath) = CONF.RUN.g_choosed_patuple
        self.add_action(None,
                        self.act_instpkg_disc_start, disc_no + 1,
                        'instpkg_disc_post', dev, fstype, reldir, bootiso_relpath, self.probe_all_disc_result[disc_no][1])

    def act_instpkg_pkg_end(self, tdata, data):
        #--- FIXME ---
        # It doesn't check the result of package_install now, but it should...
        # It should popup an dialog to let the user choose 'continue' or
        #  'abandon' the installation.
        (disc_no, pkg_no, asize, is_skip) = data

        if not is_skip:
            res = tdata
            if res != 0:
                RpmErrDialog(self, self.uixmldoc, res, 'rpmerr.dialog', data)
                return

        self.donepkg = self.donepkg + 1
        self.cursize = self.cursize + asize
        remainsize = self.totalsize - self.cursize
        elapsed = time.time() - self.starttime
        self.tadlg.name_map['donepkg'].set_text(str(self.donepkg))
        self.tadlg.name_map['remainpkg'].set_text(str(self.totalpkg - self.donepkg))
        self.tadlg.name_map['donesize'].set_text(self.szfmt(self.cursize))
        self.tadlg.name_map['remainsize'].set_text(self.szfmt(remainsize))
        self.tadlg.name_map['elapsed'].set_text(self.tmfmt(elapsed))
        if elapsed < 60:
            self.tadlg.name_map['totaltime'].set_text('--:--:--')
            self.tadlg.name_map['remaintime'].set_text('--:--:--')
        else:
            self.tadlg.name_map['totaltime'].set_text(self.tmfmt(elapsed * self.totalsize / self.cursize))
            self.tadlg.name_map['remaintime'].set_text(self.tmfmt(elapsed * remainsize / self.cursize))
        self.tadlg.name_map['topprog'].set_fraction(float(self.cursize)/float(self.totalsize))
        self.tadlg.name_map['pkgprog'].set_fraction(1)
        self.act_instpkg_pkg_start(tdata, (disc_no, pkg_no + 1))

    def act_end_instpkg(self):
        self.rootobj.tm.pop_progress()
        self.tadlg.name_map['pkgname'].set_text('')
        self.tadlg.name_map['pkgprog'].set_fraction(1)
        self.tadlg.name_map['frame_packages'].set_sensitive(False)
##### End install package
    def act_start_mkinitrd(self):
        self.tadlg.name_map['frame_other'].set_sensitive(True)
        self.rootobj.tm.push_progress(self.tadlg.name_map['otprog'],
                                      self.tadlg.name_map['otname'])
        scsi_module_list = self.get_data(self.values, 'scsi.modules')
        if scsi_module_list == None or scsi_module_list == '':
            dolog('No scsi driver has to be written into modprobe.conf.\n')
        else:
            dolog('scsi_modprobe_conf(%s)\n' % scsi_module_list)
            self.add_action(_("Generate modprobe.conf"), None, None,
                            'scsi_modprobe_conf', scsi_module_list)
        dolog('action_mkinitrd\n')
        self.add_action(_('Make initrd'), self.nextop, None, 'do_mkinitrd', 0)
############################ Bootloader ###################################
    def act_start_bootloader(self):
        bltype = self.get_data(self.values, 'bootloader.bltype')
        instpos = self.get_data(self.values, 'bootloader.instpos')
        mbr_device = self.get_data(self.values, 'bootloader.mbr_device')
        win_device = self.get_data(self.values, 'bootloader.win_device')
        dolog('action_bootloader: bltype = %s\n' % bltype)
        if bltype == 'none':
            self.add_action(None, self.nextop, None, 'sleep', 0)
            return
        if CONF.RUN.g_root_device == CONF.RUN.g_boot_device:
            bootdev = ''
        else:
            bootdev = CONF.RUN.g_boot_device
        if win_device:
            win_fs = get_devinfo(win_device, CONF.RUN.g_all_part_infor).fstype
        else:
            win_fs = ''
        timeout = int(float(self.get_data(self.values, 'bootloader.timeout')))
        usepassword = self.get_data(self.values, 'bootloader.usepassword')
        password = self.get_data(self.values, 'bootloader.password')
        lba = self.get_data(self.values, 'bootloader.lba')
        options = self.get_data(self.values, 'bootloader.options')
        entries = []
        elnode = self.srh_data_node(self.values, 'bootloader.entrylist')
        for node in elnode.getElementsByTagName('row'):
            entries.append((node.getAttribute('c1'),
                            node.getAttribute('c2'),
                            node.getAttribute('c3')))
        default = self.get_data(self.values, 'bootloader.default')
        dolog('%s\n' % str(('setup_' + bltype, timeout, usepassword,
                            password, lba, options, entries, default,
                            instpos, bootdev, mbr_device, win_device, win_fs)))
        #### TODO: add clean server operate.
        
        self.add_action(_('Prepare bootloader'), self.bl_umount, bltype,
                        'prepare_' + bltype, timeout, usepassword, password,
                        lba, options, entries, default, instpos, bootdev, mbr_device, win_device, win_fs)
        ### TODO: real do self.bl_setup() and support grub2
        ### and then do nextop.

    def bl_umount(self, tdata, data):
        res = tdata
        if type(res) == types.IntType:
            self.add_action(None, self.nextop, None, 'sleep', 0)
            return
        self.add_action(_('Umount all target partitions before bootloader setup.'),
                        self.bl_setup, (data, res),
                        'umount_all_tgtpart', CONF.RUN.g_mount_all_list, 0)

    def bl_setup(self, tdata, data):
        (bltype, (grubdev, grubsetupdev, grubopt)) = data
        self.add_action(_('Setup bootloader'), None, None,
                        'setup_' + bltype, grubdev, grubsetupdev, grubopt)

    def nextop(self, tdata, data):
        if tdata:
            result = tdata
            if result:
                # Error occurred. Stop it?
                dolog('ERROR: %s\n' % str(result))

        dolog('nextop\n')
        self.act_leave()
        
############################ Ghraphic Button Action ###################################

    def retry_clicked(self, widget, data):
        (pafile, dev, fstype, reldir, bootiso_relpath) = CONF.RUN.g_choosed_patuple
        self.add_action(_('Researching packages...'),
                        self.reprobe_all_disc_0, None,
                        'instpkg_post', dev, reldir, fstype)
        
    def reprobe_all_disc_0(self, tdata, data):
        (pafile, dev, fstype, reldir, bootiso_relpath) = CONF.RUN.g_choosed_patuple
        self.add_action(_('Researching packages...'),
                        self.reprobe_all_disc_1, None,
                        'probe_all_disc', dev, reldir, fstype, self.disc_first_pkgs)

    def reprobe_all_disc_1(self, tdata, data):
        (errmsg, self.probe_all_disc_result) = tdata
        dolog('probe_all_disc_result: %s\n' % str(self.probe_all_disc_result))
        (pafile, dev, fstype, reldir, bootiso_relpath) = CONF.RUN.g_choosed_patuple
        self.add_action(_('Researching packages...'),
                        self.act_instpkg_disc_start, self.cur_disc_no,
                        'instpkg_prep', dev, reldir, fstype, self.installmode)

    def abort_clicked(self, widget, data):
        (pafile, dev, fstype, reldir, bootiso_relpath) = CONF.RUN.g_choosed_patuple
        self.add_action(_('Aborting...'),
                        self.nextop, None,
                        'instpkg_post', dev, reldir, fstype)

    def reboot_clicked(self, widget, data):
        (pafile, dev, fstype, reldir, bootiso_relpath) = CONF.RUN.g_choosed_patuple
        msg = _('Umount the target filesystem(s).')
        self.add_action(msg, None, None,
                        'instpkg_post', dev, mntpoint, reldir, fstype)                         #### TODO: mntpoint
        #### TODO Add an clean server operator
        #self.add_action(msg, self.reboot_0, None,
                        #'umount_all_tgtpart', CONF.RUN.g_mount_all_list, 'y')
        reboot_0(None, None)

    def reboot_0(self, tdata, data):
        self.rebootdlg = \
                       magicpopup.magicmsgbox(self,
                                              _('Click "OK" to reboot your system!\nEject the cdrom if you are installed from cdrom.'),
                                              magicpopup.magicmsgbox.MB_ERROR,
                                              magicpopup.magicpopup.MB_OK,
                                              'reboot_0_')

    def reboot_0_ok_clicked(self, widget, data):
        self.add_action('Quit', None, None, 'quit', 0)
        self.rebootdlg.topwin.destroy()

def TestTaDialog():
    import gtk
    from miutils.common import search_file
    import gtk
    uixml_file = 'takeactions.xml'
    uixml_path = search_file( uixml_file,
                              [CONF.LOAD.CONF_HOTFIXDIR, '.'],
                              postfix = 'UIxml')
    uixmldoc = parse(uixml_path)
    tadlg = TaDialog(None, uixmldoc, 'actions.dialog')
    tadlg.name_map['otname'].set_text('')
    tadlg.name_map['otprog'].set_fraction(1)
    tadlg.name_map['frame_other'].set_sensitive(False)
    #import pdb; pdb.set_trace()
    #tadlg.topwin.destroy()
    gtk.main()
        
def TestMIStep_takeactions():
    import gtk
    from mitest import TestMIStep
    win = TestMIStep(gtk.WINDOW_TOPLEVEL)
    h = MIStep_takeactions(win)
    win.add_mistep(h)
    win.show_all()
    gtk.main()
    
if __name__ == '__main__':
    TestMIStep_takeactions()
    