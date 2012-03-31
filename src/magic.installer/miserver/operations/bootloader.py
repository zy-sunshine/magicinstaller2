#!/usr/bin/python
import os, time, string
import getdev, isys
from miutils.common import mount_dev, umount_dev
from miutils.miconfig import MiConfig
CONF = MiConfig.get_instance()
CONF_INITRD_FN = CONF.LOAD.CONF_INITRD_FN
CONF_KERNEL_FN = CONF.LOAD.CONF_KERNEL_FN
CONF_DISTKERNELVER = CONF.LOAD.CONF_DISTKERNELVER
CONF_TGTSYS_ROOT = CONF.LOAD.CONF_TGTSYS_ROOT
CONF_FSTYPE_MAP = CONF.LOAD.CONF_FSTYPE_MAP

from miutils.miregister import MiRegister
register = MiRegister()

from miserver.utils import Logger
Log = Logger.get_instance(__name__)
dolog = Log.i

@register.server_handler('long')
def do_mkinitrd(mia, operid, dummy):
    mia.set_step(operid, 0, -1)
    os.system('rm -f %s' % os.path.join(CONF_TGTSYS_ROOT, 'boot', CONF_INITRD_FN))
    isys.sync()
    time.sleep(1)
    # Remove Dirty Work
    #os.system('cp -f %s/tmp/fstab.* %s/etc/fstab' % (CONF_TGTSYS_ROOT, CONF_TGTSYS_ROOT))
    if CONF_USEUDEV:
        os.system('cp -f %s/etc/fstab %s/etc/mtab' % (CONF_TGTSYS_ROOT, CONF_TGTSYS_ROOT)) # make udev happy
    #dolog('/sbin/mkinitrd --fstab=/etc/fstab /boot/%s %s\n' % (CONF_INITRD_FN, CONF_DISTKERNELVER))
    #os.system('/usr/sbin/chroot %s /sbin/mkinitrd --fstab=/etc/fstab /boot/%s %s' % (CONF_TGTSYS_ROOT, CONF_INITRD_FN, CONF_DISTKERNELVER))
    dolog('/sbin/new-kernel-pkg --install --mkinitrd --depmod %s\n' % CONF_DISTKERNELVER)
    os.system('/usr/sbin/chroot %s /sbin/new-kernel-pkg --install --mkinitrd --depmod %s' % (CONF_TGTSYS_ROOT, CONF_DISTKERNELVER))
    return 0

