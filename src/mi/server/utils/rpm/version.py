import os
def get_pkg_name(pkgrpm):
    pkg = os.path.basename(pkgrpm)
    pkgname = ''
    try:
        pkgname = pkg[:pkg.rindex('-')]
        pkgname = pkg[:pkgname.rindex('-')]
    except ValueError, e:
        return pkg
    return pkgname
