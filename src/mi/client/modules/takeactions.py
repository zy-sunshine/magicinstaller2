#!/usr/bin/python
import os, gtk, time
from mi.client.utils import _
from mi.client.utils import magicstep, magicpopup, xmlgtk
from mi.utils.common import get_devinfo
from mi.games.xglines import xglines
from xml.dom.minidom import parse, parseString

from mi.client.utils import logger, CF

class DiscDialog(magicpopup.magicpopup):
    def __init__(self, upobj, uixml, msg, uirootname=None):
        self.upobj = upobj
        magicpopup.magicpopup.__init__(self, upobj, uixml,
                                        _('Package not found'), 0,
                                        uirootname)
        self.name_map['msg'].set_text(msg)

    def retry_clicked(self, widget, data):
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
    def __init__(self, sself, uixml, msg, uirootname):
        self.sself = sself
        magicpopup.magicpopup.__init__(self, sself, uixml,
                                        _('Package install error'), 0,
                                        uirootname)
        self.name_map['msg'].set_text(msg)

    def retry_clicked(self, widget, data):
        self.sself.retry_clicked(widget, data)
        self.topwin.destroy()

    def skip_clicked(self, widget, data):
        self.sself.skip_clicked(widget, data)
        self.topwin.destroy()

    def reboot_clicked(self, widget, data):
        self.sself.reboot_clicked(widget, data)
        self.topwin.destroy()
    
