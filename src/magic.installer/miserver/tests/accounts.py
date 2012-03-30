import sys
from t_regist_server_handler import Register
register = Register()

@register.server_handler('short')
def handler_short1(arg1, k1 = 0):
    name = sys._getframe(0).f_code.co_name
    print arg1, k1
    print 'I am ' + name

@register.server_handler('short')
def handler_short2():
    name = sys._getframe(0).f_code.co_name
    print 'I am ' + name

@register.server_handler('long')
def handler_long1(arg1, k1 = 0):
    name = sys._getframe(0).f_code.co_name
    print arg1, k1
    print 'I am ' + name

@register.server_handler('long')
def handler_long2():
    name = sys._getframe(0).f_code.co_name
    print 'I am ' + name

print register
register['short']['handler_short1'][0]('t1', k1 = 't2')
register['short']['handler_short2'][0]()
register['long']['handler_long1'][0]('tt1', k1 = 'tt2')
register['long']['handler_long2'][0]()
