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
import glob
import os
import os.path
import sys
import syslog
import time

import kudzu
import rpm

import isys
import tftpc

if operation_type == 'short':
    pass
elif operation_type == 'long':
    cd_papath = '%s/base' % distname
    hd_papathes = ['boot',
                   distname,
                   'usr/share/MagicInstaller',
                   '',
                   'tmp']
    pafile = 'pkgarr.py'
    isoloop = 'loop3'  # Use the last loop device.
    cur_rpm_fd = 0
    ts = None
    pkg_install_list = []
    use_noscript = False
    installmode = 'rpminstallmode'
    rpmdb = 'rpmdb.tar.bz2'
    etctar = 'etc.tar.bz2'
    etc_script = 'etc_install.sh'
    tmp_config_dir = 'tmp/MI_configure'
    
    def pkgarr_probe(mia, operid, hdpartlist):
        def probe_position(localfn, pos_id, cli, device, new_device, fstype, dir, isofn):
            if not os.path.exists(localfn):
                return None
            try:
                execfile(localfn)
            except Exception, errmsg:
                syslog.syslog(syslog.LOG_ERR,
                              "Load %s failed(%s)." % (localfn, str(errmsg)))
                return None
            remotefn = 'allpa/%s.%d.%s' % \
                       (os.path.basename(new_device),
                        pos_id,
                        os.path.basename(localfn))
            cli.put(localfn, remotefn)
            # Leave the mntpoint to 0 now because the mntpoint can't be get easily.
            return (remotefn, new_device, 0, fstype, dir, isofn)

        global cd_papath
        global hd_papathes
        global pafile
        global isoloop

        loopmntdir = os.path.join('/tmpfs/mnt', isoloop)
        if not os.path.isdir(loopmntdir):
            os.makedirs(loopmntdir)
        mia.set_step(operid, 0, -1)
        cli = tftpc.TFtpClient()
        cli.connect('127.0.0.1')
        result = []
        all_drives = hdpartlist
        cdlist = kudzu.probe(kudzu.CLASS_CDROM,
                             kudzu.BUS_IDE | kudzu.BUS_SCSI | kudzu.BUS_MISC,
                             kudzu.PROBE_ALL)
        map(lambda cd: all_drives.append((os.path.join('/dev', cd.device),
                                          'iso9660',
                                          os.path.join('/dev', cd.device))),
            cdlist)
        for (device, fstype, new_device) in all_drives:
            if not fstype_map.has_key(fstype):
                continue
            if fstype_map[fstype][0] == '':
                continue
            mntdir = os.path.join('/tmpfs/mnt', os.path.basename(device))
            syslog.syslog(syslog.LOG_INFO,
                          "Probe: Device = %s Mount = %s Fstype = %s" % \
                          (device, mntdir, fstype))
            if not os.path.isdir(mntdir):
                os.makedirs(mntdir)
            else:
                # attempt to umount the device always. 
                try:
                    isys.umount(mntdir)
                except SystemError, errmsg:
                    pass
                
            try:
                isys.mount(fstype_map[fstype][0], device, mntdir, 1, 0)
            except SystemError, errmsg:
                syslog.syslog(syslog.LOG_ERR,
                              "Mount %s on %s as %s failed: %s" % \
                              (device, mntdir, fstype_map[fstype][0], str(errmsg)))
            else:
                if fstype == 'iso9660':
                    search_dirs = [cd_papath]
                else:
                    search_dirs = hd_papathes
                pos_id = 0
                for dir in search_dirs:
                    pos_id = pos_id + 1
                    # Try bare pafile.
                    localfn = os.path.join(mntdir, dir, pafile)
                    r = probe_position(localfn, pos_id, cli, device, new_device, fstype, dir, '')
                    if r:
                        result.append(r)
                    # Try pafile in bootcd and debugbootcd.
                    for (pi_add, isofn) in ((100, bootcdfn),):
                        isopath = os.path.join(mntdir, dir, isofn)
                        if not os.path.exists(isopath):
                            continue
                        try:
                            isys.lomount(os.path.join('/dev', isoloop),
                                         isopath, loopmntdir, 'iso9660', 'readonly')
                        except SystemError, errmsg:
                            syslog.syslog(syslog.LOG_ERR,
                                          "LoMount %s(%s) on %s as %s failed: %s" % \
                                          (os.path.join('/dev', isoloop),
                                           isopath, loopmntdir,
                                           'iso9660', str(errmsg)))
                        else:
                            localfn = os.path.join(loopmntdir, cd_papath, pafile)
                            r = probe_position(localfn, pi_add + pos_id, cli,
                                               device, new_device, fstype, dir, isofn)
                            try:
                                isys.loumount(os.path.join('/dev', isoloop),
                                              loopmntdir)
                            except SystemError, errmsg:
                                syslog.syslog(syslog.LOG_ERR,
                                              "LoUMount(%s, %s) failed: %s" % \
                                              (os.path.join('/dev', isoloop),
                                               loopmntdir,
                                               str(errmsg)))
                                return str(errmsg)
                            if r:
                                result.append(r)
                try:
                    isys.umount(mntdir)
                except SystemError, errmsg:
                    syslog.syslog(syslog.LOG_ERR,
                                  "UMount(%s) failed: %s" % (mntdir, str(errmsg)))
                    return  str(errmsg)
        del(cli)
        return result

    def probe_all_disc(mia, operid, device, mntpoint, dir, fstype, disc_first_pkgs):
        '''
            probe the package from all disk
            dir is the directory name between / and /packages
        '''
        global  isoloop
        dolog('probe_all_disc(%s, %s, %s, %s, %s)\n' % \
              (device, str(mntpoint), dir, fstype, disc_first_pkgs))
        loopmntdir = os.path.join('/tmpfs/mnt', isoloop)
        if not os.path.isdir(loopmntdir):
            os.makedirs(loopmntdir)
        if mntpoint != 0:
            # The packages are placed in the mounted partitions.
            mntdir = os.path.join(tgtsys_root, mntpoint)
        else:
            mntdir = os.path.join('/tmpfs/mnt', os.path.basename(device))
            if not os.path.isdir(mntdir):
                os.makedirs(mntdir)
            try:
                isys.mount(fstype_map[fstype][0], device, mntdir, 1, 0)
            except SystemError, errmsg:
                syslog.syslog(syslog.LOG_ERR,
                              "Mount %s on %s as %s failed: %s" % \
                              (device, mntdir, fstype_map[fstype][0], str(errmsg)))
                return  (str(errmsg), [])
        result = []
        for disc_no in range(len(disc_first_pkgs)):
            proberes = 0
            for probedir in ['../packages',
                             'packages',
                             '../packages-%d' % (disc_no + 1),
                             'packages-%d' % (disc_no + 1)]:
                probepath = os.path.realpath(os.path.join(mntdir, dir, probedir))
                if not os.path.isdir(probepath):
                    continue
                probepkg = os.path.join(probepath, disc_first_pkgs[disc_no])
                if os.path.isfile(probepkg):
                    proberes = (0, probepkg)
                    break
            if not proberes:
                discfn = isofn_fmt % (distname, distver, disc_no + 1)
                discpath = os.path.join(mntdir, dir, discfn)
                if os.path.isfile(discpath):
                    try:
                        isys.lomount(os.path.join('/dev', isoloop),
                                     discpath, loopmntdir, 'iso9660', 'readonly')
                    except SystemError, errmsg:
                        syslog.syslog(syslog.LOG_ERR,
                                      "LoMount %s(%s) on %s as %s failed: %s" % \
                                      (os.path.join('/dev', isoloop),
                                       discpath, loopmntdir,
                                       'iso9660', str(errmsg)))
                    else:
                        probepkg = os.path.join(loopmntdir, '%s/packages' % distname, disc_first_pkgs[disc_no])
                        if os.path.isfile(probepkg):
                            dolog('Have found the first_pkg %s in iso %s\n' % (probepkg, discpath))
                            proberes = (discpath, probepkg)
                        try:
                            isys.loumount(os.path.join('/dev', isoloop),
                                          loopmntdir)
                        except SystemError, errmsg:
                            syslog.syslog(syslog.LOG_ERR,
                                          "LoUMount(%s, %s) failed: %s" % \
                                          (os.path.join('/dev', isoloop),
                                           loopmntdir,
                                           str(errmsg)))
                            return  (str(errmsg), [])
            result.append(proberes)
        dolog('probe_all_disc return result is : %s\n' % str(result))
        if mntpoint == 0:
            try:
                isys.umount(mntdir)
            except SystemError, errmsg:
                syslog.syslog(syslog.LOG_ERR,
                              "UMount(%s) failed: %s" % (mntdir, str(errmsg)))
                if result != []:
                    # we can't umount the mntdir, but if we have found the package result we must return it.
                    return(0, result)
                else:
                    return (str(errmsg), [])
        return  (0, result)

    def instpkg_prep(mia, operid, dev, mntpoint, dir, fstype, instmode):
        # Set the package install mode.
        global installmode
        installmode = instmode
        dolog('InstallMode: %s\n' % installmode)
        
        dolog('instpkg_prep(%s, %s, %s, %s)\n' % (dev, mntpoint, dir, fstype))
        #--- This code is according to rpm.spec in rpm-4.2-0.69.src.rpm. ---
        # This code is specific to rpm.
        var_lib_rpm = os.path.join(tgtsys_root, 'var/lib/rpm')
        if not os.path.isdir(var_lib_rpm):
            os.makedirs(var_lib_rpm)
        #touch_files = ['Basenames', 'Conflictname', 'Dirnames', 'Group',
                       #'Installtid', 'Name', 'Packages', 'Providename',
                       #'Provideversion', 'Requirename', 'Requireversion',
                       #'Triggername', 'Filemd5s', 'Pubkeys', 'Sha1header',
                       #'Sigmd5', '__db.001', '__db.002', '__db.003',
                       #'__db.004', '__db.005', '__db.006', '__db.007',
                       #'__db.008', '__db.009']
        #os.system('touch ' +
                  #string.join(map(lambda x: os.path.join(var_lib_rpm, x),
                                  #touch_files)))
        #-------------------------------------------------------------------
        if fstype == 'iso9660':
            return  0  # It is ok for CDROM installation.
        # It is harddisk installation.
        global  isoloop
        loopmntdir = os.path.join('/tmpfs/mnt', isoloop)
        if not os.path.isdir(loopmntdir):
            os.makedirs(loopmntdir)
        if mntpoint != 0:
            mntdir = os.path.join(tgtsys_root, mntpoint)
        else:
            mntdir = os.path.join('/tmpfs/mnt', os.path.basename(dev))
            if not os.path.isdir(mntdir):
                os.makedirs(mntdir)
            try:
                isys.mount(fstype_map[fstype][0], dev, mntdir, 1, 0)
            except SystemError, errmsg:
                return  str(errmsg)
        return  0

    def instpkg_disc_prep(mia, operid, dev, mntpoint, dir, fstype, iso_fn):
        global  isoloop
        dolog('instpkg_disc_prep(%s, %s, %s, %s, %s)\n' % \
              (dev, mntpoint, dir, fstype, iso_fn))
        if mntpoint != 0:
            mntdir = os.path.join(tgtsys_root, mntpoint)
        else:
            mntdir = os.path.join('/tmpfs/mnt', os.path.basename(dev))
        if fstype == 'iso9660':
            # It is CDROM installation.
            # assert(mntpoint == 0) because CDROM can't be mount as part
            #    of target system.
            if not os.path.isdir(mntdir):
                os.makedirs(mntdir)
            try:
                isys.mount(fstype_map[fstype][0], dev, mntdir, 1, 0)
            except SystemError, errmsg:
                return  str(errmsg)
        elif iso_fn:
            # iso file is placed in mntdir.
            isopath = os.path.join(mntdir, dir, iso_fn)
            loopmntdir = os.path.join('/tmpfs/mnt/', isoloop)
            try:
                isys.lomount(os.path.join('/dev', isoloop),
                             isopath, loopmntdir, 'iso9660', 'readonly')
            except SystemError, errmsg:
                syslog.syslog(syslog.LOG_ERR,
                              "LoMount %s(%s) on %s as %s failed: %s" % \
                              (os.path.join('/dev', isoloop),
                               isopath, loopmntdir,
                               'iso9660', str(errmsg)))
                return  str(errmsg)
        return  0

    # Now package_install support rpm only.
    def rpm_installcb(what, bytes, total, h, data):
        global  cur_rpm_fd
        (mia, operid) = data
        if what == rpm.RPMCALLBACK_INST_OPEN_FILE:
            cur_rpm_fd = os.open(h, os.O_RDONLY)
            return  cur_rpm_fd
        elif what == rpm.RPMCALLBACK_INST_CLOSE_FILE:
            os.close(cur_rpm_fd)
        elif what == rpm.RPMCALLBACK_INST_PROGRESS:
            mia.set_step(operid, bytes, total)

    def run_bash(cmd, argv, root='/'):
        import subprocess
        def chroot():
            os.chroot(root)

        cmd_res = {}
        res = subprocess.Popen([cmd] + argv, 
                                stdout = subprocess.PIPE, 
                                stderr = subprocess.PIPE, 
                                preexec_fn = chroot, cwd = root,
                                close_fds = True)
        res.wait()
        cmd_res['out']=res.stdout.readlines()
        cmd_res['err']=res.stderr.readlines()
        cmd_res['ret']=res.returncode
        return cmd_res
        
    def package_install(mia, operid, pkgname, firstpkg):
        global tgtsys_root
        use_ts = False
        pkgpath = os.path.join(os.path.dirname(firstpkg), pkgname)
        dolog('pkg_install(%s, %s)\n' % (pkgname, str(pkgpath)))
        
        def do_ts_install():
            global ts
            if ts is None:
                dolog('Create TransactionSet\n')
                ts = rpm.TransactionSet(tgtsys_root)
                ts.setProbFilter(rpm.RPMPROB_FILTER_OLDPACKAGE |
                                 rpm.RPMPROB_FILTER_REPLACENEWFILES |
                                 rpm.RPMPROB_FILTER_REPLACEOLDFILES |
                                 rpm.RPMPROB_FILTER_REPLACEPKG)
                ts.setVSFlags(~(rpm.RPMVSF_NORSA | rpm.RPMVSF_NODSA))
                
                # have been removed from last rpm version
                #ts.setFlags(rpm.RPMTRANS_FLAG_ANACONDA)
            try:
                rpmfd = os.open(pkgpath, os.O_RDONLY)
                hdr = ts.hdrFromFdno(rpmfd)
                ts.addInstall(hdr, pkgpath, 'i')
                os.close(rpmfd)
                # Sign the installing pkg name in stderr.
                print >>sys.stderr, '%s ERROR :\n' % pkgname
                problems = ts.run(rpm_installcb, (mia, operid))
                if problems:
                    dolog('PROBLEMS: %s\n' % str(problems))
                    # problems is a list that each elements is a tuple.
                    # The first element of the tuple is a human-readable string
                    # and the second is another tuple such as:
                    #    (rpm.RPMPROB_FILE_CONFLICT, conflict_filename, 0L)
                    return  problems
            except Exception, errmsg:
                dolog('FAILED: %s\n' % str(errmsg))
                return str(errmsg)
                
        def do_bash_rpm_install():
            global pkg_install_list
            global use_noscript
            mia.set_step(operid, 1, 1)
            # If we use use_noscript we should open the option --noscript in rpm command,
            # and then we will do some configuration in instpkg_post.
            use_noscript = False
            if use_noscript:
                pkg_install_list.append(pkgpath)
                
            try:
                cmd = '/bin/rpm'
                argv = ['-i', '--noorder','--nosuggest',
                        '--force','--nodeps',
                        #'--noscript',       # we use the noscript option
                        '--root', tgtsys_root,
                        pkgpath,
                    ]
                cmd_res = run_bash(cmd, argv)
                # Sign the installing pkg name in stderr
                if cmd_res['err']:
                    # Ok the stderr will dup2 a log file, so we just out it on err screen
                    print >>sys.stderr, '***INSTALLING %s:\n**STDERR:\n%s\n' \
                            %(pkgname, ''.join(cmd_res['err']))
                problems = cmd_res['ret']
                if problems:
                    errormsg = ''.join(cmd_res['err'])
                    message = 'PROBLEMS on %s: \n return code is %s error message is\n[%s]' \
                              % (pkgname, str(problems), errormsg)
                    dolog(message)
                    return  message
            except Exception, errmsg:
                dolog('FAILED on %s: %s\n' % (pkgname, str(errmsg)))
                return str(errmsg)
                
        def do_copy_install():
            mia.set_step(operid, 1, 1)
            try:
                cmd = 'cd %s && /usr/bin/rpm2cpio %s | /bin/cpio -dui --quiet' % (tgtsys_root, pkgpath)
                problems = os.system(cmd)
                if problems:
                    errormsg = ''.join(cmd_res['err'])
                    message = 'PROBLEMS on %s: \n return code is %s error message is\n[%s]' \
                              % (pkgname, str(problems), errormsg)
                    dolog(message)
                    return  message
            except Exception, errmsg:
                dolog('FAILED on %s: %s\n' % (pkgname, str(errmsg)))
                return str(errmsg)
                
        # Decide using which mode to install.
        if installmode == 'rpminstallmode':
            if use_ts:
                # Use rpm-python module to install rpm pkg, but at this version it is very slowly.
                do_ts_install()
            else:
                # Because I can not use rpm-python module to install quickly.
                # So use the bash mode to install the pkg, it is very fast.
                # If you can use rpm-python module install pkg quickly, you can remove it.
                do_bash_rpm_install()
        elif installmode == 'copyinstallmode':
            # Use rpm2cpio name-ver-release.rpm | cpio -diu to uncompress the rpm files to target system.
            # Then we will do some configuration in instpkg_post.
            do_copy_install()
        return 0

    def instpkg_disc_post(mia, operid, dev, mntpoint, dir, fstype, iso_fn, first_pkg):
        # determine the rpmdb.tar.bz2 and etc.tar.bz2. If exist copy it to tmp_config_dir in target system.
        rpmpkgdir = os.path.dirname(first_pkg)
        rpmdb_abs = os.path.join(rpmpkgdir, rpmdb)
        etctar_abs = os.path.join(rpmpkgdir, etctar)
        tgt_tmp_config_dir = os.path.join(tgtsys_root, tmp_config_dir)
        if not os.path.exists(tgt_tmp_config_dir):
            os.makedirs(tgt_tmp_config_dir)
        if os.path.exists(rpmdb_abs):
            ret = os.system('cp %s %s' % (rpmdb_abs, os.path.join(tgt_tmp_config_dir, rpmdb)))
            if ret != 0:
                dolog('copy %s to target system failed.\n' % rpmdb)
            else:
                dolog('copy %s to target system successfully.\n' % rpmdb)
        if os.path.exists(etctar_abs):
            ret = os.system('cp %s %s' % (etctar_abs, os.path.join(tgt_tmp_config_dir, etctar)))
            if ret != 0:
                dolog('copy %s to target system failed.\n' % rpmdb)
            else:
                dolog('copy %s to target system successfully.\n' % rpmdb)
                
        global isoloop
        dolog('instpkg_disc_post(%s, %s, %s, %s, %s)\n' % \
              (dev, mntpoint, dir, fstype, iso_fn))
        # We don't know which package start the minilogd but it
        # will lock the disk, so it must be killed.
        if os.system('/usr/bin/killall minilogd') == 0:
            time.sleep(2)
        if mntpoint != 0:
            mntdir = os.path.join(tgtsys_root, mntpoint)
        else:
            mntdir = os.path.join('/tmpfs/mnt', os.path.basename(dev))
        if fstype == 'iso9660':
            # It is CDROM installation.
            # assert(mntpoint == 0) because CDROM can't be mount as part
            #    of target system.
            try:
                isys.umount(mntdir)
            except SystemError, errmsg:
                syslog.syslog(syslog.LOG_ERR, 'UMount(%s) failed: %s' % \
                              (mntdir, str(errmsg)))
                return str(errmsg)
            # Eject the cdrom after used.
            try:
                cdfd = os.open(dev, os.O_RDONLY | os.O_NONBLOCK)
                isys.ejectcdrom(cdfd)
                os.close(cdfd)
            except Exception, errmsg:
                syslog.syslog(syslog.LOG_ERR, 'Eject(%s) failed: %s' % \
                              (dev, str(errmsg)))
                return str(errmsg)
        elif iso_fn:
            # iso file is placed in mntdir.
            loopmntdir = os.path.join('/tmpfs/mnt/', isoloop)
            try:
                isys.loumount(os.path.join('/dev', isoloop), loopmntdir)
            except SystemError, errmsg:
                syslog.syslog(syslog.LOG_ERR, 'LoUMount(%s, %s) failed: %s' % \
                              (os.path.join('/tmpfs/mnt', isoloop),
                               loopmntdir,
                               str(errmsg)))
                return str(errmsg)
        return  0

    def instpkg_post(mia, operid, dev, mntpoint, dir, fstype):
        if installmode == 'rpminstallmode' and use_noscript:
            # we will excute all the pre_in and post_in scripts there, if we use
            # the --noscript option during rpm installation
            def run_pre_post_in_script(tgtsys_root, path):
                def get_pkg_name(pkgrpm):
                    pkg = os.path.basename(pkgrpm)
                    pkgname = ''
                    try:
                        pkgname = pkg[:pkg.rindex('-')]
                        pkgname = pkg[:pkgname.rindex('-')]
                    except ValueError, e:
                        return pkg
                    return pkgname
                def excute_pre_post(h):
                    if h[rpm.RPMTAG_PREIN]:
                        ret = os.system(h[rpm.RPMTAG_PREIN])
                        if ret != 0:
                            dolog('error pre_install in %s-%s-%s\n' \
                                    % (h['name'],h['version'],h['release']))
                    if h[rpm.RPMTAG_POSTIN]:
                        ret = os.system(h[rpm.RPMTAG_POSTIN])
                        if ret != 0:
                            dolog('error post_install in %s-%s-%s\n' \
                                    % (h['name'],h['version'],h['release']))
                os.chroot(tgtsys_root)
                ts_m = rpm.TransactionSet()
                for pkg in pkg_install_list:
                    pkgname = get_pkg_name(pkg)
                    mi = ts_m.dbMatch('name', pkgname)
                    for h in mi:
                        if h['name'] == pkgname:
                            excute_pre_post(h)

            from multiprocessing import Process
            p = Process(target=run_pre_post_in_script)
            p.start()
            p.join()
            
        if installmode == 'copyinstallmode':
            tgt_tmp_config_dir = os.path.join(tgtsys_root, tmp_config_dir)
            rpmdb_abs = os.path.join(tgt_tmp_config_dir, rpmdb)
            etctar_abs = os.path.join(tgt_tmp_config_dir, etctar)
            if os.path.exists(rpmdb_abs):
                ret = os.system('tar -xjf %s -C %s' % (rpmdb_abs, tgtsys_root))
                if ret != 0:
                    dolog('ERROR: Extract %s from target system %s to target system Failed.\n' \
                    %(rpmdb, rpmdb_abs[len(tgtsys_root):]))
                os.system('rm -r %s' % rpmdb_abs)
            else:
                dolog('Warning: cannot find the needed file %s.\n' % rpmdb_abs[len(tgtsys_root):])
            if os.path.exists(etctar_abs):
                ret = os.system('tar -xjf %s -C %s' % (etctar_abs, os.path.join(tgtsys_root, tmp_config_dir)))
                if ret != 0:
                    dolog('ERROR: Extract %s from target system %s to target system Failed.\n' \
                    %(etctar, etctar_abs[len(tgtsys_root):]))
            else:
                dolog('Warning: cannot find the needed file %s.\n' % etctar_abs[len(tgtsys_root):])
            # do chroot and excute the etc_install.sh
            ret = os.system('/usr/sbin/chroot %s /%s %s' \
                    % (tgtsys_root, os.path.join(tmp_config_dir, etc_script), tmp_config_dir))
            if ret != 0:
                dolog('ERROR: run %s failed.\n' % os.path.join(tmp_config_dir, etc_script))
            else:
                dolog('Run %s successfully.\n' % os.path.join(tmp_config_dir, etc_script))
            os.system('rm -r %s' % os.path.join(tgtsys_root, tmp_config_dir))
            
        global ts
        if ts is not None:
            dolog('Close TransactionSet\n')
            ts.closeDB()
            ts = None
        dolog('instpkg_post(%s, %s, %s, %s)\n' % (dev, mntpoint, dir, fstype))
        if fstype == 'iso9660':
            return  0  # It is ok for CDROM installation.
        mia.set_step(operid, 0, -1) # Sync is the long operation.
        if mntpoint != 0:
            mntdir = os.path.join(tgtsys_root, mntpoint)
        else:
            mntdir = os.path.join('/tmpfs/mnt', os.path.basename(dev))
            try:
                isys.umount(mntdir)
            except SystemError, errmsg:
                syslog.syslog(syslog.LOG_ERR, 'UMount(%s) failed: %s' % \
                              (mntdir, str(errmsg)))
                return str(errmsg)
        try:
            isys.sync()
        except Expection, errmsg:
            syslog.syslog(syslog.LOG_ERR, 'sync failed: %s' % str(errmsg))
            return str(errmsg)
        return  0
