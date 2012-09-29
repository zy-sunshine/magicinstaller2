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

import gettext
import gobject
import gtk, os
import string
import types
from xml.dom.minidom import parse, parseString
from gettext import gettext as _
import pdb

def __(str):
    if not str:
        return str
    if str[:2] == '((' and str[-2:] == '))':
        return gettext.gettext(str[2:-2])
    return str

def N_(str):
    return str

def xgc_get_bool(str):
    if str == 'false':
        return False
    return True

def xgc_get_policy(str):
    if str == 'always':
        return gtk.POLICY_ALWAYS
    elif str == 'automatic':
        return gtk.POLICY_AUTOMATIC
    else:
        return gtk.POLICY_NEVER

def xgc_get_position_type(str):
    if str == 'left':
        return gtk.POS_LEFT
    elif str == 'right':
        return gtk.POS_RIGHT
    elif str == 'bottom':
        return gtk.POS_BOTTOM
    else:
        return gtk.POS_TOP

def xgc_get_progress_bar_orientation(str):
    if str == 'right2left':
        return gtk.PROGRESS_RIGHT_TO_LEFT
    elif str == 'bottom2top':
        return gtk.PROGRESS_BOTTOM_TO_TOP
    elif str == 'top2bottom':
        return gtk.PROGRESS_TOP_TO_BOTTOM
    else:
        return gtk.PROGRESS_LEFT_TO_RIGHT

def xgc_get_progress_bar_style(str):
    if str == 'discrete':
        return gtk.PROGRESS_DISCRETE
    else:
        return gtk.PROGRESS_CONTINUOUS

def xgc_get_selection_mode(str):
    if str == 'single':
        return gtk.SELECTION_SINGLE
    elif str == 'browse':
        return gtk.SELECTION_BROWSE
    elif str == 'multiple':
        return gtk.SELECTION_MULTIPLE
    else:
        return gtk.SELECTION_NONE

def xgc_get_shadow_type(str):
    if str == 'in':
        return gtk.SHADOW_IN
    elif str == 'out':
        return gtk.SHADOW_OUT
    elif str == 'etched_in':
        return gtk.SHADOW_ETCHED_IN
    elif str == 'etched_out':
        return gtk.SHADOW_ETCHED_OUT
    else:
        return gtk.SHADOW_NONE

def xgc_get_wrap_mode(str):
    if str == 'char':
        return gtk.WRAP_CHAR
    elif str == 'word':
        return gtk.WRAP_WORD
    else:
        return gtk.WRAP_NONE

def xgc_get_gobject_type(str):
    if str == 'boolean':
        return gobject.TYPE_BOOLEAN
    elif str == 'uint':
        return gobject.TYPE_UINT
    elif str == 'string':
        return gobject.TYPE_STRING
    elif str == 'pixmap':
        return gobject.type_from_name('GdkPixbuf') #@UndefinedVariable
    else:
        return str

def xgc_get_treeview_column_size(str):
    if str == 'growonly':
        return gtk.TREE_VIEW_COLUMN_GROW_ONLY
    elif str == 'autosize':
        return gtk.TREE_VIEW_COLUMN_AUTOSIZE
    else:
        return gtk.TREE_VIEW_COLUMN_FIXED

def xgc_true_false(b):
    return ('false', 'true')[bool(b)]

