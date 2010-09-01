/* Copyright (C) 2003, Charles Wang.
 * Author:  Charles Wang <charles@linux.net.cn>
 * All rights reserved.
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the Free
 * Software Foundation; either version 2, or (at your option) any later
 * version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANT; without even the implied warranty of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE. See the GNU General Public LIcense for more
 * details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program; if not, write to the Free Software Foundation, 59 Temple
 * Place - Suite 330, Boston, MA 02111-1307, USA.
 */
#include <Python.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/ipc.h>
#include <sys/sem.h>
#include <sys/shm.h>
#include <sys/wait.h>
#include <errno.h>
#include <unistd.h>

/*******************************************
 *     Definitions for process control.    *
 *******************************************/
/*--- The data structure of the shared memory ---*/
/*   Firstly:   1 * shmstruct.
 *   Secondly:  queuespace * operqueue_entry.
 *   Thirdly:   bufspace * sizeof(unsigned char).
 *   Forthly:   resultspace * sizeof(unsigned char).
 */

/* SEMQLOCK: 0 ~ 1(initial), used to lock the write permission to the queue. */
#define  SEMQLOCK  0
/* SEMQUSED: 0(initial) ~ queuespace, used to ensure an empty queue entry. */
#define  SEMQUSED  1
/* SEMQFREE: 0 ~ queuespace(initial), used to ensure an exist entry. */
#define  SEMQFREE  2
/* SEMRLOCK: 0 ~ 1(initial), used to lock the write permission to the result. */
#define  SEMRLOCK  3
/* SEMEXIT: 0(initial) ~ 1, used to prevent the control process exit before action process. */
#define  SEMEXIT   4
/* SEMMAX:  Pass to the semget as the second parameter. */
#define  SEMMAX    5

typedef struct {
    unsigned       oper_id;       /* The identifier of this operation. */
    unsigned       operdata_len;  /* The length of the operation data. */
}  operqueue_entry;

/* NOTICE: queuespace and resultspace must less than SEMVMX. */
typedef struct {
    /* The following four values are set in the initialization. After that,
     * it is provided for reference only. */
    unsigned       queuespace;    /* The space of the whole operation queue. */
    unsigned       bufspace;      /* The space of the whole buffer. */
    unsigned       resultspace;   /* The space of the result buffer. */
    operqueue_entry *queue;       /* Point to the first entry in queue in the shared memory. */
    char          *data;          /* Point to the first char of buffer in the shared memory. */
    char          *result;        /* Point to the first char of result in the shared memory. */
    unsigned       resultlen;     /* The bytes in the result. */

    /* The following three values are written by action process, the control
     * process will read it when probe request is encountered. */
    int            oper_id;       /* The current operation identifier. */
    long           oper_step;     /* The current step number. */
    long           oper_stepnum;  /* The total number of steps. */

    /* The following two values can be modified by both control process and
     * action process. So semphore SEMQLOCK is required for it. */
    unsigned       bufdata_start; /* The start of all data in buffer. */
    unsigned       bufdata_len;   /* The length of all data in buffer. */
}  shmstruct;

#define SBOPLEN(sb)  (sizeof(sb) / sizeof(sb[0]))

/* The control process use sbqput to put an operation in queue. */
static struct sembuf sbqput[] = {
    { SEMQLOCK, -1, IPC_NOWAIT },
    { SEMQUSED,  1, IPC_NOWAIT },
    { SEMQFREE, -1, IPC_NOWAIT }
};

/* The control process use sbqunput when put failed. */
static struct sembuf sbqunput[] = {
    { SEMQLOCK,  1, 0 },
    { SEMQUSED, -1, 0 },
    { SEMQFREE,  1, 0 }
};

/* The action process use sbqget to get an operation in queue. */
static struct sembuf sbqget[] = {
    { SEMQLOCK, -1, 0 },
    { SEMQUSED, -1, 0 },
    { SEMQFREE,  1, 0 }
};

/* The action process use sbqunget when get failed. */
static struct sembuf sbqunget[] = {
    { SEMQLOCK,  1, 0 },
    { SEMQUSED,  1, 0 },
    { SEMQFREE, -1, 0 }
};

