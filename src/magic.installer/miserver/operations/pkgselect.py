#!/usr/bin/python
import os, glob, sys, syslog
import rpm, tarfile, time
import isys, tftpc, getdev
from miutils.common import mount_dev, umount_dev, run_bash
from miutils.miconfig import MiConfig
CONF = MiConfig.get_instance()
CONF_DISTNAME = CONF.LOAD.CONF_DISTNAME
CONF_DISTVER = CONF.LOAD.CONF_DISTVER
CONF_FSTYPE_MAP = CONF.LOAD.CONF_FSTYPE_MAP
CONF_TGTSYS_ROOT = CONF.LOAD.CONF_TGTSYS_ROOT
CONF_PKGTYPE = CONF.LOAD.CONF_PKGTYPE
CONF_BOOTCDFN = CONF.LOAD.CONF_BOOTCDFN
CONF_ISOFN_FMT = CONF.LOAD.CONF_ISOFN_FMT

from miutils.miregister import MiRegister
register = MiRegister()

from miserver.utils import Logger
Log = Logger.get_instance(__name__)
dolog = Log.i

cd_papath = '%s/base' % CONF_DISTNAME
hd_papathes = ['boot',
               CONF_DISTNAME,
               'usr/share/MagicInstaller',
               '',
               'tmp']
pafile = 'pkgarr.py'
isoloop = 'loop3'  # Use the last loop device.
cur_rpm_fd = 0
ts = None

# If we use use_noscripts we should open the option --noscripts in rpm command,
# and then we will do some configuration in instpkg_post.
use_noscripts = False
# if we not use_noscripts option, when package accept a noscripts parameter during
# install, it will also use --noscripts option to avoid run pre_install and
# post_install scripts, run these scripts in instpkg_post at last(same as use_noscripts).
noscripts_pkg_list = []
noscripts_log = '/var/log/mi/run_noscripts.log'
tmp_noscripts_dir = 'tmp/MI_noscripts'

installmode = 'rpminstallmode'
rpmdb = 'rpmdb.tar.bz2'
etctar = 'etc.tar.bz2'
etc_script = 'etc_install.sh'
tmp_config_dir = 'tmp/MI_configure'

