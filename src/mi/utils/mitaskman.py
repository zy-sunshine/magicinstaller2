#!/usr/bin/python
#coding=utf-8
import gobject, gtk
import xmlrpclib, socket
from mi.utils import _
import time
from xml.dom.minidom import parseString

from mi.client.utils import logger, magicpopup
import threading
dolog = logger.i
from mi.utils.miconfig import MiConfig
CF = MiConfig.get_instance()
# The task manager: It only manage the long operation.
class MiTaskman :
    def __init__(self, port, action_prog, aplabel, err_dialog = None):
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
        # cur_tmid: Use to provide unique cur_tmid.
        self.cur_tmid = 0
        # results: The results indexed by cur_tmid.
        self.results = {}

        #--- running action status ---
        self.run_tmid = -1  # -1 means not any action is running.
        # run_id: reserve the id of self.actserver.method(*params)
        self.run_id = -1
        self.run_show = 0
        self.run_rcfunc = None
        self.run_rcdata = None
        self.run_prev_pulse_time = -1.0
        self.err_dialog = err_dialog

    def push_progress(self, actprog, aplabel):
        if len(self.apstack) == 1:
            self.action_prog.hide()
            self.aplabel.hide()
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
        self.cur_tmid = self.cur_tmid + 1
        self.tasks.append([(self.cur_tmid, describe, rcfunc, rcdata, method, params)])
        return self.cur_tmid

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

        try:
            id = eval('self.actserver.%s(*params)' % method)
        except socket.error:
            # put action failed.
            return  False
        #except xmlrpclib.Fault:
        #    import pdb; pdb.set_trace()
        # put action successfully.
        if method == 'quit':
            gtk.main_quit()
            
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
            exe_ok = res_tuple[0][2]
            method = res_tuple[1]  # Not used yet.
            if id != self.run_id:
                dolog('WARNING: id(%s) != self.run_id(%s) in magic.installer.py:get_results().\n' % (id, self.run_id))
                # Weird encountered.
                continue
            if self.run_show and len(self.apstack) == 1:
                self.aplabel.hide()
                self.action_prog.hide()
                self.run_show = 0
            if self.run_rcfunc:
                if not exe_ok:
                    dolog('%s - %s' % ('ERROR EXECUTE %s' % method, result))
                    if self.err_dialog and CF.D.DEBUG:
                        self.err_dialog(result)
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


class MiTask(object):
    def __init__(self, describe, rcfunc, rcdata, method, *params):
        self.describe = describe
        self.rcfunc = rcfunc
        self.rcdata = rcdata
        self.method = method
        self.params = params
        
    def get_params(self):
        return self.describe, self.rcfunc, self.rcdata, self.method, self.params
    
