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

def usage():
    return '''
    %s filepath
    ''' % sys.argv[0]
    
def main0():
    ret = pyldd.ldd(sys.argv[1])
    print ret
    
def _recurseldd(depmap, fpath):
    for f in pyldd.ldd(fpath):
        depmap.setdefault(f, []).append(fpath)
        recurseldd(depmap, f)

def recurseldd(depmap, fpaths):
    if type(fpaths) is str:
        fpaths = [fpaths]
        
    for fpath in fpaths:
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
    def __init__(self, flist = []):
        self.depmap = {}
        self.flist = flist
        
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
            copyfile2tgtsys(fpath, tgtsys)
    
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
        
def copyfile2tgtsys(fpath, tgtsys):
    tdir = recurse_make_target_dir(os.path.dirname(fpath), tgtsys)
    tgtfile = os.path.join(tdir, os.path.basename(fpath))
    
    if os.path.exists(tgtfile):
        return
    
    if os.path.islink(fpath):
        srcdir = os.path.dirname(fpath)
        tgtdir = os.path.dirname(tgtfile)
        linkto = os.readlink(fpath)
        # copy linkto file to target system
        s_linkto_path = os.path.normpath(os.path.join(srcdir, linkto))
        d_linkto_path = os.path.normpath(os.path.join(tgtdir, linkto))
        
        if not os.path.exists(d_linkto_path):
            print 'copy link real file %s' % s_linkto_path
            copyfile2tgtsys(s_linkto_path, tgtsys)
        print 'link %s -> %s' % (tgtfile, linkto)
        os.symlink(linkto, tgtfile)
    else:
        print 'cp %s to %s' % (fpath, tgtfile)
        shutil.copy(fpath, tgtfile)
        
#    shutil.copymode(fpath, tdir) # not use this because shutil.copy include copymode
    
def recurse_make_target_dir(sdir, dpath_base):
    '''
    sdir is the source path to be copied
    dpath_base is the base path copy to, it is the destination root.
    '''
    if sdir == '/':
        return
    
    tdir = os.path.join(dpath_base, sdir.lstrip('/'))
    if not os.path.exists(tdir):
        tdir_dirname = os.path.dirname(tdir)
        if not os.path.exists(tdir_dirname):
            recurse_make_target_dir(os.path.dirname(sdir), dpath_base)
        
        os.mkdir(tdir)
        st = os.stat(sdir)
        mode = stat.S_IMODE(st.st_mode)
        os.chmod(tdir, mode)
    return tdir
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print usage()
        sys.exit(0)
        
    main1()
    