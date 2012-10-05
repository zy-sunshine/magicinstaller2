#!/usr/bin/python
#coding=utf-8
import os, sys
import gtk
from mi.client.utils import _, xmlgtk
from mi.client.leftpanel import MILeftPanel
from mi.client.rightpanel import MIRightPanel
from mi.client.header import MIHeader
from mi.client.bottom import MIBottom
from mi.client.statusbar import MIStatusBar
from mi.client.buttonbar import MIButtonBar
from xml.dom.minidom import parse
from mi.utils.common import search_file
# This can import MIStem_* from modules.* automatically
from mi.client.modules import *

from mi.utils.miconfig import MiConfig
from mi.client.utils.magicpopup import magicmsgbox, magichelp_popup
CF = MiConfig.get_instance()
from mi.utils.mitaskman import MiTaskman
from mi.client.utils import magicpopup

from mi.client.utils import logger
dolog = logger.i

class Step(object):
    def __init__(self, s_id, name, obj, title, valid):
        self.id = s_id
        self.name = name
        self.obj = obj
        self.title = title
        self.valid = valid
        
    def __str__(self):
        return "Step id: %s, name: %s, title: %s, valid: %s" % (self.id, self.name, self.title, self.valid)
        
class Steps(object):
    def __init__(self, sself, step_name_list):
        self.sself = sself
        __step_l = []
        
        for group, name in step_name_list:
            cls = self.get_step_class(name)
            if cls:
                __step_l.append([group, cls.NAME, cls(sself), cls.LABEL, True])
            else:
                raise Exception('Can not find class by name %s' % name)
        i = -1
        self.step_lst = []
        self.step_map = {}
        self.group_step_map = {}
        for s in __step_l:
            i += 1
            step = Step(i, *s[1:])
            self.step_lst.append(step)
            self.step_map[step.name] = step
            self.group_step_map.setdefault(s[0], []).append(step)
            step.obj.widget.hide()
            
    def get_step_class(self, name):
        from mi.client.modules import module_list
        for mod in module_list:
#            import pdb; pdb.set_trace()
            if mod.NAME == name:
                return mod
        return None
    
    def get_step_group(self, step):
        for k, v in self.group_step_map.items():
            if step in v:
                return k
        return None
    
    def init(self):
        
        for step in self.step_lst:
            self.sself.leftpanel.addstep(self.get_step_group(step), step.name)
        
        #### Init startup action
        if not CF.D.DEBUG_GUI:
            for step in self.step_lst:
                if hasattr(step.obj, 'startup_action'):
                    logger.d('init %s' % step.obj.startup_action)
                    step.obj.startup_action()

    def has_key(self, key):
        return self.step_map.has_key(key)
        
    def get_step_by_name(self, name):
        return self.step_map[name]
        
    def get_step_by_id(self, s_id):
        return self.step_lst[s_id]
        
    def get_id_by_name(self, name):
        return self.step_map[name].id
        
    def get_name_by_id(self, s_id):
        return self.step_lst[s_id].name

    def __len__(self):
        return len(self.step_lst)

XML_DATA = '''
<frame width="800" height="600">
<vbox>
<hbox>
<label text="MagicInstaller" />
<label expand="true" />
<leftpanel />
</hbox>
<!-- <header logo="images/banner.png.800x600" /> -->
<tableV2 expand="true" fill="true">
<tr>
   <rightpanel expandfill="true" />
</tr>
</tableV2>
<statusbar />
<buttonbar />
</vbox>
</frame>
'''
class MainXmlUi(xmlgtk.xmlgtk):
    def __init__(self, sself):
        self.sself = sself
        self.header0 = MIHeader(sself)
        self.leftpanel = MILeftPanel(sself, _('Steps'))
        self.rightpanel = MIRightPanel(sself, _(''))
        self.statusbar = MIStatusBar(sself)
        self.buttonbar = MIButtonBar(sself)
        xmlgtk.xmlgtk.__init__(self, XML_DATA)
        
    def xgc_header(self, node):
        logo = node.getAttribute('logo')
        self.header0.set_logo(logo)
        return self.header0
    
    def xgc_leftpanel(self, node):
        return self.leftpanel
    
    def xgc_rightpanel(self, node):
        return self.rightpanel
    
    def xgc_statusbar(self, node):
        return self.statusbar
    
    def xgc_buttonbar(self, node):
        return self.buttonbar
    
