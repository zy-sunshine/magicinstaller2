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
#include <structmember.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/socket.h>
#include <fcntl.h>
#include <netdb.h>

#define  TIMEOUT  5

static struct servent *sp;
static PyObject *PyExc_TFtpError;
static PyObject *PyExc_GetHostByName;
static PyObject *PyExc_GetServByName;
static PyObject *PyExc_Socket;
static PyObject *PyExc_Bind;
static PyObject *PyExc_Connect;

/* Satisfy tftp.c */
const int trace = 0;
const int verbose = 0;
const int rexmtval = TIMEOUT;
const int maxtimeout = 5 * TIMEOUT;

typedef struct {
    PyObject_HEAD
    int      socketfd;
    u_short  port;
    int      connected;
    int      mode;
    struct sockaddr_in  peeraddr;
}  PyTFtpClientObject;

static char ascii_doc[] =
"ascii()\n\
\n\
Set the transfer mode to ASCII.\n\
No parameter.\n\
For example:\n\
    cli = tftpc.TFtpClient()\n\
    cli.connect('127.0.0.1')\n\
    cli.ascii()";
static PyObject * tftpc_ascii(PyTFtpClientObject *obj);

static char binary_doc[] =
"binary()\n\
\n\
Set the transfer mode to BINARY(default).\n\
No parameter.\n\
For example:\n\
    cli = tftpc.TFtpClient()\n\
    cli.connect('127.0.0.1')\n\
    cli.binary()";
static PyObject * tftpc_binary(PyTFtpClientObject *obj);

static char connect_doc[] =
"connect(address[, port])\n\
\n\
Connect to the tftp server.\n\
The first parameter is a string of the target address.\n\
The second parameter is optional integer to specify the port.\n\
For example:\n\
    cli = tftpc.TFtpClient()\n\
    cli.connect('127.0.0.1', '69')";
static PyObject * tftpc_connect(PyTFtpClientObject *obj, PyObject *args);

static char get_doc[] =
"get(remotefile[, localfile]) -> bytes-received\n\
\n\
Get the specified file.\n\
The first parameter is the path of remote file.\n\
The second parameter is the optional path of local file. If it is omitted,\n\
use the first parameter as the path of local file.\n\
For example:\n\
    cli = tftpc.TFtpClient()\n\
    cli.connect('127.0.0.1')\n\
    cli.get('test.txt')";
static PyObject * tftpc_get(PyTFtpClientObject *obj, PyObject *args);

static char put_doc[] =
"put(localfile[, remotefile]) -> bytes-sent.\n\
\n\
Put the specified file.\n\
The first parameter is the path of local file.\n\
The second parameter is the optional path of remote file. If it is omitted,\n\
use the first parameter as the path of remote file.\n\
For example:\n\
    cli = tftpc.TFtpClient()\n\
    cli.connect('127.0.0.1')\n\
    cli.put('test.txt')";
static PyObject * tftpc_put(PyTFtpClientObject *obj, PyObject *args);
static PyMethodDef tftpc_methods [] = {
    { "ascii", (PyCFunction)tftpc_ascii, METH_NOARGS, ascii_doc },
    { "binary", (PyCFunction)tftpc_binary, METH_NOARGS, binary_doc },
    { "connect", (PyCFunction)tftpc_connect, METH_VARARGS, connect_doc},
    { "get", (PyCFunction)tftpc_get, METH_VARARGS, get_doc },
    { "put", (PyCFunction)tftpc_put, METH_VARARGS, put_doc },
    { NULL, NULL }
};

#define OFF(x)  offsetof(PyTFtpClientObject, x)

static PyMemberDef tftpc_memberlist[] = {
    { "port", T_INT, OFF(port), RO,
      "Connection port" },
    { "mode", T_INT, OFF(mode), RO,
      "Transfer mode (0 = binary, 1 = ascii" },
    { NULL }
};