class xmlgtk:
    def __init__(self, uixmldoc, uixml_rootname=None):
        if type(uixmldoc) is str:
            if len(uixmldoc) < 4096 and os.path.exists(uixmldoc):
                # a file
                uixmldoc = parse(uixmldoc)
            else:
                uixmldoc = parseString(uixmldoc)
        self.uixmldoc = uixmldoc
        self.name_map = {}
        self.id_map = {}
        self.group_map = {}
        self.readonly_map = {}
        self.togglebutton_map = {}
        self.checkbutton_map = {}
        self.radiobutton_map = {}
        self.radiogroup_map = {}
        self.range_map = {}
        self.optionmenu_map = {}
        self.list_map = {}
        self.choose_list_map = {}
        self.entry_map = {}
        self.spinbutton_map = {}
        self.combo_map = {}
        self.tooltips_map = {}
        self.enable_map = {}
        self.disable_map = {}
        self.mnemonic_label_map = {}
        self.pixbuf_map = {}  # Use to convert from string to pixbuf.
        self.pixbuf_revmap = {}  # Use to convert from pixbuf to string.
        self.anonymous_tooltips = [] # Use to keep the anonymous alive.
        if not uixml_rootname:
            uixml_rootnode = uixmldoc.documentElement
        else:
            uixml_rootnodes = uixmldoc.getElementsByTagName(uixml_rootname)
            if uixml_rootnodes == []:
                uixml_rootnode = uixmldoc.documentElement
            else:
                for uixml_rootnode in uixml_rootnodes[0].childNodes:
                    if uixml_rootnode.nodeType == uixml_rootnode.ELEMENT_NODE:
                        break
        self.widget = self.xgcwidget_create(uixml_rootnode)
        for enable in self.enable_map.keys():
            self.name_map[enable].connect('toggled', self.enable_toggle, enable)
        for disable in self.disable_map.keys():
            self.name_map[disable].connect('toggled', self.disable_toggle, disable)
        for mnemonic in self.mnemonic_label_map.keys():
            mnemonic.set_mnemonic_widget(self.name_map[self.mnemonic_label_map[mnemonic]])

    def name_widget(self, name):
        if hasattr(self, 'name_map'):
            return  self.name_map[name]

    def search_hook(self, uixml, tag, hookvalue):
        for node in uixml.getElementsByTagName(tag):
            if node.getAttribute('hook') == hookvalue:
                return node
        return  None

    def get_pixbuf_map(self, pixbuf_name):
        if self.pixbuf_map.has_key(pixbuf_name):
            pixbuf = self.pixbuf_map[pixbuf_name]
        else:
            pixbuf = gtk.gdk.pixbuf_new_from_file(pixbuf_name) #@UndefinedVariable
            self.pixbuf_map[pixbuf_name] = pixbuf
            self.pixbuf_revmap[id(pixbuf)] = pixbuf_name
        return  pixbuf

    def _xgc_attr(self, node, attrname, attrdefault):
        attrval = node.getAttribute(attrname)
        if not attrval:
            attrval = attrdefault
        return  attrval

    def _xgc_connect(self, widget, node, attrname, data=None):
        attrsignal = node.getAttribute(attrname)
        if attrsignal:
            if data:
                widget.connect(attrname, getattr(self, attrsignal), data)
            else:
                widget.connect(attrname, getattr(self, attrsignal), self)

    def _xgc_misc_public(self, widget, node):
        xalign = node.getAttribute('xalign')
        yalign = node.getAttribute('yalign')
        if xalign or yalign:
            if xalign:
                xalign = float(xalign)
            else:
                xalign = 0.5
            if yalign:
                yalign = float(yalign)
            else:
                yalign = 0.5
            widget.set_alignment(xalign, yalign)
        xpad = node.getAttribute('xpad')
        ypad = node.getAttribute('ypad')
        if xpad or ypad:
            if xpad:
                xpad = int(xpad)
            else:
                xpad = 0
            if ypad:
                ypad = int(ypad)
            else:
                ypad = 0
            widget.set_padding(xpad, ypad)

    def _xgc_container_public(self, widget, node):
        margin = node.getAttribute('margin')
        if margin:
            widget.set_border_width(int(margin))
            
        width = node.getAttribute("width")
        height = node.getAttribute("height")
            
        if width and height:
            widget.set_size_request(int(width), int(height))
        elif height:
            widget.set_size_request(-1, int(height))
        elif width:
            widget.set_size_request(int(width), -1)
            
        for subnode in node.childNodes:
            if subnode.nodeType == subnode.ELEMENT_NODE:
                subwidget = self.xgcwidget_create(subnode)
                widget.add(subwidget)
                break

    def _xgc_box_public(self, widget, node):
        margin = node.getAttribute('margin')
        if margin:
            widget.set_border_width(int(margin))
        def_pack = self._xgc_attr(node, 'def_pack', 'start')
        def_expand = self._xgc_attr(node, 'def_expand', 'false')
        def_fill = self._xgc_attr(node, 'def_fill', 'false')
        def_padding = self._xgc_attr(node, 'def_padding', '0')
        for subnode in node.childNodes:
            if subnode.nodeType == subnode.ELEMENT_NODE:
                child = self.xgcwidget_create(subnode)
                pack = self._xgc_attr(subnode, 'pack', def_pack)
                expand = xgc_get_bool(self._xgc_attr(subnode, 'expand', def_expand))
                fill = xgc_get_bool(self._xgc_attr(subnode, 'fill', def_fill))
                padding = int(self._xgc_attr(subnode, 'padding', def_padding))
                if pack == 'start':
                    widget.pack_start(child, expand, fill, padding)
                else:
                    widget.pack_end(child, expand, fill, padding)

    def _xgc_adjustment(self, node):
        lower = float(self._xgc_attr(node, 'lower', '0'))
        upper = float(self._xgc_attr(node, 'upper', '31'))
        stepinc = float(self._xgc_attr(node, 'stepinc', '1'))
        pagesize = float(self._xgc_attr(node, 'pagesize', '0'))
        pageinc = float(self._xgc_attr(node, 'pageinc', '4'))
        return gtk.Adjustment(lower, lower, upper, stepinc,
                              float(pageinc), float(pagesize))

    def _xgc_range_public(self, widget, node, attrname):
        value = node.getAttribute('value')
        if value:
            self.range_map[widget] = value
        self._xgc_connect(widget, node, attrname)

    def _xgc_scale_public(self, widget, node, attrname):
        self._xgc_range_public(widget, node, attrname)
        digits = node.getAttribute('digits')
        if digits:
            widget.set_digits(int(digits))
        valuepos = node.getAttribute('valuepos')
        if valuepos:
            widget.set_value_pos(xgc_get_position_type(valuepos))

    def _xgc_tooltips_public(self, widget, node):
        tips = node.getAttribute('tips')
        if tips:
            tipsgroup = node.getAttribute('tipsgroup')
            if tipsgroup:
                if self.tooltips_map.has_key(tipsgroup):
                    tooltips = self.tooltips_map[tipsgroup]
                else:
                    tooltips = gtk.Tooltips()
                    self.tooltips_map[tipsgroup] = tooltips
            else:
                tooltips = gtk.Tooltips()
                # Keep the tooltips alive, it will be destroied otherwise.
                self.anonymous_tooltips.append(tooltips)
            tipsdetail = self._xgc_attr(node, 'tipsdetail', '')
            delay = node.getAttribute('tipsdelay')
            if delay:
                tooltips.set_delay(int(delay))
            tooltips.set_tip(widget, __(tips), __(tipsdetail))

    def xgc_frame(self, node):
        label = node.getAttribute('label')
        if label:
            widget = gtk.Frame(__(label))
        else:
            widget = gtk.Frame()
        label_align = node.getAttribute('label_align')
        if label_align:
            widget.set_label_align(float(label_align), 0.5)

        type = xgc_get_shadow_type(self._xgc_attr(node, 'type', 'etched_in'))
        widget.set_shadow_type(type)
        self._xgc_container_public(widget, node)
        return widget

    def xgc_vbox(self, node):
        homogeneous = xgc_get_bool(self._xgc_attr(node, 'homogeneous', 'false'))
        spacing = int(self._xgc_attr(node, 'spacing', '0'))
        widget = gtk.VBox(homogeneous, spacing)
        self._xgc_box_public(widget, node)
        return widget

    def xgc_hbox(self, node):
        homogeneous = xgc_get_bool(self._xgc_attr(node, 'homogeneous', 'false'))
        spacing = int(self._xgc_attr(node, 'spacing', '0'))
        widget = gtk.HBox(homogeneous, spacing)
        self._xgc_box_public(widget, node)
        return widget

    def xgc_tableV2(self, node):
        cell_list = []
        cell_fill_map = {}
        
        def get_cur_col(row, col):
            while True:
                if not cell_fill_map.has_key((row, col)):
                    break
                col += 1
            return col
        
        def get_cur_row(row, col):
            while True:
                if not cell_fill_map.has_key((row, col)):
                    break
                row += 1
            return row
        
        def inc_col(row, col, inc):
            for i in range(inc):
                col = get_cur_col(row, col)
                cell_fill_map[(row, col)] = 'y'
                col += 1
            return  col
        
        def inc_row(row, col, inc):
            for i in range(inc):
                row = get_cur_row(row, col)
                cell_fill_map[(row, col)] = 'y'
                row += 1
            return row
        
        def add_cell(subnode, cur_row, cur_col):
            rowspan = int(self._xgc_attr(subnode, 'rowspan', '1'))
            colspan = int(self._xgc_attr(subnode, 'colspan', '1'))
            
            top = get_cur_row(cur_row, cur_col)
            bottom = top + int(rowspan) - 1
            
            left = get_cur_col(cur_row, cur_col)
            right = left + int(colspan) - 1
                
            for row in range(top, bottom + 1):
                for col in range(left, right + 1):
                    cell_fill_map[(row, col)] = 'y'

            cell_list.append((subnode, cur_row, cur_col, left, right, top, bottom))
            return right + 1
        cur_row = -1
        for trnode in node.childNodes:
            if trnode.nodeType != trnode.ELEMENT_NODE:
                continue
            cur_row += 1
            cur_col = get_cur_col(cur_row, 0)
            if trnode.tagName == 'tr':
                # do td in tr parse
                for tdnode in trnode.childNodes:
                    if tdnode.nodeType != tdnode.ELEMENT_NODE:
                        continue
                    if tdnode.tagName == 'td':
                        for subnode in tdnode.childNodes:
                            if subnode.nodeType != subnode.ELEMENT_NODE:
                                continue
                            cur_col = add_cell(subnode, cur_row, cur_col)
                    else:
                        cur_col = add_cell(tdnode, cur_row, cur_col)
            else:
                # do one row
                cur_col = add_cell(trnode, cur_row, cur_col)
        if cell_list:
            rows = max(cell_list, key=lambda s: s[6])[6] + 1
            columns = max(cell_list, key=lambda s: s[4])[4] + 1
        else:
            rows = 1
            columns = 1
            #raise Exception('Error', 'Cannot create zero table')
        
        homogeneous = xgc_get_bool(self._xgc_attr(node, 'homogeneous', 'false'))
        widget = gtk.Table(rows, columns, homogeneous)
        def_xoptions = self._xgc_attr(node, 'def_xoptions', 'notexpandfill')
        def_yoptions = self._xgc_attr(node, 'def_yoptions', 'notexpandfill')
        def_xpadding = self._xgc_attr(node, 'def_xpadding', '0')
        def_ypadding = self._xgc_attr(node, 'def_ypadding', '0')
        colspacings = node.getAttribute('colspacings')
        if colspacings:
            widget.set_col_spacings(int(colspacings))
        rowspacings = node.getAttribute('rowspacings')
        if rowspacings:
            widget.set_row_spacings(int(rowspacings))
        margin = node.getAttribute('margin')
        if margin:
            widget.set_border_width(int(margin))
            
        for subnode, cur_row, cur_col, left, right, top, bottom in cell_list:
            child = self.xgcwidget_create(subnode)
            expand = xgc_get_bool(self._xgc_attr(subnode, 'expand', 'false'))
            fill = xgc_get_bool(self._xgc_attr(subnode, 'fill', 'false'))
            expandfill = xgc_get_bool(self._xgc_attr(subnode, 'expandfill', 'false'))
            if (expand and fill) or expandfill:
                def_xoptions = 'expandfill'
                def_yoptions = 'expandfill'
            elif expand:
                def_xoptions = 'expand'
                def_yoptions = 'expand'
            elif fill: 
                def_xoptions = 'fill'
                def_yoptions = 'fill'

            xoptions = self._xgc_attr(subnode, 'xoptions', def_xoptions)
            if xoptions == 'expand':
                xoptions = gtk.EXPAND
            elif xoptions == 'fill':
                xoptions = gtk.FILL
            elif xoptions == 'expandfill':
                xoptions = gtk.EXPAND | gtk.FILL
            else:
                xoptions = 0
            yoptions = self._xgc_attr(subnode, 'yoptions', def_yoptions)
            if yoptions == 'expand':
                yoptions = gtk.EXPAND
            elif yoptions == 'fill':
                yoptions = gtk.FILL
            elif yoptions == 'expandfill':
                yoptions = gtk.EXPAND | gtk.FILL
            else:
                yoptions = 0
            xpadding = int(self._xgc_attr(subnode, 'xpadding', def_xpadding))
            ypadding = int(self._xgc_attr(subnode, 'ypadding', def_ypadding))

            widget.attach(child, left, right + 1, top, bottom + 1,
                          xoptions, yoptions, xpadding, ypadding)
        return widget
    def xgc_table(self, node):
        rows = int(self._xgc_attr(node, 'rows', '1'))
        columns = int(self._xgc_attr(node, 'columns', '1'))
        homogeneous = xgc_get_bool(self._xgc_attr(node, 'homogeneous', 'false'))
        widget = gtk.Table(rows, columns, homogeneous)
        def_xoptions = self._xgc_attr(node, 'def_xoptions', 'expandfill')
        def_yoptions = self._xgc_attr(node, 'def_yoptions', 'expandfill')
        def_xpadding = self._xgc_attr(node, 'def_xpadding', '0')
        def_ypadding = self._xgc_attr(node, 'def_ypadding', '0')
        colspacings = node.getAttribute('colspacings')
        if colspacings:
            widget.set_col_spacings(int(colspacings))
        rowspacings = node.getAttribute('rowspacings')
        if rowspacings:
            widget.set_row_spacings(int(rowspacings))
        margin = node.getAttribute('margin')
        if margin:
            widget.set_border_width(int(margin))
        cur_row = 0
        cur_col = 0
        for subnode in node.childNodes:
            if subnode.nodeType == subnode.ELEMENT_NODE:
                child = self.xgcwidget_create(subnode)
                # Try self-position scheme firstly.
                left = subnode.getAttribute('left')
                right = subnode.getAttribute('right')
                top = subnode.getAttribute('top')
                bottom = subnode.getAttribute('bottom')
                if left and right and top and bottom:
                    left = int(left)
                    right = int(right)
                    top = int(top)
                    bottom = int(bottom)
                else:
                    # Use auto-position scheme.
                    yspan = int(self._xgc_attr(subnode, 'yspan', '0'))
                    skip = int(self._xgc_attr(subnode, 'skip', '0'))
                    span = int(self._xgc_attr(subnode, 'span', '1'))
                    if yspan > 0:
                        cur_col = 0
                        cur_row = cur_row + yspan
                    cur_col = cur_col + skip
                    while cur_col >= columns:
                        cur_col = cur_col - columns
                        cur_row = cur_row + 1
                    left = cur_col
                    right = cur_col + span
                    top = cur_row
                    bottom = cur_row + 1
                    cur_col = cur_col + span
                xoptions = self._xgc_attr(subnode, 'xoptions', def_xoptions)
                if xoptions == 'expand':
                    xoptions = gtk.EXPAND
                elif xoptions == 'fill':
                    xoptions = gtk.FILL
                elif xoptions == 'expandfill':
                    xoptions = gtk.EXPAND | gtk.FILL
                else:
                    xoptions = 0
                yoptions = self._xgc_attr(subnode, 'yoptions', def_yoptions)
                if yoptions == 'expand':
                    yoptions = gtk.EXPAND
                elif yoptions == 'fill':
                    yoptions = gtk.FILL
                elif yoptions == 'expandfill':
                    yoptions = gtk.EXPAND | gtk.FILL
                else:
                    yoptions = 0
                xpadding = int(self._xgc_attr(subnode, 'xpadding', def_xpadding))
                ypadding = int(self._xgc_attr(subnode, 'ypadding', def_ypadding))
                widget.attach(child, left, right, top, bottom,
                              xoptions, yoptions, xpadding, ypadding)
        return widget

    def xgc_list(self, node):
        col_list = node.getElementsByTagName('column')

        storelist = []
        rstorelist = []
        for colnode in col_list:
            store = xgc_get_gobject_type(self._xgc_attr(colnode, 'type', 'string'))
            storelist.append(store)
            if type(store) is types.UnicodeType:
                rstorelist.append(gobject.TYPE_STRING)
            else:
                rstorelist.append(store)
        model = gtk.ListStore(*rstorelist)

        count = 0
        tvclist = []
        for colnode in col_list:
            label = __(self._xgc_attr(colnode, 'label', ''))
            coltype = self._xgc_attr(colnode, 'type', 'string')
            if coltype == 'boolean':
                renderer = gtk.CellRendererToggle()
                tvcolumn = gtk.TreeViewColumn(label, renderer, active=count)
                toggled = colnode.getAttribute('toggled')
                if toggled:
                    renderer.connect('toggled', getattr(self, toggled), model)
            elif coltype == 'pixmap':
                renderer = gtk.CellRendererPixbuf()
                tvcolumn = gtk.TreeViewColumn(label, renderer, pixbuf=count)
            else:
                renderer = gtk.CellRendererText()
                tvcolumn = gtk.TreeViewColumn(label, renderer, text=count)
            visible = colnode.getAttribute('visible')
            if visible:
                tvcolumn.set_visible(xgc_get_bool(visible))
            resizable = colnode.getAttribute('resizable')
            if resizable:
                tvcolumn.set_resizable(xgc_get_bool(resizable))
            fixedwidth = colnode.getAttribute('fixedwidth')
            if fixedwidth:
                tvcolumn.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
                tvcolumn.set_fixed_width(int(fixedwidth))
            else:
                minwidth = colnode.getAttribute('minwidth')
                if minwidth:
                    tvcolumn.set_min_width(int(minwidth))
                maxwidth = colnode.getAttribute('maxwidth')
                if maxwidth:
                    tvcolumn.set_max_width(int(maxwidth))
            spacing = colnode.getAttribute('spacing')
            if spacing:
                tvcolumn.set_spacing(int(spacing))
            align = colnode.getAttribute('align')
            if align:
                tvcolumn.set_alignment(float(align))
            tvclist.append(tvcolumn)
            count = count + 1

        hpolicy = xgc_get_policy(self._xgc_attr(node, 'hpolicy', 'automatic'))
        vpolicy = xgc_get_policy(self._xgc_attr(node, 'vpolicy', 'automatic'))
        shadow_type = xgc_get_shadow_type(self._xgc_attr(node, 'shadow_type', 'in'))
        headers_visible = xgc_get_bool(self._xgc_attr(node, 'headers_visible', 'true'))
        selection_mode = xgc_get_selection_mode(self._xgc_attr(node, 'selection_mode', 'single'))

        widget = gtk.ScrolledWindow()
        widget.set_policy(hpolicy, vpolicy)
        widget.set_shadow_type(shadow_type)

        tv = gtk.TreeView(model)
        tv.show()
        for tvc in tvclist:
            tv.append_column(tvc)
        tv.set_headers_visible(headers_visible)

        name = node.getAttribute('name')
        if name:
            self.name_map[name + '_treeview'] = tv
        
        selection = tv.get_selection()
        selection.set_mode(selection_mode)
        self._xgc_connect(selection, node, 'changed', selection)

        widget.add(tv)

        value = node.getAttribute('value')
        if value:
            self.list_map[model] = (value, storelist)

        choose_value = node.getAttribute('choose_value')
        choose_id = node.getAttribute('choose_id')
        if choose_value and choose_id:
            self.choose_list_map[model] = (choose_value,
                                           int(choose_id),
                                           selection)
        readonly = node.getAttribute('readonly')
        if readonly and readonly == 'true':
            self.readonly_map[model] = 'true'
        return widget

    def xgc_label(self, node):
        label = __(node.getAttribute('text'))
        widget = gtk.Label(label)
        mnemonic = node.getAttribute('mnemonic')
        if mnemonic:
            self.mnemonic_label_map[widget] = mnemonic
        use_underline = node.getAttribute('use_underline')
        if use_underline == 'true':
            widget.set_use_underline(True)
        elif use_underline == 'false':
            widget.set_use_underline(False)
        elif mnemonic:
            # Default to use_underline when mnemonic is provided.
            widget.set_use_underline(True)
        else:
            widget.set_use_underline(False)
        self._xgc_misc_public(widget, node)
        line_wrap = node.getAttribute('line_wrap')
        if line_wrap:
            widget.set_line_wrap(True)
        return widget

    # This text widget is used for show some text only.
    def xgc_text(self, node):
        # Make the filename translatable let us can provide files in different language.
        filename = __(node.getAttribute('filename'))
        try:
            f = file(filename, 'r')
        except IOError:
            data = _("File is not found: ") + filename
        else:
            data = f.read()
            f.close()

        hpolicy = xgc_get_policy(self._xgc_attr(node, 'hpolicy', 'never'))
        vpolicy = xgc_get_policy(self._xgc_attr(node, 'vpolicy', 'automatic'))
        shadow_type = xgc_get_shadow_type(self._xgc_attr(node, 'shadow_type', 'in'))
        wrap_mode = xgc_get_wrap_mode(self._xgc_attr(node, 'wrap_mode', 'word'))

        widget = gtk.ScrolledWindow()
        widget.set_policy(hpolicy, vpolicy)
        widget.set_shadow_type(shadow_type)

        tv = gtk.TextView()
        tv.show()
        widget.add(tv)
        widget.tv = tv
        buffer = gtk.TextBuffer(None)
        tv.set_buffer(buffer)
        tv.set_editable(False)
        tv.set_cursor_visible(False)
        tv.set_wrap_mode(wrap_mode)
        
        iter = buffer.get_iter_at_offset(0)
        buffer.insert(iter, data)
        return widget
        
    def xgc_button(self, node):
        label = __(node.getAttribute('label'))
        text = __(node.getAttribute('text'))
        label = label and label or text
        if label:
            widget = gtk.Button(label)
        else:
            widget = gtk.Button()
        self._xgc_connect(widget, node, 'clicked')
        self._xgc_container_public(widget, node)
        self._xgc_tooltips_public(widget, node)
        return widget

    def xgc_togglebutton(self, node):
        label = __(node.getAttribute('label'))
        widget = gtk.ToggleButton(label)
        self._xgc_connect(widget, node, 'toggled')
        self._xgc_container_public(widget, node)
        value = node.getAttribute('value')
        if value:
            self.togglebutton_map[widget] = value
        return widget

    def xgc_checkbutton(self, node):
        label = __(node.getAttribute('label'))
        widget = gtk.CheckButton(label)
        self._xgc_connect(widget, node, 'toggled')
        self._xgc_container_public(widget, node)
        value = node.getAttribute('value')
        if value:
            self.checkbutton_map[widget] = value
        return widget

    def xgc_radiobutton(self, node):
        label = __(node.getAttribute('label'))
        value = node.getAttribute('value')
        if value:
            if self.radiogroup_map.has_key(value):
                widget = gtk.RadioButton(self.radiogroup_map[value], label)
                self.radiogroup_map[value] = widget
            else:
                widget = gtk.RadioButton(label = label)
                self.radiogroup_map[value] = widget
            valuedata = node.getAttribute('valuedata')
            self.radiobutton_map[widget] = (value, valuedata)
        else:
            widget = gtk.RadioButton(label = label)
        self._xgc_connect(widget, node, 'toggled')
        self._xgc_container_public(widget, node)
        return widget

    def xgc_optionmenu(self, node):
        values = []
        widget = gtk.ComboBox()
        menu = gtk.ListStore(str)
        cell = gtk.CellRendererText()
        widget.pack_start(cell)
        widget.add_attribute(cell, 'text', 0)
        for itemnode in node.getElementsByTagName('value'):
            valstr = itemnode.getAttribute('valstr')
            tmpstr = ''
            for subnode in itemnode.childNodes:
                if subnode.nodeType == subnode.TEXT_NODE:
                    tmpstr = tmpstr + subnode.data
            if valstr:
                values.append(valstr)
            else:
                values.append(tmpstr)
            menu.append([__(tmpstr)])
            name = itemnode.getAttribute('name')
            if name:
                pass
                #self.name_map[name] = menu_item
        widget.set_model(menu)
        self._xgc_connect(widget, node, 'changed')
        value = node.getAttribute('value')
        if value:
            self.optionmenu_map[widget] = (value, values)
        return widget

    def xgc_entry(self, node):
        max = int(self._xgc_attr(node, 'max', 0))
        widget = gtk.Entry(max)
        type_ = node.getAttribute('type')
        if type_ == 'password':
            widget.set_visibility(False)
        editable = node.getAttribute('editable')
        if editable == 'false':
            widget.set_editable(False)
        width = node.getAttribute('width')
        if width:
            widget.set_width_chars(int(width))
        value = node.getAttribute('value')
        if value:
            self.entry_map[widget] = value
        return widget

    def xgc_spinbutton(self, node):
        climb_rate = float(self._xgc_attr(node, 'climbrate', '0'))
        digits = int(self._xgc_attr(node, 'digits', '0'))
        widget = gtk.SpinButton(self._xgc_adjustment(node), climb_rate, digits)
        widget.set_update_policy(gtk.UPDATE_IF_VALID)
        value = node.getAttribute('value')
        if value:
            self.spinbutton_map[widget] = value
        return widget

    def xgc_hscrollbar(self, node):
        widget = gtk.HScrollbar(self._xgc_adjustment(node))
        self._xgc_range_public(widget, node, 'value-changed')
        return widget

    def xgc_vscrollbar(self, node):
        widget = gtk.VScrollbar(self._xgc_adjustment(node))
        self._xgc_range_public(widget, node, 'value-changed')
        return widget

    def xgc_hscale(self, node):
        widget = gtk.HScale(self._xgc_adjustment(node))
        self._xgc_scale_public(widget, node, 'value-changed')
        return widget

    def xgc_vscale(self, node):
        widget = gtk.VScale(self._xgc_adjustment(node))
        self._xgc_scale_public(widget, node, 'value-changed')
        return widget

    def xgc_progressbar(self, node):
        widget = gtk.ProgressBar()
        text = node.getAttribute('text')
        if text:
            widget.set_text(__(text))
        orient = node.getAttribute('orient')
        if orient:
            widget.set_orientation(xgc_get_progress_bar_orientation(orient))
        style = node.getAttribute('style')
        if style:
            widget.set_bar_style(xgc_get_progress_bar_style(style))
        return widget

    def xgc_combo(self, node):
        items = gtk.ListStore(str)
        values = []
        for subnode in node.getElementsByTagName('value'):
            valuestr = ''
            for subsubnode in subnode.childNodes:
                if subsubnode.nodeType == subsubnode.TEXT_NODE:
                    valuestr = valuestr + subsubnode.data
            values.append(__(valuestr))
            items.append([__(valuestr)])
        widget = gtk.ComboBoxEntry(items)
        editable = node.getAttribute('editable')
        if editable == 'false':
            widget.set_sensitive(False)
        value = node.getAttribute('value')
        if value:
            self.combo_map[widget] = (value, values)
        return widget

    def xgc_image(self, node):
        widget = gtk.Image()
        imgfile = node.getAttribute('file')
        if imgfile:
            widget.set_from_file(imgfile)
        self._xgc_misc_public(widget, node)
        return widget

    def xgc_hseparator(self, node):
        return gtk.HSeparator()

    def xgc_vseparator(self, node):
        return gtk.VSeparator()

    def xgcwidget_create(self, node):
        if node.nodeType != node.ELEMENT_NODE:
            return None
        xgcfunc = getattr(self, 'xgc_' + node.tagName, None)
        if xgcfunc:
            widget = xgcfunc(node)
        else:
            print "Can't create widget for node: %s" % node.tagName
            widget = None
        if widget is None:
            return None
        name = node.getAttribute('name')
        if name:
            self.name_map[name] = widget
            
        id_ = node.getAttribute('id')
        if id_:
            if self.id_map.has_key(id_):
                raise Exception('Error', 'there have duplicate id in xml "%s"' % id_)
            self.id_map[id_] = widget
            
        group = node.getAttribute('group')
        if group:
            if self.group_map.has_key(group):
                self.group_map[group].append(widget)
            else:
                self.group_map[group] = [widget]
        visible = xgc_get_bool(self._xgc_attr(node, 'visible', 'true'))
        if visible:
            widget.show()
        sensitive = node.getAttribute('sensitive')
        if sensitive == 'false':
            widget.set_sensitive(False)
        enable = node.getAttribute('enable')
        if enable:
            if self.enable_map.has_key(enable):
                self.enable_map[enable].append(widget)
            else:
                self.enable_map[enable] = [widget]
        disable = node.getAttribute('disable')
        if disable:
            if self.disable_map.has_key(disable):
                self.disable_map[disable].append(widget)
            else:
                self.disable_map[disable] = [widget]
        desclabel = node.getAttribute('desclabel')
        desctext = node.getAttribute('desctext')
        if desclabel and desctext:
            widget.connect('enter-notify-event', self.set_desc_label,
                           (desclabel, __(desctext)))
            widget.connect('leave-notify-event', self.set_desc_label,
                           (desclabel, ''))
        return widget

    def set_desc_label(self, widget, event, data):
        (desclabel, desctext) = data
        self.name_map[desclabel].set_text(desctext)

    def enable_toggle(self, toggle_button, enable):
        if toggle_button.get_active():
            value = True
        else:
            value = False
        for widget in self.enable_map[enable]:
            widget.set_sensitive(value)

    def disable_toggle(self, toggle_button, disable):
        if toggle_button.get_active():
            value = False
        else:
            value = True
        for widget in self.disable_map[disable]:
            widget.set_sensitive(value)

    def srh_data_node(self, data_xml, valuename):
        cur_node = data_xml
        for step in string.split(valuename, '.'):
            got_it = None
            for subnode in cur_node.childNodes:
                if subnode.nodeType == subnode.ELEMENT_NODE:
                    if subnode.tagName == step:
                        cur_node = subnode
                        got_it = 1
                        break
            if not got_it:
                return None
        return cur_node

    def get_data(self, data_xml, valuename):
        cur_node = self.srh_data_node(data_xml, valuename)
        if not cur_node:
            return None
        value = ''
        for subnode in cur_node.childNodes:
            if subnode.nodeType == subnode.TEXT_NODE:
                value = value + subnode.data
        return value

    def set_data(self, data_xmldoc, valuename, valuedata, data_xml=None):
        if not data_xml:
            data_xml = data_xmldoc.documentElement
        cur_node = self.srh_data_node(data_xml, valuename)
        if not cur_node:
            return
        for subnode in cur_node.childNodes:
            if subnode.nodeType == subnode.TEXT_NODE:
                subnode.data = valuedata
                return
        # There is no node for it yet, so it have to be created.
        cur_node.appendChild(data_xmldoc.createTextNode(valuedata))

    def set_child_data(self, data_xml, valuename, subnodename, multi_data):
        cur_node = self.srh_data_node(data_xml, valuename)
        if not cur_node:
            return
        childnodes = []
        for subnode in cur_node.childNodes:
            if subnode.nodeType == subnode.ELEMENT_NODE and \
               subnode.tagName == subnodename:
                childnodes.append(subnode)
        n_child = len(childnodes)
        n_data = len(multi_data)
        pos = 0
        while pos < n_child or pos < n_data:
            if pos >= n_child:
                cur_node.appendChild(multi_data[pos])
            elif pos >= n_data:
                cur_node.removeChild(childnodes[pos])
            else:
                cur_node.replaceChild(multi_data[pos], childnodes[pos])
            pos = pos + 1

    def clear_data_children(self, data_xml, valuename):
        cur_node = self.srh_data_node(data_xml, valuename)
        if not cur_node:
            return
        while 1:
            subnode = cur_node.firstChild
            if subnode:
                cur_node.removeChild(subnode)
            else:
                break

    def create_collist_from_node(self, node, storelist):
        collist = []
        for i in range(len(storelist)):
            collist.append(i)
            value = node.getAttribute('c' + str(i))
            if storelist[i] == gobject.TYPE_BOOLEAN:
                if value == 'true':
                    collist.append(True)
                else:
                    collist.append(False)
            elif storelist[i] == gobject.TYPE_UINT:
                if value:
                    collist.append(int(value))
                else:
                    collist.append(0)
            elif storelist[i] == gobject.TYPE_STRING:
                if value:
                    collist.append(value)
                else:
                    collist.append('')
            elif storelist[i] == gobject.type_from_name('GdkPixbuf'): #@UndefinedVariable
                if type(value) == types.StringType or type(value) == types.UnicodeType:
                    pixbuf = self.get_pixbuf_map(value)
                else:
                    pixbuf = value
                collist.append(pixbuf)
            elif storelist[i][:5] == 'i18n.':
                collist.append(_(node.getAttribute('c' + storelist[i][5:])))
        return collist

    def setup_node_from_iter(self, node, model, iter, storelist):
        for i in range(len(storelist)):
            if storelist[i] == gobject.type_from_name('GdkPixbuf'): #@UndefinedVariable
                node.setAttribute('c' + str(i), self.pixbuf_revmap[id(model.get_value(iter, i))])
            elif type(storelist[i]) is not types.UnicodeType:
                # XXX use pixbuf_revmap to revert ti
                node.setAttribute('c' + str(i), str(model.get_value(iter, i)))

    def fill_values(self, data_xml):
        for widget in self.togglebutton_map.keys():
            value = self.get_data(data_xml, self.togglebutton_map[widget])
            if value == 'true':
                widget.set_active(True)
            else:
                widget.set_active(False)
        for widget in self.checkbutton_map.keys():
            value = self.get_data(data_xml, self.checkbutton_map[widget])
            if value == 'true':
                widget.set_active(True)
            else:
                widget.set_active(False)
        for widget in self.radiobutton_map.keys():
            value = self.get_data(data_xml, self.radiobutton_map[widget][0])
            if value == self.radiobutton_map[widget][1]:
                widget.set_active(True)
            else:
                widget.set_active(False)
        for widget in self.optionmenu_map.keys():
            value = self.get_data(data_xml, self.optionmenu_map[widget][0])
            for i in range(len(self.optionmenu_map[widget][1])):
                if self.optionmenu_map[widget][1][i] == value:
                    widget.set_active(i)
                    break
        for model in self.list_map.keys():
            cur_node = self.srh_data_node(data_xml, self.list_map[model][0])
            if cur_node:
                model.clear()
                storelist = self.list_map[model][1]
                for subnode in cur_node.getElementsByTagName('row'):
                    collist = self.create_collist_from_node(subnode, storelist)
                    iter = model.append()
                    model.set(iter, *collist)
        for model in self.choose_list_map.keys():
            (choose_value, choose_id, selection) = self.choose_list_map[model]
            cur_node = self.srh_data_node(data_xml, choose_value)
            if cur_node:

                selection.unselect_all()
                id_map = {}
                for subnode in cur_node.getElementsByTagName('select'):
                    id = subnode.getAttribute('id')
                    id_map[id] = 'y'
                iter = model.get_iter_first()
                while iter:
                    id = model.get_value(iter, choose_id)
                    if id_map.has_key(id):
                        selection.select_iter(iter)
                    iter = model.iter_next(iter)
                del(id_map)
        for widget in self.entry_map.keys():
            widget.set_text(self.get_data(data_xml, self.entry_map[widget]))
        for widget in self.spinbutton_map.keys():
            widget.set_value(float(self.get_data(data_xml, self.spinbutton_map[widget])))
        for widget in self.combo_map.keys():
            value = self.get_data(data_xml, self.combo_map[widget][0])
            has_find = False
            for i in range(len(self.combo_map[widget][1])):
                if self.combo_map[widget][1][i] == value:
                    widget.set_active(i)
                    has_find = True
                    break
            if not has_find:
                widget.child.set_text(self.get_data(data_xml, self.combo_map[widget][0]))
        for enable in self.enable_map.keys():
            self.enable_toggle(self.name_map[enable], enable)
        for disable in self.disable_map.keys():
            self.disable_toggle(self.name_map[disable], disable)
        # SO STRANGE: widget.set_value will change data_xml. Can't understand.
        for widget in self.range_map.keys():
            value = self.get_data(data_xml, self.range_map[widget])
            widget.set_value(float(value))

    def each_choose_id(self, model, path, iter, data):
        (data_xmldoc, data_xml, choose_value, choose_id) = data
        cur_node = self.srh_data_node(data_xml, choose_value)
        subnode = data_xmldoc.createElement('select')
        subnode.setAttribute('id', model.get_value(iter, choose_id))
        cur_node.appendChild(subnode)

    def get_widget_value(self, widget_name):
        w = self.name_map[widget_name]
        w_type = type(w)
        
        if w_type is gtk.Entry:
            return w.get_text()
        elif w_type is gtk.Label:
            return w.get_text()
        elif w_type is gtk.OptionMenu:
            return self.optionmenu_map[w][1][w.get_active()]
        elif w_type is gtk.CheckButton:
            return xgc_true_false(w.get_active())
        elif w_type is gtk.RadioButton:
            return xgc_true_false(w.get_active())
        elif w_type is gtk.ToggleButton:
            return xgc_true_false(w.get_active())
        elif w_type is gtk.Range:
            return str(w.get_value())
        elif w_type is gtk.SpinButton:
            w.update()
            return str(w.get_value())
        elif w_type is gtk.Combo:
            return w.child.get_text()
        else:
            raise Exception("Unsupported type %s of widget %s" %
                            (str(w_type), widget_name))
        
    def set_widget_value(self, widget_name, value):
        w = self.name_map[widget_name]
        w_type = type(w)

        if w_type is gtk.Entry:
            w.set_text(value)
        elif w_type is gtk.Label:
            w.set_text(value)
        elif w_type is gtk.OptionMenu:
            for i, v in enumerate(self.optionmenu_map[widget_name][1]):
                if v == value:
                    w.set_active(i)
                    break
        elif w_type is gtk.CheckButton:
            w.set_active(xgc_get_bool(value))
        elif w_type is gtk.RadioButton:
            w.set_active(xgc_get_bool(value))
        elif w_type is gtk.ToggleButton:
            w.set_active(xgc_get_bool(value))
        elif w_type is gtk.Range:
            w.set_value(float(value))
        elif w_type is gtk.SpinButton:
            w.set_value(float(value))
        elif w_type is gtk.Combo:
            w.child.set_text(value)
        else:
            raise Exception("Unsupported type %s of widget %s" %
                            (str(w_type), widget_name))
        
    def fetch_values(self, data_xmldoc, data_xml=None, valuename_list=None):
        if not data_xml:
            data_xml = data_xmldoc.documentElement
            
        for widget in self.togglebutton_map.keys():
            valuename = self.togglebutton_map[widget]
            if valuename_list and \
                    valuename not in valuename_list:
                continue
            self.set_data(data_xmldoc,
                          valuename,
                          xgc_true_false(widget.get_active()))
            
        for widget in self.checkbutton_map.keys():
            valuename = self.checkbutton_map[widget]
            if valuename_list and \
                    valuename not in valuename_list:
                continue
            self.set_data(data_xmldoc,
                          valuename,
                          xgc_true_false(widget.get_active()))

        for widget in self.radiobutton_map.keys():
            valuename = self.radiobutton_map[widget][0]
            if valuename_list and \
                    valuename not in valuename_list:
                continue
            if widget.get_active():
                self.set_data(data_xmldoc,
                              valuename,
                              self.radiobutton_map[widget][1])

        for widget in self.range_map.keys():
            valuename = self.range_map[widget]
            if valuename_list and \
                    valuename not in valuename_list:
                continue
            self.set_data(data_xmldoc,
                          valuename,
                          str(widget.get_value()))

        for widget in self.optionmenu_map.keys():
            valuename = self.optionmenu_map[widget][0]
            if valuename_list and \
                    valuename not in valuename_list:
                continue
            try:
                value = self.optionmenu_map[widget][1] \
                              [widget.get_active()]
            except IndexError:
                value = widget.get_model()[widget.get_active()][0]
            self.set_data(data_xmldoc,
                          valuename,
                          value)

        for model in self.list_map.keys():
            if self.readonly_map.has_key(model):
                continue
            valuename = self.list_map[model][0]
            if valuename_list and \
                    valuename not in valuename_list:
                continue
            child_values = []
            iter = model.get_iter_first()
            while iter:
                node = data_xmldoc.createElement('row')
                self.setup_node_from_iter(node, model, iter, self.list_map[model][1])
                child_values.append(node)
                iter = model.iter_next(iter)
            self.set_child_data(data_xml, valuename, 'row', child_values)

        for model in self.choose_list_map.keys():
            if self.readonly_map.has_key(model):
                continue
            (choose_value, choose_id, selection) = self.choose_list_map[model]
            if valuename_list and \
                    choose_value not in valuename_list:
                continue
            self.clear_data_children(data_xml, choose_value)
            selection.selected_foreach(self.each_choose_id,
                                       (data_xmldoc, data_xml, choose_value, choose_id))
        for widget in self.entry_map.keys():
            valuename = self.entry_map[widget]
            if valuename_list and \
                    valuename not in valuename_list:
                continue
            self.set_data(data_xmldoc,
                          valuename,
                          widget.get_text().strip())

        for widget in self.spinbutton_map.keys():
            valuename = self.spinbutton_map[widget]
            if valuename_list and \
                    valuename not in valuename_list:
                continue
            widget.update() # Do update to ensure the valid value.
            self.set_data(data_xmldoc,
                          valuename,
                          str(widget.get_value()))

        for widget in self.combo_map.keys():
            valuename = self.combo_map[widget][0]
            if valuename_list and \
                    valuename not in valuename_list:
                continue
            self.set_data(data_xmldoc,
                          valuename,
                          widget.child.get_text())

    # Some additional function to help the operation of list.
    def srh_model(self, valuename):
        for model in self.list_map.keys():
            if self.list_map[model][0] == valuename:
                return model
        return None

    def list_append(self, valuename, new_node):
        model = self.srh_model(valuename)
        if not model:
            return
        collist = self.create_collist_from_node(new_node, self.list_map[model][1])
        iter = model.append()
        model.set(iter, *collist)

    def list_insert(self, valuename, position, new_node):
        model = self.srh_model(valuename)
        if not model:
            return
        collist = self.create_collist_from_node(new_node, self.list_map[model][1])
        iter = model.insert(position)
        model.set(iter, *collist)

    def list_insert_before(self, valuename, iter, new_node):
        model = self.srh_model(valuename)
        if not model:
            return
        collist = self.create_collist_from_node(new_node, self.list_map[model][1])
        niter = model.insert_before(iter)
        model.set(niter, *collist)

    def list_insert_after(self, valuename, iter, new_node):
        model = self.srh_model(valuename)
        if not model:
            return
        collist = self.create_collist_from_node(new_node, self.list_map[model][1])
        niter = model.insert_after(iter)
        model.set(niter, *collist)

    def list_replace(self, valuename, iter, new_node):
        model = self.srh_model(valuename)
        if not model:
            return
        collist = self.create_collist_from_node(new_node, self.list_map[model][1])
        niter = model.insert_after(iter)
        model.set(niter, *collist)
        model.remove(iter)

    def list_remove(self, valuename, iter):
        model = self.srh_model(valuename)
        if not model:
            return
        model.remove(iter)