@register.server_handler('long')
def prepare_grub(mia, operid, timeout, usepassword, password,
                 lba, options, entrylist, default, instpos, bootdev, mbrdev, windev, winfs):
    def get_grub_device_map():
        """The content of grub device map file is:
        (hd0)   /dev/hda
        (hd1)   /dev/hdd

        This function return a map of:
            {'hda': '(hd0)', 'hdd': '(hd1)'
        according to the map file."""
        #dm_file = os.path.join(CONF_TGTSYS_ROOT, 'grub.device.map')
        #os.system('echo quit | /usr/sbin/chroot %s grub --no-floppy --batch --device-map %s' % (CONF_TGTSYS_ROOT, 'grub.device.map'))
        # use grub in mi instead of in tgtsys (no dev file in tgtsys/dev with udev, which cause trouble)
        dm_file = os.path.join('/tmpfs', 'grub.device.map')
        #os.system('echo quit | /sbin/grub --no-floppy --batch --device-map %s' % dm_file)
        os.system('echo quit | grub --no-floppy --batch --device-map %s' % dm_file)
        device_map = {}
        try:
            dmf = file(dm_file, 'r')
            l = dmf.readline()
            while l:
                (grubdev, linuxdev) = string.split(l[:-1], '\t')
                device_map[os.path.basename(linuxdev)] = grubdev
                l = dmf.readline()
            dmf.close()
        except:
            dolog('Read the grub device file %s failed.\n' % dm_file)
        try:
            os.unlink(dm_file)
        except:
            pass
        dolog('The GRUB device map is: %s\n' % str(device_map))
        return  device_map

    def linuxdev2grubdev(devmap, linuxdev):
        """Convert Linux device name to Grub device name, and
        returns a tuple of grub device name and mbr name, e.g.
            /dev/hda1 --> ('(hd0,0)', '(hd0)' )
            /dev/hda  --> ('(hd0,-1)', '(hd0)')
        If not found, return (None, None)"""
        ld = os.path.basename(linuxdev)
        if len(ld) > 3:
            base = ld[:3]
            partnum = int(ld[3:]) -1
        else:
            base = ld
            partnum = -1
        if devmap.has_key(base):
            gd = devmap[base]
            return  ('(%s,%d)' % (gd[1:-1], partnum), gd)
        dolog('%s(%s) is not a key of GRUB device map.\n' % (base, linuxdev))
        return  (None, None)

    mia.set_step(operid, 0, -1)

    device_map = get_grub_device_map()
    dolog('(timeout, usepassword, password, lba, options, default, instpos, bootdev, mbrdev, windev, winfs) = %s\n' % \
          str((timeout, usepassword, password, lba, options, default, instpos, bootdev, mbrdev, windev, winfs)))
    dolog('entrylist = %s\n' % str(entrylist))

    #has_dos = len(entrylist) == 2
    entry_text = ''
    default_number = 0
    number = 0
    for (label, dev, default_or_not) in entrylist:
        #if has_dos and dev == windev:
        if dev == windev:
            text = 'title %s\n' % label
            text = text + '\trootnoverify %s\n' % \
                   (linuxdev2grubdev(device_map, dev)[0])
            text = text + '\tchainloader +1\n'
        else:
            text = 'title %s\n' % label
            if bootdev:
                (grubdev, grubmbrdev) = linuxdev2grubdev(device_map, bootdev)
                grubpath = ''
            else:
                (grubdev, grubmbrdev) = linuxdev2grubdev(device_map, dev)
                grubpath = 'boot'
            # get grub setup device
            grubsetupdev = None
            if instpos == 'mbr':
                grubsetupdev = linuxdev2grubdev(device_map, mbrdev)[1]
            elif instpos == 'boot':
                grubsetupdev = grubdev
            elif instpos == 'win':
                grubsetupdev = windev

            if grubdev == None or grubsetupdev == None:
                return 1 # Install grub failed.

            # init new bootsplash
            text = text + '\troot %s\n' % grubdev
            text = text + '\tkernel %s  ro root=%s %s\n' % \
                   (os.path.join('/', grubpath, CONF_KERNEL_FN), dev, options)
            text = text + '\tinitrd %s\n' % \
                   (os.path.join('/', grubpath, CONF_INITRD_FN))

            # normal graphics
            #text = text + 'title %s (Graphics Mode)\n' % label
            #text = text + '\troot %s\n' % grubdev
            #text = text + '\tkernel %s init 5 ro root=%s %s\n' % \
            #       (os.path.join('/', grubpath, CONF_KERNEL_FN), dev, options)
            #text = text + '\tinitrd %s\n' % \
            #       (os.path.join('/', grubpath, CONF_INITRD_FN))
            # add by yourfeng for init 3 init 1 init 5
            #init console
            #text = text + 'title %s (Console Mode)\n' % label
            #text = text + '\troot %s\n' % grubdev
            #text = text + '\tkernel %s init 3 ro root=%s %s\n' % \
            #        (os.path.join('/', grubpath, CONF_KERNEL_FN), dev, options)
            #text = text + '\tinitrd %s\n' % \
            #       (os.path.join('/', grubpath, CONF_INITRD_FN))
            #init 1
            text = text + 'title %s (Single Mode)\n' % label
            text = text + '\troot %s\n' % grubdev
            text = text + '\tkernel %s single ro root=%s %s\n' % \
                   (os.path.join('/', grubpath, CONF_KERNEL_FN), dev, options)
            text = text + '\tinitrd %s\n' % \
                   (os.path.join('/', grubpath, CONF_INITRD_FN))

        if default_or_not == 'true':
            default_number = number
        number = number + 1
        entry_text = entry_text + text

    # create grubdir
    if instpos == 'win':
        ret, win_mntdir = mount_dev(winfs, windev)
        if not ret:
            return 1
        #grubdir = os.path.join(win_mntdir, 'grub')
        grubdir = win_mntdir        # Put it in the root 
    else:
        grubdir = os.path.join(CONF_TGTSYS_ROOT, 'boot/grub')
    if not os.path.isdir(grubdir):
        os.makedirs(grubdir)

    # Check the grub.conf.bk[N].
    grubconf = os.path.join(grubdir, 'grub.conf')
    if os.path.exists(grubconf):
        # Try to backup the exists grub.conf
        bkcnt = 0
        while 1:
            bkfilename = os.path.join(grubdir, 'grub.conf.bk')
            if bkcnt > 0:
                bkfilename = bkfilename + str(bkcnt)
            if not os.path.exists(bkfilename):
                break
            bkcnt = bkcnt + 1
        try:
            os.rename(grubconf, bkfilename)
        except Exception, errmsg:
            dolog('rename(%s, %s) failed: %s\n' % \
                  (grubconf, bkfilename, str(errmsg)))
    # Generate the grub.conf
    dolog('bootloader: generate file %s\n' % grubconf)
    gc = file(grubconf, 'w')
    header = """# grub.conf generated by MagicInstaller.

# Note that you do not have to rerun grub after making changes to this file.
"""
    gc.write(header)
    gc.write('default=%d\n' % default_number)
    gc.write('timeout=%d\n' % timeout)
    #gc.write('splashimage=%s\n' % \
    #         os.path.join(grubdev, grubpath, 'grub/splash.xpm.gz'))
    gc.write('gfxmenu=%s\n' % \
             os.path.join(grubdev, grubpath, 'grub/message'))
    gc.write(entry_text)
    gc.close()
    try:
        os.chmod(grubconf, 0600)
        # Create a symlink to grub.conf
        os.remove(os.path.join(grubdir, 'menu.lst'))
    except Exception:
        pass
    try:
        os.symlink('grub.conf', os.path.join(grubdir, 'menu.lst'))
    except Exception:
        os.system('cp %s %s' % (os.path.join(grubdir, 'grub.conf'),
                                os.path.join(grubdir, 'menu.lst')))

    if instpos == 'win':
        dolog('bootload: open file %s\n' % os.path.join(win_mntdir, 'boot.ini'))
        boot_ini = open(os.path.join(win_mntdir, 'boot.ini'), 'r+')
        found = False
        for line in boot_ini.readlines():
            dolog('%s' % line)
            if 'grldr' in line.lower():
                found = True
                break
        if not found:
            dolog('APPEND')
            boot_ini.seek(0, 2)
            boot_ini.write('\nc:\\grldr="Grub"\n')
        boot_ini.close()

        os.system('cp -a %s %s/' % ('/usr/share/grldr',
                                   win_mntdir))
        umount_dev(win_mntdir)
        return 0

    else:
        if os.path.exists('/tmpfs/debug/nobootloader'):
            dolog('TURN ON: nobootloader\n')
            return 0
        # Get the command arguments for grub.
        #floppy = kudzu.probe(kudzu.CLASS_FLOPPY,
        #                     kudzu.BUS_IDE | kudzu.BUS_SCSI | kudzu.BUS_MISC,
        #                     kudzu.PROBE_ALL)
        floppy = getdev.probe(getdev.CLASS_FLOPPY)

        # Because --batch will cause a bus error, we don not use this
        # option.
        #grubopt = '--batch'
        grubopt = ''
        if floppy == []:
            grubopt = grubopt + ' --no-floppy'

        os.system('cp -p %s/*stage1*   %s 2>/dev/null || true' % \
                  (os.path.join(CONF_TGTSYS_ROOT, 'usr/lib/grub'),
                   os.path.join(CONF_TGTSYS_ROOT, 'boot/grub')))
        os.system('cp -p %s/*/*stage1* %s 2>/dev/null || true' % \
                  (os.path.join(CONF_TGTSYS_ROOT, 'usr/lib/grub'),
                   os.path.join(CONF_TGTSYS_ROOT, 'boot/grub')))
        os.system('dd if=%s/stage2 of=%s/stage2 bs=256k' % \
                  (os.path.join(CONF_TGTSYS_ROOT, 'usr/lib/grub'),
                   os.path.join(CONF_TGTSYS_ROOT, 'boot/grub')))
        os.system('sync')
                   
        return (grubdev, grubsetupdev, grubopt)

