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
#include  <Python.h>
#include  <iconv.h>
#include  <stdlib.h>
#include  <string.h>

static PyObject *IC_iconv(PyObject *self, PyObject *args);

static PyMethodDef IconvMethods[] = {
    { "iconv", IC_iconv, METH_VARARGS,
      "do iconv to the provided string." },
    { NULL, NULL, 0, NULL }
};

void initiconv(void) {
    (void) Py_InitModule("iconv", IconvMethods);
}

static char *IC_iconv_internal(const char *from_encoding,
			       const char *to_encoding,
			       const char *fromstr) {
    char       * from_string, *to_string;
    char       * inbuf;   size_t  ibl;
    char       * outbuf;  size_t  obl, maxobl;
    iconv_t      ic;
    char       * newto_string;  size_t  oklength;

    from_string = strdup(fromstr);
    ibl = strlen(fromstr); maxobl = obl = ibl * 2;
    to_string = malloc(maxobl);

    if (from_string == NULL || to_string == NULL)  goto memory_err_out;

    ic = iconv_open(to_encoding, from_encoding);
    if ((int)ic == -1)  goto value_err_out;

    inbuf = from_string;  outbuf = to_string;
    while (ibl > 0)
	if (iconv(ic, &inbuf, &ibl, &outbuf, &obl) < 0) {
	    switch (errno) {
	    case E2BIG:
		printf("E2BIG");
		oklength = outbuf - to_string;
		newto_string = malloc(maxobl + maxobl);
		if (newto_string == NULL)  goto memory_err_out;
		maxobl = maxobl + maxobl;
		memcpy(newto_string, to_string, oklength);
		free(to_string);
		to_string = newto_string;
		outbuf = to_string + oklength;
		obl = maxobl - oklength;
		break;
	    default:
		goto value_err_out;
	    }
	}

    iconv_close(ic);
    *outbuf = 0; /* Add the tailing 0. */
    free(from_string);
    return  to_string;
 value_err_out:
    PyErr_SetFromErrno(PyExc_ValueError);
    if (from_string)  free(from_string);
    if (to_string)  free(to_string);
    return NULL;
 memory_err_out:
    PyErr_SetFromErrno(PyExc_MemoryError);
    if (from_string)  free(from_string);
    if (to_string)  free(to_string);
    return NULL;
}

static PyObject *IC_iconv(PyObject *self, PyObject *args) {
    const char * from_encoding, *to_encoding;
    const char * fromstr;
    char       * tostr;
    PyObject   * result;

    if (!PyArg_ParseTuple(args, "sss:iconv", &from_encoding, &to_encoding, &fromstr))
	return NULL;
    tostr = IC_iconv_internal(from_encoding, to_encoding, fromstr);
    if (!tostr)  return NULL;
    result = Py_BuildValue("s", tostr);
    free(tostr);
    return  result;
}
