#!/usr/bin/python
import gtk
from mi.client.utils import logger, CF
from mi.client.utils.xmlgtk import xmlgtk
XML_DATA = '''
<vbox>
  <hbox name="LeftPanelStepBox" id="step_box" />
  <frame id="sub_step_frame" />
</vbox>
'''
class StepButton(gtk.Button):
    def __init__(self, img_path, step_name, label_text, *args, **kw):
        gtk.Button.__init__(self, *args, **kw)
        self.img = None
        self.label = None
        self.step_name = step_name
        self.box = self.img_label_box(img_path, label_text)
        self.add(self.box)
        self.box.show()

    def img_label_box(self, img_path, label_text):
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(0)
        #self.img = gtk.Image()
        #self.img.set_from_file(img_path)
        self.label = gtk.Label()
        self.label.set_use_markup(gtk.TRUE)
        self.label.set_markup('<span size="9500">%s</span>' % label_text)
        #hbox.pack_start(self.img, False, False, 2)
        hbox.pack_start(self.label, False, False, 2)
        #self.img.show()
        self.label.show()
        return hbox
    
    def get_step_name(self):
        return self.step_name
    
    #def change_image(self, img_path):
    #    self.img.set_from_file(img_path)
    def set_finished(self):
        self.label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(0,65535,0))
        
    def set_active(self):
        self.label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(65535,0,0))

class GroupBtn(gtk.Button):
    def __init__(self, title, *args, **kwargs):
        gtk.Button.__init__(self, *args, **kwargs)
        self.set_border_width(2)
        self.label = gtk.Label(title)
        self.label.set_line_wrap(False)
        self.label_step = gtk.Label()
        self.hbox = gtk.HBox()
        self.hbox.pack_start(self.label, False, False)
        self.hbox.pack_start(self.label_step, False, False)
        self.add(self.hbox)
        if not CF.D.DEBUG:
            self.set_sensitive(False)
        self.stepid = 0
        self.total = 0
            
    def set_step(self, stepid, total=None):
        self.stepid = stepid
        if total is not None:
            self.total = total
        self.label_step.set_text('(%s/%s)' % (self.stepid, self.total))
        
    def set_finished(self):
        self.label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(0,65535,0))
        self.label_step.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(0,65535,0))
        
    def set_active(self):
        self.label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(65535,0,0))
        self.label_step.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(65535,0,0))
        
class MILeftPanel(gtk.Frame):
    def __init__(self, sself, *args, **kw):
        gtk.Frame.__init__(self, *args, **kw)
        self.sself = sself
        
        self.xml_obj = xmlgtk(XML_DATA)
        
        self.btn_lst = []
        self.stash_stack = []
        self.stash_stack.append(self.xml_obj.widget)
        self.add(self.stash_stack[-1])
        
        self.group_btn_map = {}
        self.cur_group = None
        
    def addstep(self, group, name):
        logger.d('addstep group(%s) name(%s)' % (group, name))
        step = self.sself.steps.get_step_by_name(name)

        btn = StepButton('images/applet-blank.png', step.name, step.title)
        btn.connect('clicked', self.on_switch_to_page, name)
        self.btn_lst.append(btn)
        
        if not self.group_btn_map.has_key(group):
            group_btn = GroupBtn(group)
            group_btn.connect('clicked', self.on_switch_to_group, group)
            self.group_btn_map[group] = {'group': group_btn, 'btn_lst': [btn], 'btn_box': gtk.HBox()}
            self.xml_obj.id_map['step_box'].pack_start(group_btn, False, False)
            group_btn.show()
            group_btn.set_step(0, 1)
        else:
            group_btn = self.group_btn_map[group]['group']
            self.group_btn_map[group]['btn_lst'].append(btn)
            group_btn.set_step(0, len(self.group_btn_map[group]['btn_lst']))
            
        self.group_btn_map[group]['btn_box'].pack_start(btn, False, False)
        btn.show()

    def skip_step(self, name):
        s_id = self.sself.steps.get_id_by_name(name)
        self.btn_lst[s_id].set_sensitive(False)
    
    def get_step_group(self, step_name):
        step_id = None
        group_name = None
        for k, v in self.group_btn_map.items():
            i = 0
            for btn in v['btn_lst']:
                if step_name == btn.get_step_name():
                    step_id = i
                    group_name = k
                    break
                i += 1
        return group_name, step_id
    
    def on_switch_to_page(self, widget, name, call_parent=True):
        #self.sself.switch_to_page(name)
        group, stepid = self.get_step_group(name)
        self.on_switch_to_group(None, group, stepid, call_parent)
        
        print 'on_switch_to_page name %s,  %s %s' % (name, group, stepid)
        self.group_btn_map[group]['btn_lst'][stepid].set_active()
        self.group_btn_map[self.cur_group]['group'].set_step(stepid+1)
        if call_parent:
            self.sself.switch_to_page(name)

            
    def on_switch_to_group(self, widget, group, stepid=0, call_parent=True):
        logger.d('on_switch_to_group group(%s) stepid(%s)' % (group, stepid))
        if self.cur_group != group:
            if self.cur_group:
                self.xml_obj.id_map['sub_step_frame'].remove(self.group_btn_map[self.cur_group]['btn_box'])
                self.group_btn_map[self.cur_group]['btn_box'].hide()
                self.group_btn_map[self.cur_group]['group'].set_finished()
                
            self.xml_obj.id_map['sub_step_frame'].add(self.group_btn_map[group]['btn_box'])#.pack_start(, False, False)
            self.group_btn_map[group]['btn_box'].show()
            
            self.cur_group = group
            self.group_btn_map[self.cur_group]['group'].set_active()
        
        #step_name = self.group_btn_map[group]['btn_lst'][stepid].get_step_name()

    def switch(self, from_id, to_id):
        logger.d('leftpanel.switch: %s, %s' % (from_id, to_id))
        if from_id >= 0:
            self.btn_lst[from_id].set_finished()
            
        #self.btn_lst[to_id].set_active()
        self.on_switch_to_page(None, self.btn_lst[to_id].get_step_name(), False)
        
    def push(self, widget):
        if self.stash_stack: self.remove(self.stash_stack[-1]); self.stash_stack[-1].hide()
        self.stash_stack.append(widget)
        self.stash_stack[-1].show()
        self.add(self.stash_stack[-1])
        
    def pop(self):
        self.remove(self.stash_stack[-1])
        widget = self.stash_stack.pop()
        if self.stash_stack: self.stash_stack[-1].show(); self.add(self.stash_stack[-1])
        widget.hide()
        return widget
        