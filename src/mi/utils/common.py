#!/usr/bin/python
import os
import sys
from mi.utils import logger, CF

class AttrDict(dict):
    """A dict class, holding the dict. Two extra method to get dict
    value, e.g.:
    attrs = attrs_dict(cat)
    attrs.tips
    attrs('tips')"""
    def __init__(self, d={}):
        self.d = d
    def __call__(self, arg):
        return self.get(arg, None)
    def __getattr__(self, attr):
        return self.get(attr, None)

class NamedTuple(tuple):
    """Access a tuple by attribute name. e.g.:
    class AutoPartTuple(NamedTuple):
        attr_oder = ['mountpoint', 'size', 'filesystem']

    part = ('/', '32G', 'ext2')
    part = AutoPartTuple(part)
    print part.mountpoint,  part.size, part.filesystem
    """
    attr_order = []
    def __init__(self, seq):
        tuple.__init__(self, seq)

    def __getattr__(self, attr):
        idx = self.attr_order.index(attr)
        return self[idx]

def run_bash(cmd, argv=[], root=None, env=None, cwd=None):
    import subprocess
    import select, time
    def chroot():
        if root:
            os.chroot(root)
    env = env and env or os.environ
    cmd_res = {}
    cmd_res['out'] = []
    cmd_res['err'] = []
    if cwd and root:
        cwd = '/%s/%s' % (root.strip('/'), cwd.strip('/'))
        
    logger.i('runbash: %s %s' % (cmd, ' '.join(argv)))
    res = subprocess.Popen([cmd] + argv, 
                            stdout = subprocess.PIPE, 
                            stderr = subprocess.PIPE, 
                            preexec_fn = chroot, cwd = cwd,
                            close_fds = True,
                            env = env)
    while True:
        ret1 = res.poll()
        if ret1 == 0:
            #print res.pid, 'end'
            break
        elif ret1 is None:
            #print  'running'
            fs = select.select([res.stdout, res.stderr], [], [], 1)
            if res.stdout in fs[0]:
                tmp = res.stdout.readlines()
                cmd_res['out'].extend(tmp)
                #print 'read std:', tmp
            elif res.stderr in fs[0]:
                tmp = res.stderr.readlines()
                cmd_res['err'].extend(tmp)
        else:
            #print res.pid, 'term'
            break
        time.sleep(0.5)

    cmd_res['ret']=res.returncode
    return cmd_res

def treedir(dir, complete_path=True):
    all_dirs = []
    all_files = []
    topdown = True
    for root, dirs, files in os.walk(dir, topdown):
        for d in dirs:
            if complete_path:
                all_dirs.append(os.path.join(root, d))
            else:
                all_dirs.append(d)
        for f in files:
            if complete_path:
                all_files.append(os.path.join(root, f))
            else:
                all_files.append(f)
    return all_dirs, all_files

def remove_empty_dir(dir):
    if not os.path.exists(dir):
        return True, ''
    if os.path.ismount(dir):
        return False, 'Remove dir failed %s is a mount point' % dir
    else:
        if not os.listdir(dir):
            try:
                os.rmdir(dir)
            except OSError, e:
                return False, str(e)
        else:
            return False, 'Remove dir failed: %s is not a empty dir' % dir
    return True, ''

def mount_dev(fstype, devfn, mntdir=None,flags=None):
    def get_mnt_dir(devfn):
        mntdir = '/tmpfs/mnt/%s' % os.path.basename(devfn)
        ret, msg = remove_empty_dir(mntdir)
        if not ret:
            for sub in range(30):
                mntdir = '/tmpfs/mnt/%s_%s' % (os.path.basename(devfn), sub)
                ret, msg = remove_empty_dir(mntdir)
                if not ret:
                    continue
                else:
                    return True, mntdir
            return False, 'Can not get mntdir automatically.'
        else:
            return True, mntdir

    if not mntdir:
        # Not special point the mnt dir, we should get it automatically.
        ret, msg = get_mnt_dir(devfn)
        if ret:
            mntdir = msg
        else:
            return False, msg
    else:
        if not os.path.exists(mntdir):
            try:
                os.makedirs(mntdir)
            except OSError, e:
                return False, str(e)

    logger.i("mount_dev: Device = %s Mount = %s Fstype = %s\n" % \
        (devfn, mntdir, fstype))
    if not os.path.exists(mntdir):
        os.makedirs(mntdir)

    cmd = ''
    argv = []
    if fstype in ['ntfs', 'ntfs-3g']:
        cmd = 'ntfs-3g'
        argv = [devfn, mntdir]
    else:
        cmd = 'busybox'
        argv.append('mount')
        if fstype:
            argv = argv + ['-t', fstype]
        if flags:
            argv = argv + ['-o', flags]
        argv = argv + [devfn, mntdir]
    logger.i("Run mount command: %s %s\n" % (cmd, ' '.join(argv)))
    cmdres = run_bash(cmd, argv)
    if cmdres['ret']:
        errmsg = "mount_dev: mount failed: %s\n" % str([cmdres['out'], cmdres['err']])
        return False, errmsg
    else:
        return True, mntdir

def umount_dev(mntdir, rmdir=True):
    os.system('sync')
    cmd = 'busybox'
    argv = ['umount', mntdir]
    logger.i("Run umount command: %s %s\n" % (cmd, ' '.join(argv)))
    cmdres = run_bash(cmd, argv)
    if cmdres['ret']:
        errmsg = "umount_dev: umount failed: %s\n" % str([cmdres['out'], cmdres['err']])
        return False, errmsg
    else:
        return True, ''


def search_file(filename, pathes,
                prefix = '', postfix = '',
                exit_if_not_found = True):
    for p in pathes:
        f = os.path.join(prefix, p, postfix, filename)
        if os.access(f, os.R_OK):
            return f
    if exit_if_not_found:
        os.write(sys.stderr.fileno(), "Can't find %s in %s\n" % (filename, str(pathes)))
        sys.exit(1)
    return None

def convert_str_size(size):
    "Convert SIZE of 1K, 2M, 3G to bytes"
    if not size:
        return 0
    k = 1
    try:
        size = int(float(size))
    except ValueError:
        if size[-1] in ('k', 'K'):
            k = 1024
        elif size[-1] in ('m', 'M'):
            k = 1024 * 1024
        elif size[-1] in ('g', 'G'):
            k = 1024 * 1024 * 1024
        try:
            size = int(float(size[:-1]))
        except ValueError:
            return None
    return size * k

class Status:
    OP_STATUS_NONE = 0
    OP_STATUS_DOING = 1
    OP_STATUS_DONE = 2
    def __init__(self):
        pass
    
STAT = Status()

def get_devinfo(devfn, all_part_infor):
    if not devfn: return AttrDict()
    for dev in all_part_infor:
        for tup in all_part_infor[dev]:
            if '%s%s' % (dev, tup[0]) == devfn:
                r = AttrDict()
                r['dev'] = devfn
                r['parted_fstype'] = tup[6]
                r['mountpoint'] = tup[7]
                r['not_touched'] = tup[8]
                try:
                    r['fstype'] = CF.D.FSTYPE_MAP[tup[6]][0]
                    r['flags'] = CF.D.FSTYPE_MAP[tup[6]][4]
                except KeyError:
                    raise KeyError, 'Unregconized filesystem type %s.' % tup[6]
                return r
    raise KeyError, 'Device %s not exists in all_part_infor.' % devfn

def cdrom_available(blk_path):
    if not os.path.exists(blk_path): return False
    else: return os.system('dd if=%s bs=1 count=1 of=/dev/null &>/dev/null' % blk_path) == 0
    