static PyObject *tftpc_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static int tftpc_init(PyObject *self, PyObject *args, PyObject *kwds);
static void tftpc_dealloc(PyTFtpClientObject *obj);
static char PyTFtpClientType__doc__[] =
"TFtpClient() -> TFtpClient object\n\
\n\
Create a tftp client object.";
PyTypeObject PyTFtpClientType = {
    PyObject_HEAD_INIT(&PyType_Type)
    0,                                       /* ob_size */
    "tftpc",                                 /* tp_name */
    sizeof(PyTFtpClientObject),              /* tp_basicsize */
    0,                                       /* tp_itemsize */
    (destructor)tftpc_dealloc,               /* tp_dealloc */
    0,                                       /* tp_print */
    0,                                       /* tp_getattr */
    0,                                       /* tp_setattr */
    0,                                       /* tp_compare */
    0,                                       /* tp_repr */
    0,                                       /* tp_as_number */
    0,                                       /* tp_as_sequence */
    0,                                       /* tp_as_mapping */
    0,                                       /* tp_hash */
    0,                                       /* tp_call */
    0,                                       /* tp_str */
    PyObject_GenericGetAttr,                 /* tp_getattro */
    0,                                       /* tp_setattro */
    0,                                       /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,/* tp_flags */
    PyTFtpClientType__doc__,                 /* tp_doc */
    0,                                       /* tp_traverse */
    0,                                       /* tp_clear */
    0,                                       /* tp_richcompare */
    0L,                                      /* tp_weaklistoffset */
    0,                                       /* tp_iter */
    0,                                       /* tp_iternext */
    tftpc_methods,                           /* tp_methods */
    tftpc_memberlist,                        /* tp_members */
    0,                                       /* tp_getset */
    0,                                       /* tp_base */
    0,                                       /* tp_dict */
    0,                                       /* tp_descr_get */
    0,                                       /* tp_descr_set */
    0,                                       /* tp_dictoffset */
    tftpc_init,                              /* tp_init */
    PyType_GenericAlloc,                     /* tp_alloc */
    tftpc_new,                               /* tp_new */
    _PyObject_Del,                           /* tp_free */
};

static PyMethodDef tftpcMethods[] = {
    { NULL, NULL, 0, NULL }
};
void inittftpc(void) {
    PyObject  *module, *dict;

    module = Py_InitModule("tftpc", tftpcMethods);
    dict = PyModule_GetDict(module);

    PyExc_TFtpError = PyErr_NewException("tftpc.tftp_error", NULL, NULL);
    if (PyExc_TFtpError == NULL)  return ;
    PyDict_SetItemString(dict, "tftp_error", PyExc_TFtpError);

    PyExc_GetHostByName = PyErr_NewException("tftpc.gethostbyname_err",
					     PyExc_TFtpError, NULL);
    if (PyExc_GetHostByName == NULL)  return ;
    PyDict_SetItemString(dict, "gethostbyname_err", PyExc_GetHostByName);

    PyExc_GetServByName = PyErr_NewException("tftpc.getservbyname_err",
					     PyExc_TFtpError, NULL);
    if (PyExc_GetServByName == NULL)  return ;
    PyDict_SetItemString(dict, "getservbyname_err", PyExc_GetServByName);

    PyExc_Socket = PyErr_NewException("tftpc.socket_err",
				      PyExc_TFtpError, NULL);
    if (PyExc_Socket == NULL)  return ;
    PyDict_SetItemString(dict, "socket_err", PyExc_Socket);

    PyExc_Bind = PyErr_NewException("tftpc.bind_err",
				    PyExc_TFtpError, NULL);
    if (PyExc_Bind == NULL)  return ;
    PyDict_SetItemString(dict, "bind_err", PyExc_Bind);

    PyExc_Connect = PyErr_NewException("tftpc.connect_err",
				       PyExc_TFtpError, NULL);
    if (PyExc_Connect == NULL)  return ;
    PyDict_SetItemString(dict, "connect_err", PyExc_Connect);

    if ((sp = getservbyname("tftp", "udp")) == NULL)
	return ;

    if (PyDict_SetItemString(dict, "TFtpClient",
			     (PyObject *)&PyTFtpClientType) != 0)
	return ;
}