@register.server_handler('long')
def pkgarr_probe(mia, operid, hdpartlist):
    dolog("=====pkgarr_probe starting...")
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
        dolog('tftpc update %s to remote %s...' % (localfn, remotefn))
        cli.put(localfn, remotefn)
        # Leave the mntpoint to 0 now because the mntpoint can't be get easily.
        mntpoint = 0
        return (remotefn, new_device, mntpoint, fstype, dir, isofn)
        # The format like ('allpa/hdc.1.pkgarr.py', '/dev/hdc', 0, 'iso9660', 'MagicLinux/base', '')

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
    #cdlist = kudzu.probe(kudzu.CLASS_CDROM,
    #                     kudzu.BUS_IDE | kudzu.BUS_SCSI | kudzu.BUS_MISC,
    #                     kudzu.PROBE_ALL)
    cdlist = getdev.probe(getdev.CLASS_CDROM)
    map(lambda cd: all_drives.append((os.path.join('/dev', cd.device),
                                      'iso9660',
                                      os.path.join('/dev', cd.device))),
        cdlist)
    dolog('======all_drives: %s' % all_drives)
    for (device, fstype, new_device) in all_drives:
        if not CONF_FSTYPE_MAP.has_key(fstype):
            continue
        if CONF_FSTYPE_MAP[fstype][0] == '':
            continue
        if fstype == 'iso9660':
            if os.system('dd if=%s bs=1 count=1 of=/dev/null &>/dev/null' % device) != 0:
                dolog('%s cannot use\n' % device)
                # cdrom cannot use
                continue
        ret, mntdir = mount_dev(CONF_FSTYPE_MAP[fstype][0], device)
        if not ret:
            syslog.syslog(syslog.LOG_ERR,
                          "Mount %s on %s as %s failed: %s" % \
                          (device, mntdir, CONF_FSTYPE_MAP[fstype][0], str(mntdir)))
        else:
            syslog.syslog(syslog.LOG_INFO,
                      "Probe: Device = %s Mount = %s Fstype = %s" % \
                      (device, mntdir, fstype))
            if fstype == 'iso9660':
                search_dirs = [cd_papath]
            else:
                search_dirs = hd_papathes
            pos_id = 0
            dolog("============search_dirs %s\n" % search_dirs)
            for dir in search_dirs:
                pos_id = pos_id + 1
                # Try bare pafile.
                localfn = os.path.join(mntdir, dir, pafile)
                r = probe_position(localfn, pos_id, cli, device, new_device, fstype, dir, '')
                if r:
                    result.append(r)
                # Try pafile in bootcd and debugbootcd.
                dolog("=============%s\n" % CONF_BOOTCDFN)
                for (pi_add, isofn) in ((100, CONF_BOOTCDFN),):
                    isopath = os.path.join(mntdir, dir, isofn)
                    if not os.path.exists(isopath):
                        continue
                    ret, errmsg = mount_dev('iso9660', isopath, loopmntdir, flags='loop')
                    if not ret:
                        syslog.syslog(syslog.LOG_ERR,
                                      "LoMount %s on %s as %s failed: %s" % \
                                      (isopath, loopmntdir,
                                       'iso9660', str(errmsg)))
                    else:
                        localfn = os.path.join(loopmntdir, cd_papath, pafile)
                        r = probe_position(localfn, pi_add + pos_id, cli,
                                           device, new_device, fstype, dir, isofn)
                        ret, errmsg = umount_dev(loopmntdir)
                        if not ret:
                            syslog.syslog(syslog.LOG_ERR,
                                          "LoUMount %s from %s failed: %s" % \
                                          (isopath,
                                           loopmntdir,
                                           str(errmsg)))
                            #return str(errmsg)
                        if r:
                            result.append(r)
                    ret, errmsg = umount_dev(loopmntdir)
                    if not ret:
                        syslog.syslog(syslog.LOG_ERR,
                                "UMount(%s) failed: %s" % (loopmntdir, str(errmsg)))
                        #return  str(errmsg)
        ret, errmsg = umount_dev(mntdir)
        if not ret:
            syslog.syslog(syslog.LOG_ERR,
                    "UMount(%s) failed: %s" % (loopmntdir, str(errmsg)))
    del(cli)
    return result