class TaskGroupQueue(object):
    '''
    This is a queue for install operation do in order.
    '''
    def __init__(self, tm):
        self.tm = tm
        self.task_que_map = {}
        self.task_grp_list = []
        self.task_grp_info = {}
        self.lock = threading.Lock()
        self.cur_tmid = None
        self.cur_grp_name = None
        #self.result_map = {}
        self.task_info_map = {}
        self._cur_grp_name_idx = -1
        
    def add_task(self, grp_name, task, new_task_grp=True):
        self.lock.acquire()
        if new_task_grp and grp_name not in self.task_grp_list:
            self.task_grp_list.append(grp_name)
            self.task_que_map.setdefault(grp_name, []).append(task)
        else:
            self.task_que_map[grp_name].append((grp_name, task))
        self._run_next_task()
        self.lock.release()
        
    def _get_next_valid_grp_name(self):
        if self._cur_grp_name_idx + 1 < len(self.task_grp_list):
            self._cur_grp_name_idx += 1
            return self.task_grp_list[self._cur_grp_name_idx]
        else:
            return None

    def _run_next_task(self):
        def run_task(grp_name, task):
            print 'run_task ', grp_name, task.describe, self.dispatch, task.rcdata, task.method, task.params
            self.cur_tmid = self.tm.add_action(task.describe, self.dispatch, task.rcdata, task.method, *task.params)
            self.task_info_map[self.cur_tmid] = {'grp_name': grp_name, 'task': task}
        #import pdb; pdb.set_trace()
        if self.cur_tmid is None:
            if self.cur_grp_name is None or \
                (self.cur_grp_name is not None and self.cur_tmid is None and self.task_que_map[self.cur_grp_name] == []):
                # start a new group, we not wait current group's next task, because, operator should add task continuously
                self.cur_grp_name = self._get_next_valid_grp_name()
                if self.cur_grp_name:
                    # valid grp_name
                    task_que = self.task_que_map[self.cur_grp_name]
                    if task_que:
                        run_task(self.cur_grp_name, task_que.pop(0))
                    else:
                        # cur group empty
                        self.cur_grp_name = None
                    
                else:
                    # no group in queue to be executed, wait next
                    pass
            else:
                # start current group next task
                task_que = self.task_que_map[self.cur_grp_name]
                if task_que:
                    run_task(*task_que.pop(0))
                else:
                    # cur group empty
                    self.cur_grp_name = None
        
    def dispatch(self, *args):
        no_err = True
        self.lock.acquire()
        task_info = self.task_info_map[self.cur_tmid]
        
        # optional record
        #self.task_grp_info[task_info['grp_name']]['last_result'] = args
        # handle with this task's result
        self.lock.release()
        if callable(task_info['task'].rcfunc):
            ret = task_info['task'].rcfunc(*args)
        else:
            ret = 'quit'
        if type(ret) is str:
            if ret == 'quit':
                # quit current task group, do next task group
                self.cur_grp_name = None
            else:
                raise Exception('Not Support', 'Unknow ret %s' % ret)
        elif len(ret) == 2:
            valid, task_or_msg = ret
            if valid or valid == 'continue':
                # add a task
                if isinstance(task_or_msg, MiTask):
                    self.add_task(task_info['grp_name'], task_or_msg, False)
                else:
                    # ??
                    pass
            else:
                # occur error show error message
                class BoxMsgHandler(object):
                    def __init__(self, sself):
                        self.sself = sself
                    def yes_clicked(self, widget, data):
                        # quit program
                        data.topwin.destroy()
                        gtk.main_quit()
                        
                    def ignore_clicked(self, widget, data):
                        # continue next task
                        data.topwin.destroy()
                        self.sself.lock.acquire()
                        self.sself._run_next_task()
                        self.sself.lock.release()
                        
                magicpopup.magicmsgbox(BoxMsgHandler(self), _("Occur error! Click Yes to quit installation!\nTask(%s) Group(%s)\nERROR:%s" % (self.task_info_map[self.cur_tmid]['task'].describe, self.cur_grp_name, task_or_msg)), 
                                       magicpopup.magicmsgbox.MB_ERROR, 
                                       magicpopup.magicpopup.MB_YES|magicpopup.magicpopup.MB_IGNORE)
                no_err = False
        else:
            raise Exception('Not Support', 'Unknow ret %s' % ret)
        
        self.lock.acquire()
        self.cur_tmid = None
        if no_err:
            self._run_next_task()
        self.lock.release()

if __name__ == '__main__':
    class FakeTm(object):
        def __init__(self):
            self.task_lst = []
            self.timeout = gobject.timeout_add(100, self.timeout_probe)
            self.tid = -1
            
        def add_action(self, describe, rcfunc, rcdata, method, *params):
            self.task_lst.append((describe, rcfunc, rcdata, method, params))
            self.tid += 1
            return self.tid
            
        def timeout_probe(self):
            #print 'timeout_probe'
            if self.task_lst:
                describe, rcfunc, rcdata, method, params = self.task_lst.pop(0)
                #print describe, rcfunc, rcdata, method, params
                if rcfunc:
                    rcfunc(describe+' result', rcdata)
            return True
        
            
    tm = FakeTm()
    tgq = TaskGroupQueue(tm)
    def task1_2(rdata, tdata):
        #return False, 'error message'
        return 'quit'
        
    def task1_1(rdata, tdata):
        print 'task1_1 recv %s %s' % (rdata, tdata)
        return True, MiTask('task1_2', task1_2, None, 'rpc method', 0, 1, 2)
        
    def task2_1(rdata, tdata):
        print 'task2_1 recv %s %s' % (rdata, tdata)
        return 'continue', MiTask('task2_2', None, None, 'rpc method', 0, 1, 2)
    
    tgq.add_task('Task 1', MiTask('task1_0', task1_1, None, 'rpc method', 0, 1, 2))
    tgq.add_task('Task 2', MiTask('task2_0', task2_1, None, 'rpc method', 0, 1, 2))
    tgq.add_task('Task 3', MiTask('task3_0', None, None, 'rpc method', 0, 1, 2))

#    import signal
#    import sys
#    def signal_handler(signal, frame):
#        print 'You pressed Ctrl+C!'
#        import pdb; pdb.set_trace()
#    signal.signal(signal.SIGINT, signal_handler)
#    
    gtk.main()