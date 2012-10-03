class PackageData(object):
    def __init__(self):
        self.packages = []
        
        
class PayLoad(object):
    def __init__(self):
        pass
    ###
    ### METHODS FOR WORKING WITH PACKAGES
    ###
    @property
    def packages(self):
        raise NotImplementedError()

    def packageSelected(self, pkgid):
        return pkgid in self.data.packages.packageList
    
    def selectPackage(self, pkgid):
        """Mark a package for installation.

           pkgid - The name of a package to be installed.  This could include
                   a version or architecture component.
        """
        if pkgid in self.data.packages.packageList:
            return

        if pkgid in self.data.packages.excludedList:
            self.data.packages.excludedList.remove(pkgid)

        self.data.packages.packageList.append(pkgid)
        
    def deselectPackage(self, pkgid):
        """Mark a package to be excluded from installation.

           pkgid - The name of a package to be excluded.  This could include
                   a version or architecture component.
        """
        if pkgid in self.data.packages.excludedList:
            return

        if pkgid in self.data.packages.packageList:
            self.data.packages.packageList.remove(pkgid)

        self.data.packages.excludedList.append(pkgid)
        
    def preInstall(self, packages=None, groups=None):
        """ Perform pre-installation tasks. """
        iutil.mkdirChain(ROOT_PATH + "/root")

        if packages:
            map(self.selectPackage, packages)

        if groups:
            map(self.selectGroup, groups)
            
            
if __name__ == '__main__':
    self.add_step("reposetup", doBackendSetup)
    self.add_step("tasksel")
    self.add_step("basepkgsel", doBasePackageSelect)
    self.add_step("group-selection")
    self.add_step("postselection", doPostSelection)
    self.add_step("install")
    self.add_step("preinstallconfig", doPreInstall)
    self.add_step("installpackages", doInstall)
    self.add_step("postinstallconfig", doPostInstall)