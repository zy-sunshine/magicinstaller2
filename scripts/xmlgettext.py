#!/usr/bin/python
# Copyright (C) 2003, Charles Wang.
# Author:  Charles Wang <charles@linux.net.cn>
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANT; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public LIcense for more
# details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.

import string
import sys
from xml.dom.minidom import parse

str_count = 0
cur_comment = ''

def do_c_escape(str):
    str = string.replace(str, '\\', '\\\\')
    str = string.replace(str, '"', '\\"')
    str = string.replace(str, '\n', '\\n')
    str = string.replace(str, '\t', '\\t')
    return  str

def character_data(data):
    global str_count
    global cur_comment
    if data[:2] == '((' and data[-2:] == '))':
        if cur_comment != '':
            print cur_comment
            cur_comment = ''
        print 's%d = _("%s")' % (str_count, do_c_escape(data[2:-2]))
        str_count = str_count + 1

def extract_doc(node):
    if node.attributes:
        i = 0
        while i < node.attributes.length:
            character_data(node.attributes.item(i).nodeValue)
            i = i + 1
    cur_text = ''
    for subnode in node.childNodes:
        if subnode.nodeType == subnode.TEXT_NODE:
            cur_text += subnode.data
        else:
            if cur_text != '':
                character_data(cur_text)
                cur_text = ''
            if subnode.nodeType == subnode.ELEMENT_NODE:
                extract_doc(subnode)
    if cur_text != '':
        character_data(cur_text)
        cur_text = ''

for input in sys.argv[1:]:
    xmldoc = parse(input)
    cur_comment = '# TO_TRANSLATOR: All of these strings are extracted from xml file: %s.' % input
    extract_doc(xmldoc)