@register.server_handler('long')
def probe_all_disc(mia, operid, device, mntpoint, dir, fstype, disc_first_pkgs):
    '''
        probe the package from all disk
        dir is the directory name between / and /packages
    '''
    global  isoloop
    dolog('probe_all_disc(%s, %s, %s, %s, %s)\n' % \
          (device, str(mntpoint), dir, fstype, disc_first_pkgs))
    loopmntdir = os.path.join('/tmpfs/mnt', isoloop)
    if mntpoint != 0:
        # The packages are placed in the mounted partitions.
        mntdir = os.path.join(CONF_TGTSYS_ROOT, mntpoint)
    else:
        mntdir = os.path.join('/tmpfs/mnt', os.path.basename(device))
        ret, errmsg = mount_dev(CONF_FSTYPE_MAP[fstype][0], device, mntdir)
        if not ret:
            syslog.syslog(syslog.LOG_ERR,
                          "Mount %s on %s as %s failed: %s" % \
                          (device, mntdir, CONF_FSTYPE_MAP[fstype][0], str(errmsg)))
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
            discfn = CONF_ISOFN_FMT % (CONF_DISTNAME, CONF_DISTVER, disc_no + 1)
            discpath = os.path.join(mntdir, dir, discfn)
            if os.path.isfile(discpath):
                ret, errmsg = mount_dev('iso9660', discpath, mntdir=loopmntdir, flags='loop')
                if not ret:
                    syslog.syslog(syslog.LOG_ERR,
                                  "LoMount %s on %s as %s failed: %s" % \
                                  (discpath, loopmntdir,
                                   'iso9660', str(errmsg)))
                else:
                    probepkg = os.path.join(loopmntdir, '%s/packages' % CONF_DISTNAME, disc_first_pkgs[disc_no])
                    if os.path.isfile(probepkg):
                        dolog('Have found the first_pkg %s in iso %s\n' % (probepkg, discpath))
                        proberes = (discpath, probepkg)
                    ret, errmsg = umount_dev(loopmntdir)
                    if not ret:
                        syslog.syslog(syslog.LOG_ERR,
                                      "LoUMount %s from %s failed: %s" % \
                                      (discpath,
                                       loopmntdir,
                                       str(errmsg)))
                        return  (str(errmsg), [])
        if proberes:
            result.append(proberes)
    dolog('probe_all_disc return result is : %s\n' % str(result))
    if mntpoint == 0:
        ret, errmsg = umount_dev(mntdir)
        if not ret:
            syslog.syslog(syslog.LOG_ERR,
                          "UMount(%s) failed: %s" % (mntdir, str(errmsg)))
            if result != []:
                # we can't umount the mntdir, but if we have found the package result we must return it.
                return(0, result)
            else:
                return (str(errmsg), [])
    return  (0, result)

@register.server_handler('long')
def instpkg_prep(mia, operid, dev, mntpoint, dir, fstype, instmode):
    # Set the package install mode.
    global installmode
    installmode = instmode
    if CONF_PKGTYPE == 'rpm':
        dolog('InstallMode: Rpm Packages %s\n' % installmode)
    elif CONF_PKGTYPE == 'tar':
        dolog('InstallMode: Tar Packages\n')
    
    dolog('instpkg_prep(%s, %s, %s, %s)\n' % (dev, mntpoint, dir, fstype))
    #--- This code is according to rpm.spec in rpm-4.2-0.69.src.rpm. ---
    # This code is specific to rpm.
    var_lib_rpm = os.path.join(CONF_TGTSYS_ROOT, 'var/lib/rpm')
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
        mntdir = os.path.join(CONF_TGTSYS_ROOT, mntpoint)
    else:
        mntdir = os.path.join('/tmpfs/mnt', os.path.basename(dev))
        ret, errmsg = mount_dev(CONF_FSTYPE_MAP[fstype][0], dev, mntdir)
        if not ret:
            return  str(errmsg)
    return  0

@register.server_handler('long')
def instpkg_disc_prep(mia, operid, dev, mntpoint, dir, fstype, iso_fn):
    global  isoloop
    dolog('instpkg_disc_prep(%s, %s, %s, %s, %s)\n' % \
          (dev, mntpoint, dir, fstype, iso_fn))
    if mntpoint != 0:
        mntdir = os.path.join(CONF_TGTSYS_ROOT, mntpoint)
    else:
        mntdir = os.path.join('/tmpfs/mnt', os.path.basename(dev))
    if fstype == 'iso9660':
        # It is CDROM installation.
        # assert(mntpoint == 0) because CDROM can't be mount as part
        #    of target system.
        ret, errmsg = mount_dev(CONF_FSTYPE_MAP[fstype][0], dev, mntdir)
        if not ret:
            return  str(errmsg)
    elif iso_fn:
        # iso file is placed in mntdir.
        isopath = os.path.join(mntdir, dir, iso_fn)
        loopmntdir = os.path.join('/tmpfs/mnt/', isoloop)
        ret, errmsg = mount_dev('iso9660', isopath, mntdir=loopmntdir, flags='loop')
        if not ret:
            syslog.syslog(syslog.LOG_ERR,
                          "LoMount %s on %s as %s failed: %s" % \
                          (isopath, loopmntdir,
                           'iso9660', str(errmsg)))
            return  str(errmsg)
    return  0

