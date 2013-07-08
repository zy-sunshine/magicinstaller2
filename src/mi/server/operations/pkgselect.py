#!/usr/bin/python
import os, glob, sys, syslog
import rpm, time
from mi.server.utils.decorators import probe_cache
from mi.server.utils.device import MiDevice

from mi.utils.miregister import MiRegister
import ftplib
register = MiRegister()

from mi.server.utils import logger, CF

import parted, _ped
class PartedUtil():
    def __init__(self):
        self.all_harddisks = {}
        self.probe_alldisk()

    def get_all_partitions(self):
        result = []
        for devpath in self.all_harddisks.keys():
            partinfo = self._get_partitions(devpath)
            ## Because we can not detect cdrom, so we regarded this condition
            #  to be cdrom
            if len(partinfo) == 1 and partinfo[0][0] == -1 and \
                partinfo[0][4] == 'N/A' and \
                self.all_harddisks[devpath][0].readOnly is True:
                result.append((devpath, 'iso9660'))
            for info in partinfo:
                if info[0] != -1:
                    result.append(('%s%s' % (devpath, info[0]), info[4]))
        return result

    def get_device_list(self):
        hd_list = filter(lambda d: d.type != parted.DEVICE_DM \
                         #and d.readOnly != True, # CD-ROM will be read only.
                         ,
                         parted.getAllDevices())
        return hd_list

    def probe_alldisk(self):
        devlist = self.get_device_list()
        if devlist:
            for dev in devlist:
                newdisklabel = None
                try:
                    disk = parted.Disk(dev)
                except _ped.DiskLabelException:
                    # For the disk without any disk label, create it.
                    # disk label is disk partition table format
                    dltype = parted.diskType['msdos']
                    disk = parted.freshDisk(device=dev, ty=dltype)
                    #newdisklabel = 'y'
                    #disk = dev.disk_new_fresh(parted.disk_type_get('msdos'))
                # Model might contain GB2312, it must be convert to Unicode.
                model = str(dev.model)
                try:
                    model = model.decode('gb18030').encode('utf8')
                except UnicodeDecodeError, e:
                    pass
                
                self.all_harddisks[dev.path] = (dev, disk, newdisklabel)

    def _get_partitions(self, devpath):
        result = []
        def part2result(part):
            flags = []
            avaflags = []
            label = 'N/A'
            if part.active:
                for f in parted.partitionFlag.keys():
                    if part.isFlagAvailable(f):
                        avaflags.append(f)
                        if part.getFlag(f):
                            flags.append(f)
                if disk.supportsFeature(parted.DISK_TYPE_PARTITION_NAME):
                    label = part.name

            if part.fileSystem:
                fs_type_name = part.fileSystem.type
            else:
                fs_type_name = 'N/A'

            return (part.number, flags, part.type, part.geometry.length,
                    fs_type_name, label, part.geometry.start, part.geometry.end, avaflags)

        if self.all_harddisks.has_key(devpath):
            disk = self.all_harddisks[devpath][1]
            if disk:
                try:
                    part = disk.getFirstPartition()
                except:
                    logger.warn('devpath %s can not get one partition.' % devpath)
                else:
                    while part:
                        if part.type & parted.PARTITION_METADATA == 0:
                            result.append(part2result(part))
                        part = part.nextPartition()
        return result


@register.server_handler('long', 'pkgarr_probe')
@probe_cache('pkgarr')
def pkgarr_probe(mia, operid):
    logger.i("pkgarr_probe starting...")
    def probe_position(localfn, pos_id, new_device, fstype, reldir, isofn):
        logger.i('probe_position: %s, %s, %s, %s, %s, %s' % (localfn, pos_id, new_device, fstype, reldir, isofn))
        if not os.path.exists(localfn):
            return None
        try:
            execfile(localfn)
        except Exception, errmsg:
            logger.e("Load %s failed(%s)." % (localfn, str(errmsg)))
            return None
        remotefn = 'allpa/%s.%d.%s' % (os.path.basename(new_device), pos_id, os.path.basename(localfn))
        logger.i('ftp upload %s to remote %s...' % (localfn, remotefn))

        try:
            ftp = ftplib.FTP("127.0.0.1")
            ftp.login("root", "magic")
            ftp.storbinary("STOR %s" % remotefn, open(localfn, "rb"), 1024)
            ftp.close()
        except:
            logger.e('Upload failed')
            return None
        logger.i('Upload success')
        return [remotefn, new_device, fstype, reldir, isofn]
        # The format like ('allpa/hdc.1.pkgarr.py', '/dev/hdc', 'iso9660', 'MagicLinux/base', '')
        # ['allpa/sda6.100.pkgarr.py', '/dev/sda6', 'ext3', 'MagicLinux/base', 'MagicLinux-3.0-1.iso']
    mia.set_step(operid, 0, -1)

    result = []
    pu = PartedUtil()
    all_drives = pu.get_all_partitions()
    
#     for k, v in cdrom_dev.items():
#         v['fstype'] = 'iso9660'   # fill cdrom file type, because it is None for default.
    
    logger.i('all_drives: %s' % all_drives)
    pos_id = -1
    for devpath, fstype in all_drives:
        if not CF.D.FSTYPE_MAP.has_key(fstype) or fstype.startswith('linux-swap'):
            continue
        if CF.D.FSTYPE_MAP[fstype][0] == '':
            continue
        midev = MiDevice(devpath, CF.D.FSTYPE_MAP[fstype][0])
        logger.d('Search %s pkgarr(%s) in dirs %s' % (CF.D.BOOTCDFN, CF.D.PKGARR_FILE, repr(CF.D.PKGARR_SER_HDPATH+CF.D.PKGARR_SER_CDPATH)))
        for f, reldir in midev.iter_searchfiles([CF.D.PKGARR_FILE, CF.D.BOOTCDFN], CF.D.PKGARR_SER_HDPATH+CF.D.PKGARR_SER_CDPATH):
            if f.endswith('.iso'):
                midev_iso = MiDevice(f, 'iso9660')
                for pkgarr, relative_dir in midev_iso.iter_searchfiles([CF.D.PKGARR_FILE], CF.D.PKGARR_SER_CDPATH):
                    pos_id += 1
                    r = probe_position(pkgarr, 100 + pos_id,
                        devpath, CF.D.FSTYPE_MAP[fstype][0], relative_dir, CF.D.BOOTCDFN)
                    if r:
                        r[-1] = os.path.join(reldir, r[-1]) #### revise iso relative path
                        result.append(r)
            else:
                pos_id += 1
                r = probe_position(f, pos_id,
                    devpath, fstype, reldir, '')
                if r: result.append(r)

    logger.w("pkgarr_probe %s" % result)
    return result

### Test Case
class MiaTest(object):
    def __init__(self):
        from mi.server.utils import FakeMiactions
        self.mia = FakeMiactions()
        self.operid = 999
        
class Test(MiaTest):
    def __init__(self):
        MiaTest.__init__(self)
        
    def test_pkgarr_probe(self):
        hdpartlist = [
            ['/dev/sda1', 'ntfs', '/dev/sda1'], 
            ['/dev/sda2', 'ntfs', '/dev/sda2'], 
            ['/dev/sda5', 'linux-swap(v1)', '/dev/sda5'], 
            ['/dev/sda6', 'ext3', '/dev/sda6'], 
            ['/dev/sda7', 'ext4', '/dev/sda7'], 
            ['/dev/sda8', 'ntfs', '/dev/sda8'], ]
        print pkgarr_probe(self.mia, self.operid)
        
if __name__ == '__main__':
    test = Test()
    test.test_pkgarr_probe()

    
    