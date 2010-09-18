#include <sys/types.h>
#include <sys/ioctl.h>
#include <sys/mount.h>
#include <sys/swap.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include "loop.h"
#include <stdio.h>
#include <stdlib.h>
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
int main()
{
    char *err = NULL;
    int rc;
    rc = check_loopdev_unused("/dev/loop1", &err);
    if(err != NULL){
        printf("%d: %s", rc, err);
    }else{
        printf("%d: NULL", rc);
    }
}
