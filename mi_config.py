### -*- python -*-
# Copyright (C) 2010, zy_sunshine.
# Author:   zy_sunshine <zy.netsec@gmail.com>
# All rights reserved

import os
import sys

mikernelver = '2.6.35.4'

#{{ User custom default value
langset = 'en:zh_CN'
#}}



udev_arg = '--use-udev'

usesudoprom = False
sudoprom = ''
if usesudoprom:
    sudoprom = ' && sudo -k'
    # If use sudo promopt, clean sudo timpstamp first.
    os.system('echo "clean sudo timestamp..." %s' % sudoprom)

pkgarr = 'none'
pkgdirs = 'none'
bootcd_dir = 'tmp/bootcd'
distname = 'magicinstaller'
distver = '3.0'
set_no = '1'
bootload = 'grub'

mitopdir = os.path.abspath(os.path.curdir)

specdir = 'spec/'
addfiles_dir = specdir + 'addfiles/'

tmpdir = os.path.abspath('tmp')
resultdir = os.path.abspath('result')

devrootdir = os.path.join(tmpdir, 'devroot')   # building sources dir
bootcd_dir = os.path.join(tmpdir, 'bootcd')
miimages_cddir = 'boot'
miimages_dir = os.path.join(bootcd_dir, miimages_cddir)

pythonbin = '/usr/bin/python'
pythondir = 'usr/lib/python2.6'
def mkisofn(iso_no):
    global distname, distver
    return 'result/%s-%s-%s.iso' % (distname, distver, iso_no)
bootiso_fn = os.path.basename(mkisofn(1))

#{{ build rootfs environment
tmp_rootfs = os.path.join(tmpdir, 'rootfs')     # Construct the rootfs temp dir.
busybox_version = '1.6.1'
#}}

# i18n translation
textdomain = 'magic.installer'
translators = ''
copyright_holder = 'Charles Wang'
all_linguas = ['zh_CN']

lang_map = { 'ja_JP': ('eucJP', 'eucJP'),
             'ko_KR' : ('eucKR', 'eucKR'),
             'zh_CN': ('gb2312', 'GB2312'),
             'zh_TW': ('big5', 'BIG5') }
