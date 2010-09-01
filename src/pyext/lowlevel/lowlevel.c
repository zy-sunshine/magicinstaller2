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
#include <fcntl.h>
#include <unistd.h>

static PyObject *LL_makedev(PyObject *self, PyObject *args);
static PyObject *LL_mknod(PyObject *self, PyObject *args);

static PyMethodDef LowlevelMethods[] = {
    { "makedev", LL_makedev, METH_VARARGS, "makedev." },
    { "mknod", LL_mknod, METH_VARARGS, "mknod." },
    { NULL, NULL, 0, NULL }
};

void initlowlevel(void) {
    PyObject  *m;
    m = Py_InitModule("lowlevel", LowlevelMethods);
    PyModule_AddIntConstant(m, "S_IFBLK", S_IFBLK);
    PyModule_AddIntConstant(m, "S_IFDIR", S_IFDIR);
    PyModule_AddIntConstant(m, "S_IFCHR", S_IFCHR);
}

static PyObject *LL_makedev(PyObject *self, PyObject *args) {
    int  major, minor, result;
    if (PyArg_ParseTuple(args, "ii:makedev", &major, &minor)) {
	result = makedev(major, minor);
	return Py_BuildValue("i", result);
    }
    return NULL;
}
static PyObject *LL_mknod(PyObject *self, PyObject *args) {
    char  *devfn;
    int    mode, dev;
    if (PyArg_ParseTuple(args, "sii:mknod", &devfn, &mode, &dev)) {
	if (mknod(devfn, (mode_t) mode, (dev_t) dev)) {
	    PyErr_SetFromErrno(PyExc_OSError);
	    return NULL;
	}
	return Py_BuildValue("O", Py_None);
    }
    return NULL;
}
