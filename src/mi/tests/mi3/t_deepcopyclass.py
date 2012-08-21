from copy import deepcopy
def Testclass1():
    class A(object):
        ARG = 1
    
    B = deepcopy(A)
    
    print A().ARG
    #1
    
    print B().ARG
    #1
    
    A.ARG = 2
    
    print B().ARG
    #2

def Testclass2():
    class A(object):
        ARG = 1
    a = A()
    B = type("B", (A,), {})
    b = B()
    b.ARG = 2

    print a.ARG
    print b.ARG


def Testclass3():
    def get_A():
        class A(object):
            ARG = 1
            @staticmethod
            def init():
                print 'static: %s' % A.ARG
        return A
        
    A = get_A()
    B = get_A()

    a = A()
    b = B()
    a.ARG = 2
    print a.ARG
    print b.ARG
    A.init()
    B.init()
    #import pdb; pdb.set_trace()


if __name__ == '__main__':
    #Testclass1()
    #Testclass2()
    Testclass3()
