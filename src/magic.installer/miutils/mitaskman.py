#!/usr/bin/python
#coding=utf-8
import gobject, gtk
import xmlrpclib, socket
import time
from xml.dom.minidom import parseString

from miui.utils import Logger
Log = Logger.get_instance(__name__)
dolog = Log.i

# The task manager: It only manage the long operation.
class MiTaskman :
    def __init__(self, port, action_prog, aplabel):
        #--- object status ---
        self.actserver = xmlrpclib.ServerProxy('http://127.0.0.1:%d' % port, allow_none=True)
        # action_prog: The progress bar widget to show the action.
        self.action_prog = action_prog
        self.aplabel = aplabel
        self.apstack =[(action_prog, aplabel)]
        # idle: The handler of gtk idle function.
        self.timeout_cnt = 0
        self.timeout = gobject.timeout_add(100, self.timeout_probe)
        # tasks: Task queue, a task might be an action or an action group.
        self.tasks = []
        # tmid: Use to provide unique tmid.
        self.tmid = 0
        # results: The results indexed by tmid.
        self.results = {}

        #--- running action status ---
        self.run_tmid = -1  # -1 means not any action is running.
        # run_id: reserve the id of self.actserver.method(*params)
        self.run_id = -1
        self.run_show = 0
        self.run_rcfunc = None
        self.run_rcdata = None
        self.run_prev_pulse_time = -1.0

    def push_progress(self, actprog, aplabel):
        self.apstack.append((actprog, aplabel))
        self.action_prog = actprog
        self.aplabel = aplabel

    def pop_progress(self):
        if len(self.apstack) == 1:
            (actprog, aplabel) = self.apstack[0]
        else:
            self.apstack.pop()
            (actprog, aplabel) = self.apstack[-1]
        self.action_prog = actprog
        self.aplabel = aplabel

    def add_action(self, describe, rcfunc, rcdata, method, *params):
        self.tmid = self.tmid + 1
        self.tasks.append([(self.tmid, describe, rcfunc, rcdata, method, params)])
        return self.tmid

    def put_action(self):
        if self.run_tmid >= 0:
            # An action is running, can't issue new action.
            return  False
        # Get an action from queue head.
        while self.tasks != []:
            if self.tasks[0] != []:
                break
            del self.tasks[0]
        if self.tasks == []:
            # The queue is empty.
            return  False
        # The first action should be self.tasks[0][0]
        (tmid, describe, rcfunc, rcdata, method, params) = self.tasks[0][0]
        if method == 'quit':
            gtk.main_quit()
        try:
            id = eval('self.actserver.%s(*params)' % method)
        except socket.error:
            # put action failed.
            return  False
        #except xmlrpclib.Fault:
        #    import pdb; pdb.set_trace()
        # put action successfully.
        self.tasks[0].pop(0) # Remove it from queue head.
        self.run_tmid = tmid
        self.run_id = id
        if describe:  # Some operation want progress bar but the others not.
            self.run_show = 1
            self.aplabel.set_text(describe)
            self.action_prog.set_fraction(0)
            if len(self.apstack) == 1:
                self.aplabel.show()
                self.action_prog.show()
        self.run_rcfunc = rcfunc
        self.run_rcdata = rcdata
        self.run_prev_pulse_time = -1.0

        return  True

    def probe_and_show(self):
        if self.run_show == 0:
            return False
        # Try to probe the current action progress.
        try:
            (id, step, stepnum) = self.actserver.probe_step()
        except socket.error:
            # Probe failed.
            return False
        if id != self.run_id:
            # Weird encountered.
            return False
        if stepnum > 0:
            # Percentage mode.
            self.action_prog.set_fraction(float(step) / float(stepnum))
        else:
            # Activity mode.
            cur_pulse_time = time.time()
            # Pulse on each 0.3 second.
            if self.run_prev_pulse_time + 0.3 < cur_pulse_time:
                self.action_prog.pulse()
                self.run_prev_pulse_time = cur_pulse_time
        return True

    def get_results(self):
        try:
            new_result_list = self.actserver.get_results()
        except socket.error:
            # get results failed.
            return  False
        for result_xmlstr in new_result_list:
            res_tuple = xmlrpclib.loads(result_xmlstr)
            id = res_tuple[0][0]
            result = res_tuple[0][1]
            method = res_tuple[1]  # Not used yet.
            if id != self.run_id:
                dolog('WARNING: id != self.run_id in magic.installer.py:get_results().\n')
                # Weird encountered.
                continue
            if self.run_show and len(self.apstack) == 1:
                self.aplabel.hide()
                self.action_prog.hide()
                self.run_show = 0
            if self.run_rcfunc:
                self.run_rcfunc(result, self.run_rcdata)
            self.run_tmid = -1
            self.run_rcfunc = None
        return  True

    def timeout_probe(self):
        if self.run_tmid > 0:
            if self.timeout_cnt == 0:
                self.probe_and_show()
            self.timeout_cnt = (self.timeout_cnt + 1) % 2
            self.get_results()
        self.put_action()
        return True