/* The control process and action process use sbqunlock to release the write
 * permission of the queue and data buffer. */
static struct sembuf sbqunlock[] = {
    { SEMQLOCK,  1, 0 }
};

/* The control process and action process use sbrlock to ensure the write
 * permission of the result buffer. */
static struct sembuf sbrlock[] = {
    { SEMRLOCK, -1, IPC_NOWAIT }
};

/* The control process and action process use sbrunlock to release the write
 * permission of the result buffer. */
static struct sembuf sbrunlock[] = {
    { SEMRLOCK,  1, 0 }
};

/* The action process use sbexitput when all of the operation is terminated. */
static struct sembuf sbexitput[] = {
    { SEMEXIT,  1, 0 }
};

/* The control process use sbexitbget to wait the action process finish its work. */
static struct sembuf sbexitbget[] = {
    { SEMEXIT, -1, 0 }
};

/* The control process use sbexitget to probe whether the action process finish its work. */
static struct sembuf sbexitget[] = {
    { SEMEXIT, -1, IPC_NOWAIT }
};


/************************************************
 *    Definitions for python MIAction object.   *
 ************************************************/
typedef struct _PyMIActions  PyMIActions;
struct _PyMIActions {
    PyObject_HEAD
    unsigned  oper_cnt;
    pid_t     pid;      /* The fork result. */
    int       semid;    /* The identifier of semaphore set. */
    int       shmid;    /* The identifier of shared memory. */
    shmstruct *ss;      /* Point to shared memory. */
};

/* Object methods. */
static PyObject *new_miactions_object(int queuespace, int bufspace, int resultspace);
static void      py_miactions_destructor(PyMIActions *self);
static PyObject *py_miactions_getattr(PyMIActions *self, char *name);
/* Control process only methods. */
static PyObject *py_put_operation(PyMIActions *self, PyObject *args);
static PyObject *py_probe_step(PyMIActions *self);
static PyObject *py_get_result(PyMIActions *self);
static PyObject *py_wait_action_exit(PyMIActions *self);
static PyObject *py_action_alive(PyMIActions *self);
static struct PyMethodDef  PyControlProcessMethods[] = {
    { "put_operation", (PyCFunction) py_put_operation, METH_VARARGS, NULL },
    { "probe_step", (PyCFunction) py_probe_step, METH_NOARGS, NULL },
    { "get_result", (PyCFunction) py_get_result, METH_NOARGS, NULL },
    { "wait_action_exit", (PyCFunction) py_wait_action_exit, METH_NOARGS, NULL },
    { "action_alive", (PyCFunction) py_action_alive, METH_NOARGS, NULL },
    { NULL, NULL, 0, NULL }
};
/* Action process only methods. */
static PyObject *py_get_operation(PyMIActions *self);
static PyObject *py_set_step(PyMIActions *self, PyObject *args);
static PyObject *py_put_result(PyMIActions *self, PyObject *args);
static struct PyMethodDef  PyActionProcessMethods[] = {
    { "get_operation", (PyCFunction) py_get_operation, METH_NOARGS, NULL },
    { "set_step", (PyCFunction) py_set_step, METH_VARARGS, NULL },
    { "put_result", (PyCFunction) py_put_result, METH_VARARGS, NULL },
    { NULL, NULL, 0, NULL }
};

static char PyMIActions__doc__[] = "This is the MagicInstaller's Actions object";
PyTypeObject PyMIActionsType = {
    PyObject_HEAD_INIT(&PyType_Type)
    0,                              /* ob_size */
    "MIActions",                    /* tp_name */
    sizeof(PyMIActions),            /* tp_size */
    0,                              /* tp_itemsize */
    (destructor) py_miactions_destructor,   /* tp_dealloc */
    0,                              /* tp_print */
    (getattrfunc) py_miactions_getattr,     /* tp_getattr */
    0,                              /* tp_setattr */
    0,                              /* tp_compare */
    0,                              /* tp_repr */
    0,                              /* tp_as_number */
    0,                              /* tp_as_sequence */
    0,                              /* tp_as_mapping */
    0,                              /* tp_hash */
    0,                              /* tp_call */
    0,                              /* tp_str */
    0,                              /* tp_getattro */
    0,                              /* tp_setattro */
    0,                              /* tp_as_buffer */
    0,                              /*tp_flags */
    PyMIActions__doc__,             /* tp_doc */
};

