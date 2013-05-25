import os, time
from mi.client.utils import logger, CF, _
'''
    We use callback method to interact with tackactions.py(It is GUI of install action)
    self.cb0_insert_next_disc    Install package out of range, ask GUI to insert next disc.
    self.cb0_install_pkg_err    Install package error, ask GUI to retry or abort.
    self.cb0_install_pkg_end    Install package end, give GUI the package (disc No., package No., size) information.
    self.cb0_install_end        Install all packages complete, just notify GUI.
'''
class MiAction_InstallRpm():
    def __init__(self, rootobj):
        self.rootobj = rootobj
        #self.actlist.append( (_('Install Package'), self.act_start_instpkg, self.act_end_instpkg) )
        #(_('Setup Keyboard'), self.act_start_keyboard, None)]

        self.add_action = self.rootobj.tm.add_action
        self.cb0_insert_next_disc = self.rootobj.cb0_insert_next_disc
        self.cb0_install_pkg_err = self.rootobj.cb0_install_pkg_err
        self.cb0_install_pkg_end = self.rootobj.cb0_install_pkg_end
        self.cb0_install_end = self.rootobj.cb0_install_end
        
        self.disc_first_pkgs = []
        self.cur_disc_no = -1 # current installing disc number
        
        self.totalsize = 0 # sum packages size.
        self.totalpkg = 0 # packages count.
        self.prepared = False
        
    def prepare(self):
        self.arch = self.rootobj.tm.actserver.get_arch()
        logger.i('Detected Arch: %s\n' % str(self.arch))
        
        self.archcompat_list = CF.G.arch_map[self.arch]
        self._calc_instpkg_map()
        self.prepared = True
        
    def get_package_size(self):
        if not self.prepared:
            raise Exception('Not Prepared', 'Please call prepare first.')
        return self.totalsize
    
    def get_package_count(self):
        if not self.prepared:
            raise Exception('Not Prepared', 'Please call prepare first.')
        return self.totalpkg
    
    def _calc_instpkg_map(self):
        '''
            RPM: calculate self.totalpkg, self.totalsize
        '''
        archsize_map = CF.G.archsize_map
        pkgpos_map = CF.G.pkgpos_map
        toplevelgrp_map = CF.G.toplevelgrp_map
        datanode = self.rootobj.srh_data_node(self.rootobj.values, 'package.choosedgroup')
        choosed_list = []
        self.totalsize = 0
        self.install_allpkg = None
        self.disc_map = {}
        self.instpkg_map = {}
        for selnode in datanode.getElementsByTagName('select'):
            thisid = selnode.getAttribute('id')
            if thisid == 'ALL':
                self.install_allpkg = 1
                self.totalsize = archsize_map[self.arch]
                break
            choosed_list.append(thisid)
        if self.install_allpkg:
            self.totalpkg = len(pkgpos_map.keys())
            return
        for grp in ['lock'] + choosed_list:
            if not toplevelgrp_map.has_key(grp):
                # Omit the invalid group name.
                continue
            for pkg in toplevelgrp_map[grp].keys():
                if not self.instpkg_map.has_key(pkg):
                    (apkg, aarch, asize) = self.pkg2archpkg(pkg)
                    self.disc_map[pkgpos_map[pkg][0]] = 'y'
                    self.instpkg_map[pkg] = 'y'
                    self.totalsize = self.totalsize + asize
        self.totalpkg = len(self.instpkg_map.keys())
        
    def start(self):
        for disc_no in range(len(CF.G.arrangement)):
            self.disc_first_pkgs.append(CF.G.arrangement[disc_no][0][1])
        
        (pafile, dev, fstype, reldir, bootiso_relpath) = CF.G.choosed_patuple
        logger.i('disc_first_pkgs: %s\n' % str(self.disc_first_pkgs))
        self.add_action(_('Search packages'),
                        self.act_install_prepare, None,
                        'probe_all_disc', dev, fstype, bootiso_relpath, reldir, self.disc_first_pkgs)

    def act_install_prepare(self, tdata, data):
        '''
            invoke install_prep(server) to mount target system partitions.
        '''
        self.probe_all_disc_result = tdata
        logger.i('probe_all_disc_result: %s\n' % str(self.probe_all_disc_result))
        (pafile, dev, fstype, reldir, bootiso_relpath) = CF.G.choosed_patuple

        self.add_action(None,
                        self.act_rpm_pre_install, 0,
                        'install_prep', (dev, fstype, bootiso_relpath, reldir), 
                                        CF.G.mount_all_list,    # partition list [(mntpoint, devfn, fstype), ...] , be filled at partition step.
                            )
        
    def act_rpm_pre_install(self, tdata, disc_no):
        if tdata != 0:
            ### TODO: Only reboot, because install_prep can not mount target system partitions, so we can not install packages in it.
            pass #### occur error, tdata is the error msg
        self.add_action(None,
                        self.act_install_disc_start, 0,
                        'rpm_pre_install', None)
        
    def act_install_disc_start(self, tdata, disc_no):
        '''
            mount each ISO, and install it.
            install_disc_prep(server) mount ISO.
        '''
        (pafile, dev, fstype, reldir, bootiso_relpath) =  CF.G.choosed_patuple
        while disc_no < len(CF.G.arrangement):
            logger.i("act_install_disc_start probe_all_disc_result: %s" % self.probe_all_disc_result)
            if not self.install_allpkg and not self.disc_map.has_key(disc_no):
                # Skip the disc which is not needed.
                disc_no = disc_no + 1
                continue

            if disc_no >= len(self.probe_all_disc_result) \
                   or not self.probe_all_disc_result[disc_no]: ## TODO multi disc will always have only one probe_all_disc_result. please fix it.
                # we known have next disc in pkgarr.py file (CF.G.arrangement is the variable in pkgarr.py)
                # but there can not find next disc with disc_no in probe_all_disc_result. so we think it should have a next disc, and ask user to insert it.
                self.cb0_insert_next_disc(disc_no + 1, self.retry_clicked, self.abort_clicked) ## This call back will active next install action.
                return
            self.cur_disc_no = disc_no
            bootiso_relpath = self.probe_all_disc_result[disc_no][0]
            self.add_action(None,
                            self.act_install_pkg_start, (disc_no, 0),
                            'install_disc_prep', dev, fstype, bootiso_relpath, reldir)
            # add install current disc action, return now, and wait next disc action after current disc install action finished.
            return
        
        ### Install all disc finished
        self.add_action(_('Last operations for package installation'),
                        self.nextop, None,
                        'rpm_post_install', None)
                        
    def act_install_pkg_start(self, tdata, data):
        if tdata != 0:
            ### TODO install_disc_prep ERROR, because package source on disc and can not access, error should exit.
            pass
        
        (disc_no, pkg_no) = data
        while pkg_no < len(CF.G.arrangement[disc_no]):
            pkgtuple = CF.G.arrangement[disc_no][pkg_no]

            if self.install_allpkg or self.instpkg_map.has_key(pkgtuple[1]):
                archpkg = self.pkg2archpkg(pkgtuple[1])
                if not archpkg:
                    data = (disc_no, pkg_no, 0, False)
                    msg = _("Target System Arch %s is not Compatible with package arch %s" % (self.arch, pkgtuple[1]))
                    self.cb0_install_pkg_err(msg, self.rpmerr_retry_clicked, self.rpmerr_skip_clicked, data)
                    return
                (apkg, aarch, asize) = archpkg
                apkg = os.path.basename(apkg)
                # Debug
                self.add_action(apkg, self.act_install_pkg_end, (disc_no, pkg_no, asize, False),
                                'sleep', 0)
