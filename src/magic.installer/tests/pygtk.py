#!/usr/bin/env python
#-*- encoding:utf-8 -*-

import pygtk
#pygtk.require('2.0')
import gtk

class base:
#destroy信号的回调函数
        def destroy(self,widget,data=None):
                gtk.main_quit()

#clicked信号的回调函数
        def hello(self,widget,data):
                print 'hello ' + data + ' this is a button clicked() test'

#delete_event事件的回调函数
        def delete_event(self, widget, event, data=None):
                print "delete event occurred"
#如果delete_event事件返回假，则会触发destroy信号，从而关闭窗口。
#如果返回真，则不会关闭窗口。这个特性在当我们需要一个确认是否退出的选择对话框时是很有用。
                return False

        def __init__(self):
                self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
#设置窗口的delete_event信号触发delete_event函数
                self.window.connect("delete_event", self.delete_event)
#设置窗口的destroy信号触发destroy函数
                handler1 = self.window.connect("destroy",self.destroy)
                print "handler1 is:%d" % handler1
                self.window.set_title('PyGTK 测试 window')
                self.window.set_default_size(200,200)
                self.window.set_border_width(100)
#控制窗口出现的位置
                self.window.set_position(gtk.WIN_POS_CENTER)
#生成按钮实例
                self.button1 = gtk.Button()
                childimage = self.button1.get_child()
                if childimage != None:
                        childimage.set_from_file('b.gif')
                else:
                        imageb=gtk.Image()
                        imageb.set_from_file('a.gif')
                        #Buttons[i].add(imageb)

                self.button2 = gtk.Button()
                self.button1.set_label('label1')
                self.button2.set_label('label2')
#设置按钮的clicked信号触发hello函数，并传递‘pyGTK’字符串参数给hello函数
                handler2 = self.button1.connect("clicked",self.hello,"pyGTK")
                print "handler2 is:%d" % handler2
#设置按钮的clicked信号触发self.window对象的gtk.Widget.destroy方法
                self.button1.connect_object("clicked", gtk.Widget.destroy, self.window)
#使用object.disconnect(id)方法取消handler2的功能
#               self.button.disconnect(handler2)
#设置一个不可见的横向的栏位self.box1
                self.box1 = gtk.HBox(False, 0)
#把box1放到窗口中
                self.window.add(self.box1)
#把button1部件放到box1中
                self.box1.pack_start(self.button1,True,True,0)
                self.button1.show()
#把button2部件放到button1部件之后
                self.box1.pack_start(self.button2,True,True,0)
                self.button2.show()
                self.box1.show()
                self.window.show()

        def main(self):
                gtk.main()

print __name__
if __name__ == "__main__":
        base = base()
        base.main()