# Setup grub with all of the partitions mounted as readonly.
# grub makes use of raw devices instead of filesystems that the operation
# systems serve, so there exists a potential problem that some cache
# inconsistency may corrupt the filesystems. So I have to run grub without
# any target partitions mounted for security.
@register.server_handler('long')
def setup_grub(mia, operid, grubdev, grubsetupdev, grubopt):
    def check_grub_result(filename):
        try:
            r = 1
            f = file(filename, 'r')
            l = f.readline()
            while l:
                dolog(l)
                if l[:9] == 'Error 15:':
                    r = None
                    break
                l = f.readline()
            f.close()
            return  r
        except Exception, errmsg:
            return  None

    # install grub
    grub_result = '/tmpfs/grub.%d.result'
    for sleep_time in [1, 2, 4, 8, 16, 32]:
        #dolog('/sbin/grub %s\n' % grubopt)
        dolog('grub %s\n' % grubopt)
        dolog('grub> root %s\n' % grubdev)
        dolog('grub> setup %s\n' % grubsetupdev)
        dolog('grub> quit\n')
        #os.system('echo -ne "root %s\nsetup %s\nquit\n" | /sbin/grub %s > %s' % \
        os.system('echo -ne "root %s\nsetup %s\nquit\n" | grub %s > %s' % \
                  (grubdev, grubsetupdev, grubopt, grub_result % sleep_time))
        if check_grub_result(grub_result % sleep_time):
            break
        isys.sync()
        time.sleep(sleep_time)
    return 0