#                self.add_action(apkg,
#                                self.act_install_pkg_end, (disc_no, pkg_no, asize, False),
#                                'rpm_install_pkg', apkg, self.probe_all_disc_result[disc_no][1])
                return
            pkg_no = pkg_no + 1
        (pafile, dev, fstype, reldir, bootiso_relpath) = CF.G.choosed_patuple
        # Install current disc finished, add action to start next disc installation.
        self.add_action(None,
                        self.act_install_disc_start, disc_no + 1,
                        'install_disc_post', dev, fstype, self.probe_all_disc_result[disc_no][0], reldir)

    def rpmerr_retry_clicked(self, data):
        (disc_no, pkg_no, asize, is_skip) = data
        self.act_install_pkg_start(-1, (disc_no, pkg_no))

    def rpmerr_skip_clicked(self, data):
        (disc_no, pkg_no, asize, is_skip) = data
        self.act_install_pkg_end(-1, (disc_no, pkg_no, asize, True))
                
    def act_install_pkg_end(self, tdata, data):
        #--- FIXME ---
        # It doesn't check the result of package_install now, but it should...
        # It should popup an dialog to let the user choose 'continue' or
        #  'abandon' the installation.
        (disc_no, pkg_no, asize, is_skip) = data

        if not is_skip and tdata != 0:  # This package can not skip and have an install error.                
            self.cb0_install_pkg_err(tdata, self.rpmerr_retry_clicked, self.rpmerr_skip_clicked, data)
            return
            
        if self.cb0_install_pkg_end:    # tell GUI to calculate package size
            self.cb0_install_pkg_end(disc_no, pkg_no, asize)
        
        self.act_install_pkg_start(tdata, (disc_no, pkg_no + 1))
        
    def act_install_end(self, tdata, data):
        '''
            will be invoked at the end of installation.
        '''
        if self.cb0_install_end:
            self.cb0_install_end()
            
    def nextop(self, tdata, data):
        (pafile, dev, fstype, reldir, bootiso_relpath) = CF.G.choosed_patuple
        self.add_action(None, self.act_install_end, None,
                        "install_post", (dev, fstype, bootiso_relpath, reldir), CF.G.mount_all_list)

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


