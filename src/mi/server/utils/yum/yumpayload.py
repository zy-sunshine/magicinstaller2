import os, sys, time, shutil, tempfile
import yum, rpm, rpmUtils
from mi.server.utils import _, logger, CF
from mi.server.utils import iutil

###
### ERROR HANDLING
###
class PayloadError(Exception):
    pass
# software selection
class NoSuchGroup(PayloadError):
    pass

class NoSuchPackage(PayloadError):
    pass

class DependencyError(PayloadError):
    pass

# installation
class PayloadInstallError(PayloadError):
    pass

#default_repos = ['productName? FIXME', "rawhide"]
default_repos = []

MI_TMP_YUM_CONF = "/tmp/mi-yum.conf"

from threading import Lock
_yum_lock = Lock()

_yum_cache_dir = "/tmp/yum.cache"

class CustomRepo():
    def __init__(self, name, baseurl):
        self.name = name
        self.baseurl = baseurl
        self.mirrorlist = None
        self.cost = None
        self.excludepkgs = None
        self.includepkgs = None
        self.proxyurl = None
        self.sslverify = False

class YumPayload(object):
    """ A YumPayload installs packages onto the target system using yum.

        User-defined (aka: addon) repos exist both in ksdata and in yum. They
        are the only repos in ksdata.repo. The repos we find in the yum config
        only exist in yum. Lastly, the base repo exists in yum and in
        ksdata.method.
    """
    def __init__(self):
        self._root_dir = "/tmp/yum.root"
        self._repos_dir = "/etc/yum.repos.d,/etc/mi.repos.d,/tmp/updates/mi.repos.d,/tmp/product/mi.repos.d"
        self._yum = None
        self._setup = False

        self.reset()
        class MockFlags():
            def __init__(self):
                self.upgrade = False
                self.selinux = False
                self.excludeDocs = False
                self.testing = False
                
        self.flags = MockFlags() ## TODO
        class MockProgress():
            def send_message(self, msg):
                print 'progress message: %s' % msg
                #logger.i('progress message: %s' % msg)
            def send_step(self, step=None, total=None):
                print 'send_step'
        self.progress = MockProgress() ## TODO post message to gui
        
    def _getReleaseVersion(self, url):
        return 'mgc30'
     
    def reset(self, root=None):
        """ Reset this instance to its initial (unconfigured) state. """
        from mi.utils.size import Size

        self._space_required = Size(bytes=0)

        self._groups = None
        self._packages = []

        self._resetYum(root=root)

    def setup(self):
        self._writeYumConfig()
        self._setup = True

        self.updateBaseRepo()

        # When setup is called, it's already in a separate thread. That thread
        # will try to select groups right after this returns, so make sure we
        # have group info ready.
        self.gatherRepoMetadata()

    def _resetYum(self, root=None, keep_cache=False):
        """ Delete and recreate the payload's YumBase instance. """
        import shutil
        if root is None:
            root = self._root_dir

        with _yum_lock:
            if self._yum:
                if not keep_cache:
                    for repo in self._yum.repos.listEnabled():
                        if repo.name == CF.S.BASE_REPO_NAME and \
                           os.path.isdir(repo.cachedir):
                            shutil.rmtree(repo.cachedir)

                del self._yum

            self._yum = yum.YumBase()

            self._yum.use_txmbr_in_callback = True  ## ??

            # Set some configuration parameters that don't get set through a config
            # file.  yum will know what to do with these.
            self._yum.preconf.enabled_plugins = ["blacklist", "whiteout", "fastestmirror"]
            self._yum.preconf.fn = MI_TMP_YUM_CONF
            self._yum.preconf.root = root
            # set this now to the best default we've got ; we'll update it if/when
            # we get a base repo set up
            self._yum.preconf.releasever = self._getReleaseVersion(None)
            # Hammer the yum logs to nothing, we log around yum.  This is
            # to prevent stuff from leaking to the screen.  Need a less hammer
            # approach to this so that we could have rich yum logs but clean
            # screens
            self._yum.preconf.debuglevel = 0
            self._yum.preconf.errorlevel = 0

        self.txID = None

    def _writeYumConfig(self):
        """ Write out mi's main yum configuration file. """
        buf = """
[main]
cachedir=%s
keepcache=0
logfile=/tmp/yum.log
metadata_expire=never
pluginpath=/usr/lib/yum-plugins,/tmp/updates/yum-plugins
pluginconfpath=/etc/yum/pluginconf.d,/tmp/updates/pluginconf.d
plugins=1
reposdir=%s
""" % (_yum_cache_dir, self._repos_dir)
# buf has other config options: 
# buf += "sslverify=0\n"
# buf += "multilib_policy=all\n"
# buf += "proxy=%s\n" % (proxy.noauth_url,)
# buf += "proxy_username=%s\n" % (proxy.username,)
# buf += "proxy_password=%s\n" % (proxy.password,)

        open(MI_TMP_YUM_CONF, "w").write(buf)

    # YUMFIXME: yum should allow a cache dir outside of the installroot
    def _yumCacheDirHack(self):
        # This is what it takes to get yum to use a cache dir outside the
        # install root. We do this so we don't have to re-gather repo meta-
        # data after we change the install root to CF.D.TGTSYS_ROOT, which can only
        # happen after we've enabled the new storage configuration.
        if not self._yum.conf.cachedir.startswith(self._yum.conf.installroot):
            return

        root = self._yum.conf.installroot
        self._yum.conf.cachedir = self._yum.conf.cachedir[len(root):]

    def _writeInstallConfig(self):
        """ Write out the yum config that will be used to install packages.

            Write out repo config files for all enabled repos, then
            create a new YumBase instance with the new filesystem tree as its
            install root.
        """
        self._repos_dir = "/tmp/yum.repos.d"
        if not os.path.isdir(self._repos_dir):
            os.mkdir(self._repos_dir)

        for repo in self._yum.repos.listEnabled():
            cfg_path = "%s/%s.repo" % (self._repos_dir, repo.id)
            #ks_repo = self.getRepo(repo.id)
            with open(cfg_path, "w") as f:
                f.write("[%s]\n" % repo.id)
                f.write("name=Install - %s\n" % repo.id)
                f.write("enabled=1\n")
                if repo.mirrorlist:
                    f.write("mirrorlist=%s" % repo.mirrorlist)
                elif repo.baseurl:
                    f.write("baseurl=%s\n" % repo.baseurl[0])
                else:
                    logger.error("repo %s has no baseurl or mirrorlist" % repo.id)
                    f.close()
                    os.unlink(cfg_path)
                    continue

        releasever = self._yum.conf.yumvar['releasever']
        self._writeYumConfig()
        self._resetYum(root=CF.D.TGTSYS_ROOT, keep_cache=True)
        logger.debug("setting releasever to previous value of %s" % releasever)
        self._yum.preconf.releasever = releasever

        self._yumCacheDirHack()
        self.gatherRepoMetadata()

        # trigger setup of self._yum.config
        logger.debug("installation yum config repos: %s"
                  % ",".join([r.id for r in self._yum.repos.listEnabled()]))

    # YUMFIXME: there should be a way to reset package sacks without all this
    #           knowledge of the yum internals or, better yet, some convenience
    #           functions for multi-threaded applications
    def release(self):
        from yum.packageSack import MetaSack
        with _yum_lock:
            logger.debug("deleting package sacks")
            if hasattr(self._yum, "_pkgSack"):
                self._yum._pkgSack = None

            self._yum.repos.pkgSack = MetaSack()

            for repo in self._yum.repos.repos.values():
                repo._sack = None

    def preStorage(self):
        self.release()
        with _yum_lock:
            self._yum.close()

    ###
    ### METHODS FOR WORKING WITH REPOSITORIES
    ###
    @property
    def repos(self):
        if not self._setup:
            return []

        return self._yum.repos.repos.keys()

