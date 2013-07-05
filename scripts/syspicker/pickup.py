'''
Created on 2013-6-20

@author: Zhang Yang
'''
import sys
from syspicker.utils import pyldd
import os
import stat
import shutil

class DuplicateFileError(Exception):
    pass
class DuplicateCopyFileError(Exception):
    pass
class RunBashError(Exception):
    pass
def usage():
    return '''
    %s filepath
    ''' % sys.argv[0]
    
def main0():
    ret = pyldd.ldd(sys.argv[1])
    print ret

def run_bash(cmd, argv=[], root=None, env=None, cwd=None):
    import subprocess
    def chroot():
        if root:
            os.chroot(root)
    env = env and env or os.environ
    cmd_res = {}
    if cwd and root:
        cwd = '/%s/%s' % (root.strip('/'), cwd.strip('/'))
    
    res = subprocess.Popen([cmd] + argv, 
                            stdout = subprocess.PIPE, 
                            stderr = subprocess.PIPE, 
                            preexec_fn = chroot, cwd = cwd,
                            close_fds = True,
                            env = env)
    res.wait()
    cmd_res['std']=res.stdout.readlines()
    cmd_res['err']=res.stderr.readlines()
    cmd_res['ret']=res.returncode
    return cmd_res

def runbash(cmd):
    cmd = 'sudo %s' % cmd
    print 'runbash: %s' % cmd
    cmds = cmd.split()
    res = run_bash(cmds[0], cmds[1:])
    if res['ret'] != 0:
        raise RunBashError('cmd %s std: %s err: %s' % (cmd, ' '.join(res['std']), ' '.join(res['err'])))
    
def is_binary(filename):
    """Return true if the given filename is binary.
    @raise EnvironmentError: if the file does not exist or cannot be accessed.
    @attention: found @ http://bytes.com/topic/python/answers/21222-determine-file-type-binary-text on 6/08/2010
    @author: Trent Mick <TrentM@ActiveState.com>
    @author: Jorge Orpinel <jorge@orpinel.com>"""
    fin = open(filename, 'rb')
    try:
        CHUNKSIZE = 1024
        while 1:
            chunk = fin.read(CHUNKSIZE)
            if '\0' in chunk: # found null byte
                return True
            if len(chunk) < CHUNKSIZE:
                break # done
    # A-wooo! Mira, python no necesita el "except:". Achis... Que listo es.
    finally:
        fin.close()

    return False
    
def _recurseldd(depmap, fpath):
    for f in pyldd.ldd(fpath):
        depmap.setdefault(f, []).append(fpath)
        recurseldd(depmap, f)

def recurseldd(depmap, fpaths):
    if type(fpaths) is str:
        fpaths = [fpaths]
        
    for fpath in fpaths:
        if os.path.isfile(fpath) and is_binary(fpath):
            _recurseldd(depmap, fpath)

def loadflist(lst, flist):
    with open(lst, 'rt') as fp:
        lines = [ line.strip() for line in set(fp.readlines()) if line ]
        flist.extend(lines)

def checkfiles(files):
    xflist = []
    for fpath in files:
        if not os.path.exists(fpath):
            xflist.append(fpath)
            
    if xflist != []:
        print '%s not exists, please check!' % str(xflist)
        os._exit(0)
        
class Picker(object):
    def __init__(self, use_bash=False, flist = []):
        self.depmap = {}
        self.flist = flist
        self.use_bash = use_bash
        
    def AddFiles(self, flist):
        '''
            flist is the new file list add to depmap
            and flist member can not duplicate with previous file list.
            return the new file tuple which have been add to depmap.
        '''
        intersect = set(self.flist).intersection(set(flist))
        if intersect:
            raise DuplicateFileError('Do not add duplicate files %s' % repr(intersect))
            
        self.flist.extend(flist)
        oldset = set(self.depmap)
        recurseldd(self.depmap, self.flist)
        return list(set(self.depmap) - oldset)

#    def paseFiles(self, flist = []):
#        if flist:
#            self.flist = flist
#        checkfiles(self.flist)
#
#        recurseldd(self.depmap, self.flist)
    
    def getDepMap(self):
        return self.depmap
    
    def copyFiles(self, flist, tgtsys):
        for fpath in set(flist):
            if os.path.isdir(fpath):
                sdir = fpath
                tdir = os.path.join(tgtsys, sdir.lstrip('/'))
                recurse_make_dir(sdir, tdir, self.use_bash)
            else:
                copyfile2tgtsys(fpath, tgtsys, self.use_bash)
    
    def copyAll(self, tgtsys):
        self.copyFiles(self.getDepMap().keys(), tgtsys)
        self.copyFiles(self.flist, tgtsys)
        
