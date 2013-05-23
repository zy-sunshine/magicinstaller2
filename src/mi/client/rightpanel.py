#!/usr/bin/python
import gtk
from mi.client.utils import logger, xmlgtk

class MIRightPanel(gtk.Frame):
    def __init__(self, sself, *args, **kw):
        gtk.Frame.__init__(self, *args, **kw)
        self.sself = sself
        self.curwidget = None
        self.stash_stack = []

    def switch(self, widget):
        if self.curwidget is not None:
            self.curwidget.hide()
            self.remove(self.curwidget)
            self.stash_stack.pop(-1)
        self.curwidget = widget
        self.stash_stack.append(self.curwidget)
        self.curwidget.show()
        self.add(self.curwidget)

    def push(self, widget):
        if self.stash_stack: self.remove(self.stash_stack[-1]); self.stash_stack[-1].hide()
        self.stash_stack.append(widget)
        self.stash_stack[-1].show()
        self.add(self.stash_stack[-1])
        
    def pop(self):
        self.remove(self.stash_stack[-1])
        widget = self.stash_stack.pop()
        if self.stash_stack: self.stash_stack[-1].show(); self.add(self.stash_stack[-1])
        widget.hide()
        return widget
