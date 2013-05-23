
    self.actlist.append( (_('Make initrd'), self.act_start_mkinitrd, None) )
##### End install package
    def act_start_mkinitrd(self):
        self.tadlg.name_map['frame_other'].set_sensitive(True)
        self.rootobj.tm.push_progress(self.tadlg.name_map['otprog'],
                                      self.tadlg.name_map['otname'])
        scsi_module_list = self.get_data(self.values, 'scsi.modules')
        if scsi_module_list == None or scsi_module_list == '':
            dolog('No scsi driver has to be written into modprobe.conf.\n')
        else:
            dolog('scsi_modprobe_conf(%s)\n' % scsi_module_list)
            self.add_action(_("Generate modprobe.conf"), None, None,
                            'scsi_modprobe_conf', scsi_module_list)
        dolog('action_mkinitrd\n')
        self.add_action(_('Make initrd'), self.nextop, None, 'do_mkinitrd', 0)