class MIMainWindow(gtk.Window):
    def __init__(self, step_name_list, *args, **kw):
        gtk.Window.__init__(self, *args, **kw)
        self.set_name(self.__class__.__name__)
        self.xml_obj = MainXmlUi(self)
        
        self.leftpanel = self.xml_obj.leftpanel
        self.rightpanel = self.xml_obj.rightpanel
        self.statusbar = self.xml_obj.statusbar
        self.buttonbar = self.xml_obj.buttonbar
        
        self.set_title(_('Magic Installer'))
        self.set_border_width(4)
        self.connect('destroy', lambda x: gtk.main_quit())
        self.values = parse(search_file('magic.values.xml', [CF.D.HOTFIXDIR, '.']))
        self.tm = MiTaskman(1325, self.statusbar.get_progressbar(),
                          self.statusbar.get_progressbar())
        self.step_name_list = step_name_list
        
    def init(self):
        self.curstep = -1

        self.steps = Steps(self, self.step_name_list)
        
        self.steps.init()
        
        self.add(self.xml_obj.widget)
        
        self.show_all()

        start_stepid = 0
        if len(sys.argv) > 1:
            try:
                start_stepid = int(sys.argv[1])
            except:
                pass
        else:
            for stepid in range(len(self.steps)):
                if os.path.exists('/tmpfs/debug/start.step.%d' % stepid):
                    start_stepid = stepid
                    break
        step = self.steps.get_step_by_id(start_stepid)
        dolog('Start step: %s' % step)
        self.load_env(step.id)
        self.switch_to_page(step.name)
        #self.switch_to_page('welcome')
        
    def load_env(self, stepid):
        if stepid > 0:
            conf_file = '/tmpfs/step_conf/step_%s.json'
            find_it = False
            for s_id in range(stepid - 1, -1, -1):
                if os.path.exists(conf_file % s_id):
                    conf_file = conf_file % s_id
                    find_it = True
                    break
            if find_it:
                CF.load_from_file(conf_file)
    def btnnext_sensitive(self, sensitive):
        self.buttonbar.next.set_sensitive(sensitive)
    
    def btnback_sensitive(self, sensitive):
        self.buttonbar.back.set_sensitive(sensitive)
    
    def switch_to_page(self, name):
        if not self.steps.has_key(name): return
        step = self.steps.get_step_by_name(name)
        if self.curstep == step.id: return
        nextstep = step.id

        if nextstep < self.curstep or \
                    ( nextstep > self.curstep and 
                     self.leave_step(self.curstep) and 
                     self.enter_step(nextstep) ):
                     
            dolog('switch_to_page "%s" step from %s to %s Success' % (name, self.curstep, nextstep))
            self.rightpanel.switch(step.obj.widget)
            self.leftpanel.switch(self.curstep, step.id)
            self.curstep = nextstep
        else:
            dolog('switch_to_page "%s" step from %s to %s Failed' % (name, self.curstep, nextstep))
            # Call set_current_page is useless here, so use timeout
            # to switch back.
            #gobject.timeout_add(10, self.page_restore)
            
    def enter_step(self, stepid):
        step = self.steps.get_step_by_id(stepid)
        if hasattr(step.obj, 'enter'):
            return step.obj.enter()
        return True
        
    def leave_step(self, stepid):
        if stepid == -1: return True
        step = self.steps.get_step_by_id(stepid)
        ret = True
        if hasattr(step.obj, 'leave'): ret = step.obj.leave()
        else: ret = True
        if ret: self.save_env(stepid)
        return ret
        
    def save_env(self, stepid):
        CF.save_to_file('/tmpfs/step_conf/step_%s.json' % stepid)
        