#    @property
#    def addOns(self):
#        #return [r.name for r in self.data.repo.dataList()]
#        return []

#    @property
#    def baseRepo(self):
#        repo_names = [CF.S.BASE_REPO_NAME] + default_repos
#        base_repo_name = None
#        for repo_name in repo_names:
#            if repo_name in self.repos and \
#               self._yum.repos.getRepo(repo_name).enabled:
#                base_repo_name = repo_name
#                break
#
#        return base_repo_name

    def updateBaseRepo(self, fallback=True, root=None):
        logger.info("updating base repo")
        # start with a fresh YumBase instance
        self.reset(root=root)
        # see if we can get a usable base repo from self.data.method
        self._configureBaseRepo()
        self._yumCacheDirHack()
        
        # Now there you can add addon repo by self.addRepo
        
        # now you can disable and/or remove any repos that don't make sense

    def gatherRepoMetadata(self):
        # now go through and get metadata for all enabled repos
        logger.info("gathering repo metadata")
        for repo_id in self.repos:
            repo = self._yum.repos.getRepo(repo_id)
            if repo.enabled:
                try:
                    self._getRepoMetadata(repo)
                except PayloadError as e:
                    logger.error("failed to grab repo metadata for %s: %s"
                              % (repo_id, e))
                    self.disableRepo(repo_id)

        logger.info("metadata retrieval complete")

    def _configureBaseRepo(self):
        logger.info("configuring base repo")
        if CF.S.BASE_REPO_URL.startswith('/'):
            url = "file://" + CF.S.BASE_REPO_URL
        else:
            url = CF.S.BASE_REPO_URL
        
        with _yum_lock:
            self._yum.preconf.releasever = self._getReleaseVersion(url)
            self._yumCacheDirHack()
        try:
            self._addYumRepo(CF.S.BASE_REPO_NAME, url)
        except:
            logger.error("base repo (%s) not valid -- removing it"
                      % (url, ))
            self._removeYumRepo(CF.S.BASE_REPO_NAME)
            raise

    def _getRepoMetadata(self, yumrepo):
        """ Retrieve repo metadata if we don't already have it. """
        from yum.Errors import RepoError, RepoMDError

        # And try to grab its metadata.  We do this here so it can be done
        # on a per-repo basis, so we can then get some finer grained error
        # handling and recovery.
        logger.debug("getting repo metadata for %s" % yumrepo.id)
        with _yum_lock:
            try:
                yumrepo.getPrimaryXML()
            except RepoError as e:
                raise Exception('MetadataError', e.value)

            # Not getting group info is bad, but doesn't seem like a fatal error.
            # At the worst, it just means the groups won't be displayed in the UI
            # which isn't too bad, because you may be doing a kickstart install and
            # picking packages instead.
            logger.debug("getting group info for %s" % yumrepo.id)
            try:
                yumrepo.getGroups()
            except RepoMDError:
                logger.error("failed to get groups for repo %s" % yumrepo.id)

            
    def _addYumRepo(self, name, baseurl, mirrorlist=None, proxyurl=None, **kwargs):
        """ Add a yum repo to the YumBase instance. """
        from yum.Errors import RepoError

        # First, delete any pre-existing repo with the same name.
        with _yum_lock:
            if name in self._yum.repos.repos:
                self._yum.repos.delete(name)

        logger.debug("adding yum repo %s with baseurl %s and mirrorlist %s"
                    % (name, baseurl, mirrorlist))
        with _yum_lock:
            # Then add it to yum's internal structures.
            obj = self._yum.add_enable_repo(name,
                                            baseurl=[baseurl],
                                            mirrorlist=mirrorlist,
                                            **kwargs)

            # this will trigger retrieval of repomd.xml, which is small and yet
            # gives us some assurance that the repo config is sane
            # YUMFIXME: yum's instant policy doesn't work as advertised
            obj.mdpolicy = "meh"
            try:
                obj.repoXML
            except RepoError as e:
                raise Exception('MetadataError', 'name: %s baseurl:%s err: %s' % (name, baseurl, e.value))

        # Adding a new repo means the cached packages and groups lists
        # are out of date.  Clear them out now so the next reference to
        # either will cause it to be regenerated.
        self._groups = None
        self._packages = []

    def addRepo(self, repo):
        """ Add a custom repo. """
        logger.debug("adding new repo %s" % repo.name)
        self._addYumRepo(repo.name, repo.baseurl, repo.mirrorlist, cost=repo.cost,
                         exclude=repo.excludepkgs, includepkgs=repo.includepkgs,
                         proxyurl=repo.proxy, sslverify=repo.sslverify)
        
    def _removeYumRepo(self, repo_id):
        if repo_id in self.repos:
            with _yum_lock:
                self._yum.repos.delete(repo_id)
                self._groups = None
                self._packages = []

    def removeRepo(self, repo_id):
        """ Remove a repo as specified by id. """
        logger.debug("removing repo %s" % repo_id)

        # if this is an NFS repo, we'll want to unmount the NFS mount after
        # removing the repo
        mountpoint = None
        yum_repo = self._yum.repos.getRepo(repo_id)
        ks_repo = self.getRepo(repo_id)
        if yum_repo and ks_repo and ks_repo.baseurl.startswith("nfs:"):
            mountpoint = yum_repo.baseurl[0][7:]    # strip leading "file://"

        self._removeYumRepo(repo_id)
        
    def enableRepo(self, repo_id):
        """ Enable a repo as specified by id. """
        logger.debug("enabling repo %s" % repo_id)
        if repo_id in self.repos:
            self._yum.repos.enableRepo(repo_id)

    def disableRepo(self, repo_id):
        """ Disable a repo as specified by id. """
        logger.debug("disabling repo %s" % repo_id)
        if repo_id in self.repos:
            self._yum.repos.disableRepo(repo_id)

            self._groups = None
            self._packages = []

    ###
    ### METHODS FOR WORKING WITH ENVIRONMENTS
    ###
    @property
    def environments(self):
        """ List of environment ids. """
        from yum.Errors import RepoError
        from yum.Errors import GroupsError

        environments = []
        yum_groups = self._yumGroups
        if yum_groups:
            with _yum_lock:
                environments = [i.environmentid for i in yum_groups.get_environments()]

        return environments

    def environmentSelected(self, environmentid):
        groups = self._yumGroups
        if not groups:
            return False

        with _yum_lock:
            if not groups.has_environment(environmentid):
                raise NoSuchGroup(environmentid)

            environment = groups.return_environment(environmentid)
            for group in environment.groups:
                if not self.groupSelected(group):
                    return False
            return True

    def environmentHasOption(self, environmentid, grpid):
        groups = self._yumGroups
        if not groups:
            return False

        with _yum_lock:
            if not groups.has_environment(environmentid):
                raise NoSuchGroup(environmentid)

            environment = groups.return_environment(environmentid)
            if grpid in environment.options:
                return True
        return False

    def environmentDescription(self, environmentid):
        """ Return name/description tuple for the environment specified by id. """
        groups = self._yumGroups
        if not groups:
            return (environmentid, environmentid)

        with _yum_lock:
            if not groups.has_environment(environmentid):
                raise NoSuchGroup(environmentid)

            environment = groups.return_environment(environmentid)

            return (environment.ui_name, environment.ui_description)

    def selectEnvironment(self, environmentid):
        groups = self._yumGroups
        if not groups:
            return

        with _yum_lock:
            if not groups.has_environment(environmentid):
                raise NoSuchGroup(environmentid)

            environment = groups.return_environment(environmentid)
            for group in environment.groups:
                self.selectGroup(group)

    def deselectEnvironment(self, environmentid):
        groups = self._yumGroups
        if not groups:
            return

        with _yum_lock:
            if not groups.has_environment(environmentid):
                raise NoSuchGroup(environmentid)

            environment = groups.return_environment(environmentid)
            for group in environment.groups:
                self.deselectGroup(group)
            for group in environment.options:
                self.deselectGroup(group)

    ###
    ### METHODS FOR WORKING WITH GROUPS
    ###
    @property
    def _yumGroups(self):
        """ yum.comps.Comps instance. """
        from yum.Errors import RepoError, GroupsError
        with _yum_lock:
            if not self._groups:
                self._groups = self._yum.comps
        return self._groups

    @property
    def groups(self):
        """ List of group ids. """
        from yum.Errors import RepoError
        from yum.Errors import GroupsError

        groups = []
        yum_groups = self._yumGroups
        if yum_groups:
            with _yum_lock:
                groups = [g.groupid for g in yum_groups.get_groups()]

        return groups

    def languageGroups(self, lang):
        groups = []
        yum_groups = self._yumGroups

        if yum_groups:
            with _yum_lock:
                groups = [g.groupid for g in yum_groups.get_groups() if g.langonly == lang]

        return groups

    def groupDescription(self, groupid):
        """ Return name/description tuple for the group specified by id. """
        groups = self._yumGroups
        if not groups:
            return (groupid, groupid)

        with _yum_lock:
            if not groups.has_group(groupid):
                raise NoSuchGroup(groupid)

            group = groups.return_group(groupid)

            return (group.ui_name, group.ui_description)

    def _isGroupVisible(self, groupid):
        groups = self._yumGroups
        if not groups:
            return False

        with _yum_lock:
            if not groups.has_group(groupid):
                return False

            group = groups.return_group(groupid)
            return group.user_visible

    def _groupHasInstallableMembers(self, groupid):
        groups = self._yumGroups
        if not groups:
            return False

        with _yum_lock:
            if not groups.has_group(groupid):
                return False

            group = groups.return_group(groupid)
            pkgs = group.mandatory_packages.keys() + group.default_packages.keys()
            if pkgs:
                return True
            return False

    def _selectYumGroup(self, groupid, default=True, optional=False):
        # select the group in comps
        pkg_types = ['mandatory']
        if default:
            pkg_types.append("default")

        if optional:
            pkg_types.append("optional")

        logger.debug("select group %s" % groupid)
        with _yum_lock:
            try:
                self._yum.selectGroup(groupid, group_package_types=pkg_types)
            except yum.Errors.GroupsError:
                raise NoSuchGroup(groupid)

    def _deselectYumGroup(self, groupid):
        # deselect the group in comps
        logger.debug("deselect group %s" % groupid)
        with _yum_lock:
            try:
                self._yum.deselectGroup(groupid, force=True)
            except yum.Errors.GroupsError:
                raise NoSuchGroup(groupid)

    ###
    ### METHODS FOR WORKING WITH PACKAGES
    ###
    @property
    def packages(self):
        from yum.Errors import RepoError

        with _yum_lock:
            if not self._packages:
                try:
                    self._packages = self._yum.pkgSack.returnPackages()
                except RepoError as e:
                    logger.error("failed to get package list: %s" % e)

            return self._packages

    def _selectYumPackage(self, pkgid):
        """Mark a package for installation.

           pkgid - The name of a package to be installed.  This could include
                   a version or architecture component.
        """
        logger.debug("select package %s" % pkgid)
        with _yum_lock:
            try:
                mbrs = self._yum.install(pattern=pkgid)
            except yum.Errors.InstallError:
                raise NoSuchPackage(pkgid)

    def _deselectYumPackage(self, pkgid):
        """Mark a package to be excluded from installation.

           pkgid - The name of a package to be excluded.  This could include
                   a version or architecture component.
        """
        logger.debug("deselect package %s" % pkgid)
        with _yum_lock:
            self._yum.tsInfo.deselect(pkgid)

    ###
    ### METHODS FOR QUERYING STATE
    ###
    @property
    def spaceRequired(self):
        """ The total disk space (Size) required for the current selection. """
        return self._space_required

    def calculateSpaceNeeds(self):
        from mi.utils.size import Size

        # XXX this will only be useful if you've run checkSoftwareSelection
        total = 0
        with _yum_lock:
            for txmbr in self._yum.tsInfo.getMembers():
                total += getattr(txmbr.po, "installedsize", 0)

        total += total * 0.10   # add 10% to account for metadata, &c
        self._space_required = Size(bytes=total)

        return self._space_required

    ###
    ### METHODS FOR INSTALLING THE PAYLOAD
    ###
    def _removeTxSaveFile(self):
        # remove the transaction save file
        if hasattr(self._yum, '_ts_save_file') and self._yum._ts_save_file:
            try:
                os.unlink(self._yum._ts_save_file)
            except (OSError, IOError):
                pass
            else:
                self._yum._ts_save_file = None

    def _handleMissing(self, exn):
        logger.w('_handleMissing %s' % exn)
        return

    def _applyYumSelections(self):
        """ Apply the selections in ksdata to yum.

            This follows the same ordering/pattern as kickstart.py.
        """
        self._selectYumGroup("core")