class MIStep_takeactions(magicstep.magicstep):
    NAME = 'takeactions'
    LABEL = _('Take Actions')
    def __init__(self, rootobj):
        magicstep.magicstep.__init__(self, rootobj, 'takeactions.xml', 'actions')
        self.rootobj = rootobj
        self.started = False
        self.arch = None
        self.tm = self.rootobj.tm
        self.add_action = self.rootobj.tm.add_action
        
        self.discdlg_open_time = -1 # user change disc time, omit it from package installation time.
        self.totalpkg = 0
        self.totalsize = 0
        self.install_finished = False
        self.install_progress_hooked = False
        self.setup_finished = False
        self.entered = False
        
    def get_label(self):
        return self.LABEL
    
    def gather_setup_information(self):
        # Get account information
        CF.ACCOUNT.rootpasswd = self.get_data(self.values, 'accounts.root.password')
        CF.ACCOUNT.acclist = []
        accnode = self.srh_data_node(self.values, 'accounts.userlist')
        for node in accnode.getElementsByTagName('row'):
            CF.ACCOUNT.acclist.append((node.getAttribute('c0'), # Username.
                            node.getAttribute('c1'), # Password.
                            node.getAttribute('c2'), # Shell.
                            node.getAttribute('c3'), # Home directory.
                            node.getAttribute('c4'))) # Real UID or 'Auto'.
        logger.i('takeactions setup_accounts %s' % str((CF.ACCOUNT.rootpasswd, CF.ACCOUNT.acclist)))
 
        # Get bootloader information
        CF.BOOTLDR.bltype = self.get_data(self.values, 'bootloader.bltype')
        CF.BOOTLDR.instpos = self.get_data(self.values, 'bootloader.instpos')
        CF.BOOTLDR.mbr_device = self.get_data(self.values, 'bootloader.mbr_device')
        CF.BOOTLDR.win_device = self.get_data(self.values, 'bootloader.win_device')
        if CF.BOOTLDR.bltype == 'none':
            logger.i('takeactions get bootloader: bltype %s' % self.bltype)
        else:
            if CF.G.root_device == CF.G.boot_device:
                CF.BOOTLDR.bootdev = ''
            else:
                CF.BOOTLDR.bootdev = CF.G.boot_device
            if CF.BOOTLDR.win_device:
                CF.BOOTLDR.win_fs = get_devinfo(CF.BOOTLDR.win_device, CF.G.all_part_infor).fstype
            else:
                CF.BOOTLDR.win_fs = ''
            CF.BOOTLDR.timeout = int(float(self.get_data(self.values, 'bootloader.timeout')))
            CF.BOOTLDR.usepassword = self.get_data(self.values, 'bootloader.usepassword')
            CF.BOOTLDR.password = self.get_data(self.values, 'bootloader.password')
            CF.BOOTLDR.lba = self.get_data(self.values, 'bootloader.lba')
            CF.BOOTLDR.options = self.get_data(self.values, 'bootloader.options')
            CF.BOOTLDR.entries = []
            elnode = self.srh_data_node(self.values, 'bootloader.entrylist')
            for node in elnode.getElementsByTagName('row'):
                CF.BOOTLDR.entries.append((node.getAttribute('c1'),
                                node.getAttribute('c2'),
                                node.getAttribute('c3')))
            self.default = self.get_data(self.values, 'bootloader.default')
            logger.i('takeactions get bootloader: %s' % str(('setup_' + CF.BOOTLDR.bltype, CF.BOOTLDR.timeout, CF.BOOTLDR.usepassword,
                                CF.BOOTLDR.password, CF.BOOTLDR.lba, CF.BOOTLDR.options, CF.BOOTLDR.entries, CF.BOOTLDR.default,
                                CF.BOOTLDR.instpos, CF.BOOTLDR.bootdev, CF.BOOTLDR.mbr_device, CF.BOOTLDR.win_device, CF.BOOTLDR.win_fs)))
        
    def enter(self):
        self.entered= True
        if not self.started:
            self.start_install()
            self.rootobj.btnnext_sensitive(False)
            self.rootobj.btnback_sensitive(False)
        if not self.install_finished:
            if not self.install_progress_hooked:
                self.tm.push_progress(self.name_map['pkgprog'],
                                      self.name_map['pkgname'])
                self.install_progress_hooked = True
        self.gather_setup_information()
        return 1
    
    def leave(self):
        if not self.install_finished:
            return 0
        elif not self.setup_finished:
            self.rootobj.btnnext_sensitive(False)
            self.name_map['frame_other'].set_sensitive(True)
            self.rootobj.tm.push_progress(self.name_map['otprog'],
                                          self.name_map['otname'])
            # make initrd
            scsi_module_list = self.get_data(self.values, 'scsi.modules')
            if scsi_module_list == None or scsi_module_list == '':
                logger.w('No scsi driver has to be written into modprobe.conf.\n')
            else:
                logger.i('scsi_modprobe_conf(%s)\n' % scsi_module_list)
                self.add_action(_("Generate modprobe.conf"), None, None,
                                'scsi_modprobe_conf', scsi_module_list)
            logger.i('action_mkinitrd\n')
            self.add_action(_('Make initrd'), None, None, 'do_mkinitrd', 0)
            
            # set bootloader
            self.add_action(_('Prepare bootloader'), None, None,
                            'prepare_' + CF.BOOTLDR.bltype, CF.BOOTLDR.timeout, CF.BOOTLDR.usepassword, CF.BOOTLDR.password,
                            CF.BOOTLDR.lba, CF.BOOTLDR.options, CF.BOOTLDR.entries, CF.BOOTLDR.default, CF.BOOTLDR.instpos, 
                            CF.BOOTLDR.bootdev, CF.BOOTLDR.mbr_device, CF.BOOTLDR.win_device, CF.BOOTLDR.win_fs)    
            # setup account
            logger.i('action_accounts')
            self.rootobj.tm.add_action(_('Setup accounts'), None, None,
                                       'setup_accounts', CF.ACCOUNT.rootpasswd, CF.ACCOUNT.acclist)
            # run post install script
            self.tm.add_action(_('Run post install script'), self.do_setup_finished, None,
                                   'run_post_install', 0)    
            return 0
        if not self.entered:
            return 0
        return 1

    def do_setup_finished(self, tdata, data):
        self.tm.pop_progress()
        self.setup_finished = True
        self.name_map['otname'].set_text('')
        self.name_map['otprog'].set_fraction(1)
        self.name_map['frame_other'].set_sensitive(False)
        self.rootobj.btnnext_sensitive(True)
        print self.rootobj.get_cur_stepobj() == self
        print self.rootobj.get_cur_stepobj(), self
        if self.rootobj.get_cur_stepobj() == self: # If user at the current page, we do next step automatically.
            self.rootobj.btnnext_clicked(None, None)
        
    def start_install(self):
        self.name_map['frame_packages'].set_sensitive(True)
        self.donepkg = 0
        self.cursize = 0
        self.starttime = time.time()
        if CF.D.PKGTYPE == 'rpm':     # In the mipublic.py
            # install rpm
            from mi.client.modules.actions.installrpm import MiAction_InstallRpm
            instrpm_action = MiAction_InstallRpm(self)
            instrpm_action.prepare()
            self.totalpkg = instrpm_action.get_package_count()
            self.totalsize = instrpm_action.get_package_size()

            instrpm_action.start()
            #from mi.client.modules.actions.probedisc import ProbeDisc
            #probeDisc = ProbeDisc()
        elif CF.D.PKGTYPE == 'rpmrepo':
            # install rpm repo
            # rpm must in one repo, and it has no multiple disc. haha.
            pass
        elif CF.D.PKGTYPE == 'tar':
            pass

        self.name_map['totalpkg'].set_text(str(self.totalpkg))
        self.name_map['donepkg'].set_text(str(self.donepkg))
        self.name_map['remainpkg'].set_text(str(self.totalpkg))
        self.name_map['totalsize'].set_text(self.szfmt(self.totalsize))
        self.name_map['donesize'].set_text(self.szfmt(0))
        self.name_map['remainsize'].set_text(self.szfmt(self.totalsize))
        self.name_map['totaltime'].set_text('--:--:--')
        self.name_map['elapsed'].set_text('--:--:--')
        self.name_map['remaintime'].set_text('--:--:--')
        
        self.started = True
        
    def cb0_install_pkg_end(self, disc_no, pkg_no, asize):
        self.donepkg = self.donepkg + 1
        self.cursize = self.cursize + asize

        remainsize = self.totalsize - self.cursize
        elapsed = time.time() - self.starttime
        self.name_map['donepkg'].set_text(str(self.donepkg))
        self.name_map['remainpkg'].set_text(str(self.totalpkg - self.donepkg))
        self.name_map['donesize'].set_text(self.szfmt(self.cursize))
        self.name_map['remainsize'].set_text(self.szfmt(remainsize))
        self.name_map['elapsed'].set_text(self.tmfmt(elapsed))
        if elapsed < 60:
            self.name_map['totaltime'].set_text('--:--:--')
            self.name_map['remaintime'].set_text('--:--:--')
        else:
            self.name_map['totaltime'].set_text(self.tmfmt(elapsed * self.totalsize / self.cursize))
            self.name_map['remaintime'].set_text(self.tmfmt(elapsed * remainsize / self.cursize))
        self.name_map['topprog'].set_fraction(float(self.cursize)/float(self.totalsize))
        self.name_map['pkgprog'].set_fraction(1)
    
    def cb0_install_end(self):
        self.rootobj.tm.pop_progress()
        self.name_map['pkgname'].set_text('')
        self.name_map['pkgprog'].set_fraction(1)
        self.name_map['frame_packages'].set_sensitive(False)
        self.rootobj.btnnext_sensitive(True)
        
        self.install_finished = True
        if self.install_progress_hooked:
            self.tm.pop_progress()
            
        if self.rootobj.get_cur_stepobj() == self and not self.setup_finished:
            self.rootobj.btnnext_clicked(None, None)
        
    def cb0_insert_next_disc(self, cur_discno, cb_retry_clicked, cb_abort_clicked):
        '''
            callback from install rpm action, wait user change disc and click "retry_clicked"
        '''
        msgtxt = _("Can't find packages in disc %d.\nIf you are using CDROM to install system, it is the chance to eject the original disc and insert the %d disc.") % (cur_discno, cur_discno+1)
        self.discdlg_open_time = time.time()
        class CallBack():
            def __init__(self, sself, cb_retry_clicked, cb_abort_clicked):
                self.sself = sself
                self.cb_retry_clicked = cb_retry_clicked
                self.cb_abort_clicked = cb_abort_clicked
                
            def retry_clicked(self, widget, data):
                if self.sself.discdlg_open_time > 0:
                    # Do adjustment to omit the influence of replace disc.
                    self.sself.starttime = self.sself.starttime + \
                                     (time.time() - self.sself.discdlg_open_time)
                    self.sself.discdlg_open_time = -1
                self.cb_retry_clicked()
                
            def abort_clicked(self, widget, data):
                self.cb_abort_clicked()
            
            def reboot_clicked(self, widget, data):
                self.sself.reboot_clicked(widget, data)
                
        DiscDialog(CallBack(self, cb_retry_clicked, cb_abort_clicked), self.uixmldoc, msgtxt, 'disc.dialog')

    def cb0_install_pkg_err(self, msg, cb_retry_clicked, cb_abort_clicked, data):
        class CallBack():
            def __init__(self, sself, cb_retry_clicked, cb_abort_clicked, data):
                self.sself = sself
                self.cb_retry_clicked = cb_retry_clicked
                self.cb_abort_clicked = cb_abort_clicked
                self.data = data
                
            def retry_clicked(self, widget, data):
                self.cb_retry_clicked(self.data)
                
            def skip_clicked(self, widget, data):
                self.cb_abort_clicked(self.data)
                
            def reboot_clicked(self, widget, data):
                self.sself.reboot_clicked(widget, data)
                    
        RpmErrDialog(CallBack(self, cb_retry_clicked, cb_abort_clicked, data), self.uixmldoc, msg, 'rpmerr.dialog')

    def reboot_clicked(self, widget, data):
        (pafile, dev, fstype, reldir, bootiso_relpath) = CF.G.choosed_patuple
        msg = _('Umount the target filesystem(s).')
        self.add_action(msg, None, None,
                        'install_post', dev, reldir, fstype)
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

    def szfmt(self, sz):
        return '%0.2fM' % (sz / 1024.0 / 1024.0)

    def tmfmt(self, tmdiff):
        h = int(tmdiff / 3600)
        m = int(tmdiff / 60) % 60
        s = int(tmdiff) % 60
        return '%02d:%02d:%02d' % (h, m, s)
    
def TestMIStep_takeactions():
    from mi.client.tests import TestRootObject
    obj = TestRootObject(MIStep_takeactions)
    obj.init()
    obj.main()
    
if __name__ == '__main__':
    TestMIStep_takeactions()
    
