import xmlrpclib
s = xmlrpclib.dumps( ({'vol':'III', 'title':'Magical Unicorn'},))
print s
print xmlrpclib.loads(s)[0]