### TODO These codes should be open by select group and packages feature.

#        for package in self.data.packages.packageList:
#            try:
#                self._selectYumPackage(package)
#            except NoSuchPackage as e:
#                self._handleMissing(e)
#
#        for group in self.data.packages.groupList:
#            default = False
#            optional = False
#            if group.include == GROUP_DEFAULT:
#                default = True
#            elif group.include == GROUP_ALL:
#                default = True
#                optional = True
#
#            try:
#                self._selectYumGroup(group.name, default=default, optional=optional)
#            except NoSuchGroup as e:
#                self._handleMissing(e)

#        for package in self.data.packages.excludedList:
#            try:
#                self._deselectYumPackage(package)
#            except NoSuchPackage as e:
#                self._handleMissing(e)
#
#        for group in self.data.packages.excludedGroupList:
#            try:
#                self._deselectYumGroup(group.name)
#            except NoSuchGroup as e:
#                self._handleMissing(e)

        self.selectKernelPackage()

    def checkSoftwareSelection(self):
        logger.info("checking software selection")
        self.txID = time.time()

        self.release()

        with _yum_lock:
            self._yum._undoDepInstalls()

        self._applyYumSelections()

        with _yum_lock:
            # doPostSelection
            # select kernel packages
            # select packages needed for storage, bootloader

            # check dependencies
            logger.info("checking dependencies")
            (code, msgs) = self._yum.buildTransaction(unfinished_transactions_check=False)
            self._removeTxSaveFile()
            if code == 0:
                # empty transaction?
                logger.debug("empty transaction")
            elif code == 2:
                # success
                logger.debug("success")
