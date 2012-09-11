import pyudev

KUDZU_FLAG = False
ALL_DEVICE_INFO = 0x1

CLASS_HD = 0x10
CLASS_ATA = 0x100
CLASS_USB = 0x1000
CLASS_OTH = 0x10000

CLASS_CDROM = 0x100000
CLASS_FLOPPY = 0x1000000
TYPE_LIST = (CLASS_HD,
        CLASS_ATA,
        CLASS_USB,
        CLASS_OTH,
        CLASS_CDROM,
        CLASS_FLOPPY)
class KudzuDevice:
    def __init__(self, desc, driver, device):
        self.desc = desc
        self.driver = driver
        self.device = device
    def __str__(self):
        str = ''
        str += 'Desc:\t\t%s\n' % self.desc
        str += 'Driver:\t\t%s\n' % self.driver
        str += 'Device:\t\t%s\n' % self.device
        return str

def get_all_devices():
    context = pyudev.Context()
    udev_devices = context.list_devices()
    devices_info = {}
    devices_size = {}
    for device in udev_devices:
        dev_info = {}
        udev_name = device.keys()
        for n in udev_name:
            try:
                dev_info[n] = device[n]
            except:
                pass
        # We use device_path as the key of the devices map, because it is:
        # Kernel device path as unicode string. This path uniquely identifies a
        # single device.
        # And device['DEVPATH'] has same value with device_path.
        devices_info[device.device_path] = dev_info
        try:
            devices_size[device.device_path] = int(device.attributes['size']) * 512
        except:
            pass
    return devices_info, devices_size

def probe(dev_class):
    def kudzu_format(dev_map, devices_info):
        def get_attr(map, attr):
            if map.has_key(attr):
                return map[attr]
            else:
                return None
        desc_list = []
        driver_list = []
        device_list = []
        for dev in dev_map.keys():
            desc = None
            driver = None
            device = None
            desc = '%s %s' % (get_attr(devices_info[dev], 'ID_VENDOR') or \
                       get_attr(devices_info[dev], 'ID_BUS'),
                       get_attr(devices_info[dev], 'ID_MODEL'))
            driver = get_attr(devices_info[dev], 'DRIVER')
            device = get_attr(devices_info[dev], 'DEVNAME')
            if device and device.startswith('/dev/'):
                device=device[5:]
            else:
                device=None
            desc_list.append(desc)
            driver_list.append(driver)
            device_list.append(device)

        KudzuList = []
        for s in range(len(desc_list)):
            KudzuList.append(KudzuDevice(desc_list[s], driver_list[s], device_list[s]))

        return KudzuList

    devices, devices_size = get_all_devices()

    if dev_class & ALL_DEVICE_INFO:
        if KUDZU_FLAG:
            return kudzu_format(devices, devices)
        else:
            return devices, devices_size

    if dev_class & CLASS_HD or \
            dev_class & CLASS_ATA or \
            dev_class & CLASS_USB or \
            dev_class & CLASS_OTH:
        ata_hd_map, usb_hd_map, oth_hd_map = get_hd_ata_usb(devices)
        hd_map = {}
        hd_map.update(ata_hd_map)
        hd_map.update(usb_hd_map)
        hd_map.update(oth_hd_map)
        if dev_class & CLASS_HD:
            if KUDZU_FLAG:
                return kudzu_format(hd_map, devices)
            else:
                return hd_map
        if dev_class & CLASS_ATA:
            if KUDZU_FLAG:
                return kudzu_format(ata_hd_map, devices)
            else:
                return ata_hd_map
        if dev_class & CLASS_USB:
            if KUDZU_FLAG:
                return kudzu_format(usb_hd_map, devices)
            else:
                return usb_hd_map
        if dev_class & CLASS_OTH:
            if KUDZU_FLAG:
                return kudzu_format(oth_hd_map, devices)
            else:
                return oth_hd_map
    if dev_class & CLASS_CDROM:
        cdrom_map = get_cdrom(devices)
        if KUDZU_FLAG:
            return kudzu_format(cdrom_map, devices)
        else:
            return cdrom_map
    if dev_class & CLASS_FLOPPY:
        floppy_map = get_floppy(devices)
        if KUDZU_FLAG:
            return kudzu_format(floppy_map, devices)
        else:
            return floppy_map

