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
//#include <asm/page.h>
#include <sys/types.h>
#include <sys/ioctl.h>
#include <sys/mount.h>
#include <sys/swap.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include "loop.h"
#include "imount.h"

#ifndef CDROMEJECT
#define CDROMEJECT 0x5309
#endif

static PyObject * doMount(PyObject * s, PyObject * args);
static PyObject * doUMount(PyObject * s, PyObject * args);
static PyObject * doSwapon(PyObject * s, PyObject * args);
static PyObject * doSwapoff(PyObject * s, PyObject * args);
static PyObject * doEjectCdrom(PyObject * s, PyObject * args);
static PyObject * doSync(PyObject * s, PyObject * args);
static PyObject * checkLoopdevUnused(PyObject * s, PyObject * args);

static PyMethodDef isysModuleMethods[] = {
    { "mount", (PyCFunction) doMount, METH_VARARGS, NULL },
    { "umount", (PyCFunction) doUMount, METH_VARARGS, NULL },
    { "swapon", (PyCFunction) doSwapon, METH_VARARGS, NULL },
    { "swapoff", (PyCFunction) doSwapoff, METH_VARARGS, NULL },
    { "ejectcdrom", (PyCFunction) doEjectCdrom, METH_VARARGS, NULL },
    { "sync", (PyCFunction) doSync, METH_VARARGS, NULL },
    { "loopstatus", (PyCFunction) checkLoopdevUnused, METH_VARARGS, NULL},
    { NULL, NULL, 0, NULL }
};

void initisys(void) {
    (void) Py_InitModule("isys", isysModuleMethods);
}