static int _round4(int value) {
    static const int round4cnv[] = { 0, 3, 2, 1 };
    return  value + round4cnv[value % 4];
}
static int _set_sem(int semid, int semnum, int semval) {
    if (semctl(semid, semnum, SETVAL, semval) < 0) {
	PyErr_SetFromErrno(PyExc_OSError);
	return 0;
    }
    return 1;
}
static PyObject *new_miactions_object(int queuespace, int bufspace, int resultspace) {
    unsigned     queue_offset, data_offset, result_offset, total_shmlen;
    shmstruct    newss;
    PyMIActions *self;

    /* Fill the newss. */
    newss.queuespace    = queuespace;
    newss.bufspace      = bufspace;
    newss.resultspace   = resultspace;
    queue_offset        = _round4(sizeof(newss));
    data_offset         = _round4(queue_offset + queuespace * sizeof(operqueue_entry));
    result_offset       = _round4(data_offset + bufspace);
    total_shmlen        = _round4(result_offset + resultspace);
    newss.oper_id       = -1;
    newss.oper_step     = 0;
    newss.oper_stepnum  = 0;
    newss.bufdata_start = 0;
    newss.bufdata_len   = 0;

    self = PyObject_New(PyMIActions, &PyMIActionsType);
    if (self == NULL)  return NULL;
    self->oper_cnt = 0;
    self->pid = -1;
    self->semid = -1;
    self->shmid = -1;
    self->ss = (shmstruct *) -1;

    self->shmid = shmget(IPC_PRIVATE, total_shmlen, 0600 | IPC_CREAT | IPC_EXCL);
    if (self->shmid < 0) {
	PyErr_SetFromErrno(PyExc_OSError);
	return NULL;
    }

    self->ss = (shmstruct *)shmat(self->shmid, NULL, 0);
    if (self->ss == (shmstruct *)-1) {
	PyErr_SetFromErrno(PyExc_OSError);
	return NULL;
    }
    newss.queue  = (operqueue_entry *)(((char *)(self->ss)) + queue_offset);
    newss.data   = ((char *)(self->ss)) + data_offset;
    newss.result = ((char *)(self->ss)) + result_offset;
    newss.resultlen = 0;
    memcpy(self->ss, &newss, sizeof(shmstruct));

    self->semid = semget(IPC_PRIVATE, SEMMAX, 0600 | IPC_CREAT | IPC_EXCL);
    if (self->semid < 0) {
	PyErr_SetFromErrno(PyExc_OSError);
	return NULL;
    }

    if (!_set_sem(self->semid, SEMQLOCK, 1))   return NULL;
    if (!_set_sem(self->semid, SEMQUSED, 0))  return NULL;
    if (!_set_sem(self->semid, SEMQFREE, queuespace))   return NULL;
    if (!_set_sem(self->semid, SEMRLOCK, 1))   return NULL;
    if (!_set_sem(self->semid, SEMEXIT, 0))   return NULL;

    self->pid = fork();
    if (self->pid < 0) {
	PyErr_SetFromErrno(PyExc_OSError);
	return NULL;
    } else if (self->pid > 0) { /* Control process. */
	PyOS_AfterFork();
	return (PyObject *)self;
    } else { /* Action process. */
	PyOS_AfterFork();
	return (PyObject *)self;
    }
}
static void      py_miactions_destructor(PyMIActions *self) {
    if (self->pid > 0) {  /* control process. */
	waitpid(self->pid, NULL, 0);
	if (self->ss != (shmstruct *) -1)  shmdt(self->ss);
	if (self->shmid != -1)  shmctl(self->shmid, IPC_RMID, NULL);
	if (self->semid != -1) 	semctl(self->semid, 0, IPC_RMID);
    } else if (self->pid == 0)  {  /* access process. */
	if (self->ss != (shmstruct *) -1)  shmdt(self->ss);
	if (self->shmid != -1)  shmctl(self->shmid, IPC_RMID, NULL);
	semop(self->semid, sbexitput, SBOPLEN(sbexitput));
    } else { /* abnormal object. */
	if (self->ss != (shmstruct *) -1)  shmdt(self->ss);
	if (self->shmid != -1)  shmctl(self->shmid, IPC_RMID, NULL);
	if (self->semid != -1) 	semctl(self->semid, 0, IPC_RMID);
    }
    PyObject_Del(self);
}
static PyObject *py_miactions_getattr(PyMIActions *self, char *name) {
    if (!strcmp(name, "pid"))
	return PyInt_FromLong((long) self->pid);
    if (self->pid > 0)
	return Py_FindMethod(PyControlProcessMethods, (PyObject *)self, name);
    else
	return Py_FindMethod(PyActionProcessMethods, (PyObject *)self, name);
}
static PyObject *py_put_operation(PyMIActions *self, PyObject *args) {
    int   trycount;
    shmstruct  *ss;
    char *operation;
    operqueue_entry *oqe;  int used;
    int   oper_id;
    char *buffer;  int remain;
    int   datalen;

    ss = self->ss;
    for (trycount = 0; trycount < 4; ++trycount) {
	if (semop(self->semid, sbqput, SBOPLEN(sbqput)) >= 0) {
	    if (!PyArg_ParseTuple(args, "s:put_operation", &operation)) {
		semop(self->semid, sbqunput, SBOPLEN(sbqunput));
		return NULL;
	    }
	    datalen = strlen(operation) + 1;
	    if (ss->bufdata_len + datalen > ss->bufspace) {
		PyErr_SetString(PyExc_ValueError, "Too long operation.");
		semop(self->semid, sbqunput, SBOPLEN(sbqunput));
		return NULL;
	    }
	    /* Save the operation entry. */
	    used = semctl(self->semid, SEMQUSED, GETVAL);
	    if (used < 0) {
		PyErr_SetFromErrno(PyExc_OSError);
		semop(self->semid, sbqunput, SBOPLEN(sbqunput));
		return NULL;
	    }
	    oqe = ss->queue;
	    oqe[used - 1].oper_id = oper_id = self->oper_cnt++;
	    oqe[used - 1].operdata_len = datalen;
	    /* Save the operation into buffer. */
	    buffer = ss->data;
	    if (ss->bufdata_start + ss->bufdata_len + datalen <= ss->bufspace)
		strcpy(buffer + ss->bufdata_start + ss->bufdata_len, operation);
	    else if (ss->bufdata_start + ss->bufdata_len < ss->bufspace) {
		remain = ss->bufspace - ss->bufdata_start - ss->bufdata_len;
		memcpy(buffer + ss->bufdata_start + ss->bufdata_len, operation, remain);
		strcpy(buffer, operation + remain);
	    } else {
		remain = ss->bufdata_start + ss->bufdata_len - ss->bufspace;
		strcpy(buffer + remain, operation);
	    }
	    ss->bufdata_len += datalen;
	    if (semop(self->semid, sbqunlock, SBOPLEN(sbqunlock)) < 0) {
		PyErr_SetFromErrno(PyExc_OSError);
		return NULL;
	    }
	    return Py_BuildValue("i", oper_id); /* put successfully. */
	}
	if (errno == EAGAIN)
	    usleep(100); /* sleep 1/10 second. */
	else {
	    PyErr_SetFromErrno(PyExc_OSError);
	    return NULL;
	}
    }
    PyErr_SetFromErrno(PyExc_OSError);
    return  NULL;
}
static PyObject *py_probe_step(PyMIActions *self) {
    return  Py_BuildValue("ill",
			  self->ss->oper_id,
			  self->ss->oper_step,
			  self->ss->oper_stepnum);
}
static PyObject *py_get_result(PyMIActions *self) {
    shmstruct  *ss;
    char       *presult;
    PyObject   *result;

    ss = self->ss;
    result = PyList_New(0);
    if (result == NULL)  return NULL;
    if (semop(self->semid, sbrlock, SBOPLEN(sbrlock)) < 0) {
	if (errno == EAGAIN) {
	    return Py_BuildValue("O", result);
	}
	PyErr_SetFromErrno(PyExc_OSError);
	goto err0;
    }

    presult = ss->result;
    while (presult - ss->result < ss->resultlen) {
	if (PyList_Append(result, PyString_FromString(presult)) < 0)
	    goto err1;
	presult += strlen(presult) + 1;
    }

    ss->resultlen = 0;

    if (semop(self->semid, sbrunlock, SBOPLEN(sbrunlock)) < 0)
	goto err0;
    return  Py_BuildValue("O", result);

 err1:
    semop(self->semid, sbrunlock, SBOPLEN(sbrunlock));
 err0:
    PyObject_Del(result);
    return  NULL;
}
static int wait_actions(PyMIActions *self) {
    int  status, result;
    while((result = waitpid(self->pid, &status, 0)) != self->pid)
	if (result < 0 && errno != EINTR) {
	    PyErr_SetFromErrno(PyExc_RuntimeError);
	    return status;
	}
    return status;
}
static PyObject *py_wait_action_exit(PyMIActions *self) {
    int  exitval;
    /* Skip all remain result in result buffer. */
    for (;;) {
	if (semop(self->semid, sbexitbget, SBOPLEN(sbexitbget)) >= 0) {
	    exitval = wait_actions(self);
	    return  Py_BuildValue("i", exitval);
	}
	if (errno != EAGAIN) {
	    PyErr_SetFromErrno(PyExc_OSError);
	    return NULL;
	}
    }
}
static PyObject *py_action_alive(PyMIActions *self) {
    int  exitval;
    /* Do not let control process pass if the result is not empty. */
    if (self->ss->resultlen > 0)
	return Py_BuildValue("ii", 1, 0);
    if (semop(self->semid, sbexitget, SBOPLEN(sbexitget)) >= 0) {
	exitval = wait_actions(self);
	return Py_BuildValue("ii", 0, exitval);
    }
    if (errno == EAGAIN)
	return Py_BuildValue("ii", 1, 0);
    PyErr_SetFromErrno(PyExc_OSError);
    return NULL;
}
static PyObject *py_get_operation(PyMIActions *self) {
    shmstruct *ss;
    int        used;
    operqueue_entry  *oqe;
    int        oper_id, datalen;
    char      *buffer;
    char      *operation;  int part;
    PyObject  *result;

    ss = self->ss;
    if (semop(self->semid, sbqget, SBOPLEN(sbqget)) < 0) {
	PyErr_SetFromErrno(PyExc_OSError);
	return NULL;
    }
    used = semctl(self->semid, SEMQUSED, GETVAL);
    if (used < 0) {
	semop(self->semid, sbqunget, SBOPLEN(sbqunget));
	PyErr_SetFromErrno(PyExc_OSError);
	return NULL;
    }
    oqe = ss->queue;
    oper_id = oqe[0].oper_id;
    datalen = oqe[0].operdata_len;
    if (used > 0)
	memmove(oqe, oqe + 1, used * sizeof(oqe[0]));
    operation = (char *)malloc(datalen);
    if (operation == NULL) {
	PyErr_SetFromErrno(PyExc_OSError);
	semop(self->semid, sbqunget, SBOPLEN(sbqunget));
	return NULL;
    }
    buffer = ss->data;
    if (ss->bufdata_start + datalen <= ss->bufspace) {
	strcpy(operation, buffer + ss->bufdata_start);
	ss->bufdata_start += datalen;
    } else {
	part = ss->bufspace - ss->bufdata_start;
	memcpy(operation, buffer + ss->bufdata_start, part);
	strcpy(operation + part, buffer);
	ss->bufdata_start = part;
    }
    ss->bufdata_len -= datalen;
    if (semop(self->semid, sbqunlock, SBOPLEN(sbqunlock)) < 0) {
	PyErr_SetFromErrno(PyExc_OSError);
	free(operation);
	return NULL;
    }
    result = Py_BuildValue("is", oper_id, operation);
    free(operation);
    return  result;
}
static PyObject *py_set_step(PyMIActions *self, PyObject *args) {
    int   oper_id;
    long  oper_step;
    long  oper_stepnum;
    if (!PyArg_ParseTuple(args, "ill:set_step", &oper_id, &oper_step, &oper_stepnum))
	return NULL;
    self->ss->oper_id      = oper_id;
    self->ss->oper_step    = oper_step;
    self->ss->oper_stepnum = oper_stepnum;
    Py_INCREF(Py_None);
    return  Py_None;
}
static PyObject *py_put_result(PyMIActions *self, PyObject *args) {
    shmstruct  *ss;
    char       *this_result;  int this_len;
    char        errbuf[64];

    if (!PyArg_ParseTuple(args, "s:put_result", &this_result))
	return NULL;
    ss = self->ss;
    this_len = strlen(this_result) + 1;
    if (this_len > ss->resultspace) {
	snprintf(errbuf, sizeof(errbuf), "The result is longer than %d.", ss->resultspace);
	PyErr_SetString(PyExc_ValueError, errbuf);
	return NULL;
    }
    for (;;) {
	if (semop(self->semid, sbrlock, SBOPLEN(sbrlock)) < 0) {
	    if (errno == EAGAIN) {
		usleep(100);
		continue;
	    }
	    PyErr_SetFromErrno(PyExc_OSError);
	    return NULL;
	}
	if (this_len <= ss->resultspace - ss->resultlen) {
	    strcpy(ss->result + ss->resultlen, this_result);
	    ss->resultlen += this_len;
	    this_len = 0;
	}
	if (semop(self->semid, sbrunlock, SBOPLEN(sbrunlock)) < 0) {
	    PyErr_SetFromErrno(PyExc_OSError);
	    return NULL;
	}
	if (this_len == 0) {
	    Py_INCREF(Py_None);
	    return Py_None; /* Ok, successfull. */
	}
	usleep(100); /* Wait a while and try again. */
    }
}

