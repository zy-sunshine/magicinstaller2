class mistep_sub_1:
    def __init__(self):
        self.CONF = GET_G_CONF()
        self.STAT = GET_G_STAT()
    def dosomething(self):
        self.CONF.dump()
        self.CONF.addvar = 'addition variable'
        self.STAT.dump()
        self.STAT.addstat = 'addition status'
class mistep_sub:
    def __init__(self):
        pass
    def dosomething(self):
        CONF.dump()
        CONF.addvar = 'addition variable'
        STAT.dump()
        STAT.addstat = 'addition status'
