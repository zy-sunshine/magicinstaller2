from xml.dom.minidom import parse, parseString

values = parse('../magic.values.xml')
curconf = 'test.xml'
f = open(curconf, 'w')
values.writexml(f)
f.close()
