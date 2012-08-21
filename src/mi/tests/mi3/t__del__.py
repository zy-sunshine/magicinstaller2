#!/usr/local/bin/python
class Study:
    def __init__(self,name=None):
        self.name = name
    def __del__(self):
        print "Iamaway,baby!"
    def say(self):
        print self.name
study = Study("zhuzhengjun")
study.say()
