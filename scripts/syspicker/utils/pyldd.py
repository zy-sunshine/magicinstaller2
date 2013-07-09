#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import subprocess
import os, sys
import json
import time

cachefpath = '_lddcache.json'
cachejson = {}
cacheb = False
def initcache(tmpdir=''):
    global cacheb, cachejson, cachefpath
    if tmpdir:
        cachefpath = os.path.join(tmpdir, cachefpath)
    if os.path.exists(cachefpath):
        print 'loading cache...'
        t = time.time()
        with open(cachefpath, 'rt') as fp:
            cachejson = json.load(fp)
        print 'load cache done ', time.time() - t
    else:
        cachejson = json.loads('{}')
    cacheb = True

def ldd(fpath):
    if cachejson.has_key(fpath):
        #print 'Hit in cache %s' % fpath
        return cachejson[fpath]
    else:
        print fpath
        pass
    libs = []
    p = subprocess.Popen(["ldd", fpath], 
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)

    result = p.stdout.readlines()
    
    for x in result:
        s = x.split()
        if "=>" in x:
            if len(s) == 3: # virtual library
                pass
            else: 
                libs.append(s[2])
        elif 'statically' in x: # statically linked library
            pass
        else: 
            if len(s) == 2:
                libs.append(s[0])
    
    cachejson[fpath] = libs
    return libs

import atexit

def all_done():
    if cacheb:
        print 'saving cache...'
        t = time.time()
        with open(cachefpath, 'wt') as fp: 
            json.dump(cachejson, fp, indent=4)
        print 'saving cache done ', time.time() - t

atexit.register(all_done)