############################ Graphic Button Action ###################################
    def retry_clicked(self):
        '''
            This is the DiscDialog retry button click callback.
            DiscDialog alert indicate that package installation pause, we should active it by reprobe disc.(If user has changed it)
        '''
        (pafile, dev, fstype, reldir, bootiso_relpath) = CF.G.choosed_patuple
        self.add_action(_('Researching packages...'),
                        self.retry_install, None,
                        'probe_all_disc', dev, fstype, bootiso_relpath, reldir, self.disc_first_pkgs)
        
    def retry_install(self, tdata, data):
        self.probe_all_disc_result = tdata
        self.act_install_disc_start(None, self.cur_disc_no + 1)
        
#    def reprobe_all_disc_0(self, tdata, data):
#        (pafile, dev, fstype, reldir, bootiso_relpath) = CF.G.choosed_patuple
#        self.add_action(_('Researching packages...'),
#                        self.reprobe_all_disc_1, None,
#                        'probe_all_disc', dev, fstype, bootiso_relpath, reldir, self.disc_first_pkgs)

#    def reprobe_all_disc_1(self, tdata, data):
#        self.probe_all_disc_result = tdata
#        logger.i('probe_all_disc_result: %s\n' % str(self.probe_all_disc_result))
#        (pafile, dev, fstype, reldir, bootiso_relpath) = CF.G.choosed_patuple
#        self.add_action(_('Researching packages...'),
#                        self.act_install_disc_start, self.cur_disc_no + 1,
#                        'install_prep', (dev, fstype, bootiso_relpath, reldir), CF.G.mount_all_list)

    def abort_clicked(self):
        self.add_action(_('Aborting...'),
                        self.nextop, None,
                        'rpm_post_install', None)
