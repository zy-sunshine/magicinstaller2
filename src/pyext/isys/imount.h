#ifndef H_IMOUNT
#define H_IMOUNT

#define IMOUNT_ERR_ERRNO          1
#define IMOUNT_ERR_OTHER          2
#define IMOUNT_ERR_MODE           3
#define IMOUNT_ERR_PERMISSIONS    4
#define IMOUNT_ERR_SYSTEM         5
#define IMOUNT_ERR_MOUNTINTERNAL  6
#define IMOUNT_ERR_USERINTERRUPT  7
#define IMOUNT_ERR_MTAB           8
#define IMOUNT_ERR_MOUNTFAILURE   9
#define IMOUNT_ERR_PARTIALSUCC    10

#include <sys/mount.h>		/* for umount() */

#define IMOUNT_RDONLY  1
#define IMOUNT_BIND    2
#define IMOUNT_REMOUNT 4

#define IMOUNT_MODE_MOUNT  1
#define IMOUNT_MODE_UMOUNT 2
#define IMOUNT_MODE_BIND   3

//int doPwMount(char * dev, char * where, char * fs, int rdonly, int istty,
//              char * acct, char * pw, int bindmnt);
//int mkdirChain(char * origChain);

int doBindMount(char* path, char *where, char **err);
int doPwMount(char *dev, char *where, char *fs, char *options, char **err);
int doPwUmount(char *where, char **err);
int mkdirChain(char * origChain);
int mountMightSucceedLater(int mountRc);

#endif
