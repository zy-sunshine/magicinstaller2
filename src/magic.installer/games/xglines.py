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

import os.path
from random import randint
from xml.dom.minidom import parse

import gtk, gobject

from miui.utils import xmlgtk

class xglines (xmlgtk.xmlgtk):
    def __init__(self, gamepath, help_func, quit_func):
        self.help_func = help_func
        self.quit_func = quit_func
        uixml = parse(os.path.join(gamepath, 'xglines.xml'))
        xmlgtk.xmlgtk.__init__(self, uixml)
        self.BOARDSIZE  = 9
        self.NUMCELLS    = self.BOARDSIZE * self.BOARDSIZE

        self.all_pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join(gamepath, 'pulse.png'))
        self.blank_pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join(gamepath, 'blank.png'))
        self.cellw = self.blank_pixbuf.get_width()
        self.cellh = self.blank_pixbuf.get_height()
        self.num_colors = self.all_pixbuf.get_height() / self.cellh
        self.anim_cycle = self.all_pixbuf.get_width() / self.cellw

        self.topscore   = 0
        self.board = [None] * self.NUMCELLS

        self.board_table = [None] * self.NUMCELLS

        for pos in range(0, self.NUMCELLS):
            (x, y) = self.pos_xy(pos)
            frame = gtk.Frame()
            self.name_map['board'].attach(frame, x, x + 1, y, y + 1, 0, 0, 0, 0)
            frame.set_shadow_type(gtk.SHADOW_IN)
            frame.show()

            eventbox = gtk.EventBox()
            frame.add(eventbox)
            eventbox.connect('button-press-event', self.pos_clicked, pos)
            eventbox.show()

            image = gtk.Image()
            eventbox.add(image)
            image.set_alignment(0.5, 0.5)
            image.set_from_pixbuf(self.blank_pixbuf)
            self.board_table[pos] = image
            image.show()

        self.game_start()
        self.timeout_id = gobject.timeout_add(100, self.anim_timeout)

    def __del__(self):
        gtk.timeout_remove(self.timeout_id)

    def pos_xy(self, pos):
        return  (pos % self.BOARDSIZE, pos / self.BOARDSIZE)

    def xy_pos(self, x, y):
        return  x + y * self.BOARDSIZE

    def show_position(self, pos, phase):
        if self.board[pos] == None:
            self.board_table[pos].set_from_pixbuf(self.blank_pixbuf)
        else:
            draw_pixbuf = self.blank_pixbuf.copy()
            self.all_pixbuf.copy_area(phase * self.cellw,
                                      self.board[pos] * self.cellh,
                                      self.cellw, self.cellh,
                                      draw_pixbuf, 0, 0)
            self.board_table[pos].set_from_pixbuf(draw_pixbuf)

    def rand_positions(self, numpos):
        blankcells = []
        for pos in range(0, self.NUMCELLS):
            if self.board[pos] == None:
                blankcells.append(pos)
        if numpos >= len(blankcells):
            return  blankcells
        poslist = []
        while len(poslist) < numpos:
            newpos = randint(0, len(blankcells) - 1)
            poslist.append(blankcells[newpos])
            del blankcells[newpos]
        return poslist

    def gen_three_next(self):
        self.next = [randint(0, self.num_colors - 1),
                     randint(0, self.num_colors - 1),
                     randint(0, self.num_colors - 1)]
        for i in range(0, 3):
            draw_pixbuf = self.blank_pixbuf.copy()
            self.all_pixbuf.copy_area(0, self.next[i] * self.cellh,
                                      self.cellw, self.cellh,
                                      draw_pixbuf, 0, 0)
            self.name_map['next%d' % i].set_from_pixbuf(draw_pixbuf)

    def game_start(self):
        update_poslist = map(lambda pos: self.board[pos] != None,
                             range(0, self.NUMCELLS))
        self.board = [None] * self.NUMCELLS
        poslist = self.rand_positions(5)
        for pos in poslist:
            v = randint(0, self.num_colors - 1)
            self.board[pos] = v
            update_poslist[pos] = True
        for pos in range(0, len(update_poslist)):
            if update_poslist[pos]:
                self.show_position(pos, 0)
        self.score = 0
        self.name_map['score'].set_text(str(self.score))
        self.actpos = -1
        self.movepath = []
        self.gen_three_next()

    def game_end(self):
        if self.score > self.topscore:
            self.topscore = self.score
            self.name_map['topscore'].set_text(str(self.topscore))

    def calc_neighbor(self, pos):
        (x, y) = self.pos_xy(pos)
        probepos = []
        if x > 0:
            probepos.append(pos - 1)
        if x < self.BOARDSIZE - 1:
            probepos.append(pos + 1)
        if y > 0:
            probepos.append(pos - self.BOARDSIZE)
        if y < self.BOARDSIZE - 1:
            probepos.append(pos + self.BOARDSIZE)
        return  probepos

    def search_path(self, frompos, topos):
        if self.board[frompos] == None or self.board[topos] != None:
            return []
        sboard = [None] * self.NUMCELLS
        stepset = [frompos]
        sboard[frompos] = 0
        stepnum = 1
        while stepset != []:
            nextstepset = []
            for steppos in stepset:
                for pos in self.calc_neighbor(steppos):
                    if self.board[pos] == None and sboard[pos] == None:
                        sboard[pos] = stepnum
                        nextstepset.append(pos)
                        if pos == topos:
                            # Got it! Generate result.
                            result = [pos]
                            while pos != frompos:
                                stepnum = stepnum - 1
                                for prevpos in self.calc_neighbor(pos):
                                    if sboard[prevpos] == stepnum:
                                        result.insert(0, prevpos)
                                        break
                                pos = prevpos
                            return result
            stepnum = stepnum + 1
            stepset = nextstepset
        return []

    def anim_timeout(self):
        if self.actpos != -1 and self.board[self.actpos] != None:
            self.show_position(self.actpos, self.actcnt)
            self.actcnt = self.actcnt + 1
            if self.actcnt >= self.anim_cycle:
                self.actcnt = 0
        elif self.movepath != []:
            frompos = self.movepath.pop(0)
            if self.movepath == []:
                self.move_terminate(frompos)
            else:
                topos = self.movepath[0]
                self.board[topos] = self.board[frompos]
                self.board[frompos] = None
                self.show_position(frompos, 0)
                self.show_position(topos, 0)
        return 1

    def check_direction(self, pos, xdelta, ydelta):
        if self.board[pos] == None:
            return []
        result = [pos]
        (x, y) = self.pos_xy(pos)
        for d in [1, -1]:
            len = d
            while 1:
                newx = x + len * xdelta
                newy = y + len * ydelta
                if newx < 0 or newx >= self.BOARDSIZE:
                    break
                if newy < 0 or newy >= self.BOARDSIZE:
                    break
                newpos = self.xy_pos(newx, newy)
                if self.board[newpos] != self.board[pos]:
                    break
                result.append(newpos)
                len = len + d
        return  result

    def move_terminate(self, pos):
        ok_lines = []
        for (xd, yd) in ((1, 0), (0, 1), (1, 1), (1, -1)):
            line = self.check_direction(pos, xd, yd)
            if len(line) >= 5:
                ok_lines.append(line)
        if ok_lines != []:
            # Some lines are ok, score them.
            for line in ok_lines:
                self.score = self.score + len(line)
                for pos in line:
                    if self.board[pos] != None:
                        self.board[pos] = None
                        self.show_position(pos, 0)
            self.name_map['score'].set_text(str(self.score))
        else:
            # Add the next three.
            poslist = self.rand_positions(3)
            cnt = 0
            for pos in poslist:
                self.board[pos] = self.next[cnt]
                self.show_position(pos, 0)
                cnt = cnt + 1
            # Find the lines accomplished by random added next three.
            ok_lines = []
            for pos in poslist:
                for (xd, yd) in ((1, 0), (0, 1), (1, 1), (1, -1)):
                    line = self.check_direction(pos, xd, yd)
                    if len(line) >= 5:
                        ok_lines.append(line)
            # Clear the balls that contained by all found lines.
            for line in ok_lines:
                for pos in line:
                    if self.board[pos] != None:
                        self.board[pos] = None
                        self.show_position(pos, 0)
            # Generate the next three.
            self.gen_three_next()
        # Check whether the board is blank.
        for v in self.board:
            if v != None:
                return
        poslist = self.rand_positions(3)
        cnt = 0
        for pos in poslist:
            self.board[pos] = self.next[cnt]
            self.show_position(pos, 0)
            cnt = cnt + 1
        self.gen_three_next()

    def pos_clicked(self, widget, event, pos):
        if self.movepath != []:
            return
        if self.board[pos] != None:
            if self.actpos != -1:
                self.show_position(self.actpos, 0)
            self.actpos = pos
            self.actcnt = 1
        elif self.actpos != -1:
            self.movepath = self.search_path(self.actpos, pos)
            if self.movepath != []:
                self.show_position(self.actpos, 0)
                self.actpos = -1

    def restart_clicked(self, widget, data):
        self.game_end()
        self.game_start()

    def help_clicked(self, widget, data):
        if self.help_func:
            self.help_func('xglines')

    def quit_clicked(self, widget, data):
        if self.quit_func:
            self.quit_func()
