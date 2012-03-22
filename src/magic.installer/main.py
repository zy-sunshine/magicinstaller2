from mainwin import MIMainWindow
import gtk

win = MIMainWindow(gtk.WINDOW_TOPLEVEL)
win.init()
win.show_all()

gtk.main()
