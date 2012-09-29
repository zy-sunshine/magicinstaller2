#!/usr/bin/python
from mi.client.utils import _
from mi.client.utils.magicstep import magicstep
from mi.client.utils import logger, magicpopup, xmlgtk
from mi.utils.miconfig import MiConfig
from xml.dom.minidom import parseString
import os
CF = MiConfig.get_instance()


class DoPartition(magicstep):
    '''
    commit the partiton info to change partiton on disk really
    '''
    NAME = 'dopartition'
    LABEL = _('Do Partition')
    def __init__(self, sself):
        magicstep.__init__(self, sself, 'dopartition.xml', 'dopartition')
        if sself is None:
            return
        self.sself = sself
        self.doparted = False
        self.add_action = self.rootobj.tm.add_action
        self.takeactions = TakeActions()
    def enter(self):
        self.sself.btnback_sensitive(False)
        self.sself.btnnext_sensitive(False)
        self.name_map['pfprog'].set_fraction(0)

        self.name_map['frame_parted'].set_sensitive(True)
        self.rootobj.tm.push_progress(self.name_map['pfprog'],
                                      self.name_map['pfname'])
        self.add_action(_('Get all dirty disk'),
                        self.act_parted_get_dirty_result, None,
                        'get_all_dirty_disk', 0)
        return 1
    
    def leave(self):
        if not self.doparted:
            self.sself.btnnext_sensitive(False)
            self.act_start_parted()
            self.doparted = True
            return 0
        else:
            self.sself.btnnext_sensitive(True)
            ### ### TODO: mount these partition before install system.
            
            self.add_action(_('Mount all target partitions.'),
                            None, None,
                            'mount_all_tgtpart', CF.G.mount_all_list, 'y')
            self.add_
            ### TODO: make a unique task queue, to make install operation run background.
            #self.add_action(_('Start Install System'), None, None)
            return 1

    def act_parted_get_dirty_result(self, tdata, data):
        self.dirty_disks = tdata
        self.format_list = []
        for devpath in CF.G.all_part_infor.keys():
            for part_tuple in CF.G.all_part_infor[devpath]:
                if part_tuple[5] == 'true': # format_or_not
                    self.format_list.append((devpath,
                                             part_tuple[3], # start
                                             part_tuple[6], # ftype
                                             part_tuple[0])) # partnum
        self.fill_all_info()
        self.name_map['pfprog'].set_fraction(1)
        # We get all information, and commit dirty partition and format can be do.
        self.sself.btnnext_sensitive(True)
        logger.info('self.dirty_disks: %s\n' % str(self.dirty_disks))
        logger.info('self.format_list: %s\n' % str(self.format_list))
        
    def fill_all_info(self):
        pkg_frame = self.id_map['pkg_frame']
        dirty_frame = self.id_map['dirty_frame']
        format_frame = self.id_map['format_frame']
        
        def gen_table(info_list):
            table_doc = parseString('<?xml version="1.0"?><tableV2></tableV2>')
            root0 = table_doc.getElementsByTagName('tableV2')[0]
            for k, v in info_list:
                trnode = table_doc.createElement('tr')
                label0 = table_doc.createElement('label')
                label0.setAttribute('text', k+'\t:\t')
                root0.appendChild(trnode)
                trnode.appendChild(label0)
                label1 = table_doc.createElement('label')
                label1.setAttribute('text', v)
                trnode.appendChild(label1)
            return table_doc
        
        # Package Information
        info_list = []
        for (pafile, dev, fstype, reldir, isofn) in [CF.G.choosed_patuple, ]:
            info_list.append((isofn, os.path.join(dev, reldir, isofn)))
        pkg_table = gen_table(info_list)
        
        # Dirty Disk
        info_list = []
        for disk in self.dirty_disks: # ['/dev/sda']
            info_list.append((disk, ""))
        dirty_table = gen_table(info_list)
        
        # Format Partition
        info_list = []
        for (devpath, start, ftype, partnum) in self.format_list: # [('/dev/sda', 935649280, 'ext3', 3)]
            info_list.append(('%s%s' % (devpath, partnum), "filesystem type is %s" % ftype))
        format_table = gen_table(info_list)
        
        for table, frame in ((pkg_table, pkg_frame), (dirty_table, dirty_frame), (format_table, format_frame)):
            widget = xmlgtk.xmlgtk(table).widget
            frame.add(widget)
        
    def act_start_parted(self):
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
            CF.G.mount_all_list = []
            for devpath in CF.G.all_part_infor.keys():
                for part_tuple in CF.G.all_part_infor[devpath]:
                    if part_tuple[7] == '':
                        # :) This mountpoint is not the obsolete "mountpoint", 
                        # which was used by mount every device, removed already, please view the source in magicinstaller1
                        # Note: this mountpoint is point by user at create partition step, / /usr /home and so on.
                        continue
                    mntpoint = part_tuple[7]
                    devfn = '%s%d' % (devpath, part_tuple[0])
                    fstype = part_tuple[6]
                    CF.G.mount_all_list.append((mntpoint, devfn, fstype))
            CF.G.mount_all_list.sort(self.malcmp)
            logger.info('CONF.RUN.g_mount_all_list: %s\n' % str(CF.G.mount_all_list))
                            
            self.act_end_parted()

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
        
        self.sself.btnnext_clicked(None, None)

if __name__ == '__main__':
    #from mi.client.tests import TestRootObject
    #rootobj = TestRootObject(DoPartition)
    #rootobj.init()
    #rootobj.main()
    import gtk
    class Ui(xmlgtk.xmlgtk):
        def __init__(self, sself):
            xmlgtk.xmlgtk.__init__(self, 'UIxml/dopartition.xml', 'dopartition')
    ui = Ui(None)
    win = gtk.Window(gtk.WINDOW_TOPLEVEL)
    win.add(ui.widget)
    win.show()
    gtk.main()
    