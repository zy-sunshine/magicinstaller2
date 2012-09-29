self.actlist.append( (_('Install Bootloader'), self.act_start_bootloader, None) )
############################ Bootloader ###################################
class InstallBootloaderActions(object):
    def __init__(self):
        pass
    def act_start_bootloader(self):
        bltype = self.get_data(self.values, 'bootloader.bltype')
        instpos = self.get_data(self.values, 'bootloader.instpos')
        mbr_device = self.get_data(self.values, 'bootloader.mbr_device')
        win_device = self.get_data(self.values, 'bootloader.win_device')
        dolog('action_bootloader: bltype = %s\n' % bltype)
        if bltype == 'none':
            self.add_action(None, self.nextop, None, 'sleep', 0)
            return
        if CF.G.root_device == CF.G.boot_device:
            bootdev = ''
        else:
            bootdev = CF.G.boot_device
        if win_device:
            win_fs = get_devinfo(win_device, CF.G.all_part_infor).fstype
        else:
            win_fs = ''
        timeout = int(float(self.get_data(self.values, 'bootloader.timeout')))
        usepassword = self.get_data(self.values, 'bootloader.usepassword')
        password = self.get_data(self.values, 'bootloader.password')
        lba = self.get_data(self.values, 'bootloader.lba')
        options = self.get_data(self.values, 'bootloader.options')
        entries = []
        elnode = self.srh_data_node(self.values, 'bootloader.entrylist')
        for node in elnode.getElementsByTagName('row'):
            entries.append((node.getAttribute('c1'),
                            node.getAttribute('c2'),
                            node.getAttribute('c3')))
        default = self.get_data(self.values, 'bootloader.default')
        dolog('%s\n' % str(('setup_' + bltype, timeout, usepassword,
                            password, lba, options, entries, default,
                            instpos, bootdev, mbr_device, win_device, win_fs)))
        #### TODO: add clean server operate.
        
        self.add_action(_('Prepare bootloader'), self.bl_umount, bltype,
                        'prepare_' + bltype, timeout, usepassword, password,
                        lba, options, entries, default, instpos, bootdev, mbr_device, win_device, win_fs)
        ### TODO: real do self.bl_setup() and support grub2
        ### and then do nextop.

    def bl_umount(self, tdata, data):
        res = tdata
        if type(res) == int:
            self.add_action(None, self.nextop, None, 'sleep', 0)
            return
        self.add_action(_('Umount all target partitions before bootloader setup.'),
                        self.bl_setup, (data, res),
                        'umount_all_tgtpart', CF.G.mount_all_list, 0)

    def bl_setup(self, tdata, data):
        (bltype, (grubdev, grubsetupdev, grubopt)) = data
        self.add_action(_('Setup bootloader'), None, None,
                        'setup_' + bltype, grubdev, grubsetupdev, grubopt)

    def nextop(self, tdata, data):
        if tdata:
            result = tdata
            if result:
                # Error occurred. Stop it?
                dolog('ERROR: %s\n' % str(result))

        dolog('nextop\n')
        self.act_leave()
        