def get_floppy(devices):
    # Because I have no floppy, so I can not test it...
    floppy_map = {}
    for devname in devices.keys():
        device = devices[devname]
        if 'ID_TYPE' in device.keys() and device['ID_TYPE'] == 'floppy':
            floppy_map[devname] = []
    return floppy_map

def get_cdrom(devices):
    cdrom_map = {}
    for devname in devices.keys():
        device = devices[devname]
        if 'ID_TYPE' in device.keys() and device['ID_TYPE'] == 'cd':
            cdrom_map[devname] = []
    return cdrom_map
        
def get_hd_ata_usb(devices):
    part_info_mm = {}
    disk_info_mm = {}
    disk_size_map = {}
    for devname in devices.keys():
        device = devices[devname]
        if 'ID_TYPE' in device.keys() and device['ID_TYPE'] == 'disk':
            if device['DEVTYPE'] == 'partition':
                part_info_mm[devname] = device
            elif device['DEVTYPE'] == 'disk':
                disk_info_mm[devname] = device

    usb_hd_map = {}
    ata_hd_map = {}
    oth_hd_map = {}
    for key, value in disk_info_mm.items():
        for k, v in value.items():
            if k == 'ID_BUS':
                if v == 'usb':
                    usb_hd_map[key] = []
                elif v == 'ata':
                    ata_hd_map[key] = []
                else:
                    oth_hd_map[key] = []

    for key, value in part_info_mm.items():
        devpath = value['DEVPATH']
        disk_name = 'None'
        try:
            disk_name = devpath[:devpath.rfind('/')]
        except:
            pass
        else:
            if disk_name:
                if usb_hd_map.has_key(disk_name):
                    usb_hd_map[disk_name].append(key)
                elif ata_hd_map.has_key(disk_name):
                    ata_hd_map[disk_name].append(key)
                elif oth_hd_map.has_key(disk_name):
                    oth_hd_map[disk_name].append(key)
    return ata_hd_map, usb_hd_map, oth_hd_map

def p_c(clist):
    print clist
    
def get_part_info(dev_class):
    devices_info, devices_size = probe(ALL_DEVICE_INFO)
    dev_map = {}
    for t in TYPE_LIST:    
        if dev_class & t:
            dev_map.update(probe(t))

    return _get_part_info(dev_map, devices_info, devices_size)
    
def _get_part_info(usb_map, all_part_info, disk_size_map):
    dev_part_info = {}
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
                part_info['disk'] = all_part_info[disk].get('DEVNAME', None)
                part_info['devpath'] = all_part_info[part].get('DEVNAME', None)
                part_info['vendor'] = all_part_info[part].get('ID_VENDOR',None)
                part_info['model'] = all_part_info[part].get('ID_MODEL', None)
                part_info['model_id'] = all_part_info[part].get('ID_MODEL_ID', None)
                part_info['fstype'] = all_part_info[part].get('ID_FS_TYPE', None)
                part_info['fsver'] = all_part_info[part].get('ID_FS_VERSION', None)
                part_info['size'] = disk_size_map[part]
                part_info['size_ex'] = '%.2f MB' % (float(disk_size_map[part])/1024/1024)
                dev_part_info[part_info['devpath']] = part_info
    return dev_part_info

if __name__ == '__main__':
    KUDZU_FLAG = False
    print 'The hd information:'
    p_c(probe(CLASS_HD))

    print 'The ata information:'
    p_c(probe(CLASS_ATA))

    print 'The usb devices:'
    p_c(probe(CLASS_USB))

    print 'The cdrom devices:'
    p_c(probe(CLASS_CDROM))
    
    print 'The floppy devices:'
    p_c(probe(CLASS_FLOPPY))
    #print probe(ALL_DEVICE_INFO)
    #devices_info, devices_size = probe(ALL_DEVICE_INFO)
    #for devices in devices_info.keys():
    #    if devices_info[devices].has_key('DEVNAME'):
    #        if devices_info[devices]['DEVNAME'] == "/dev/hda1":
    #            print devices_info[devices]
    print get_part_info(CLASS_HD)
    print get_part_info(CLASS_CDROM | CLASS_HD)
    #usb_map = probe(CLASS_HD)
    #for device in devices:
    #    print device
    #    print devices_info[device]
    #print get_part_info(usb_map, devices_info, devices_size)
    #print 'Disk Size:'
    #devices_info, devices_size = probe(ALL_DEVICE_INFO)#get_all_devices()
    #print devices_size

    #print 'All Devices:'
    #print probe(ALL_DEVICE_INFO)
