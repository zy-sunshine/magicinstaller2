import os.path
import types
from SCons.Action import ActionFactory

### Package Build Class
def listfy_arg(listfy_arg):
    def listfy_f(f):
        def new_f(*args, **kwds):
            special_arg = args[listfy_arg]
            if type(special_arg) is types.ListType:
                result = []
                args_dup = list(args)
                #print args_dup, type(args_dup)
                for arg in special_arg:
                    args_dup[listfy_arg] = arg
                    result.append(f(*args_dup, **kwds))
                return result
            else:
                return f(*args, **kwds)
        new_f.func_name = f.func_name
        return new_f
    return listfy_f

class BaseMaker(object):
    archive_map = {'.tar.gz'    : 'tar -zxf %(srcfile)s -C %(destdir)s',
                   '.tgz'       : 'tar -zxf %(srcfile)s -C %(destdir)s',
                   '.tar.bz2'   : 'tar -jxf %(srcfile)s -C %(destdir)s',
                   '.tbz2'      : 'tar -jxf %(srcfile)s -C %(destdir)s',
                   '.tar'       : 'tar -xf %(srcfile)s -C %(destdir)s',
                   '.zip'       : 'unzip %(srcfile)s -d %(destdir)s',
                   '.rpm'       : 'rpm2cpio %(srcfile)s' + \
                        ' | (cd %(destdir)s; cpio -i --make-directories)',
                   }
    source_list = []
    build_cmds = []

    @listfy_arg(2)
    def path_prefix(self, path_prefix, filename):
        return os.path.join(path_prefix, filename)

    @listfy_arg(1)
    def get_abspath(self, path):
        return os.path.isabs(path) and path \
               or self.env.Dir(path).get_abspath()

    @listfy_arg(1)
    def get_extract_cmd(self, srcfile, destdir='$build_root'):
        templ = '/bin/cp -a %(srcfile)s %(destdir)s'
        for ext in self.archive_map:
            if srcfile.endswith(ext):
                templ = self.archive_map[ext]
                break
        return templ % \
               {'srcfile': srcfile,
                'destdir': destdir}

    @listfy_arg(1)
    def get_patch_cmd(self, patch_file, destdir='$build_prefix', patch_opt='-p1'):
        if patch_file.endswith('.bz2'):
            cat = 'bzcat'
        elif patch_file.endswith('.bzip'):
            cat = 'zcat'
        else:
            cat = 'cat'
        return '%s %s | patch -d %s %s' % \
               (cat, patch_file, destdir, patch_opt)

class StepMaker(BaseMaker):
    target_list = []
    name = ''
    BUILD = ''
    ROOT = ''
    steps = []
    def __init__(self, env):
        self.env = env.Clone()

    def initenv(self):
        env = self.env
        env['name'] = self.name
        env['BUILD'] = self.BUILD
        env['ROOT'] = self.ROOT

    def all_steps(self, steps=None):
        if steps is None:
            steps = self.steps
        all_srcs = []
        all_cmds = []
        for step in steps:
            srcs, cmds = getattr(self, step)()
            all_srcs.extend(srcs)
            all_cmds.extend(cmds)
        return all_srcs, all_cmds

    def make(self):
        self.initenv()
        env = self.env
        self.source_list, self.build_cmds = self.all_steps()
        env.Command(self.target_list,
                    self.source_list,
                    self.build_cmds)

