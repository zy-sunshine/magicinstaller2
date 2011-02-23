#!/usr/bin/python
# Copyright (C) 2011, zy_sunshine <zy.netsec@gmail.com>
# Author:  zy_sunshine.
import gtk
import gobject
import threading
import os, sys
sys.path.insert(0, 'libs')
from xml.dom.minidom import parse
import getdev
getdev.KUDZU_FLAG=False
import xmlgtk
import types
import signal
from magictaskman import *
from mipublic import *
import gettext
from gettext import gettext as _
USE_TEXTDOMAIN = True
os.chdir(DATADIR)

if USE_TEXTDOMAIN:
    sys_locale = '/usr/share/locale'
    all_dirs, all_files = treedir(sys_locale, False)
    if TEXTDOMAIN+'.mo' in all_files:
        gettext.bindtextdomain(TEXTDOMAIN, sys_locale)
        gettext.textdomain(TEXTDOMAIN)
    else:
        gettext.bindtextdomain(TEXTDOMAIN, 'libs')
        gettext.textdomain(TEXTDOMAIN)

logfileList = ['/var/log/']
xml_interface = parse(search_file('magic.logger.xml', [hotfixdir, '.']))

class CustomSender(gobject.GObject):
    def __init__(self):
        self.__gobject_init__()

gobject.type_register(CustomSender)
gobject.signal_new('copy_logfiles_finished', CustomSender, 
                    gobject.SIGNAL_RUN_FIRST,
                    #gobject.SIGNAL_RUN_LAST,
                    gobject.TYPE_NONE,
                    #(gobject.TYPE_PYOBJECT,)
                    ()
                )
        