# setup_lilo is not debug and not finished.
@register.server_handler('long')
def setup_lilo(mia, operid, timeout, usepassword, password,
               lba, options, entrylist, default, bootdev, mbrdev):
    dolog('(timeout, usepassword, password, lba, options, default, bootdev) = %s\n' % \
          str((timeout, usepassword, password, lba, options, default, bootdev)))
    dolog('entrylist = %s\n' % str(entrylist))
    etcpath = os.path.join(CONF_TGTSYS_ROOT, 'etc')
    if not os.path.isdir(etcpath):
        os.makedirs(etcpath)
    liloconf = os.path.join(etcpath, 'lilo.conf')
    lc = file(lilo.conf, 'w')
    header = """# lilo.conf generated by MagicInstaller.

# Note that you must rerun lilo after making changes to this file.
"""
    lc.write(header)
    has_dos = len(entrylist) == 2
    entry_text = ''
    default_label = None
    for (dummy, label, dev, default_or_not) in entrylist:
        if has_dos and dev == mbrdev + '1':
            text = 'other=%s\n' % dev
            text = text + '\toptional\n'
            text = text + 'label=%s\n' % label
        else:
            text = 'image=/boot/%s\n' % CONF_KERNEL_FN
            text = text + '\tlabel=%s\n' % label
            text = text + '\tread-only\n'
            text = text + '\troot=%s\n' % dev
            linuxdev = dev
        if default_or_not:
            default_label = label
        entry_text = entry_text + text
    if len(entrylist) > 1:
        lc.write('prompt\n')
    lc.write('timeout=%d\n' % timeout)
    lc.write('default=%s\n' % default_label)
    lc.write('boot=%s\n' % os.path.join(os.path.dirname(linuxdev), os.path.basename(linuxdev)[:3]))
    lc.write('map=/boot/map\n')
    lc.write('install=/boot/boot.b\n')
    lc.write('message=/boot/message\n')
    if lba:
        lc.write('linear\n')
    lc.write(entry_text)
    lc.close()
    os.chmod(liloconf, 0600)
    if os.path.exists('/tmpfs/debug/nobootloader'):
        dolog('TURN ON: nobootloader\n')
        return 0
    # Run lilo.
    return 0

@register.server_handler('long')
def win_probe(mia, operid, hdpartlist):
    mia.set_step(operid, 0, -1)
    result = []
    all_drives = hdpartlist
    for (device, fstype, new_device) in all_drives:
        dolog('Search %s for Windows files\n' % device)
        if fstype not in CONF_FSTYPE_MAP or \
               CONF_FSTYPE_MAP[fstype][0] not in ('vfat', 'ntfs', 'ntfs-3g'):
            continue
        ret, mntdir = mount_dev(CONF_FSTYPE_MAP[fstype][0], device)
        if ret:
            if os.path.exists(os.path.join(mntdir, 'bootmgr')):
                result.append((new_device, 'vista/7'))
            elif os.path.exists(os.path.join(mntdir, 'ntldr')):
                result.append((new_device, 'winnt'))
            elif os.path.exists(os.path.join(mntdir, 'io.sys')):
                result.append((new_device, 'win98'))
            else:
                 result.append((new_device, 'win'))
            umount_dev(mntdir)
    return result
