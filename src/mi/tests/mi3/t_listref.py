class Test(object):
    def __init__(self):
        self.m_lst = ['a', 'b', 'c', 'd']

g_lst = ['a', 'b', 'c']
if __name__ == '__main__':
    l_lst = g_lst
    l_lst.append('4')
    print 'l_lst %s' % l_lst
    print 'g_lst %s' % g_lst
    t = Test()
    l_m_lst = t.m_lst
    l_m_lst.append('3')
    print 'l_m_lst %s' % l_m_lst
    print 't.m_lst %s' % t.m_lst