static PyObject *MIA_MIActions(PyObject *notused, PyObject *args, PyObject *kwds);
static PyObject *MIA_usleep(PyObject *notused, PyObject *args);
static PyMethodDef MIActionsModuleMethods[] = {
    { "MIActions", (PyCFunction)MIA_MIActions, METH_VARARGS | METH_KEYWORDS, "" },
    { "usleep", (PyCFunction)MIA_usleep, METH_VARARGS, "" },
    { NULL, NULL, 0, NULL }
};

void initmiactions(void) {
    (void)Py_InitModule("miactions", MIActionsModuleMethods);
}

static int _check_new_parameters(int queuespace, int bufspace, int resultspace) {
    /* No need to check up-boundary. Because queuespace is the initialize value
       of some semaphore, if any of the value greater than SEMVMX, ERANGE will
       be issued when semctl(..., ..., SETVAL, ...) is called. */
    if (queuespace < 2) {
	PyErr_SetString(PyExc_ValueError, "queuespace should be greater than 2.");
	return  0;
    }
    if (bufspace < 256) {
	PyErr_SetString(PyExc_ValueError, "bufspace should be greater than 255.");
	return  0;
    }
    if (resultspace < 16) {
	PyErr_SetString(PyExc_ValueError, "resultspace should be greater than 15.");
	return  0;
    }
    return  1;
}
static PyObject *MIA_MIActions(PyObject *notused, PyObject *args, PyObject *kwds) {
    int  queuespace, bufspace, resultspace;
    static char *kwlist[] = { "queuespace",
			      "bufspace",
			      "resultspace", NULL };

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|iii:MIActions",
				     kwlist,
				     &queuespace, &bufspace, &resultspace))
	return NULL;
    if (!_check_new_parameters(queuespace, bufspace, resultspace))  return NULL;
    return  new_miactions_object(queuespace, bufspace, resultspace);
}
static PyObject *MIA_usleep(PyObject *notused, PyObject *args) {
    int  usec;
    if (!PyArg_ParseTuple(args, "i:usleep", &usec))
	return NULL;
    usleep(usec);
    Py_INCREF(Py_None);
    return  Py_None;
}