static PyObject *tftpc_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
    PyTFtpClientObject *obj;

    obj = (PyTFtpClientObject *)type->tp_alloc(type, 0);
    if (obj != NULL) {
	obj->socketfd = -1;
	obj->port = (sp == NULL) ? 0 : sp->s_port;
	obj->connected = 0;
	obj->mode = 0;
	bzero(&(obj->peeraddr), sizeof(obj->peeraddr));
    }
    return (PyObject *)obj;
}
static int tftpc_init(PyObject *self, PyObject *args, PyObject *kwds) {
    int                 socketfd;
    struct sockaddr_in  s_in;
    PyTFtpClientObject *s = (PyTFtpClientObject *)self;

    if (sp == NULL) {
	PyErr_SetString(PyExc_GetServByName, "tftp service is not available.");
	return -1;
    }

    socketfd = socket(AF_INET, SOCK_DGRAM, 0);
    if (socketfd < 0) {
	PyErr_SetFromErrno(PyExc_Socket);
	return -1;
    }
    bzero((char *)&s_in, sizeof(s_in));
    s_in.sin_family = AF_INET;
    if (bind(socketfd, (struct sockaddr *)&s_in, sizeof(s_in)) < 0) {
	PyErr_SetFromErrno(PyExc_Bind);
	close(socketfd);
	return -1;
    }

    s->socketfd = socketfd;
    return 0;
}
static void tftpc_dealloc(PyTFtpClientObject *obj) {
    if (obj->socketfd >= 0)
	close(obj->socketfd);
    PyObject_Del(obj);
}

static PyObject * tftpc_ascii(PyTFtpClientObject *obj) {
    obj->mode = 1;
    Py_INCREF(Py_None);
    return Py_None;
}
static PyObject * tftpc_binary(PyTFtpClientObject *obj) {
    obj->mode = 0;
    Py_INCREF(Py_None);
    return Py_None;
}
static PyObject * tftpc_connect(PyTFtpClientObject *obj, PyObject *args) {
    struct hostent *host;
    char  *addr = NULL;
    int    port = 0;
    if (!PyArg_ParseTuple(args, "s|i:connect", &addr, port))
	return NULL;
    host = gethostbyname(addr);
    if (host == 0) {
	PyErr_SetString(PyExc_GetHostByName, "Unknown host.");
	return NULL;
    }
    obj->port = (port == 0) ? sp->s_port : port;
    obj->peeraddr.sin_family = host->h_addrtype;
    bcopy(host->h_addr, &(obj->peeraddr.sin_addr), host->h_length);
    obj->connected = 1;
    Py_INCREF(Py_None);
    return Py_None;
}
static PyObject * tftpc_get(PyTFtpClientObject *obj, PyObject *args) {
    int    localfd;
    int    amount;
    char  *remote_file = NULL;
    char  *local_file = NULL;
    if (!PyArg_ParseTuple(args, "s|s:get", &remote_file, &local_file))
	return NULL;
    if (!obj->connected) {
	PyErr_SetString(PyExc_Connect, "Not connected yet.");
	return NULL;
    }
    if (local_file == NULL)  local_file = remote_file;
    localfd = open(local_file, O_WRONLY|O_CREAT|O_TRUNC, 0666);
    if (localfd < 0) {
	PyErr_SetFromErrno(PyExc_IOError);
	return NULL;
    }
    obj->peeraddr.sin_port = obj->port;
    amount = tftp_recvfile(obj->socketfd, &(obj->peeraddr),
			   localfd, remote_file,
			   obj->mode ? "netascii" : "octet");
    return Py_BuildValue("i", amount);
}
static PyObject * tftpc_put(PyTFtpClientObject *obj, PyObject *args) {
    int    localfd;
    int    amount;
    char  *local_file = NULL;
    char  *remote_file = NULL;
    if (!PyArg_ParseTuple(args, "s|s:put", &local_file, &remote_file))
	return NULL;
    if (!obj->connected) {
	PyErr_SetString(PyExc_Connect, "Not connected yet.");
	return NULL;
    }
    if (remote_file == NULL)  remote_file = local_file;
    localfd = open(local_file, O_RDONLY);
    if (localfd < 0) {
	PyErr_SetFromErrno(PyExc_IOError);
	return NULL;
    }
    obj->peeraddr.sin_port = obj->port;
    amount = tftp_sendfile(obj->socketfd, &(obj->peeraddr),
			   localfd, remote_file,
			   obj->mode ? "netascii" : "octet");			   
    return Py_BuildValue("i", amount);
}