class BasePkgMaker(BaseMaker):
    # Package Info
    alias = ''
    name = ''
    version = ''
    package = '$name-$version'
    package_bin = '${package}.bin.tar.bz2'

    source_list = []
    patch_list = []
    target_list = []
    install_map = {}
    install_list = []                   # converted from install_map
    depend_list = []

    # Build Directories
    source_prefix = ''                  # source directory
    build_root = ''                     # top directory for building packages
    build_prefix = ''                   # directory for building this package
    install_prefix = ''                 # install directory

    extract_cmds = []                   # customed extract cmd list
    patch_cmds = []                     # customed patch cmd list
    conf_cmds = []                      # customed configure cmd list
    build_cmds = []                     # customed build cmd list
    install_cmds = []                   # customed install cmd list
    pack_cmds = []                      # customed pack cmd list

    def __init__(self, env):
        self.env = env.Clone()
        self.alias = self.alias or self.name

    def get_target_list(self):
        return self.path_prefix('$build_prefix', self.target_list)

    def get_install_list(self):
        install_list = []
        for dest in self.install_list:
            for target in self.install_list[dest]:
                install_list.append((self.path_prefix('$build_prefix',  target),
                                     self.path_prefix('$install_prefix', dest)))

        #print 'get_install_list:', install_list
        return install_list

    def initenv(self):
        env = self.env

        # basic info
        env['name'] = self.name
        env['version'] = self.version
        env['package'] = self.package

        env['build_root'] = self.get_abspath(self.build_root)
        env['source_prefix'] = self.get_abspath(self.source_prefix)
        if not self.build_prefix:
            env['build_prefix'] = '$build_root/$name-$version'
        else:
            env['build_prefix'] = self.get_abspath(self.build_prefix)
        # install_prefix
        env['install_prefix'] = self.get_abspath(self.install_prefix)

        env['pwd'] = os.getcwd()

        self.source_list = self.path_prefix('$source_prefix', self.source_list)
        self.target_list = self.path_prefix('$build_prefix', self.target_list)
        self.patch_list = self.path_prefix('$pwd', self.patch_list)
        self.install_list =  []
        for dest in self.install_map:
            for target in self.install_map[dest]:
                self.install_list.append((self.path_prefix('$build_prefix',  target),
                                          self.path_prefix('$install_prefix', dest)))

    def prepare(self):
        env = self.env
        source_list = self.source_list
        patch_list = self.patch_list

        if not source_list:
            msg = env.subst("Empty Source List: $package")
            raise Exception, msg

        extract_cmds = self.get_extract_cmd(source_list)
        patch_cmds = self.get_patch_cmd(patch_list)
        env.Command('$build_prefix/.prepared',
                    source_list + patch_list,
                    ['rm -rf $build_prefix',
                     'mkdir -p $build_root'] +
                    extract_cmds +
                    patch_cmds +
                    [self.get_touch_cmd()])

        env.Clean('$build_prefix/.prepared', env.subst('$build_prefix'))

    def configure(self):
        env = self.env
        conf_cmds = self.conf_cmds
        env.Command('$build_prefix/.configured',
                    '$build_prefix/.prepared',
                    conf_cmds +
                    [self.get_touch_cmd()])

    def build(self):
        env = self.env
        target_list = self.target_list
        install_list = self.install_list
        build_cmds = self.build_cmds
        depend_list = self.depend_list
        #print 'target_list', target_list
        #print 'build_cmds', build_cmds
        env.Command(target_list,
                    '$build_prefix/.configured',
                    build_cmds)
        if depend_list:
            env.Depends(target_list, depend_list)

        for target, dest in install_list:
            if target not in target_list:
                #print 'sideeffect', target
                env.SideEffect(target, target_list)

    def install(self):
        env = self.env
        install_list = self.install_list
        install_cmds = self.install_cmds

        if install_cmds:
            env.Alias(self.alias,
                      env.Command([target[1] for target in install_list],
                                  [target[0] for target in install_list],
                                  install_cmds))
        elif install_list:
            for target, dest in install_list:
                if dest[-1] != '/':
                    env.Alias(self.alias,
                              env.InstallAs(dest, target))
                else:
                    env.Alias(self.alias,
                              env.Install(dest, target))

    def make(self):
        self.initenv()
        self.prepare()
        self.configure()
        self.build()
        self.install()

    def get_touch_cmd(self, target=None):
        return '/bin/date > %s' % (target or '$TARGET')

class BinPkgMaker(BasePkgMaker):
    conf_cmds = ['cd $build_prefix; ' +
                 './configure --prefix=$install_prefix']
    build_cmds = ['make -C $build_prefix']
    install_cmds = ['make -C $build_prefix install']
    pack_cmds = None

    def initenv(self):
        # call parent
        BasePkgMaker.initenv(self)
        env = self.env
        install_prefix = self.install_prefix
        if not install_prefix:
            install_prefix = '$build_prefix/_inst'
        env['install_prefix'] = install_prefix
        env['package_bin'] = self.package_bin
        env['pack_prefix'] = self.get_abspath(self.pack_prefix)

    def build(self):
        env = self.env
        build_cmds = self.build_cmds
        env.Command('$build_prefix/.built',
                    '$build_prefix/.configured',
                    build_cmds +
                    [self.get_touch_cmd()])

    def install(self):
        env = self.env
        install_cmds = self.install_cmds
        env.Command('$build_prefix/.installed',
                    '$build_prefix/.built',
                    install_cmds +
                    [self.get_touch_cmd()])

    def fetch_pack_cmds(self):
        if self.pack_cmds is not None:
            pack_cmds = self.pack_cmds
        else:
            if self.package_bin.endswith('.tar.bz2'):
                opt = 'j'
            else:
                opt = 'z'
            pack_cmds = [('tar -c%sf $pack_prefix/$package_bin' + \
                          ' -C $install_prefix .') % opt]
        return pack_cmds

    def pack(self):
        env = self.env
        pack_cmds = self.fetch_pack_cmds()
        env.Alias(self.alias,
                  env.Command('$pack_prefix/$package_bin',
                              '$build_prefix/.installed',
                              pack_cmds))

    def make(self):
        # call parent
        BasePkgMaker.make(self)
        self.pack()

