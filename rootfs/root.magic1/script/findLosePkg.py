#!/usr/bin/python

import subprocess
import re
import sys
#test = subprocess.call(["ls","-l","/tmp/"])

class rpmPkg:
	def __init__(self, pkgname, provides, requires, scripts):
		self.provides = pkgname

		self.requires = requires

		self.scripts = scripts
		self.name = pkgname


def runBash(cmd = []):
    cmd_res = {}
    res = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True)
    res.wait()
    #ret = res.returncode
    cmd_res['out']=res.stdout.readlines()
    cmd_res['err']=res.stderr.readlines()
    #print res.pid
    for s in range( len(cmd_res['out']) ):
        cmd_res['out'][s] = cmd_res['out'][s].strip('\n')
    for s in range( len(cmd_res['err']) ):
        cmd_res['err'][s] = cmd_res['err'][s].strip('\n')
    return cmd_res['out'] 

def strToList(str):
	str1 = str.strip('[]')
	list = str1.split(',')
	for s in range( len(list) ):
		list[s] = list[s].strip('\' ')
		p = re.compile('\\\\t')
		list[s] = p.sub('\t', list[s])
	return list

def stripStr(str):
	str = str.strip('\t \n')

def getPkgInfo(fileName):
	fp = open(fileName)
	txtContent = fp.readlines()
	
	pkgMap = {}
	pkgname = ''
	provides = []
	requires = []
	scripts  = []
	def removeNoPkg(list):
		newList = []
		for pkg in list:
			if not pkg.startswith('no package provides'):
				newList.append(pkg)
		return newList
				
	
	for line in txtContent:
		if line.startswith('Name:'):
			pkgname = line[5:]
			pkgname = pkgname.strip('\t \n')

		if line.startswith('Provides:'):
			provides = line[9:]
			provides = provides.strip('\t \n')
			provides = strToList(provides)

		if line.startswith('Requires:'):
			requires = line[9:]
			requires = requires.strip('\t \n')
			requires = strToList(requires)
			requires = removeNoPkg(requires)
					

		if line.startswith('Scripts:'):
			scripts  = line[8:]
			scripts  = scripts.strip('\t \n')
			scripts  = strToList(scripts)
			pkgMap[pkgname]=rpmPkg(pkgname, provides, requires, scripts)

	return pkgMap

#pkgMap = getPkgInfo('pkgInfo.txt')
#pkgNameList = pkgMap.keys()


def getAllRequire(pkgs, rList):
	for pkg in pkgs:
		rPkg = getRequire(pkg)
		listUnique = list(set(rPkg) - set(rList))
		rList.extend(listUnique)
		if len(listUnique) != 0 and listUnique[0] != '':
			getAllRequire(listUnique, rList)

def getRequire(pkg):
	return pkgMap[pkg].requires

#pkgXorg = runBash(['cat xorg.pkg'])
#xorgRPkg = []
#print pkgXorg
#print getRequire('ncurses-base-5.7-2.20090207mgc25.i686')

def rmBlankItem(list):
	newList = []
	for l in list:
		if l != '':
			newList.append(l)
	return newList

#for pkg in allRPkg:
#	print pkg
lddList = []
lddInfo = runBash(['ldd %s' % sys.argv[1] ])
for line in lddInfo:
	m = re.match(r'.*=> (/.*) \(.*', line)
	if m:
#		print m.group(1)
		lddList.append(m.group(1))
#	print line

lddList = list(set(lddList))
lddPkgList = []
for line in lddList:
	pkg = runBash(['rpm -qf %s' % line])
	lddPkgList.extend(pkg)

lddPkgList = list(set(lddPkgList))

losePkg = []
for pkg in lddPkgList:
	hasPkg = runBash(['grep -n -H %s ../*' % ( pkg)])  # There is the path of the xml Files
#	print 'grep -n -H %s %s' % ( pkg, sys.argv[2])
	if hasPkg == '':
		losePkg.extend(pkg)
	else:
		print hasPkg
		print pkg

print 'The lose package is:\n'
for pkg in losePkg:
	print pkg
