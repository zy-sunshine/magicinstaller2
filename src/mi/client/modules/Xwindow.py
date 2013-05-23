# -*- python -*-
from mi.client.utils import _
from mi.client.utils import magicstep, magicpopup
import rhpxl.monitor, rhpxl.videocard, rhpxl.mouse
import string
from xml.dom.minidom import parseString

class MIStep_Xwindow (magicstep.magicstepgroup):
    NAME = 'Xwindow'
    LABEL = _("Xwindow")
    def __init__(self, rootobj):
        magicstep.magicstepgroup.__init__(self, rootobj, 'Xwindow.xml',
                                          ['monitor', 'videocard', 'mouse', 'misc'],
                                          'steps')
        m = rhpxl.monitor.MonitorInfo()
        self.mondb = m.monitorsDB()
        self.x_settings = {}

    def get_label(self):
        return self.LABEL

    def startup_action(self):
        self.rootobj.tm.add_action(_('Probe Monitor'),
                                   self.probe_monitor_ok, None,
                                   'probe_monitor', 0)
        self.rootobj.tm.add_action(_('Probe VideoCard'),
                                   self.probe_videocard_ok, None,
                                   'probe_videocard', 0)
        self.rootobj.tm.add_action(_('Probe Mouse'),
                                   self.probe_mouse_ok, None,
                                   'probe_mouse', 0)
    def check_leave_monitor(self):
        self.fetch_values(self.rootobj.values)
        return 1

    def check_leave_videocard(self):
        self.fetch_values(self.rootobj.values)
        return 1

    def check_leave_mouse(self):
        self.fetch_values(self.rootobj.values)
        return 1

    def leave(self):
        if not magicstep.magicstepgroup.leave(self):  return 0
        if not self.gen_x_settings():
            magicpopup.magicmsgbox(None,
                                   _('Failed to collect the information about Xwindow configuration.'),
                                   magicpopup.magicmsgbox.MB_ERROR,
                                   magicpopup.magicpopup.MB_OK)
            return  0
        self.rootobj.tm.add_action(_('Generate Xwindow configuration'),
                                     None, None, 'gen_x_config', self.x_settings)
        return  1
        
    def reprobe_monitor(self, widget, data):
        self.rootobj.tm.add_action(_('Probe Monitor'),
                                   self.probe_monitor_ok, None,
                                   'probe_monitor', 0)

    def reprobe_videocard(self, widget, data):
        self.rootobj.tm.add_action(_('Probe VideoCard'),
                                   self.probe_videocard_ok, None,
                                   'probe_videocard', 0)

    def reprobe_mouse(self, widget, data):
        self.rootobj.tm.add_action(_('Probe Mouse'),
                                   self.probe_mouse_ok, None,
                                   'probe_mouse', 0)

    def probe_monitor_ok(self, tdata, data):
        (m_name, m_horiz, m_vert) = tdata
        self.set_data(self.rootobj.values, 'Xwindow.monitor.name', m_name)
        self.set_data(self.rootobj.values, 'Xwindow.monitor.horiz_sync', m_horiz)
        self.set_data(self.rootobj.values, 'Xwindow.monitor.vert_refresh', m_vert)
        self.fill_values(self.rootobj.values.documentElement)

    def probe_videocard_ok(self, tdata, data):
        vclist = tdata
        if len(vclist) == 0 or len(vclist[0]) == 0:  return
        (vc0name, vc0driver, vc0vidram) = vclist[0]
        self.set_data(self.rootobj.values, 'Xwindow.videocard.name', vc0name)
        self.set_data(self.rootobj.values, 'Xwindow.videocard.driver', vc0driver)
        self.set_data(self.rootobj.values, 'Xwindow.videocard.videoram', str(vc0vidram))
        self.fill_values(self.rootobj.values.documentElement)

    def probe_mouse_ok(self, tdata, data):
        mouse = tdata
        (name, protocol, device, xemu3, shortname) = mouse
        self.set_data(self.rootobj.values, 'Xwindow.mouse.name', name)
        self.set_data(self.rootobj.values, 'Xwindow.mouse.protocol', protocol)
        self.set_data(self.rootobj.values, 'Xwindow.mouse.device', device)
        self.set_data(self.rootobj.values, 'Xwindow.mouse.xemu3', xemu3)
        self.set_data(self.rootobj.values, 'Xwindow.mouse.shortname', shortname)
        self.fill_values(self.rootobj.values.documentElement)

    def popup_monitor_dialog(self, widget, data):
        def xmlesc(s):
            s = string.replace(s, "&", "&amp;")
            s = string.replace(s, "<", "&lt;")
            s = string.replace(s, ">", "&gt;")
            return  s

        (model, iter) = self.name_map['monitor_vender_list_treeview'].get_selection().get_selected()
        if not iter:  return
        vender = model.get_value(iter, 0)
        if not self.mondb.has_key(vender):  return
        xmlstr = ''
        for (m_name, dummy, m_vert, m_horiz) in self.mondb[vender]:
            xmlstr = xmlstr + '<row c0="%s" c1="%s" c2="%s"/>' % (xmlesc(m_name), xmlesc(m_horiz), xmlesc(m_vert))
        xmldoc = parseString('<?xml version="1.0"?><data><monlist>' + xmlstr + '</monlist></data>')
        self.mondlg = magicpopup.magicpopup(self, self.uixmldoc,
                                            _("Please choose your monitor here."),
                                            magicpopup.magicpopup.MB_OK | magicpopup.magicpopup.MB_CANCEL,
                                            "monitor.dialog", "mondlg_")
        self.mondlg.topwin.set_size_request(600, 400)
        self.mondlg.fill_values(xmldoc.documentElement)

    def mondlg_ok_clicked(self, widget, data):
        (model, iter) = self.mondlg.name_map['monitor_list_treeview'].get_selection().get_selected()
        if not iter:  return
        name = model.get_value(iter, 0)
        horiz_sync = model.get_value(iter, 1)
        vert_refresh = model.get_value(iter, 2)
        self.set_data(self.rootobj.values, 'Xwindow.monitor.name', name)
        self.set_data(self.rootobj.values, 'Xwindow.monitor.horiz_sync', horiz_sync)
        self.set_data(self.rootobj.values, 'Xwindow.monitor.vert_refresh', vert_refresh)
        self.fill_values(self.rootobj.values.documentElement)
        self.mondlg.topwin.destroy()

    def load_videocard(self, widget, data):
        (model, iter) = self.name_map['videocard_list_treeview'].get_selection().get_selected()
        if iter:
            name = model.get_value(iter, 0)
            driver = model.get_value(iter, 1)
            self.set_data(self.rootobj.values, 'Xwindow.videocard.name', name)
            self.set_data(self.rootobj.values, 'Xwindow.videocard.driver', driver)
            self.fill_values(self.rootobj.values.documentElement)

    def load_mouse(self, widget, data):
        (model, iter) = self.name_map['mouse_list_treeview'].get_selection().get_selected()
        if iter:
            name = model.get_value(iter, 0)
            protocol = model.get_value(iter, 1)
            device = model.get_value(iter, 2)
            xemu3 = model.get_value(iter, 3)
            self.set_data(self.rootobj.values, 'Xwindow.mouse.name', name)
            self.set_data(self.rootobj.values, 'Xwindow.mouse.protocol', protocol)
            self.set_data(self.rootobj.values, 'Xwindow.mouse.device', device)
            self.set_data(self.rootobj.values, 'Xwindow.mouse.xemu3', xemu3)
            self.fill_values(self.rootobj.values.documentElement)

    def test_x_settings(self, widget, data):
        if not self.gen_x_settings():  return
        self.rootobj.tm.add_action(_('Test X Settings'),
                                   self.test_x_settings_result, None,
                                   'test_x_settings', self.x_settings)

    def test_x_settings_result(self, tdata, data):
        result = tdata
        print 'test_x_settings:', result
        if result == 'SUCCESS':
            magicpopup.magicmsgbox(None, _('Success!'),
                                   magicpopup.magicmsgbox.MB_INFO,
                                   magicpopup.magicpopup.MB_OK)
        else:
            magicpopup.magicmsgbox(None, _(result),
                                   magicpopup.magicmsgbox.MB_ERROR,
                                   magicpopup.magicpopup.MB_OK)

    def widemode_res_changed(self, optmenu, data):
        res_om = self.name_map["widemode_res_om"]
        val = self.optionmenu_map[res_om][1][res_om.get_active()]
        x, y = val.split('x')
        self.name_map["widemode_x_entry"].set_text(x);
        self.name_map["widemode_y_entry"].set_text(y);

    def gen_x_settings(self):
        self.fetch_values(self.rootobj.values)
        self.x_settings['monitor'] = (
            self.get_data(self.values, 'Xwindow.monitor.name'),
            self.get_data(self.values, 'Xwindow.monitor.horiz_sync'),
            self.get_data(self.values, 'Xwindow.monitor.vert_refresh'))
        self.x_settings['videocard'] = (
            self.get_data(self.values, 'Xwindow.videocard.name'),
            self.get_data(self.values, 'Xwindow.videocard.driver'),
            self.get_data(self.values, 'Xwindow.videocard.videoram'))
        self.x_settings['mouse'] = (
            self.get_data(self.values, 'Xwindow.mouse.name'),
            self.get_data(self.values, 'Xwindow.mouse.protocol'),
            self.get_data(self.values, 'Xwindow.mouse.device'),
            self.get_data(self.values, 'Xwindow.mouse.xemu3'),
            self.get_data(self.values, 'Xwindow.mouse.shortname'))
        self.x_settings['modes'] = {}

        resmap = {640: '640x480', 800: '800x600', 1024: '1024x768', 1280: '1280x1024'}
        for depth in [8, 15, 16, 24]:
            for res in [1280, 1024, 800, 640]:
                if self.get_data(self.values, 'Xwindow.modes.m%dx%d' % (res, depth)) == 'true':
                    self.x_settings['modes'].setdefault(str(depth), []).append(resmap[res])
        # wide mode
        widemode_x = self.get_data(self.values, 'Xwindow.modes.widemode_x')
        widemode_y = self.get_data(self.values, 'Xwindow.modes.widemode_y')
        widemode_depth = self.get_data(self.values, 'Xwindow.modes.widemode_depth')
        widemode_refresh = self.get_data(self.values, 'Xwindow.modes.widemode_refresh')
        self.x_settings['wide_mode'] = (widemode_x, widemode_y, widemode_depth, widemode_refresh)
        print self.x_settings
        
        if len(widemode_x) != 0 and len(widemode_y) != 0:
            try:
                widemode_x = int(widemode_x)
                widemode_y = int(widemode_y)
                widemode_refresh = int(widemode_refresh)
            except ValueError, e:
                magicpopup.magicmsgbox(None,
                                       _('Widemode resolution or refresh rate error.'),
                                       magicpopup.magicmsgbox.MB_ERROR,
                                       magicpopup.magicpopup.MB_OK)
                return 0
            self.x_settings['modes'].setdefault(widemode_depth, []).insert(0, "%dx%d" % (widemode_x, widemode_y))

        if len(self.x_settings['modes']) == 0:
            magicpopup.magicmsgbox(None,
                                   _('At least one mode has to be chosen.'),
                                   magicpopup.magicmsgbox.MB_ERROR,
                                   magicpopup.magicpopup.MB_OK)
            return  0

        self.x_settings['init'] = self.get_data(self.values, 'Xwindow.init')
        self.x_settings['FontPathes'] = []
        return  1
