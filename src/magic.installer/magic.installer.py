#!/usr/bin/python
#-*- encoding:GB18030 -*-
# Copyright (C) 2003, Charles Wang.
# Author:  Charles Wang <charles@linux.net.cn>
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANT; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public LIcense for more
# details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.

import gettext
import glob
import gtk

import os

import string
import sys
import syslog

import types

from gettext import gettext as _
from xml.dom.minidom import Document
from xml.dom.minidom import parse
from xml.dom.minidom import parseString

from mipublic import *

import parted
import rhpxl.monitor
import rhpxl.videocard
import rhpxl.mouse

import xmlgtk
import magicstep
import magicpopup
from xmlgtk import N_
USE_TEXTDOMAIN = True
openlog('/var/log/mi/client.log')

# Setup constants and working directory.
os.chdir(DATADIR)

sys.path.append(os.path.join(DATADIR, 'games'))
from xglines import xglines

if USE_TEXTDOMAIN:
    sys_locale = '/usr/share/locale'
    all_dirs, all_files = treedir(sys_locale, False)
    if TEXTDOMAIN+'.mo' in all_files:
        gettext.bindtextdomain(TEXTDOMAIN, sys_locale)
        gettext.textdomain(TEXTDOMAIN)
    else:
        gettext.bindtextdomain(TEXTDOMAIN, 'libs')
        gettext.textdomain(TEXTDOMAIN)
        
from magictaskman import *
CONF = MiConfig()
#--- all_part_infor --------------------------------------------------
# If 'reprobe_all_disk_required' is set to True, the parted step must reprobe
# all disks.
CONF.reprobe_all_disks_required = 0

# all_part_infor is a map which indexed by device filename, such as '/dev/hda'.
# Its value is a list. The element of the list is a tuple. Each tuple represent
# a partition.
# The tuple is (partnum, parttype, partflag, start, end, format_or_not,
#               orig_filesystem/format_to_filesystem, mountpoint, not_touched)
# The all_part_infor is filled by parted module for each leave.
# It is read by the other modules that run after parted.

CONF.all_part_infor = {}

# list of (orig_partdevname, filesystem, new_partdevname)
CONF.all_orig_part = []

# root_device: used to store the partition device file name mount on '/'.
CONF.root_device = None

# boot_device: used to store the partition device file name which contain '/boot'.
CONF.boot_device = None

# swap_device: used to store the partition device file name which used as swap.
CONF.swap_device = None

CONF.mount_all_list = []

CONF.skipxsetting = 0

CONF.path_tftproot = '/tmpfs/tftpboot'

class Status:
    def __init__(self):
        pass    
STAT = Status()
STAT.OP_STATUS_NONE = 0
STAT.OP_STATUS_DOING = 1
STAT.OP_STATUS_DONE = 2

CONF.path_allpa = os.path.join(path_tftproot, 'allpa')
STAT.pkgarr_probe_status = STAT.OP_STATUS_NONE
CONF.pkgarr_probe_result = None
STAT.win_probe_status = STAT.OP_STATUS_NONE
CONF.win_probe_result = None

CONF.choosed_patuple = ()
CONF.arch_map = {}
CONF.arrangement = []
CONF.archsize_map = {}
CONF.pkgpos_map = {}
CONF.toplevelgrp_map = {}

def get_devinfo(devfn):
    global all_part_infor
    global fstype_map

    for dev in all_part_infor:
        for tup in all_part_infor[dev]:
            if '%s%s' % (dev, tup[0]) == devfn:
                r = AttrDict()
                r['parted_fstype'] = tup[6]
                r['mountpoint'] = tup[7]
                r['not_touched'] = tup[8]
                try:
                    r['fstype'] = fstype_map[tup[6]][0]
                    r['flags'] = fstype_map[tup[6]][4]
                except KeyError:
                    raise KeyError, 'Unregconized filesystem type %s.' % tup[6]
                return r
    raise KeyError, 'Device %s not exists in all_part_infor.' % devfn