# Now package_install support rpm only.
@register.server_handler('long')
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
        
class CBFileObj(file):
    def __init__(self, filepath, data):
        self.mia, self.operid, self.total_size = data
        file.__init__(self, filepath)
    def read(self, size):
        self.mia.set_step(self.operid, self.tell(), self.total_size)
        return file.read(self, size)

@register.server_handler('long')
def package_install(mia, operid, pkgname, firstpkg, noscripts):
    use_ts = False
    pkgpath = os.path.join(os.path.dirname(firstpkg), pkgname)
    #dolog('pkg_install(%s, %s)\n' % (pkgname, str(pkgpath)))
    
    def do_ts_install():
        global ts
        if ts is None:
            dolog('Create TransactionSet\n')
            ts = rpm.TransactionSet(CONF_TGTSYS_ROOT)
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
        global noscripts_pkg_list
        global use_noscripts
        mia.set_step(operid, 1, 1)
            
        try:
            cmd = '/bin/rpm'
            argv = ['-i', '--noorder','--nosuggest',
                    '--force','--nodeps',
                    '--ignorearch',
                    '--root', CONF_TGTSYS_ROOT,
                    pkgpath,
                ]
            if use_noscripts or noscripts:
                argv.append('--noscripts')
                noscripts_pkg_list.append(pkgpath)

            #cmd_res = {'err':[], 'std': [], 'ret':0}   # DEBUG
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
            cmd = 'cd %s && /usr/bin/rpm2cpio %s | /bin/cpio -dui --quiet' % (CONF_TGTSYS_ROOT, pkgpath)
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
            
    def do_tar_extract_install():
        tar_size = os.path.getsize(pkgpath)
        try:
            tarobj = tarfile.open(fileobj=CBFileObj(pkgpath, (mia, operid, tar_size)))
        except:
            errstr = 'Faild on create tarfile object on file "%s" size"%d"\n' % (pkgpath, tar_size)
            dolog(errstr)
            return errstr
        try:
            tarobj.extractall(path=CONF_TGTSYS_ROOT)
        except:
            if tarobj:
                tarobj.close()
            errstr = 'Faild on extract file "%s" size"%d" to directory "%s"\n' % (pkgpath, tar_size, CONF_TGTSYS_ROOT)
            dolog(errstr)
            return errstr
        try:
            tarobj.close()
        except:
            pass
        
    # Decide using which mode to install.
    ret = 'Nothing'
    if CONF_PKGTYPE == 'rpm':     # In the mipublic.py
        if installmode == 'rpminstallmode':
            if use_ts:
                # Use rpm-python module to install rpm pkg, but at this version it is very slowly.
                ret = do_ts_install()
            else:
                # Because I can not use rpm-python module to install quickly.
                # So use the bash mode to install the pkg, it is very fast.
                # If you can use rpm-python module install pkg quickly, you can remove it.
                ret = do_bash_rpm_install()
        elif installmode == 'copyinstallmode':
            # Use rpm2cpio name-ver-release.rpm | cpio -diu to uncompress the rpm files to target system.
            # Then we will do some configuration in instpkg_post.
            ret = do_copy_install()
    elif CONF_PKGTYPE == 'tar':
        ret = do_tar_extract_install()
    if ret:
        return ret
    else:
        return 0

