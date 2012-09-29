
######################   Install package below code    #########################
# Now package_install support rpm only.

@register.server_handler('long')
def pkg_install(mia, operid, pkgname, firstpkg, noscripts):
    use_ts = False
    global dev_hd
    global dev_iso
    pkgpath = os.path.join(os.path.dirname(firstpkg), pkgname)
    pkgpath = dev_iso and dev_iso.get_file_path(pkgpath) or dev_hd.get_file_path(pkgpath)
    #dolog('pkg_install(%s, %s)\n' % (pkgname, str(pkgpath)))

    # Decide using which mode to install.
    ret = 'Nothing'
    if CF.D.PKGTYPE == 'rpm':     # In the mipublic.py
        if installmode == 'rpminstallmode':
            if use_ts:
                # Use rpm-python module to install rpm pkg, but at this version it is very slowly.
                ret = do_ts_install()
            else:
                # Because I can not use rpm-python module to install quickly.
                # So use the bash mode to install the pkg, it is very fast.
                # If you can use rpm-python module install pkg quickly, you can remove it.
                ret = do_bash_rpm_install()
        elif installmode == 'copyinstallmode':
            # Use rpm2cpio name-ver-release.rpm | cpio -diu to uncompress the rpm files to target system.
            # Then we will do some configuration in instpkg_post.
            ret = do_copy_install()

    if ret:
        return ret
    else:
        return 0
    
def pkg_post(mia):
    mia.set_step(operid, 1, 1)
    