#            elif self.data.packages.handleMissing == KS_MISSING_IGNORE:
#                logger.debug("ignoring missing due to ks config")
#            elif self.data.upgrade.upgrade:
#                logger.debug("ignoring unresolved deps on upgrade")
            else:
                for msg in msgs:
                    logger.warning(msg)

                raise DependencyError(msgs)

        self.calculateSpaceNeeds()
        logger.info("%d packages selected totalling %s"
                 % (len(self._yum.tsInfo.getMembers()), self.spaceRequired))

    @property
    def kernelPackages(self):
        kernels = ["kernel"]

        if iutil.isPaeAvailable():
            kernels.insert(0, "kernel-PAE")
        return kernels
    
    def selectKernelPackage(self):
        kernels = self.kernelPackages
        selected = None
        # XXX This is optimistic. I'm curious if yum will DTRT if I just say
        #     "select this kernel" without jumping through hoops to figure out
        #     which arch it should use.
        for kernel in kernels:
            try:
                # XXX might need explicit arch specification
                self._selectYumPackage(kernel)
            except NoSuchPackage as e:
                logger.info("no %s package" % kernel)
                continue
            else:
                logger.info("selected %s" % kernel)
                selected = kernel
                # select module packages for this kernel

                # select the devel package if gcc will be installed
                if self._yum.tsInfo.matchNaevr(name="gcc"):
                    logger.info("selecting %s-devel" % kernel)
                    # XXX might need explicit arch specification
                    self._selectYumPackage("%s-devel" % kernel)

                break

        if not selected:
            logger.error("failed to select a kernel from %s" % kernels)

    def preInstall(self, packages=None, groups=None):
        """ Perform pre-installation tasks. """
        self.progress.send_message(_("Starting package installation process"))

        self._writeInstallConfig()
        self.checkSoftwareSelection()

        # doPreInstall
        # create mountpoints for protected device mountpoints (?)
        # write static configs (storage, modprobe.d/anaconda.conf, network, keyboard)
        #   on upgrade, just make sure /etc/mtab is a symlink to /proc/self/mounts

        if not self.flags.upgrade: #not self.data.upgrade.upgrade:
            # this adds nofsync, which speeds things up but carries a risk of
            # rpmdb data loss if a crash occurs. that's why we only do it on
            # initial install and not for upgrades.
            rpm.addMacro("__dbi_htconfig", #@UndefinedVariable
                         "hash nofsync %{__dbi_other} %{__dbi_perms}")

        if self.flags.excludeDocs: #if self.data.packages.excludeDocs:
            rpm.addMacro("_excludedocs", "1") #@UndefinedVariable

        if self.flags.selinux:
            for d in ["/tmp/updates",
                      "/etc/selinux/targeted/contexts/files",
                      "/etc/security/selinux/src/policy",
                      "/etc/security/selinux"]:
                f = d + "/file_contexts"
                if os.access(f, os.R_OK):
                    rpm.addMacro("__file_context_path", f) #@UndefinedVariable
                    break
        else:
            rpm.addMacro("__file_context_path", "%{nil}") #@UndefinedVariable

    def install(self):
        """ Install the payload. """
        from yum.Errors import PackageSackError, RepoError, YumBaseError

        logger.info("preparing transaction")
        logger.debug("initialize transaction set")
        with _yum_lock:
            self._yum.initActionTs()
            if rpmUtils and rpmUtils.arch.isMultiLibArch():
                self._yum.ts.ts.setColor(3)

            logger.debug("populate transaction set")
            try:
                # uses dsCallback.transactionPopulation
                self._yum.populateTs(keepold=0)
            except RepoError as e:
                logger.error("error populating transaction: %s" % e)
                exn = PayloadInstallError(str(e))
                #if errorHandler.cb(exn) == ERROR_RAISE:
                raise exn

            logger.debug("check transaction set")
            self._yum.ts.check()
            logger.debug("order transaction set")
            self._yum.ts.order()
            self._yum.ts.clean()

            # Write scriptlet output to a file to be logged later
            script_log = tempfile.NamedTemporaryFile(delete=False)
            self._yum.ts.ts.scriptFd = script_log.fileno()
            rpm.setLogFile(script_log) #@UndefinedVariable

            # create the install callback
            rpmcb = RPMCallback(self._yum, script_log, self.progress,
                                upgrade=False)

            if self.flags.testing:
                self._yum.ts.setFlags(rpm.RPMTRANS_FLAG_TEST) #@UndefinedVariable

            logger.info("running transaction")
            self.progress.send_step()
            try:
                self._yum.runTransaction(cb=rpmcb)
            except PackageSackError as e:
                logger.error("error running transaction: %s" % e)
                exn = PayloadInstallError(str(e))
                #if errorHandler.cb(exn) == ERROR_RAISE:
                raise exn
            except YumBaseError as e:
                logger.error("error [2] running transaction: %s" % e)
                for error in e.errors:
                    logger.error("%s" % error[0])
                exn = PayloadInstallError(str(e))
                #if errorHandler.cb(exn) == ERROR_RAISE:
                raise exn
            else:
                logger.info("transaction complete")
                self.progress.send_step()
            finally:
                self._yum.ts.close()
                iutil.resetRpmDb()
                script_log.close()

                # log the contents of the scriptlet logfile
                logger.info("==== start rpm scriptlet logs ====")
                with open(script_log.name) as f:
                    for l in f:
                        logger.info(l)
                logger.info("==== end rpm scriptlet logs ====")
                os.unlink(script_log.name)

    def writeMultiLibConfig(self):
        #if not self.data.packages.multiLib:
        #    return
        return

        # write out the yum config with the new multilib_policy value
        # FIXME: switch to using yum-config-manager once it stops expanding
        #        all yumvars and writing out the expanded pairs to the conf
        yb = yum.YumBase()
        yum_conf_path = "/etc/yum.conf"
        yb.preconf.fn = CF.D.TGTSYS_ROOT + yum_conf_path
        yb.conf.multilib_policy = "all"

        # this will appear in yum.conf, which is silly
        yb.conf.config_file_path = yum_conf_path

        # hack around yum having expanded $basearch in the cachedir value
        cachedir = yb.conf.cachedir.replace("/%s/" % yb.arch.basearch,
                                            "/$basearch/")
        yb.conf.cachedir = cachedir
        yum_conf = CF.D.TGTSYS_ROOT + yum_conf_path
        if os.path.exists(yum_conf):
            try:
                os.rename(yum_conf, yum_conf + ".anacbak")
            except OSError as e:
                logger.error("failed to back up yum.conf: %s" % e)

        try:
            yb.conf.write(open(yum_conf, "w"))
        except Exception as e:
            logger.error("failed to write out yum.conf: %s" % e)

    def postInstall(self):
        """ Perform post-installation tasks. """
        self._yum.close()

        # clean up repo tmpdirs
        self._yum.cleanPackages()
        self._yum.cleanHeaders()

        # remove cache dirs of install-specific repos
        for repo in self._yum.repos.listEnabled():
            if repo.name == CF.S.BASE_REPO_NAME or repo.id.startswith("mi-"):
                shutil.rmtree(repo.cachedir)

        # clean the yum cache on upgrade
        #if self.data.upgrade.upgrade:
        #    self._yum.cleanMetadata()

        # TODO: on preupgrade, remove the preupgrade dir

        self._removeTxSaveFile()

        self.writeMultiLibConfig()

