#!/usr/bin/python
from mi.server.utils import _
import os, string
import rhpxl.monitor, rhpxl.videocard, rhpxl.mouse

from mi.utils.miregister import MiRegister
register = MiRegister()
from mi.server.utils import logger
dolog = logger.info

from mi.utils.miconfig import MiConfig
CF = MiConfig.get_instance()

@register.server_handler('long')
def avoid_none(val, default):
    if val is None:
        return default
    else:
        return val
    
@register.server_handler('long')
def probe_monitor(mia, operid, dummy):
    mon = rhpxl.monitor.MonitorInfo()
    return (avoid_none(mon.monName, ''),
            avoid_none(mon.monHoriz, ''),
            avoid_none(mon.monVert, ''))

@register.server_handler('long')
def probe_videocard(mia, operid, dummy):
    vci = rhpxl.videocard.VideoCardInfo()
    vclist = []
    for vc in vci.videocards:
        vidram = avoid_none(vc.getVideoRam(), 0)
        vclist.append((vc.getDescription(), vc.getDriver(), vidram))
    return vclist

@register.server_handler('long')
def probe_mouse(mia, operid, dummy):
    # Call rhpxl.mouse.Mouse will affect the action of mouse, so do not use it.
    mouse = rhpxl.mouse.Mouse()
    #mouse = rhpxl.mouse.Mouse(skipProbe = 1)
    dev = avoid_none(mouse.getDevice(), 'none')
    xemu3 = mouse.emulate and 'true' or 'false'
    return (mouse.info['FULLNAME'],
            mouse.info['XMOUSETYPE'],
            dev, xemu3,
            mouse.mousetype) # shortname indeed

