
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
    """Rpm install error dialogger."""
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
    

class InstallRpmActions(object):
    def __init__(self, rootobj):
        self.rootobj = rootobj
        self.actlist = []

        self.actlist.append( (_('Install Package'), self.act_start_instpkg, self.act_end_instpkg) )
        #(_('Setup Keyboard'), self.act_start_keyboard, None)]
        self.actpos = 0
        self.discdlg_open_time = -1
        self.installmode = 'rpminstallmode'   # Default
        self.minorarch_pkgs = []
        self.minorarch_later = False     # push back minor arch packages ### current close this feature.
        self.add_action = self.rootobj.tm.add_action

############################ install package ###################################
##### Start install package

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
        (pafile, dev, fstype, reldir, bootiso_relpath) = CF.G.choosed_patuple
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
                                        { '/': (CF.G.root_device, get_devinfo(CF.G.root_device, CF.G.all_part_infor).fstype),
                                          '/boot': (CF.G.boot_device, get_devinfo(CF.G.boot_device, CF.G.all_part_infor).fstype),
                                          'swap': (CF.G.swap_device, get_devinfo(CF.G.swap_device, CF.G.all_part_infor).fstype),
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
        (pafile, dev, fstype, reldir, bootiso_relpath) =  CF.G.choosed_patuple
        while disc_no < len(CF.G.arrangement):
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
        while pkg_no < len(CF.G.arrangement[disc_no]):
            pkgtuple = CF.G.arrangement[disc_no][pkg_no]
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
        (pafile, dev, fstype, reldir, bootiso_relpath) = CF.G.choosed_patuple
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

###################### ################################################################ ################

    def pkg2archpkg(self, pkg):
        (disc_no, pkg_no) = CF.G.pkgpos_map[pkg]
        pkgarchmap = {}
        pkgpathes = CF.G.arrangement[disc_no][pkg_no][4] # pkgpublic.pathes == 4.
        for (apkg, aarch, asize) in pkgpathes:
            if aarch == 'noarch':
                return (apkg, aarch, asize)
            pkgarchmap[aarch] = (apkg, aarch, asize)
        for a in self.archcompat_list:
            if pkgarchmap.has_key(a):
                return pkgarchmap[a]
        # It is an error to reach here!!!
        logger.e('Unresolved package: pkg = %s, pkgarchmap = %s, archcompat_list = %s\n' % (pkg, str(pkgarchmap), str(self.archcompat_list)))

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
                self.totalsize = CF.G.archsize_map[self.arch]
                break
            choosed_list.append(thisid)
        if self.install_allpkg:
            self.totalpkg = len(CF.G.pkgpos_map.keys())
            return        for (apkg, aarch, asize) in pkgpathes:
            if aarch == 'noarch':
                return (apkg, aarch, asize)
            pkgarchmap[aarch] = (apkg, aarch, asize)
        for a in self.archcompat_list:
            if pkgarchmap.has_key(a):
                return pkgarchmap[a]
        # It is an error to reach here!!!
        logger.e('Unresolved package: pkg = %s, pkgarchmap = %s, archcompat_list = %s\n' % (pkg, str(pkgarchmap), str(self.archcompat_list)))

        for grp in ['lock'] + choosed_list:
            if not CF.G.toplevelgrp_map.has_key(grp):
                # Omit the invalid group name.
                continue
            for pkg in CF.G.toplevelgrp_map[grp].keys():
                if not self.instpkg_map.has_key(pkg):
                    (apkg, aarch, asize) = self.pkg2archpkg(pkg)
                    self.disc_map[CF.G.pkgpos_map[pkg][0]] = 'y'
                    self.instpkg_map[pkg] = 'y'
                    self.totalsize = self.totalsize + asize
        self.totalpkg = len(self.instpkg_map.keys())
        
############################ Ghraphic Button Action ###################################

    def retry_clicked(self, widget, data):
        (pafile, dev, fstype, reldir, bootiso_relpath) = CF.G.choosed_patuple
        self.add_action(_('Researching packages...'),
                        self.reprobe_all_disc_0, None,
                        'instpkg_post', dev, reldir, fstype)
        
    def reprobe_all_disc_0(self, tdata, data):
        (pafile, dev, fstype, reldir, bootiso_relpath) = CF.G.choosed_patuple
        self.add_action(_('Researching packages...'),
                        self.reprobe_all_disc_1, None,
                        'probe_all_disc', dev, reldir, fstype, self.disc_first_pkgs)

    def reprobe_all_disc_1(self, tdata, data):
        (errmsg, self.probe_all_disc_result) = tdata
        dolog('probe_all_disc_result: %s\n' % str(self.probe_all_disc_result))
        (pafile, dev, fstype, reldir, bootiso_relpath) = CF.G.choosed_patuple
        self.add_action(_('Researching packages...'),
                        self.act_instpkg_disc_start, self.cur_disc_no,
                        'instpkg_prep', dev, reldir, fstype, self.installmode)

    def abort_clicked(self, widget, data):
        (pafile, dev, fstype, reldir, bootiso_relpath) = CF.G.choosed_patuple
        self.add_action(_('Aborting...'),
                        self.nextop, None,
                        'instpkg_post', dev, reldir, fstype)

    def reboot_clicked(self, widget, data):
        (pafile, dev, fstype, reldir, bootiso_relpath) = CF.G.choosed_patuple
        msg = _('Umount the target filesystem(s).')
        self.add_action(msg, None, None,
                        'instpkg_post', dev, reldir, fstype)                         #### TODO: mntpoint
        #### TODO Add an clean server operator
        #self.add_action(msg, self.reboot_0, None,
                        #'umount_all_tgtpart', CF.G.mount_all_list, 'y')
        self.reboot_0(None, None)

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