def main1():
    checkfiles(sys.argv[1:])
    
    flist = []
    if len(sys.argv[1:]) == 1 and sys.argv[1].endswith('.lst'):
        loadflist(sys.argv[1], flist)
        
    checkfiles(flist)
    
    depmap = {}
    recurseldd(depmap, flist)
    print '\n'.join(depmap.keys())
#    for key, value in depmap.items():
#        print "%s ==> %s" % (key, value)
    print len(depmap)
    print len(set(depmap))
    
    print 'copy to target system'
    tgtsys = '/tmpfs/tgtsys'
    for fpath in flist:
        copyfile2tgtsys(fpath, tgtsys)
        
    for fpath in depmap.keys():
        copyfile2tgtsys(fpath, tgtsys)
        
def copyfile2tgtsys(fpath, tgtsys, use_bash=False):
    sdir = os.path.dirname(fpath)
    tdir = os.path.join(tgtsys, sdir.lstrip('/'))
    recurse_make_dir(sdir, tdir, use_bash)
    tgtfile = os.path.join(tdir, os.path.basename(fpath))
    
    if os.path.exists(tgtfile):
        return
    
    copy_link(fpath, tgtfile, use_bash)
    
def copy_link(src, dst, use_bash=False):
    if os.path.exists(dst):
        raise DuplicateCopyFileError('src: %s, dst: %s' % (src, dst))
    
    if os.path.islink(src):
        linkto = os.readlink(src)
        srcdir = os.path.dirname(src)
        dstdir = os.path.dirname(dst)
        if linkto.startswith('/'):
            tgtdir = dst[:-len(src)]
            s_linkto_path = os.path.normpath(linkto)
            d_linkto_path = os.path.normpath(os.path.join(tgtdir, linkto.lstrip('/')))
        else:
            s_linkto_path = os.path.normpath(os.path.join(srcdir, linkto))
            d_linkto_path = os.path.normpath(os.path.join(dstdir, linkto))
        if not os.path.exists(d_linkto_path):
            copy_link(s_linkto_path, d_linkto_path, use_bash)
        print '#!# link %s -> %s' % (dst, linkto)
        st = os.stat(src)
        if use_bash:
            runbash('ln -s %s %s' % (linkto, dst))
            runbash('chown %s:%s %s' % (st.st_uid, st.st_gid, dst))
        else:
            os.symlink(linkto, dst)
            os.lchown(dst, st.st_uid, st.st_gid)
    else:
        if os.path.isdir(src):
            print '#!# copy dir %s %s' % (src, dst)
            recurse_make_dir(src, dst, use_bash)
        else:
            print '#!# copy file %s %s' % (src, dst)
            if not os.path.exists(os.path.dirname(dst)):
                recurse_make_dir(os.path.dirname(src), os.path.dirname(dst), use_bash)
            
            st = os.stat(src)
            mode = stat.S_IMODE(st.st_mode)
            
            if use_bash:
                runbash('cp %s %s' % (src, dst))
                runbash('chmod %s %s' % (mode_to_str(mode), dst))
                runbash('chown %s:%s %s' % (st.st_uid, st.st_gid, dst))
            else:
                shutil.copy(src, dst)
                os.lchown(dst, st.st_uid, st.st_gid)
            # shutil.copymode(src, dst) # not use this because shutil.copy include copymode

def mode_to_str(mode):
    a1 = (mode&0b000000000111) >> 0
    a2 = (mode&0b000000111000) >> 3
    a3 = (mode&0b000111000000) >> 6
    a4 = (mode&0b111000000000) >> 9
    return '%s%s%s%s' % (a4, a3, a2, a1)

def recurse_make_dir(sdir, tdir, use_bash=False):
    '''
    sdir is the source path to be copied
    dpath_base is the base path copy to, it is the destination root.
    '''
    if sdir == '/':
        return
    
    if not os.path.exists(tdir):
        tdir_dirname = os.path.dirname(tdir)
        if not os.path.exists(tdir_dirname):
            recurse_make_dir(os.path.dirname(sdir), tdir_dirname, use_bash)
        
        if os.path.islink(sdir):
            copy_link(sdir, tdir, use_bash)
        else:
            st = os.stat(sdir)
            mode = stat.S_IMODE(st.st_mode)
            if use_bash:
                runbash('mkdir %s' % tdir)
                runbash('chmod %s %s' % (mode_to_str(mode), tdir))
                runbash('chown %s:%s %s' % (st.st_uid, st.st_gid, tdir))
            else:
                os.mkdir(tdir)
                os.chmod(tdir, mode)
                os.lchown(tdir, st.st_uid, st.st_gid)
            
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print usage()
        sys.exit(0)
        
    main1()
    