# Create the main window.
class mi_main (xmlgtk.xmlgtk):
    def __init__(self, uixml, confnode):
        self.curstep = -1
        self.stepobj_list = []			# The classname of each Func File	
        self.stepobj_group_list = []
        
        self.namestep_map = {}         # The classname to step number map
        self.available_steps = []            # available classname (step)
        self.steptitle_list = []        # every step's title
        
        self.values = parse(search_file('magic.values.xml', [hotfixdir, '.']))
        # Set the host name and boot label to distname.
        self.set_data(self.values, 'network.hostname', distname)
        self.set_data(self.values, 'bootloader.linuxlabel', distname)

        stepid = -1
        confdir = '/tmpfs/step_conf/'
        if not os.path.exists(confdir):
            os.mkdir(confdir)
        for groupnode in confnode.getElementsByTagName('group'):
            groupname = groupnode.getAttribute('name')
            for modulenode in groupnode.getElementsByTagName('module'):
                pyfname = modulenode.getAttribute('file')
                if pyfname:
                    pypath = search_file(pyfname, [hotfixdir, '.'],
                                         postfix = 'modules')
                    execfile(pypath)
                    classname = 'mistep_' + pyfname
                    if classname[-3:] == '.py':
                        classname = classname[:-3]
                    clsobj = eval(classname + '(self)')
                    stepid += 1
                    clsobj.stepid = stepid
                    clsobj.confdir = confdir
                    clsobj.pypath = pypath
                    self.stepobj_list.append(clsobj)
                    self.stepobj_group_list.append(groupname)
                    self.namestep_map[classname] = len(self.stepobj_list) - 1
                    self.available_steps.append(1)
                    
        self.uixml = uixml
        xmlgtk.xmlgtk.__init__(self, uixml, 'whole')
        self.tm = taskman(1325, self.name_map['mi_step'],
                          self.name_map['mi_step_label'])
                          
        self.stepsarr = []
        for step in self.stepobj_list:
            self.steptitle_list.append(step.get_label())

        table = self.name_map['steptables']
        for i in range(len(self.stepobj_list)):
            image = gtk.Image()
            image.set_from_file('images/applet-blank.png')
            image.show()
            self.stepsarr.append(image)
            table.attach(image, 0, 1, i, i + 1, 0, 0, 0, 0)
            label = gtk.Label(self.steptitle_list[i])
            label.set_alignment(0.0, 0.5)
            label.show()
            table.attach(label, 1, 2, i, i + 1,
                         gtk.EXPAND | gtk.FILL, gtk.EXPAND | gtk.FILL,
                         0, 0)
                          
        for stepobj in self.stepobj_list:
            if hasattr(stepobj, 'startup_action'):
                stepobj.startup_action()
        start_step = 0
        for stepno in range(len(self.stepobj_list)):
            debugFile = '/tmpfs/debug/start.step.%d' % stepno
            if os.path.exists(debugFile):
                start_step = stepno
                break
                
        self.curstep = start_step
        self.stepsarr[start_step].set_from_file('images/applet-busy.png')
        self.stepobj_list[start_step].widget.show()         # First show this widget
        self.enter_step(start_step)                         # Second judge the enter condition (or execute something)
        #self.switch2step(start_step)                        # Third switch to dest page (execute set_current_page,in reality)
        self.name_map['mi_main'].set_current_page(start_step)
        self.stepobj_list[start_step].init()

    def btnback_sensitive(self, sensitive):
        widget = self.name_widget('btnback')
        if widget:
            widget.set_sensitive(sensitive)

    def btnnext_sensitive(self, sensitive):
        widget = self.name_widget('btnnext')
        if widget:
            widget.set_sensitive(sensitive)

    def xgc_mim_notebook(self, node):
        widget = gtk.Notebook()
        widget.set_tab_pos(gtk.POS_LEFT)
        widget.set_scrollable(True)
        widget.set_show_tabs(False)
        for step in self.stepobj_list:
            label = gtk.Label(step.get_label())
            label.set_use_underline(True)
            widget.append_page(step.widget, label)
            step.widget.hide()
