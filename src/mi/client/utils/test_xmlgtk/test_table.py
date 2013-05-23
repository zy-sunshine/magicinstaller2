import gtk
import xmlgtk
XML_DATA='''
<frame>
<tableV2>
<tr><button colspan="2" text="0.0" /><label text="0.1" /><button text="0.2" /></tr>
<tr><button text="1.0" /><label text="1.1" /><button text="1.2" /></tr>
<tr><button text="2.0" /><label text="2.1" /><button text="2.2" /></tr>
</tableV2>
</frame>
'''
xml_obj = xmlgtk.xmlgtk(XML_DATA)
win = gtk.Window(gtk.WINDOW_TOPLEVEL)
win.add(xml_obj.widget)
win.show()
gtk.main()