@register.server_handler('long')
def instpkg_disc_post(mia, operid, dev, mntpoint, dir, fstype, iso_fn, first_pkg):
    # determine the rpmdb.tar.bz2 and etc.tar.bz2. If exist copy it to tmp_config_dir in target system.
    rpmpkgdir = os.path.dirname(first_pkg)
    rpmdb_abs = os.path.join(rpmpkgdir, rpmdb)
    etctar_abs = os.path.join(rpmpkgdir, etctar)
    tgt_tmp_config_dir = os.path.join(CONF_TGTSYS_ROOT, tmp_config_dir)
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
        mntdir = os.path.join(CONF_TGTSYS_ROOT, mntpoint)
    else:
        mntdir = os.path.join('/tmpfs/mnt', os.path.basename(dev))
    if fstype == 'iso9660':
        # It is CDROM installation.
        # assert(mntpoint == 0) because CDROM can't be mount as part
        #    of target system.
        ret, errmsg = umount_dev(mntdir)
        if not ret:
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
        ret, errmsg = umount_dev(loopmntdir)
        if not ret:
            syslog.syslog(syslog.LOG_ERR, 'LoUMount %s from %s failed: %s' % \
                          (iso_fn,
                           loopmntdir,
                           str(errmsg)))
            return str(errmsg)
    return  0

