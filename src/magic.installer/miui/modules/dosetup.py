#!/usr/bin/python
from miui.utils import _, Logger
from miui.utils import magicstep
Log = Logger.get_instance(__name__)
dolog = Log.i

class MIStep_dosetup (magicstep.magicstep):
    def __init__(self, rootobj):
        magicstep.magicstep.__init__(self, rootobj, 'dosetup.xml', 'dosetup')
        self.doing = 1
        self.x_settings = {}
        
        # monitor
        self.monitor_name = ''
        self.monitor_horiz_sync = ''
        self.monitor_vert_refresh = ''
        # videocard
        self.videocard_name = ''
        self.videocard_driver = ''
        self.videocard_videoram = ''
        # mouse
        self.mouse_name = ''
        self.mouse_protocol = ''
        self.mouse_device = ''
        self.mouse_xemu3 = ''
        self.mouse_shortname = ''

    def get_label(self):
        return  _("Do Setup")

    def probe_monitor_ok(self, tdata, data):
        (m_name, m_horiz, m_vert) = tdata
        #self.set_data(self.rootobj.values, 'Xwindow.monitor.name', m_name)
        #self.set_data(self.rootobj.values, 'Xwindow.monitor.horiz_sync', m_horiz)
        #self.set_data(self.rootobj.values, 'Xwindow.monitor.vert_refresh', m_vert)
        #self.fill_values(self.rootobj.values.documentElement)
        self.monitor_name = m_name
        self.monitor_horiz_sync = m_horiz
        self.monitor_vert_refresh = m_vert

    def probe_videocard_ok(self, tdata, data):
        vclist = tdata
        if len(vclist) == 0 or len(vclist[0]) == 0:  return
        (vc0name, vc0driver, vc0vidram) = vclist[0]
        #self.set_data(self.rootobj.values, 'Xwindow.videocard.name', vc0name)
        #self.set_data(self.rootobj.values, 'Xwindow.videocard.driver', vc0driver)
        #self.set_data(self.rootobj.values, 'Xwindow.videocard.videoram', str(vc0vidram))
        #self.fill_values(self.rootobj.values.documentElement)
        self.videocard_name = vc0name
        self.videocard_driver = vc0driver
        self.videocard_videoram = vc0vidram

    def probe_mouse_ok(self, tdata, data):
        mouse = tdata
        (name, protocol, device, xemu3, shortname) = mouse
        #self.set_data(self.rootobj.values, 'Xwindow.mouse.name', name)
        #self.set_data(self.rootobj.values, 'Xwindow.mouse.protocol', protocol)
        #self.set_data(self.rootobj.values, 'Xwindow.mouse.device', device)
        #self.set_data(self.rootobj.values, 'Xwindow.mouse.xemu3', xemu3)
        #self.set_data(self.rootobj.values, 'Xwindow.mouse.shortname', shortname)
        #self.fill_values(self.rootobj.values.documentElement)
        self.mouse_name = name
        self.mouse_protocol = protocol
        self.mouse_device = device
        self.mouse_xemu3 = xemu3
        self.mouse_shortname = shortname

    def gen_x_settings(self):
        #self.fetch_values(self.rootobj.values)
        self.x_settings['monitor'] = (
            #self.get_data(self.values, 'Xwindow.monitor.name'),
            #self.get_data(self.values, 'Xwindow.monitor.horiz_sync'),
            #self.get_data(self.values, 'Xwindow.monitor.vert_refresh')
            self.monitor_name,
            self.monitor_horiz_sync,
            self.monitor_vert_refresh,
            )
        self.x_settings['videocard'] = (
            #self.get_data(self.values, 'Xwindow.videocard.name'),
            #self.get_data(self.values, 'Xwindow.videocard.driver'),
            #self.get_data(self.values, 'Xwindow.videocard.videoram')
            self.videocard_name,
            self.videocard_driver,
            self.videocard_videoram,
            )
        self.x_settings['mouse'] = (
            #self.get_data(self.values, 'Xwindow.mouse.name'),
            #self.get_data(self.values, 'Xwindow.mouse.protocol'),
            #self.get_data(self.values, 'Xwindow.mouse.device'),
            #self.get_data(self.values, 'Xwindow.mouse.xemu3'),
            #self.get_data(self.values, 'Xwindow.mouse.shortname')
            self.mouse_name,
            self.mouse_protocol,
            self.mouse_device,
            self.mouse_xemu3,
            self.mouse_shortname
            )
        self.x_settings['modes'] = {}

        resmap = {640: '640x480', 800: '800x600', 1024: '1024x768', 1280: '1280x1024'}
        #for depth in [8, 15, 16, 24]:
        #    for res in [1280, 1024, 800, 640]:
        #        if self.get_data(self.values, 'Xwindow.modes.m%dx%d' % (res, depth)) == 'true':
        #            self.x_settings['modes'].setdefault(str(depth), []).append(resmap[res])
        for depth in [16, 24]:
            for res in [1280, 1024]:
                self.x_settings['modes'].setdefault(str(depth), []).append(resmap[res])

        # wide mode
        #widemode_x = self.get_data(self.values, 'Xwindow.modes.widemode_x')
        widemode_x = '1024'
        #widemode_y = self.get_data(self.values, 'Xwindow.modes.widemode_y')
        widemode_y = '640'
        #widemode_depth = self.get_data(self.values, 'Xwindow.modes.widemode_depth')
        widemode_depth = '24'
        #widemode_refresh = self.get_data(self.values, 'Xwindow.modes.widemode_refresh')
        widemode_refresh = '60'
        self.x_settings['wide_mode'] = (widemode_x, widemode_y, widemode_depth, widemode_refresh)
        print self.x_settings
        
        #if len(widemode_x) != 0 and len(widemode_y) != 0:
        #    try:
        #        widemode_x = int(widemode_x)
        #        widemode_y = int(widemode_y)
        #        widemode_refresh = int(widemode_refresh)
        #    except ValueError, e:
        #        magicpopup.magicmsgbox(None,
        #                               _('Widemode resolution or refresh rate error.'),
        #                               magicpopup.magicmsgbox.MB_ERROR,
        #                               magicpopup.magicpopup.MB_OK)
        #        return 0
        #    self.x_settings['modes'].setdefault(widemode_depth, []).insert(0, "%dx%d" % (widemode_x, widemode_y))

        widemode_x = int(widemode_x)
        widemode_y = int(widemode_y)
        widemode_refresh = int(widemode_refresh)
        self.x_settings['modes'].setdefault(widemode_depth, []).insert(0, "%dx%d" % (widemode_x, widemode_y))

        #if len(self.x_settings['modes']) == 0:
        #    magicpopup.magicmsgbox(None,
        #                           _('At least one mode has to be chosen.'),
        #                           magicpopup.magicmsgbox.MB_ERROR,
        #                           magicpopup.magicpopup.MB_OK)
        #    return  0

        #self.x_settings['init'] = self.get_data(self.values, 'Xwindow.init')
        self.x_settings['init'] = 'gra'
        self.x_settings['FontPathes'] = []
        return  1

    def startup_action(self):
        # If we skip X Setting, we should auto detect the hardware, and copy
        # the generated Xorg.conf to target system.
        if 1:#skipxsetting:
            self.rootobj.tm.add_action(_('Probe Monitor'),
                                   self.probe_monitor_ok, None,
                                   'probe_monitor', 0)
            self.rootobj.tm.add_action(_('Probe VideoCard'),
                                   self.probe_videocard_ok, None,
                                   'probe_videocard', 0)
            self.rootobj.tm.add_action(_('Probe Mouse'),
                                   self.probe_mouse_ok, None,
                                   'probe_mouse', 0)

    def enter(self):
        if skipxsetting:
            if not self.gen_x_settings():
                magicpopup.magicmsgbox(None,
                                   _('Failed to collect the information about Xwindow configuration.'),
                                   magicpopup.magicmsgbox.MB_ERROR,
                                   magicpopup.magicpopup.MB_OK)
                # Continue anyway.
                #return 0
            self.rootobj.tm.add_action(_('Generate Xwindow configuration'),
                                     None, None, 'gen_x_config', self.x_settings)
            self.rootobj.tm.add_action(_('Backup Xwindow configuration files'),
                                     None, None, 'backup_xconfig', 0)

        self.rootobj.btnback_sensitive(False)
        self.rootobj.btnnext_sensitive(False)

        dolog('action_accounts\n')
        rootpasswd = self.get_data(self.values, 'accounts.root.password')
        acclist = []
        accnode = self.srh_data_node(self.values, 'accounts.userlist')
        for node in accnode.getElementsByTagName('row'):
            acclist.append((node.getAttribute('c0'), # Username.
                            node.getAttribute('c1'), # Password.
                            node.getAttribute('c2'), # Shell.
                            node.getAttribute('c3'), # Home directory.
                            node.getAttribute('c4'))) # Real UID or 'Auto'.
        dolog('%s\n' % 'setup_accounts') #str(('setup_accounts', rootpasswd, acclist)))

        self.rootobj.tm.add_action(_('Setup accounts'), self.doshort, None,
                                   'setup_accounts', rootpasswd, acclist)

        return  1

    def leave(self):
        if self.doing:
            magicpopup.magicmsgbox(None,
                                   _('We are doing setup, do not leave please.'),
                                   magicpopup.magicmsgbox.MB_ERROR,
                                   magicpopup.magicmsgbox.MB_OK)
            return  0
        return  1

    def doshort(self, tdata, data):
        hostname = self.get_data(self.values, 'network.hostname')
        ret = self.rootobj.tm.actserver.config_network_short(hostname)
        ret = self.rootobj.tm.actserver.config_keyboard()
        self.rootobj.tm.add_action(_('Run post install script'), self.do_umount_all, None,
                                   'run_post_install', 0)

    def do_umount_all(self, tdata, data):
        self.rootobj.tm.add_action(_('Umount all target partition(s)'), self.done, None,
                                   'umount_all_tgtpart', CONF.RUN.g_mount_all_list, 'y')

    def done(self, tdata, data):
        self.doing = None
        self.rootobj.btnnext_do()