class RPMCallback(object):
    def __init__(self, yb, log, progress, upgrade=False):
        self._yum = yb              # yum.YumBase
        self.install_log = log      # logfile for yum script logs
        self.upgrade = upgrade      # boolean

        self.package_file = None    # file instance (package file management)

        self.total_actions = 0
        self.completed_actions = None   # will be set to 0 when starting tx
        self.base_arch = iutil.getArch()
        self.progress = progress
        
    def _get_txmbr(self, key):
        """ Return a (name, TransactionMember) tuple from cb key. """
        if hasattr(key, "po"):
            # New-style callback, key is a TransactionMember
            txmbr = key
            name = key.name
        else:
            # cleanup/remove error
            name = key
            txmbr = None

        return (name, txmbr)

    def callback(self, event, amount, total, key, userdata):
        """ Yum install callback. """
        if event == rpm.RPMCALLBACK_TRANS_START: #@UndefinedVariable
            if amount == 6:
                self.progress.send_message(_("Preparing transaction from installation source"))
            self.total_actions = total
            self.completed_actions = 0
        elif event == rpm.RPMCALLBACK_TRANS_PROGRESS: #@UndefinedVariable
            # amount / total complete
            pass
        elif event == rpm.RPMCALLBACK_TRANS_STOP: #@UndefinedVariable
            # we are done
            pass
        elif event == rpm.RPMCALLBACK_INST_OPEN_FILE: #@UndefinedVariable
            # update status that we're installing/upgrading %h
            # return an open fd to the file
            txmbr = self._get_txmbr(key)[1]

            # If self.completed_actions is still None, that means this package
            # is being opened to retrieve a %pretrans script. Don't log that
            # we're installing the package unless we've been called with a
            # TRANS_START event.
            if self.completed_actions is not None:
                if self.upgrade:
                    mode = _("Upgrading")
                else:
                    mode = _("Installing")

                self.completed_actions += 1
                msg_format = "%s %s (%d/%d)"
                progress_package = txmbr.name
                if txmbr.arch not in ["noarch", self.base_arch]:
                    progress_package = "%s.%s" % (txmbr.name, txmbr.arch)

                progress_msg =  msg_format % (mode, progress_package,
                                              self.completed_actions,
                                              self.total_actions)
                log_msg = msg_format % (mode, txmbr.po,
                                        self.completed_actions,
                                        self.total_actions)
                logger.info(log_msg)
                self.install_log.write(log_msg+"\n")
                self.install_log.flush()

                self.progress.send_message(progress_msg)

            self.package_file = None
            repo = self._yum.repos.getRepo(txmbr.po.repoid)
            while self.package_file is None:
                try:
                    # checkfunc gets passed to yum's use of URLGrabber which
                    # then calls it with the file being fetched. verifyPkg
                    # makes sure the checksum matches the one in the metadata.
                    #
                    # From the URLGrab documents:
                    # checkfunc=(function, ('arg1', 2), {'kwarg': 3})
                    # results in a callback like:
                    #   function(obj, 'arg1', 2, kwarg=3)
                    #     obj.filename = '/tmp/stuff'
                    #     obj.url = 'http://foo.com/stuff'
                    checkfunc = (self._yum.verifyPkg, (txmbr.po, 1), {})
                    package_path = repo.getPackage(txmbr.po, checkfunc=checkfunc)
                except yum.URLGrabError as e:
                    logger.error("URLGrabError: %s" % (e,))
                    exn = PayloadInstallError("failed to get package")
                    #if errorHandler.cb(exn, txmbr.po) == ERROR_RAISE:
                    raise exn
                except (yum.Errors.NoMoreMirrorsRepoError, IOError):
                    if os.path.exists(txmbr.po.localPkg()):
                        os.unlink(txmbr.po.localPkg())
                        logger.debug("retrying download of %s" % txmbr.po)
                        continue
                    exn = PayloadInstallError("failed to open package")
                    #if errorHandler.cb(exn, txmbr.po) == ERROR_RAISE:
                    raise exn
                except yum.Errors.RepoError:
                    continue

                self.package_file = open(package_path)

            return self.package_file.fileno()
        elif event == rpm.RPMCALLBACK_INST_PROGRESS: #@UndefinedVariable
            txmbr = self._get_txmbr(key)[1]
            progress_package = txmbr.name
            if txmbr.arch not in ["noarch", self.base_arch]:
                progress_package = "%s.%s" % (txmbr.name, txmbr.arch)
            #self.progress.send_message('%s (%s/%s)' % (progress_package, amount, total))
        elif event == rpm.RPMCALLBACK_INST_CLOSE_FILE: #@UndefinedVariable
            # close and remove the last opened file
            # update count of installed/upgraded packages
            package_path = self.package_file.name
            self.package_file.close()
            self.package_file = None

            if package_path.startswith(_yum_cache_dir):
                try:
                    os.unlink(package_path)
                except OSError as e:
                    logger.debug("unable to remove file %s" % e.strerror)

            # rpm doesn't tell us when it's started post-trans stuff which can
            # take a very long time.  So when it closes the last package, just
            # display the message.
            if self.completed_actions == self.total_actions:
                self.progress.send_message(_("Performing post-install setup tasks"))
        elif event == rpm.RPMCALLBACK_UNINST_START: #@UndefinedVariable
            # update status that we're cleaning up %key
            #self.progress.set_text(_("Cleaning up %s" % key))
            pass
        elif event in (rpm.RPMCALLBACK_CPIO_ERROR, #@UndefinedVariable
                       rpm.RPMCALLBACK_UNPACK_ERROR, #@UndefinedVariable
                       rpm.RPMCALLBACK_SCRIPT_ERROR): #@UndefinedVariable
            name = self._get_txmbr(key)[0]

            # Script errors store whether or not they're fatal in "total".  So,
            # we should only error out for fatal script errors or the cpio and
            # unpack problems.
            if event != rpm.RPMCALLBACK_SCRIPT_ERROR or total: #@UndefinedVariable
                exn = PayloadInstallError("cpio, unpack, or fatal script error")
                #if errorHandler.cb(exn, name) == ERROR_RAISE:
                raise exn

