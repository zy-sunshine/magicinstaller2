#!/usr/bin/python

import os

pkg_from = '/mnt/magic_iso/MagicLinux/packages'
if(os.path.exists("pkg.lst")):
	os.system("rm pkg.lst")
	
if(os.path.exists("pkg_filter.lst")):
	os.system("rm pkg_filter.lst")
if(os.path.exists("pkg_to")):
	os.system("rm -rf pkg_to")
os.system("mkdir pkg_to")
os.system("for var in `ls ../*.xml`; do perl ch_file.pl $var > pkg.lst;done")
os.system("perl filter_file.pl pkg.lst > pkg_filter.lst")
input = open('pkg_filter.lst')
pkg_to = os.path.abspath('pkg_to')
s = input.readlines()
InputTuple = []
singleline = ''
for line in s:
	singleline = line.strip()
	InputTuple.append(singleline)

print 'OUT PUT'
for line in InputTuple:
#	print line
	os.system( 'cp %s %s' % (pkg_from + '/' + line + '*', pkg_to) )
