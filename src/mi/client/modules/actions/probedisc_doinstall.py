    def act_start_instpkg(self):
        self.tadlg.name_map['frame_packages'].set_sensitive(True)
        self.rootobj.tm.push_progress(self.tadlg.name_map['pkgprog'],
                                      self.tadlg.name_map['pkgname'])
        self.arch = self.rootobj.tm.actserver.get_arch()
        self.archcompat_list = CF.G.arch_map[self.arch]
        dolog('Detected Arch: %s\n' % str(self.arch))
        self.calc_instpkg_map()
        dolog('install_allpkg = %s\n' % str(self.install_allpkg))
        self.disc_first_pkgs = []
        for disc_no in range(len(CF.G.arrangement)):
            self.disc_first_pkgs.append(CF.G.arrangement[disc_no][0][1])
        (pafile, dev, fstype, reldir, bootiso_relpath) = CF.G.choosed_patuple
        dolog('disc_first_pkgs: %s\n' % str(self.disc_first_pkgs))
        self.add_action(_('Search packages'),
                        self.act_instpkg_prepare, None,
                        'probe_all_disc', dev, fstype, bootiso_relpath, reldir, self.disc_first_pkgs)