def show_groups(payload):
    #repo = ksdata.RepoData(name="anaconda", baseurl="http://cannonball/install/rawhide/os/")
    #obj.addRepo(repo)

    desktops = []
    addons = []

    for grp in payload.groups:
        if grp.endswith("-desktop"):
            desktops.append(payload.groupDescription(grp))
            #desktops.append(grp)
        elif not grp.endswith("-support"):
            addons.append(payload.groupDescription(grp))
            #addons.append(grp)

    import pprint

    print "==== DESKTOPS ===="
    pprint.pprint(desktops)
    print "==== ADDONS ===="
    pprint.pprint(addons)

    print payload.groups


if __name__ == '__main__':
    TEST_INSTALL = False
    payload = YumPayload()
    CF.S.BASE_REPO_NAME = 'magiclinux'
    #CF.S.BASE_REPO_URL = '/mnt/fedora_iso'
    CF.S.BASE_REPO_URL = '/home/netsec/work/RPMS.base64'
    
    payload.setup()
    
    for repo in payload._yum.repos.repos.values():
        print repo.name, repo.enabled
        
    
    if TEST_INSTALL:
        payload.preStorage()
        t_packages = []
        packages = t_packages + ["authconfig", "system-config-firewall-base"]
        payload.preInstall(packages=packages, groups=payload.languageGroups('zh_CN'))
        payload.install()
        payload.postInstall()
    else:
        # Show some information
        # list all of the groups
        show_groups(payload)
    
        
# Switch repo.. to http:// protocal on internet
#    CF.S.BASE_REPO_NAME = 'fedora'
#    CF.S.BASE_REPO_URL = 'http://dl.fedoraproject.org/pub/fedora/linux/development/18/x86_64/os/'
#    
#    payload.updateBaseRepo()
#    for repo in payload._yum.repos.repos.values():
#        print repo.name, repo.enabled
#        
#    # list all of the groups
#    show_groups(payload)
    print 'Finished'