class CrossPkgMaker(BasePkgMaker):
    CROSS_COMPILE = ''
    ARCH = ''

    ASFLAGS = ''
    CFLAGS = ''
    CPPDEFINES = {}
    CPPFLAGS = ''
    CPPPATH = []
    LIBPATH = []
    LIBS = []
    LINKFLAGS = ''

    CC_EXTRA = ''                       # appears in CC

    PKG_CFLAGS = ''
    PKG_LINKFLAGS = ''

    _CONFIGURE_OPT = '''CC="$CC" \
CXX="$CXX" \
CPP="$CPP" \
GCC="$GCC" \
LD="$LD" \
RANLIB="$RANLIB" \
STRIP="$STRIP" \
AR="$AR" \
AS="$AS" \
RANLIB="$RANLIB" \
CFLAGS="$_CCCOMCOM $PKG_CFLAGS" \
LDFLAGS="$_LIBFLAGS $PKG_LINKFLAGS"'''

    conf_cmds = ['cd $build_prefix;' +
                 ' $_CONFIGURE_OPT ./configure ' +
                 ' --target=$ARCH --host=$ARCH']
    build_cmds = ['make $_CONFIGURE_OPT -C $build_prefix']

    def initenv(self):
        BasePkgMaker.initenv(self)
        env = self.env

        env['CROSS_COMPILE'] = self.CROSS_COMPILE
        env['ARCH'] = self.ARCH

        env['ASFLAGS'] = self.ASFLAGS
        env['CFLAGS'] = self.CFLAGS
        env['CPPDEFINES'] = self.CPPDEFINES
        env['CPPFLAGS'] = self.CPPFLAGS
        env['CPPPATH'] = self.CPPPATH
        env['LIBPATH'] = self.LIBPATH
        env['LIBS'] = self.LIBS
        env['LINKFLAGS'] = self.LINKFLAGS

        env['CC_EXTRA'] = self.CC_EXTRA
        env['PKG_CFLAGS'] = self.PKG_CFLAGS
        env['PKG_LINKFLAGS'] = self.PKG_LINKFLAGS

        env['CC'] = '${CROSS_COMPILE}cc $CC_EXTRA'
        env['CXX'] = '${CROSS_COMPILE}cxx $CC_EXTRA'
        env['CPP'] = '${CROSS_COMPILE}cc $CC_EXTRA'
        env['GCC'] = '${CROSS_COMPILE}gcc $CC_EXTRA'
        env['LD'] = '${CROSS_COMPILE}ld'
        env['RANLIB'] = '${CROSS_COMPILE}ranlib'
        env['STRIP'] = '${CROSS_COMPILE}strip'
        env['AR'] = '${CROSS_COMPILE}ar'
        env['AS'] = '${CROSS_COMPILE}as'
        env['RANLIB'] = '${CROSS_COMPILE}ranlib'

        env['_CONFIGURE_OPT'] = self._CONFIGURE_OPT

### Custom Action
def search_exec_strfunc(topdir, prunepathes, cmd_str):
    return 'Execute "%s" in %s except %s' % \
           (cmd_str, topdir, prunepathes)

def search_exec(topdir, prunepathes, cmd_str):
    if type(prunepathes) is types.ListType:
        pass
    else:
        prunepathes = prunepathes.split()
    dirlist = [topdir]
    #execlist = []
    fullprunepathes = {}
    for pp in prunepathes:
        fullprunepathes[topdir + '/' + pp] = 'y'
    while dirlist != []:
        curdir = dirlist.pop(0)
        for file in os.listdir(curdir):
            filepath = curdir + '/' + file
            if os.path.islink(filepath):
                # Do nothing on link.
                pass
            elif os.path.isdir(filepath):
                if not fullprunepathes.has_key(filepath):
                    dirlist.append(filepath)
            elif os.path.isfile(filepath):
                # Check common file.
                f = os.popen('file ' + filepath, 'r')
                input = f.readline()
                f.close()
                if input.find('ELF 32-bit LSB') >= 0 and \
                       input.find('not stripped'):
                    print cmd_str % filepath
                    os.system(cmd_str % filepath)
                    #execlist.append(filepath)
    #return execlist

SearchExecAction = ActionFactory(search_exec, search_exec_strfunc)