@register.server_handler('long')
def instpkg_post(mia, operid, dev, mntpoint, dir, fstype):
    global noscripts_pkg_list
    if installmode == 'rpminstallmode' and noscripts_pkg_list:
        # we will execute all the pre_in and post_in scripts there, if we use
        # the --noscripts option during rpm installation
        dolog('Execute Pre Post Scripts:\n\t%s\n' % str(noscripts_pkg_list))
        def run_pre_post_in_script(CONF_TGTSYS_ROOT):
            def get_pkg_name(pkgrpm):
                pkg = os.path.basename(pkgrpm)
                pkgname = ''
                try:
                    pkgname = pkg[:pkg.rindex('-')]
                    pkgname = pkg[:pkgname.rindex('-')]
                except ValueError, e:
                    return pkg
                return pkgname
            def write_script(script_cmd, script_file, mode='w'):
                tfd = open(script_file, mode)
                tfd.write(script_cmd)
                tfd.close()
            def excute_pre_post(h):
                pkgnvr = "%s-%s-%s" % (h['name'],h['version'],h['release'])
                script_dir = os.path.join(CONF_TGTSYS_ROOT, tmp_noscripts_dir)
                scripts = []
                if h[rpm.RPMTAG_PREIN]:
                    script_name = "%s.preinstall.sh" % pkgnvr
                    script_path = os.path.join(script_dir, script_name)
                    write_script(h[rpm.RPMTAG_PREIN], script_path)
                    scripts.append(script_name)
                if h[rpm.RPMTAG_POSTIN]:
                    script_name = "%s.postinstall.sh" % pkgnvr
                    script_path = os.path.join(script_dir, script_name)
                    write_script(h[rpm.RPMTAG_POSTIN], script_path)
                    scripts.append(script_name)
                for script_name in scripts:
                    spath = os.path.join('/', tmp_noscripts_dir, script_name)
                    write_script("**%s\n" % script_name, noscripts_log, 'a')  # do log
                    ret = os.system("/usr/sbin/chroot %s /bin/sh %s  2>&1 >> %s" % (CONF_TGTSYS_ROOT, spath, noscripts_log))
                    if ret != 0:
                        err_msg = 'Error run scripts(noscripts) in %s-%s-%s\n' \
                                % (h['name'],h['version'],h['release'])
                        dolog(err_msg)
                        write_script(err_msg, noscripts_log, 'a')   # do log
            write_script('Execute Pre Post Scripts:\n\t%s\n' % str(noscripts_pkg_list), noscripts_log, 'a')  # do log            
            script_dir = os.path.join(CONF_TGTSYS_ROOT, tmp_noscripts_dir)
            if not os.path.exists(script_dir):
                os.makedirs(script_dir)
            ts_m = rpm.TransactionSet(CONF_TGTSYS_ROOT)
            for pkg in noscripts_pkg_list:
                pkgname = get_pkg_name(pkg)
                mi = ts_m.dbMatch('name', pkgname)
                for h in mi:
                    if h['name'] == pkgname:
                        excute_pre_post(h)
            noscripts_pkg_list = []

        run_pre_post_in_script(CONF_TGTSYS_ROOT)

    if installmode == 'copyinstallmode':
        tgt_tmp_config_dir = os.path.join(CONF_TGTSYS_ROOT, tmp_config_dir)
        rpmdb_abs = os.path.join(tgt_tmp_config_dir, rpmdb)
        etctar_abs = os.path.join(tgt_tmp_config_dir, etctar)
        if os.path.exists(rpmdb_abs):
            ret = os.system('tar -xjf %s -C %s' % (rpmdb_abs, CONF_TGTSYS_ROOT))
            if ret != 0:
                dolog('ERROR: Extract %s from target system %s to target system Failed.\n' \
                %(rpmdb, rpmdb_abs[len(CONF_TGTSYS_ROOT):]))
            os.system('rm -r %s' % rpmdb_abs)
        else:
            dolog('Warning: cannot find the needed file %s.\n' % rpmdb_abs[len(CONF_TGTSYS_ROOT):])
        if os.path.exists(etctar_abs):
            ret = os.system('tar -xjf %s -C %s' % (etctar_abs, os.path.join(CONF_TGTSYS_ROOT, tmp_config_dir)))
            if ret != 0:
                dolog('ERROR: Extract %s from target system %s to target system Failed.\n' \
                %(etctar, etctar_abs[len(CONF_TGTSYS_ROOT):]))
        else:
            dolog('Warning: cannot find the needed file %s.\n' % etctar_abs[len(CONF_TGTSYS_ROOT):])
        # do chroot and excute the etc_install.sh
        ret = os.system('/usr/sbin/chroot %s /%s %s' \
                % (CONF_TGTSYS_ROOT, os.path.join(tmp_config_dir, etc_script), tmp_config_dir))
        if ret != 0:
            dolog('ERROR: run %s failed.\n' % os.path.join(tmp_config_dir, etc_script))
        else:
            dolog('Run %s successfully.\n' % os.path.join(tmp_config_dir, etc_script))
        os.system('rm -r %s' % os.path.join(CONF_TGTSYS_ROOT, tmp_config_dir))
        
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
        mntdir = os.path.join(CONF_TGTSYS_ROOT, mntpoint)
    else:
        mntdir = os.path.join('/tmpfs/mnt', os.path.basename(dev))
        ret, errmsg = umount_dev(mntdir)
        if not ret:
            syslog.syslog(syslog.LOG_ERR, 'UMount(%s) failed: %s' % \
                          (mntdir, str(errmsg)))
            return str(errmsg)
    try:
        isys.sync()
    except Expection, errmsg:
        syslog.syslog(syslog.LOG_ERR, 'sync failed: %s' % str(errmsg))
        return str(errmsg)
    return  0

if __name__ == '__main__':
    from miserver.utils import FakeMiactions
    mia = FakeMiactions()
    operid = 999
    hdpartlist = [
        ['/dev/sda1', 'ntfs', '/dev/sda1'], 
        ['/dev/sda2', 'ntfs', '/dev/sda2'], 
        ['/dev/sda5', 'linux-swap(v1)', '/dev/sda5'], 
        ['/dev/sda6', 'ext3', '/dev/sda6'], 
        ['/dev/sda7', 'ext4', '/dev/sda7'], 
        ['/dev/sda8', 'ntfs', '/dev/sda8'], 
        ['/dev/sda1', 'ntfs', '/dev/sda1'], 
        ['/dev/sda2', 'ntfs', '/dev/sda2'], 
        ['/dev/sda5', 'linux-swap(v1)', '/dev/sda5'], 
        ['/dev/sda6', 'ext3', '/dev/sda6'], 
        ['/dev/sda7', 'ext4', '/dev/sda7'], 
        ['/dev/sda8', 'ntfs', '/dev/sda8']]
    pkgarr_probe(mia, operid, hdpartlist)
    