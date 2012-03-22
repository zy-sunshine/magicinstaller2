import threading

class Single(object):
    def __init__():
        "disable the __init__ method"

    __inst = None # make it so-called private

    __lock = threading.Lock() # used to synchronize code

    @staticmethod
    def get_instance():
        Single.__lock.acquire()
        if not Single.__inst:
            Single.__inst = object.__new__(Single)
            object.__init__(Single.__inst)
        Single.__lock.release()
        return Single.__inst