@register.server_handler('long')
def gen_x_config(mia, operid, x_settings):
    def trim_scope(s):
        def trim_num(s):
            try:
                n = str(float(string.strip(s)))
            except:
                n = '0.0'
            return n
        if string.find(s, '-') >= 0:
            (n0, n1) = string.split(s, '-', 1)
            return  trim_num(n0) + ' - ' + trim_num(n1)
        else:
            return  trim_num(s)

    (mouse_name, mouse_protocol,
     mouse_device, mouse_xemu3,
     mouse_shortname) = x_settings['mouse']
    # Generate XF86Config.
    # Wide screen
    if len(x_settings['wide_mode'][0]) != 0 and \
       len(x_settings['wide_mode'][1]) != 0: # wide_mode selected
        wide_mode_line = os.popen("gtf %s %s %s" % (x_settings['wide_mode'][0],
                                                    x_settings['wide_mode'][1],
                                                    x_settings['wide_mode'][3])).read()
    else:
        wide_mode_line = ''
    # ServerLayout Section
    #if mouse_device != 'input/mice':
    #    alwayscore_mouse = ''
    #else:
    #    alwayscore_mouse = '        InputDevice     "DevInputMice" "AlwaysCore"\n'
    alwayscore_mouse = ''          # seems no use and error prone
    serverlayout = '''
# XFree86 4 configuration created by MagicInstaller.

Section "ServerLayout"
        Identifier      "Default Layout"
        Screen      0   "Screen0" 0 0
        InputDevice     "Mouse0" "CorePointer"
        InputDevice     "Keyboard0" "CoreKeyboard"
%sEndSection
''' % alwayscore_mouse

    # File Section
    files = '''
Section "Files"
        FontPath        "/usr/lib/X11/fonts/misc:unscaled"
        FontPath        "/usr/lib/X11/fonts/75dpi:unscaled"
        FontPath        "/usr/lib/X11/fonts/100dpi:unscaled"
        FontPath        "/usr/lib/X11/fonts/misc"
        FontPath        "/usr/lib/X11/fonts/Type1"
        FontPath        "/usr/lib/X11/fonts/cyrillic"
        FontPath        "/usr/lib/X11/fonts/TTF"
        FontPath        "/usr/share/fonts/default/Type1"
        FontPath        "/usr/share/fonts/pcf/zh_CN"
        FontPath        "/usr/share/fonts/msttcorefonts"
        FontPath        "/usr/share/fonts/ttf/zh_CN"
%s
EndSection
''' % string.join(map(lambda fp: "        FontPath        \"" + fp + "\"\n",
                      x_settings['FontPathes']), '\n')
    # Module Section
    module = '''
Section "Module"
        Load    "dbe"
        Load    "extmod"
        Load    "fbdevhw"
        Load    "glx"
        Load    "record"
        Load    "freetype"
        Load    "dri"
        Load    "v4l"
        Load    "xtrap"
EndSection

Section "DRI" 
        Group   0 
        Mode    0666 
EndSection

Section "ServerFlags"
        Option          "DontZap" "false"
        Option          "AllowEmptyInput"   "false"
EndSection

Section "Extensions" 
        Option          "Composite" "Enable"
        Option          "BackingStore" "false"
EndSection
'''
    # InputDevice Section for Keyboard
    keyboard = '''
Section "InputDevice"
        Identifier      "Keyboard0"
        Driver          "kbd"
        Option          "XkbRules" "xfree86"
        Option          "XbkModel" "pc105"
        Option          "XkbLayout" "us"
EndSection
'''
    # InputDevice Section for Mouse
    if mouse_xemu3 == 'true':
        xemu3 = 'yes'
    else:
        xemu3 = 'no'
    if mouse_shortname == 'synaptics': # Synaptics Touchpad support
                                       # The removed by '#' options are not necessary, Xorg will auto detect them.
                                       # Rest options are necessary to Apply OR Disable.
                                       # synaptics should has the option of "Emulate3Buttons".
        mouse = '''
Section "InputDevice"
        Identifier      "Mouse0"
        Driver          "synaptics"
        Option          "Device" "/dev/%s"
        Option          "Protocol" "auto-dev"
        Option          "Emulate3Buttons" "%s"
        Option          "SendCoreEvents" "true"
#        Option          "LeftEdge" "0"
#        Option          "RightEdge" "850"
#        Option          "TopEdge" "0"
#        Option          "BottomEdge" "645"
#        Option          "MinSpeed" "0.4"
#        Option          "MaxSpeed" "1"
#        Option          "AccelFactor" "0.03"
#        Option          "FingerLow" "55"
#        Option          "FingerHigh" "60"
#        Option          "MaxTapMove" "20"
#        Option          "MaxTapTime" "100"
        Option          "TapButton1" "0"
        Option          "TapButton2" "3"
        Option          "TabButton3" "2"
#        Option          "HorizScrollDelta" "10"
#        Option          "VertScrollDelta" "30"
        Option          "SHMConfig" "on"
EndSection
''' % (mouse_device, xemu3)
    else:
        mouse = '''
Section "InputDevice"
        Identifier      "Mouse0"
        Driver          "mouse"
        Option          "Protocol" "%s"
        Option          "Device" "/dev/%s"
        Option          "ZAxisMapping" "4 5 6 7"
        Option          "Emulate3Buttons" "%s"
EndSection
''' % (mouse_protocol, mouse_device, xemu3)

    # Add DevInputMice as needed.
    if mouse_device != 'input/mice':
        mouse = mouse + '''
Section "InputDevice"
# If the normal CorePointer mouse is not a USB mouse then
# this input device can be used in AlwaysCore mode to let you
# also use USB mice at the same time.
        Identifier      "DevInputMice"
        Driver          "mouse"
        Option          "Protocol" "%s"
        Option          "Device" "/dev/input/mice"
        Option          "ZAxisMapping" "4 5"
        Option          "Emulate3Buttons" "%s"
EndSection
''' % (mouse_protocol, xemu3)

    # Monitor Section
    monitor = '''
Section "Monitor"
        Identifier      "Monitor0"
        VendorName      "Monitor Vendor"
        ModelName       "%s"
        HorizSync       %s
        VertRefresh     %s
%s
EndSection
''' % (x_settings['monitor'][0],
       trim_scope(x_settings['monitor'][1]),
       trim_scope(x_settings['monitor'][2]),
       wide_mode_line)
    # Device Section
    videocard = '''
Section "Device"
        Identifier      "Videocard0"
        Driver          "%s"
        VendorName      "Videocard vendor"
        BoardName       "%s"
%s       VideoRam        %s
EndSection
''' % (x_settings['videocard'][1],
       x_settings['videocard'][0],
       x_settings['videocard'][2] != '0' and ' ' or '#',
       x_settings['videocard'][2])
    # Screen Section
    depthlist = map(lambda depth: int(depth), x_settings['modes'].keys())
    depthlist.sort()
    default_depth = depthlist[-1]
    display_list = []
    display_string = ''
    for depth in depthlist:
        modes_string = ' '.join(map(lambda m: '"' + m + '"',
                                    x_settings['modes'][str(depth)]))
        display_string = display_string + '\tSubSection\t"Display%d"\n' % depth
        display_string = display_string + '\t\tDepth\t%d\n' % depth
        display_string = display_string + '\t\tModes\t%s\n' % modes_string
        display_string = display_string + '\tEndSubSection\n'
    screen = '''
Section "Screen"
        Identifier      "Screen0"
        Device          "Videocard0"
        Monitor         "Monitor0"
        DefaultDepth    %d
%sEndSection
''' % (default_depth,  display_string)

    # Generate the XF86Config file.
    if not os.path.isdir(os.path.join(CF.D.TGTSYS_ROOT, 'etc/X11')):
        os.makedirs(os.path.join(CF.D.TGTSYS_ROOT, 'etc/X11'))
    f = file(os.path.join(CF.D.TGTSYS_ROOT, 'etc/X11/XF86Config'), 'w')
    f.write(serverlayout)
    f.write(files)
    f.write(module)
    f.write(keyboard)
    f.write(mouse)
    f.write(monitor)
    f.write(videocard)
    f.write(screen)
    f.close()
    os.system('cp %s %s' % \
              (os.path.join(CF.D.TGTSYS_ROOT, 'etc/X11/XF86Config'),
               os.path.join(CF.D.TGTSYS_ROOT, 'etc/X11/xorg.conf')))
    # Fix /etc/inittab
    if x_settings['init'] == 'text':
        os.system('/bin/sed -i s/id:.:initdefault/id:3:initdefault/ %s' % \
                      (os.path.join(CF.D.TGTSYS_ROOT, 'etc/inittab')))
    else:
        os.system('/bin/sed -i s/id:.:initdefault/id:5:initdefault/ %s' % \
                  (os.path.join(CF.D.TGTSYS_ROOT, 'etc/inittab')))
    os.system('/usr/sbin/chroot %s /usr/bin/fc-cache -f' % CF.D.TGTSYS_ROOT)
    return  1