class magic_logger (xmlgtk.xmlgtk):
    def __init__(self, xmlui):
        xmlgtk.xmlgtk.__init__(self, xmlui, 'magic.logger')
        self.xmlui = xmlui
        self.msgbox = None
        self.msgbuffer = None
        self.usb_part_info = None
        self.part_combo = self.name_map["part_combo"]
        self.pbar = self.name_map["process_progress"]
        self.checkfilebox = self.name_map["checkfilebox"]
        self.device_type = getdev.CLASS_USB
        scrolledwindow = self.name_map["showinfo"]
        for child in scrolledwindow.get_children():
            if type(child) == gtk.TextView:
                self.msgbox = child
                break
        if self.msgbox:
            self.msgbuffer = self.msgbox.get_buffer()
        else:
            pass # Error encountered
            
        self.refresh_device()
        self.fill_logfiles()
        self.tm = taskman(326, None, None)
        
    def fill_logfiles(self):
        for logfile in logfileList:
            button = gtk.CheckButton(logfile)
            self.checkfilebox.pack_start(button)
            if os.path.exists(logfile):
                button.set_active(True)
            button.show()
            
    def showinfo(self, title, info, clear=True, format='normal'):
        #iter = textbuffer.get_start_iter()
        #iter = textbuffer.get_end_iter()
        #textbuffer.insert(iter, text)
        #textbuffer.set_text(text)
        pr_str = '%s:\n' % title
        if type(info) == types.DictType:
            keys = list(i for i in info.keys())
            keys.sort()
            for k in keys:
                pr_str = pr_str + '%s: %s\n' % (k, info[k])
        else:
            pr_str = pr_str + '%s' % str(info)
        if clear:
            self.msgbuffer.set_text(pr_str)
        else:
            iter = self.msgbuffer.get_end_iter()
            self.msgbuffer.insert(iter, pr_str)
            
    def chooseusb(self, radiobutton, data):
        self.showinfo(_("ChooseType"), _("USB Devices"))
        self.device_type = getdev.CLASS_USB
            
    def chooseall(self, radiobutton, data):
        self.showinfo(_("ChooseType"), _("ALL Devices"))
        self.device_type = getdev.CLASS_HD
        
    def refresh_device_cb(self, button, data):
        self.refresh_device()
        
    def refresh_device(self):
        devices_info, devices_size = getdev.probe(getdev.ALL_DEVICE_INFO)
        usb_map = getdev.probe(self.device_type)
        self.usb_part_info = self.get_usb_part( usb_map,
                                    devices_info,
                                    devices_size )
        
        model = self.part_combo.get_model()
        self.part_combo.set_model(None)
        model.clear()
        model.append

        model.append([_('Select a partition:')])
        for part in self.usb_part_info.keys():
            model.append([part])
        self.part_combo.set_model(model)
        self.part_combo.set_active(0)
        
    def device_changed_cb(self, combobox, data):
        model = combobox.get_model()
        index = combobox.get_active()
        if index:
            usb_part = model[index][0]
            self.showinfo(_('USB INFO'), self.usb_part_info[usb_part])
        else:
            self.showinfo(_('USB INFO'), _("You haven't choose a device"))
        return
  
    def get_usb_part(self, usb_map, all_part_info, disk_size_map):
        usb_part_info = {}
        def get_attr(tmap, attr):
            if not tmap.has_key(attr):
                return None
            else:
                return tmap[attr]

        for disk in usb_map.keys():
            for part in [disk] + usb_map[disk]:
                if all_part_info[part].has_key('ID_FS_TYPE'):
                #if all_part_info[part].has_key('DEVTYPE') and all_part_info[part]['DEVTYPE'] == 'partition':
                    # Disk maybe a partition... , so we check the disk too.
                    # disk:     partition belong to this disk.
                    # devpath:  the partition's dev path.
                    # vendor:   the vendor of the usb.
                    # model:    the flash model of the usb.
                    # model_id: the flash model's id of the usb.
                    # fstype:   the filesystem type of this partition.
                    # fsver:    the filesystem's version of this partition.
                    # size:     the size of this partition.
                    part_info = {}
                    part_info['disk'] = get_attr(all_part_info[disk], 'DEVNAME')
                    part_info['devpath'] = get_attr(all_part_info[part],'DEVNAME')
                    part_info['vendor'] = get_attr(all_part_info[part],'ID_VENDOR')
                    part_info['model'] = get_attr(all_part_info[part],'ID_MODEL')
                    part_info['model_id'] = get_attr(all_part_info[part],'ID_MODEL_ID')
                    part_info['fstype'] = get_attr(all_part_info[part],'ID_FS_TYPE')
                    part_info['fsver'] = get_attr(all_part_info[part],'ID_FS_VERSION')
                    part_info['size'] = '%.2f MB' % (float(disk_size_map[part])/1024/1024)
                    usb_part_info[part_info['devpath']] = part_info
        return usb_part_info

    def start_copy(self, widget, data):
        self.close_button()
        self.sender = CustomSender()
        self.sender.connect('copy_logfiles_finished', self.start_copy_cb)
        
        paras = []
        if not self.get_parameters(paras):
            self.sender.emit('copy_logfiles_finished')
            return
        (self.inst_usb_part, self.inst_usb_disk, self.logfiles) = paras
        self.usb_dev_path = self.usb_part_info[self.inst_usb_part]['devpath']
        self.usb_fs_type = self.usb_part_info[self.inst_usb_part]['fstype']
        self.tm.push_progress(self.pbar, self.pbar)
        self.tm.add_action(_("Start Copy"), self.logger_copy_logfiles_cb, None,
            'logger_copy_logfiles', (self.usb_dev_path, self.usb_fs_type, self.logfiles))
        
    def logger_copy_logfiles_cb(self, operid, data):
        self.tm.pop_progress()
        ret = self.tm.results[operid]
        if ret:
            self.showinfo(_("Failed"), ret)
            self.pbar.set_text(_("Failed"))
        else:
            self.showinfo(_("Success"), _("copy %s to %s device") % (self.logfiles, self.usb_dev_path))
            self.pbar.set_text(_("Success"))
        self.sender.emit('copy_logfiles_finished')
        
    def start_copy_cb(self, widget):
        self.open_button()

    def close_button(self):
        self.name_map["addfile"].set_sensitive(False)
        self.name_map["startcopy"].set_sensitive(False)

    def open_button(self):
        self.name_map["addfile"].set_sensitive(True)
        self.name_map["startcopy"].set_sensitive(True)
        
    def test_clicked(self, button, data):
        result = []
        self.get_parameters(result)
        print result
        
    def add_logfile(self, button, data):
        logfile = ""
        dialog = gtk.FileChooserDialog( _('Select...'), 
                                        None, 
                                        gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                        (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        
        filter = gtk.FileFilter()
        filter.set_name(_("All Files"))
        filter.add_pattern("*")
        dialog.add_filter(filter)

        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            logfile = dialog.get_filename()
        elif response == gtk.RESPONSE_CANCEL:
            #print 'Closed, no files selected'
            pass
        dialog.destroy()
        if os.path.exists(logfile):
            button = gtk.CheckButton(logfile)
            button.show()
            self.checkfilebox.pack_start(button)
            button.set_active(True)
            button.show()
    
    def del_logfile(self, button, data):
        for checkbutton in self.checkfilebox.get_children():
            if checkbutton.get_active():
                checkbutton.set_active(False)
                checkbutton.hide()

    def default_logfile(self, button, data):
        for checkbutton in self.checkfilebox.get_children():
            self.checkfilebox.remove(checkbutton)
        self.fill_logfiles()
        
    def get_parameters(self, result):
        inst_usb_part = ''
        inst_usb_disk = ''
        logfiles = []
        for checkbutton in self.checkfilebox.get_children():
            if checkbutton.get_active():
                logfiles.append(checkbutton.get_label())
                
            #if checkbutton.
        model = self.part_combo.get_model()
        index = self.part_combo.get_active()
        if index:
            inst_usb_part = model[index][0]
            inst_usb_disk = self.usb_part_info[inst_usb_part]['disk']
        def check_para(title, value):
            pr_str = ''
            if not value.strip():
                pr_str = pr_str + _('none "%s" value, please check!') % title
            return pr_str
        pr_str = ''
        pr_str += '%s\n' % check_para(_('Usb Partition'), inst_usb_part)
        pr_str += '%s\n' % check_para(_('Usb Disk Belong'), inst_usb_disk)
        pr_str = pr_str.strip()
        if pr_str:
            self.showinfo(_('Can not get some parameters'), pr_str)
            return False
        else:
            result.extend([inst_usb_part, inst_usb_disk, logfiles])
            return True
        
    def exit_clicked(self, button, data):
        self.quit()
        
    def quit(self):
        #self.tm.add_action(None, None, None, 'quit', 0)
        gtk.main_quit()

xgobj = magic_logger(xml_interface)

def handler(signum, frame):
    xgobj.quit()

window = gtk.Window(gtk.WINDOW_TOPLEVEL)
window.add(xgobj.widget)
window.set_size_request(full_width, full_height)
window.show_all()

window.connect('destroy', lambda w: xgobj.quit())
window.set_position(gtk.WIN_POS_CENTER)

root = gtk.gdk.get_default_root_window()
cursor = gtk.gdk.Cursor(gtk.gdk.LEFT_PTR)
root.set_cursor(cursor)
signal.signal(signal.SIGQUIT, handler)
gtk.main()
