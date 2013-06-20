#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import subprocess
import os, sys
import json
import time

cachefpath = 'lddcache.json'
if os.path.exists(cachefpath):
    print 'loading cache...'
    t = time.time()
    with open(cachefpath, 'rt') as fp:
        cachejson = json.load(fp)
    print 'load cache done ', time.time() - t
else:
    cachejson = json.loads('{}')

def ldd(fpath):
    if fpath in cachejson:
        return cachejson[fpath]
    
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
    print 'saving cache...'
    t = time.time()
    with open(cachefpath, 'wt') as fp:
        json.dump(cachejson, fp)
    print 'saving cache done ', time.time() - t

atexit.register(all_done)
