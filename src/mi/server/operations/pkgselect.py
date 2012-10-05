#!/usr/bin/python
import os, glob, sys, syslog
import rpm, time
from mi import isys, getdev #@UnresolvedImport
from mi.server.utils.decorators import probe_cache
from mi.server.utils.device import MiDevice

from mi.utils.miregister import MiRegister
register = MiRegister()

from mi.server.utils import logger, CF

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
        logger.i('tftpc update %s to remote %s...' % (localfn, remotefn))
#        cli.put(localfn, remotefn)
        os.system('tftp 127.0.0.1 69 -p -l %s -r %s' % (localfn, remotefn))
        return [remotefn, new_device, fstype, reldir, isofn]
        # The format like ('allpa/hdc.1.pkgarr.py', '/dev/hdc', 'iso9660', 'MagicLinux/base', '')
        # ['allpa/sda6.100.pkgarr.py', '/dev/sda6', 'ext3', 'MagicLinux/base', 'MagicLinux-3.0-1.iso']
    mia.set_step(operid, 0, -1)
    #cli = tftpc.TFtpClient()
    #cli.connect('127.0.0.1')
    result = []
    
    all_drives = getdev.get_part_info(getdev.CLASS_CDROM | getdev.CLASS_HD)
    #map(lambda cd: all_drives.append((os.path.join('/dev', cd.device),
    #                                  'iso9660',
    #                                  os.path.join('/dev', cd.device))),
    #                                  cdlist)
    logger.i('all_drives: %s' % all_drives)
    pos_id = -1
    for k, value in all_drives.items():
        devpath = value['devpath']
        fstype = value['fstype']
        if not CF.D.FSTYPE_MAP.has_key(fstype):
            continue
        if CF.D.FSTYPE_MAP[fstype][0] == '':
            continue
        midev = MiDevice(devpath, CF.D.FSTYPE_MAP[fstype][0])
        for f, reldir in midev.iter_searchfiles([CF.D.PKGARR_FILE, CF.D.BOOTCDFN], CF.D.PKGARR_SER_HDPATH):
            if f.endswith('iso'):
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
                r = probe_position(pkgarr, pos_id,
                    devpath, fstype, reldir, '')
                if r: result.append(r)
#    del(cli)
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
        pkgarr_probe(self.mia, self.operid)
        
if __name__ == '__main__':
    test = Test()
    test.test_pkgarr_probe()

    
    