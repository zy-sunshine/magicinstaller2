#!/usr/bin/python
import rhpxl
import rhpxl.monitor
import rhpxl.videocard
import rhpxl.mouse
if 1:
    def avoid_none(val, default):
        if val is None:
            return default
        else:
            return val
    def probe_monitor():
        mon = rhpxl.monitor.MonitorInfo()
        return (avoid_none(mon.monName, ''),
                avoid_none(mon.monHoriz, ''),
                avoid_none(mon.monVert, ''))

    def probe_videocard():
        vci = rhpxl.videocard.VideoCardInfo()
        vclist = []
        for vc in vci.videocards:
            vidram = avoid_none(vc.getVideoRam(), 0)
            vclist.append((vc.getDescription(), vc.getDriver(), vidram))
        return vclist

    def probe_mouse():
        # Call rhpxl.mouse.Mouse will affect the action of mouse, so do not use it.
        mouse = rhpxl.mouse.Mouse()
        #mouse = rhpxl.mouse.Mouse(skipProbe = 1)
        dev = avoid_none(mouse.getDevice(), 'none')
        xemu3 = mouse.emulate and 'true' or 'false'
        return (mouse.info['FULLNAME'],
                mouse.info['XMOUSETYPE'],
                dev, xemu3,
                mouse.mousetype) # shortname indeed
                
print probe_monitor()
print probe_videocard()
print probe_mouse()