from mi.client.utils.xmlgtk import xmlgtk
from xml.dom.minidom import parse, parseString
class TestFrame(xmlgtk):
    def __init__(self):
        xmlgtk.__init__(self, parse())