####----------------------------------------------------

    def btnhelp_clicked(self, widget, data):
        step = self.steps.get_step_by_id(self.curstep)
        if hasattr(step, 'get_help'):
            help = step.get_help()
            if os.path.exists(help):
                with open(help) as f:
                    content = f.read()
            else:
                content = help
        else:
            content = _('This page has no help information.')
        box = magichelp_popup()
        tv = box.id_map['msg'].tv
        tv.get_buffer().set_text(content)

    def btncancel_clicked(self, widget, data):
        self.steps.get_step_by_id(self.curstep).btncancel_clicked(widget, data)

    def btnback_clicked(self, widget, data):
        step = self.steps.get_step_by_id(self.curstep)
        if step.obj.btnback_clicked(widget, data):
            #self.name_map['mi_main'].set_current_page(self.curstep - 1)
            self.btnback_do()

    def btnnext_clicked(self, widget, data):
        step = self.steps.get_step_by_id(self.curstep)
        if hasattr(step.obj, 'btnnext_clicked'):
            # if step not has btnnext_clicked method, we regard it as success to next (and some thing can be checked in leave function)
            if step.obj.btnnext_clicked(widget, data):
                self.btnnext_do()
        else:
            self.btnnext_do()

    def btnback_do(self):
        self.switch_to_page(self.curstep - 1)
        
    def btnnext_do(self):
        step = self.steps.get_step_by_id(self.curstep)
        self.skip_steps(step.obj.skip_stepnames)
        
        n_step_id = self.get_next_available_step(self.curstep)
        self.switch_to_page(self.steps.get_name_by_id(n_step_id))
        
    def skip_steps(self, skip_stepnames):
        for name in skip_stepnames:
            dolog('Skip Step: %s ...' % name)
            self.steps.get_step_by_name(name).valid = False
            self.leftpanel.skip_step(name)
            dolog('Skip Step: %s Done' % name)

    def get_next_available_step(self, curstep):
        n_step_id = 0
        for s_id in range(curstep+1, len(self.steps)):
            step = self.steps.get_step_by_id(s_id)
            if step.valid:
                n_step_id = s_id
                break
        return n_step_id
        
    #def switch_to_page(self, pageno):
        #if self.curstep != pageno:
            #if pageno < self.curstep:
                #self.stepsarr[self.curstep].set_from_file('images/applet-blank.png')
                #self.stepsarr[pageno].set_from_file('images/applet-busy.png')
                #self.switch2step(pageno)
            #elif pageno > self.curstep:
                #if self.leave_step(self.curstep) and self.enter_step(pageno): # only check next
                    #self.stepsarr[self.curstep].set_from_file('images/applet-okay.png')
                    #self.stepsarr[pageno].set_from_file('images/applet-busy.png')
                    #self.switch2step(pageno)
            #else:
                ## Call set_current_page is useless here, so use timeout
                ## to switch back.
                #gobject.timeout_add(10, self.page_restore)

    def cb_push_leftpanel(self, widget):
        logger.d('cb_push_leftpanel')
        self.leftpanel.push(widget)
        
    def cb_pop_leftpanel(self):
        logger.d('cb_pop_leftpanel')
        return self.leftpanel.pop()
        
    def cb_push_rightpanel(self, widget):
        logger.d('cb_push_rightpanel rightpanel.stash_stack.len %s' % len(self.rightpanel.stash_stack))
        self.rightpanel.push(widget)
        
    def cb_pop_rightpanel(self):
        logger.d('cb_pop_rightpanel')
        return self.rightpanel.pop()
#-------------------------- TODO ---------------------------------------

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
        xml_data = '''
        <themedlg>
          <vbox>
            <label line_wrap="true" fill="true"
                   text="((Click the button to choose the theme that you like.))"/>
            <hbox name="themes" expand="true" fill="true">
              <image file="images/gnome-ccthemes.png" fill="true"/>
            </hbox>
          </vbox>
        </themedlg>
        '''
        self.themedlg = magicpopup.magicpopup(self, xml_data,
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
            path = themenode.getAttribute('dir')
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
                    if path:
                        name = path
                    else:
                        name = _('Default')
                thebutton = gtk.Button(name)
            thebutton.connect('clicked', self.theme_clicked, path)
            thetable.attach(thebutton, left, left + 1, top, top + 1, 0, 0, 0, 0)
            top = top + 1
            if top == rows:
                top = 0
                left = left + 1
        thetable.show()
        self.themedlg.name_map['themes'].pack_start(thetable, True, True)
        
    def btnlogger_clicked(self, widget, data):
        pass
        #self.tm.add_action(None, None, None, 'start_magiclogger', 0)

    def start_install(self):
        '''
            hard code,
            because we collect all information for install package to target system, so we start this action in backend.
            The install action is in tackactions.py
        '''
        step = self.steps.get_step_by_name('takeactions')
        step.obj.start_install()
        