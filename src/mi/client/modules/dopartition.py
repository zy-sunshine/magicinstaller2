#!/usr/bin/python
from mi.client.utils import _
from mi.client.utils.magicstep import magicstep
from mi.client.utils import logger, magicpopup
from mi.utils.miconfig import MiConfig
CONF = MiConfig.get_instance()


class DoPartition(magicstep):
    '''
    commit the partiton info to change partiton on disk really
    '''
    NAME = 'partition'
    LABEL = _('Do Partition')
    def __init__(self, sself):
        magicstep.__init__(self, sself, 'dopartition.xml', 'dopartition')
        if sself is None:
            return
        self.add_action = self.rootobj.tm.add_action
        self.act_start_parted()

    def act_start_parted(self):
        self.name_map['pfprog'].set_fraction(0)

        self.name_map['frame_parted'].set_sensitive(True)
        self.rootobj.tm.push_progress(self.name_map['pfprog'],
                                      self.name_map['pfname'])
        self.add_action(_('Get all dirty disk'),
                        self.act_parted_get_dirty_result, None,
                        'get_all_dirty_disk', 0)

    def act_parted_get_dirty_result(self, tdata, data):
        self.dirty_disks = tdata
        self.format_list = []
        for devpath in CONF.RUN.g_all_part_infor.keys():
            for part_tuple in CONF.RUN.g_all_part_infor[devpath]:
                if part_tuple[5] == 'true':
                    self.format_list.append((devpath,
                                             part_tuple[3],
                                             part_tuple[6],
                                             part_tuple[0]))
        logger.info('self.dirty_disks: %s\n' % str(self.dirty_disks))
        logger.info('self.format_list: %s\n' % str(self.format_list))
        self.act_parted_commit_start(0)

    def act_parted_commit_start(self, pos):
        if pos < len(self.dirty_disks):
            actinfor = _('Write the partition table of %s.')
            actinfor = actinfor % self.dirty_disks[pos]
            self.add_action(actinfor, self.act_parted_commit_result, pos,
                            'commit_devpath', self.dirty_disks[pos])
        else:
            self.act_parted_format_start(0)

    def act_parted_commit_result(self, tdata, data):
        result = tdata
        if result:
            # Error occurred. Stop it?
            logger.error('commit_result ERROR: %s\n' % str(result))
        self.act_parted_commit_start(data + 1)

    def malcmp(self, c0, c1):
        if c0[0] < c1[0]:    return -1
        elif c0[0] > c1[0]:  return 1
        return 0

    def act_parted_format_start(self, pos):
        if pos < len(self.format_list):
            actinfor = 'Formating %s on %s%d.'
            actinfor = actinfor % (self.format_list[pos][2],
                                   self.format_list[pos][0],
                                   self.format_list[pos][3])
            logger.info('format_start: %s\n' % str(actinfor))
            self.add_action(actinfor, self.act_parted_format_result, pos,
                            'format_partition',
                            self.format_list[pos][0], # devpath.
                            self.format_list[pos][1], # part_start.
                            self.format_list[pos][2]) # fstype
        else:
            CONF.RUN.g_mount_all_list = []
            for devpath in CONF.RUN.g_all_part_infor.keys():
                for part_tuple in CONF.RUN.g_all_part_infor[devpath]:
                    if part_tuple[7] == '':  # mountpoint ### TODO
                        continue
                    mntpoint = part_tuple[7]
                    devfn = '%s%d' % (devpath, part_tuple[0])
                    fstype = part_tuple[6]
                    CONF.RUN.g_mount_all_list.append((mntpoint, devfn, fstype))
            CONF.RUN.g_mount_all_list.sort(self.malcmp)
            logger.info('CONF.RUN.g_mount_all_list: %s\n' % str(CONF.RUN.g_mount_all_list))
            #self.add_action(_('Mount all target partitions.'),
                            #self.nextop, None,
                            #'mount_all_tgtpart', CONF.RUN.g_mount_all_list, 'y')
            self.nextop(None, None)
                            
            #### Because we can mount device many times, so we not check below
            ## Check whether the packages are stored in mounted partitions.
            #pkgmntpoint = 0
            #(pafile, dev, fstype, dir, isofn) = CONF.RUN.g_choosed_patuple
            #for (mntpoint, devfn, fstype) in CONF.RUN.g_mount_all_list:
                #if dev == devfn:
                    #pkgmntpoint = mntpoint
                    #if len(pkgmntpoint) > 0 and pkgmntpoint[0] == '/':
                        #pkgmntpoint = pkgmntpoint[1:]
                    #CONF.RUN.g_choosed_patuple = (pafile, dev, pkgmntpoint,
                                       #fstype, dir, isofn)
                    #dolog('The packages is placed in the mounted partition(%s)\n' %\
                          #pkgmntpoint)
                    #break

    def act_parted_format_result(self, tdata, data):
        result = tdata
        if result:
            # Error occurred. Stop it?
            # Yes, we should stop it, and we should stop at mount failed place too.
            logger.info('format_result ERROR: %s\n' % str(result))
            magicpopup.magicmsgbox(None, _('Format Partition Error: %s' % result),
                       magicpopup.magicmsgbox.MB_ERROR,
                       magicpopup.magicpopup.MB_OK)
            #self.rootobj.btnback_do()
        self.act_parted_format_start(data + 1)

    def act_end_parted(self):
        self.rootobj.tm.pop_progress()
        self.name_map['pfname'].set_text('')
        self.name_map['pfprog'].set_fraction(1)
        self.name_map['frame_parted'].set_sensitive(False)

if __name__ == '__main__':
    pass
    #from mi.client.tests import TestRootObject
    #rootobj = TestRootObject(DoPartition)
    #rootobj.init()
    #rootobj.main()