#        widget.connect('switch-page', self.switch_page)
        return  widget

    def leave_step(self, step):
        if step >= 0:
            stepobj = self.stepobj_list[step]
            if hasattr(stepobj, 'leave'):
                return  stepobj.leave()
        return 1

    def switch2step(self, dststep):
        if self.curstep == dststep: return
        dolog('From %d: switch2step(%d/%s)\n' % \
              (self.curstep, dststep, self.stepobj_list[dststep].get_label()))
        stepobj = self.stepobj_list[dststep]
        for btn in ['btnhelp', 'btncancel', 'btnback', 'btnnext', 'btnfinish']:
            if hasattr(stepobj, btn + '_clicked'):
                self.name_map[btn].show()
            else:
                self.name_map[btn].hide()
        self.name_map['mi_main'].set_current_page(dststep)
        self.stepobj_list[self.curstep].widget.hide()
        self.stepobj_list[self.curstep].fini()
        self.stepobj_list[dststep].widget.show()
        self.stepobj_list[dststep].init()
        self.curstep = dststep

    def enter_step(self, step):
        stepobj = self.stepobj_list[step]
        if hasattr(stepobj, 'enter'):
            return stepobj.enter()
        return  1

    def page_restore(self):
        self.name_map['mi_main'].set_current_page(self.curstep)
        return  False

    #def switch_page(self, widget, page, pageno):
    #    if self.curstep != pageno:
    #        if pageno < self.curstep  \
    #               or ( self.leave_step(self.curstep) and self.enter_step(pageno) ): # only check next
    #            self.switch2step(pageno)
    #        else:
    #            # Call set_current_page is useless here, so use timeout
    #            # to switch back.
    #            gobject.timeout_add(10, self.page_restore)

    def btnhelp_clicked(self, widget, data):
        self.stepobj_list[self.curstep].btnhelp_clicked(widget, data)

    def btncancel_clicked(self, widget, data):
        self.stepobj_list[self.curstep].btncancel_clicked(widget, data)

    def btnback_clicked(self, widget, data):
        if self.stepobj_list[self.curstep].btnback_clicked(widget, data):
            #self.name_map['mi_main'].set_current_page(self.curstep - 1)
            self.btnback_do()

    def btnnext_clicked(self, widget, data):
        if self.stepobj_list[self.curstep].btnnext_clicked(widget, data):
            self.btnnext_do()
            
    def btnback_do(self):
        self.switch_to_page(self.curstep - 1)
        
    def btnnext_do(self):