static PyObject * doMount(PyObject * s, PyObject * args) {
    char *err = NULL, * fs, * device, * mntpoint, *flags = NULL;
    int rc;

    if (!PyArg_ParseTuple(args, "sss|z", &fs, &device, &mntpoint,
			  &flags)) return NULL;

    rc = doPwMount(device, mntpoint, fs, flags, &err);
    if (rc == IMOUNT_ERR_ERRNO)
	PyErr_SetFromErrno(PyExc_SystemError);
    else if (rc) {
        PyObject *tuple = PyTuple_New(2);

        PyTuple_SetItem(tuple, 0, PyInt_FromLong(rc));

        if (err == NULL) {
            Py_INCREF(Py_None);
            PyTuple_SetItem(tuple, 1, Py_None);
        } else {
            PyTuple_SetItem(tuple, 1, PyString_FromString(err));
        }

        PyErr_SetObject(PyExc_SystemError, tuple);
    }

    if (rc) return NULL;

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject * doUMount(PyObject * s, PyObject * args) {
    char *err = NULL, *mntpoint = NULL;
    int rc;
    
    if (!PyArg_ParseTuple(args, "s", &mntpoint)){
        return NULL;
    }

    rc = doPwUmount(mntpoint, &err);
    if (rc == IMOUNT_ERR_ERRNO){
        PyErr_SetFromErrno(PyExc_SystemError);
    } else if (rc) {
        PyObject *tuple = PyTuple_New(2);

        PyTuple_SetItem(tuple, 0, PyInt_FromLong(rc));

        if (err == NULL) {
            Py_INCREF(Py_None);
            PyTuple_SetItem(tuple, 1, Py_None);
        } else {
            PyTuple_SetItem(tuple, 1, PyString_FromString(err));
        }

        PyErr_SetObject(PyExc_SystemError, tuple);
    }

    if (rc){
        return NULL;
    }

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject * doSwapon (PyObject * s, PyObject * args) {
    char * path;

    if (!PyArg_ParseTuple(args, "s", &path)) return NULL;

    if (swapon (path, 0)) {
        PyErr_SetFromErrno(PyExc_SystemError);
        return NULL;
    }

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject * doSwapoff (PyObject * s, PyObject * args) {
    char * path;

    if (!PyArg_ParseTuple(args, "s", &path)) return NULL;

    if (swapoff (path)) {
        PyErr_SetFromErrno(PyExc_SystemError);
        return NULL;
    }

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject * doEjectCdrom(PyObject * s, PyObject * args) {
    int fd;

    if (!PyArg_ParseTuple(args, "i", &fd)) return NULL;

    if (ioctl(fd, CDROMEJECT, 1)) {
        PyErr_SetFromErrno(PyExc_SystemError);
        return NULL;
    }

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject * doSync(PyObject * s, PyObject * args) {
    int fd;

    if (!PyArg_ParseTuple(args, "", &fd)) return NULL;
    sync();
    
    Py_INCREF(Py_None);
    return Py_None;
}

static int check_loopdev_unused(const char *device, char **errmsg);

static PyObject * checkLoopdevUnused(PyObject * s, PyObject * args){
    char *looppath = NULL;
    char *err = NULL;
    int rc;
    
    if (!PyArg_ParseTuple(args, "s", &looppath)) return NULL;

    rc = check_loopdev_unused(looppath, &err);
    
    PyObject *tuple = PyTuple_New(2);
    PyTuple_SetItem(tuple, 0, PyInt_FromLong(rc));
    if (err == NULL) {
        PyTuple_SetItem(tuple, 1, Py_None);
    } else {
        PyTuple_SetItem(tuple, 1, PyString_FromString(err));
    }

    //Py_INCREF(Py_None);
    //return Py_None;
    Py_INCREF(tuple);
    return tuple;
    //return Py_BuildValue("i", !rc);

}

static int check_loopdev_unused(const char *device, char **errmsg) {
    int              fd;
    struct stat      statbuf;
    struct loop_info loopinfo;

    if (stat(device, &statbuf)) {
        //PyErr_SetFromErrno(PyExc_SystemError);
        return 1;
    }
    if (!S_ISBLK(statbuf.st_mode)) {
    *errmsg = calloc(4096, sizeof(char));
	snprintf(*errmsg, 4096, "%s is not a block device file.\n", device);
	//PyErr_SetString(PyExc_SystemError, *errmsg);
        return 1;
    }
    fd = open(device, O_RDONLY);
    if (fd < 0) {
	//PyErr_SetFromErrno(PyExc_SystemError);
        return 1;
    }
    if (ioctl(fd, LOOP_GET_STATUS, &loopinfo) == 0) {
	close(fd);
    *errmsg = calloc(4096, sizeof(char));
	snprintf(*errmsg, 4096, "%s is used already.\n", device);
	//PyErr_SetString(PyExc_SystemError, *errmsg);
        return 1;
    }
    if (errno == ENXIO) {
        close(fd);
        return 0;
    }
    //PyErr_SetFromErrno(PyExc_SystemError);
    close(fd);
    return 1;
}
static int set_loop(const char *device, const char *file, int mode) {
    struct loop_info loopinfo;
    int              fd, ffd;

    if ((ffd = open(file, mode)) < 0) {
	PyErr_SetFromErrno(PyExc_SystemError);
        return 1;
    }
    if ((fd = open(device, mode)) < 0) {
	PyErr_SetFromErrno(PyExc_SystemError);
        close(ffd);
        return 1;
    }
    memset(&loopinfo, 0, sizeof(loopinfo));
    strncpy(loopinfo.lo_name, file, LO_NAME_SIZE);
    loopinfo.lo_name[LO_NAME_SIZE - 1] = 0;
    loopinfo.lo_offset = 0;
    loopinfo.lo_encrypt_key_size = 0;
    if (ioctl(fd, LOOP_SET_FD, ffd) < 0) {
	PyErr_SetFromErrno(PyExc_SystemError);
        close(fd);
        close(ffd);
        return 1;
    }
    if (ioctl(fd, LOOP_SET_STATUS, &loopinfo) < 0) {
        (void)ioctl(fd, LOOP_CLR_FD, 0);
	PyErr_SetFromErrno(PyExc_SystemError);
        close(fd);
        close(ffd);
        return 1;
    }
    close(fd);
    close(ffd);
    return 0;
}
static int del_loop(const char *device) {
    int fd;
    if ((fd = open(device, O_RDONLY)) < 0) {
	PyErr_SetFromErrno(PyExc_SystemError);
        return 1;
    }
    if (ioctl(fd, LOOP_CLR_FD, 0) < 0) {
	PyErr_SetFromErrno(PyExc_SystemError);
        close(fd);
        return 1;
    }
    close(fd);
    return 0;
}
