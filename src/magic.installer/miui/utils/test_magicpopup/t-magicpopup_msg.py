#!/usr/bin/env python
# example base.py
import pygtk
#pygtk.require('2.0')
import gtk
import magicpopup

class Base:
    def __init__(self):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        m_button = gtk.Button("A Button")
        self.window.add(m_button)
        m_button.show()
        m_button.connect("clicked", self.click_m_button)
        self.window.show()
        #magicpopup.magichelp_popup(self.window, "/home/sunshine/magicinstaller2/src/magic.installer/tests/test-help.txt")
        magicpopup.magicmsgbox(None, 'Format Partition Error: errormsg',
                       magicpopup.magicmsgbox.MB_ERROR,
                       magicpopup.magicpopup.MB_OK)
        #dialog = gtk.Dialog("Test Diaglog",
                            #self.window,
                            #gtk.DIALOG_MODAL,
                            #(gtk.STOCK_CANCEL,
                             #gtk.RESPONSE_CANCEL,
                             #gtk.STOCK_OK,
                             #gtk.RESPONSE_OK))
        #label = gtk.Label("title test")
        #label.show()
        #dialog.vbox.pack_start(label)
        #dialog.action_area.pack_start(label)
        #res = dialog.run()
        #if res == gtk.RESPONSE_OK:
            #print "get the ok button"
        #elif res == gtk.RESPONSE_CANCEL:
            #print "get the cancel button"
        #dialog.destroy()
    def click_m_button(self):
        print "clicked the button"
    def main(self):
        gtk.main()

print __name__
if __name__ == "__main__":
    base = Base()
    base.main()