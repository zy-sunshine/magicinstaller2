class Test(object):
    static_var = None
    def __init__(self):
        pass

    def init(self, i):
        Test.static_var = i

if __name__ == '__main__':
    t = Test()
    t.init(1)
    print t.static_var
    t2 = Test()
    t2.init(2)
    print t2.static_var
    print t.static_var