@register.server_handler('long')
def test_x_settings(mia, operid, x_settings):
    if not os.path.exists(CF.D.TGTSYS_ROOT):
        return  _('Failed: The target system is not exists yet.')
    if not os.path.exists(os.path.join(CF.D.TGTSYS_ROOT, 'usr/bin/xinit')):
        return  _('Failed: xinit is not installed.')
    if not os.path.exists(os.path.join(CF.D.TGTSYS_ROOT, 'usr/bin/X')):
        return  _('Failed: X is not inistalled.')

    mark_file = os.path.join(CF.D.TGTSYS_ROOT, 'tmp/testxdlg/probe_x_mark')
    gen_x_config(mia, operid, x_settings)
    os.system('/bin/gunzip -c %s | /bin/tar x -C %s' % \
              (os.path.join('operations', 'testxdlg.tar.gz'), CF.D.TGTSYS_ROOT))
    os.system('/bin/touch %s' % mark_file)
    os.system('/usr/sbin/chroot %s /usr/bin/xinit /tmp/testxdlg/testxdlg -- /usr/bin/X :1' % CF.D.TGTSYS_ROOT)
    if not os.path.exists(mark_file):
        result = 'SUCCESS'
    else:
        result = _('Failed: Please recheck X settings.')
    os.system('/bin/rm -rf %s' % os.path.join(CF.D.TGTSYS_ROOT, 'tmp/testxdlg'))
    return  result

@register.server_handler('long')
def backup_xconfig(mia, operid, dummy):
    os.system('sync')
    xorg_files = ['xorg.conf', 'XF86Config']
    tgt_etc_x = os.path.join(CF.D.TGTSYS_ROOT, 'etc/X11')
    for xorg_file in xorg_files:
        if os.path.exists(os.path.join(tgt_etc_x, xorg_file)):
            os.system('mv %s %s' % \
                      (os.path.join(tgt_etc_x, xorg_file),
                       os.path.join(tgt_etc_x, xorg_file+'.bak')))

