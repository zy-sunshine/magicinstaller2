class Test(object):
    def __init__(self):
        pass
    def get_class_name(self):
        return self.__class__.__name__
        

if __name__ == '__main__':
    t = Test()
    print t.get_class_name()

