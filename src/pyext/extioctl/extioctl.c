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
#include <sys/ioctl.h>
#include <linux/hdreg.h>
#include <fcntl.h>

static PyObject *EI_HDIO_GETGEO(PyObject *self, PyObject *args);

static PyMethodDef ExtioctlMethods[] = {
    { "HDIO_GETGEO", EI_HDIO_GETGEO, METH_VARARGS,
      "HDIO_GETGEO ioctl." },
    { NULL, NULL, 0, NULL }
};

void initextioctl(void) {
    (void) Py_InitModule("extioctl", ExtioctlMethods);
}

static PyObject *EI_HDIO_GETGEO(PyObject *self, PyObject *args) {
    int    fd;
    char  *devfn;
    struct hd_geometry geometry;
    PyObject *pyobj, *value;

    if (PyArg_ParseTuple(args, "s:HDIO_GETGEO", &devfn)) {
	fd = open(devfn, O_RDONLY);
	if (fd < 0) {
	    PyErr_SetFromErrno(PyExc_OSError);
	    return NULL;
	}
	if (ioctl(fd, HDIO_GETGEO, &geometry)) {
	    PyErr_SetFromErrno(PyExc_IOError);
	    return NULL;
	}
	pyobj = PyDict_New();
	value = PyInt_FromLong((long)(geometry.heads));
	PyDict_SetItemString(pyobj, "heads", value);
	value = PyInt_FromLong((long)(geometry.sectors));
	PyDict_SetItemString(pyobj, "sectors", value);
	value = PyInt_FromLong((long)(geometry.cylinders));
	PyDict_SetItemString(pyobj, "cylinders", value);
	value = PyLong_FromUnsignedLong(geometry.start);
	PyDict_SetItemString(pyobj, "start", value);
	return Py_BuildValue("O", pyobj);
    }
    return NULL;
}