#  These code will remove special classname from stepobj_list, But we will skip some step rather remove it.
#
#        def remove_list_elem(list, elem_num):
#            list.pop(elem_num)
#                
#        def remove_listmap_elem(listmap, elem_key):
#            if not listmap.has_key(elem_key):
#                return
#            num = listmap.pop(elem_key)
#            for key in listmap.keys():
#                if listmap[key] > num:
#                    listmap[key] -= 1
#
#        remove_classnames = self.stepobj_list[self.curstep].skip_stepnames
#        if remove_classnames != []:
#            for rclassname in remove_classnames:
#                if self.namestep_map.has_key(rclassname):
#                    rnum = self.namestep_map[rclassname]
#                    remove_list_elem(self.stepobj_list, rnum)
#                    remove_listmap_elem(self.namestep_map, rclassname)
#                    # Remove the page from mim_notebook()
#                    self.name_map['mi_main'].remove_page(rnum)
        
        skip_classnames = self.stepobj_list[self.curstep].skip_stepnames
        if skip_classnames != []:
            for skip_classname in skip_classnames:
                if self.namestep_map.has_key(skip_classname):
                    skip_num = self.namestep_map[skip_classname]
                    self.available_steps[skip_num] = 0           # Skip this step
                    self.stepobj_list[skip_num].widget.hide()          # Hide this step
                    

        #if self.stepobj_group_list[self.curstep] != \
        #       self.stepobj_group_list[self.curstep + 1]:
        #    for step in range(self.curstep, -1, -1):
        #        if self.stepobj_group_list[step] != \
        #               self.stepobj_group_list[self.curstep + 1]:
        #        self.stepobj_list[step].widget.hide()

        next_step = self.get_next_available_step(self.curstep)
        self.switch_to_page(next_step)
        
    def get_next_available_step(self, curstep):
        next_step = curstep + 1
        for s in range(curstep + 1, len(self.stepobj_list) - 1 ):
            if self.available_steps[s]:
                next_step = s
                break
        return next_step
        
    def switch_to_page(self, pageno):
        if self.curstep != pageno:
            if pageno < self.curstep:           # 如果向后变更 step，则表明，当前页面未完成。
                self.stepsarr[self.curstep].set_from_file('images/applet-blank.png')
                self.stepsarr[pageno].set_from_file('images/applet-busy.png')
                self.switch2step(pageno)
            elif pageno > self.curstep:         # 如果向前变更 step，则表明，当前页面已经完成。
                # 我们只处理下一步的leave和enter
                if self.leave_step(self.curstep) and self.enter_step(pageno): # only check next
                    self.stepsarr[self.curstep].set_from_file('images/applet-okay.png')
                    self.stepsarr[pageno].set_from_file('images/applet-busy.png')
                    self.switch2step(pageno)
            else:
                # Call set_current_page is useless here, so use timeout
                # to switch back.
                gobject.timeout_add(10, self.page_restore)



    def btnfinish_clicked(self, widget, data):
        if self.stepobj_list[self.curstep].btnfinish_clicked(widget, data):
            # Do real installation.
            pass
        
    def theme_clicked(self, widget, themedir):
        # Use 'gtk.settings' instead of 'gtk.rc'             By demonlj@linuxfans.org
        settings = gtk.settings_get_default()
        if themedir:
            settings.set_string_property("gtk-theme-name", themedir, "")
            #gtk.rc_parse_string('gtk-theme-name = "%s"' % themedir)
        else:
            settings.set_string_property("gtk-theme-name", "Default", "")
            #gtk.rc_parse_string('gtk-theme-name = "Default"')

    def btntheme_clicked(self, widget, data):
        self.themedlg = magicpopup.magicpopup(self, self.uixml,
                                              _('Theme Choice'),
                                              magicpopup.magicpopup.MB_OK,
                                              'themedlg', 'theme')
        themesdoc = parse('/etc/gtk-2.0/themes.xml')
        themelist = themesdoc.getElementsByTagName('theme')
        rows = 2
        thetable = gtk.Table(rows, (len(themelist) + rows - 1) / rows, True)
        thetable.set_col_spacings(4)
        thetable.set_row_spacings(4)
        left = 0
        top = 0
        for themenode in themelist:
            dir = themenode.getAttribute('dir')
            pic = themenode.getAttribute('pic')
            if pic:
                thebutton = gtk.Button()
                theimage = gtk.Image()
                theimage.set_from_file('/etc/gtk-2.0/pics/' + pic)
                theimage.show()
                thebutton.add(theimage)
                thebutton.show()
            else:
                name = themenode.getAttribute('name')
                if not name:
                    if dir:
                        name = dir
                    else:
                        name = _('Default')
                thebutton = gtk.Button(name)
            thebutton.connect('clicked', self.theme_clicked, dir)
            thetable.attach(thebutton, left, left + 1, top, top + 1, 0, 0, 0, 0)
            top = top + 1
            if top == rows:
                top = 0
                left = left + 1
        thetable.show()
        self.themedlg.name_map['themes'].pack_start(thetable, True, True)
        
    def btnlogger_clicked(self, widget, data):
        self.tm.add_action(None, None, None, 'start_magiclogger', 0)

mi_win = gtk.Window(gtk.WINDOW_TOPLEVEL)
mi_win.connect('destroy', gtk.main_quit)

# Lock the position and size of the toplevel window.
mi_win.set_position(gtk.WIN_POS_CENTER)
#mi_win.set_default_size(800, 600)
mi_win.set_size_request(full_width, full_height)
mi_win.set_resizable(False)

xgobj = mi_main(parse(search_file('mi_main.xml', [hotfixdir, '.'], postfix = 'UIxml')),
                parse(search_file('magic.installer.xml', [hotfixdir, '.'])).documentElement)

mi_win.add(xgobj.widget)

mi_win.show()

root = gtk.gdk.get_default_root_window()
cursor = gtk.gdk.Cursor(gtk.gdk.LEFT_PTR)
root.set_cursor(cursor)

gtk.main()

closelog()
