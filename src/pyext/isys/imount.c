#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#include <sys/wait.h>

#include "imount.h"

#define _(foo) foo

static int mkdirIfNone(char * directory);
static int check_special_mountprog(char * dev, char * where, char * fs,
                                   char * filteropts, int *status);

int doPwMount(char * dev, char * where, char * fs, int rdonly, int istty,
              char * acct, char * pw, int bindmnt) { 
    char * buf = NULL;
    int isnfs = 0;
    char * mount_opt = NULL;
    long int flag;
    char * chptr;
    int rc;

    if (check_special_mountprog(dev, where, fs,
                                rdonly ? "ro" : NULL,
                                &rc)) {
        return rc ? IMOUNT_ERR_OTHER : 0;
    }
        
    if (!strcmp(fs, "nfs")) isnfs = 1;

    /*logMessage("mounting %s on %s as type %s", dev, where, fs);*/

    if (!strcmp(fs, "smb")) {
#if 0 /* disabled for now */
	mkdirChain(where);

	if (!acct) acct = "guest";
	if (!pw) pw = "";

	buf = alloca(strlen(dev) + 1);
	strcpy(buf, dev);
	chptr = buf;
	while (*chptr && *chptr != ':') chptr++;
	if (!*chptr) {
	    /*logMessage("bad smb mount point %s", where);*/
	    return IMOUNT_ERR_OTHER;
	} 
	
	*chptr = '\0';
	chptr++;

#ifdef __i386__
	/*logMessage("mounting smb filesystem from %s path %s on %s",
			buf, chptr, where);*/
	return smbmount(buf, chptr, acct, pw, "localhost", where);
#else 
	errorWindow("smbfs only works on Intel machines");
#endif
#endif /* disabled */
    } else {
	if (mkdirChain(where))
	    return IMOUNT_ERR_ERRNO;

  	if (!isnfs && (*dev == '/' || !strcmp(dev, "none"))) {
	    buf = dev;
	} else if (!isnfs) {
	    buf = alloca(200);
	    strcpy(buf, "/tmp/");
	    strcat(buf, dev);
	} else {
#ifndef DISABLE_NETWORK
	    char * extra_opts = NULL;
	    int flags = 0;

	    buf = dev;
	    /*logMessage("calling nfsmount(%s, %s, &flags, &extra_opts, &mount_opt)",
			buf, where);*/

	    if (nfsmount(buf, where, &flags, &extra_opts, &mount_opt)) {
		/*logMessage("\tnfsmount returned non-zero");*/
		/*fprintf(stderr, "nfs mount failed: %s\n",
			nfs_error());*/
		return IMOUNT_ERR_OTHER;
	    }
#endif
	}
	flag = MS_MGC_VAL;
	if (rdonly)
	    flag |= MS_RDONLY;
        if (bindmnt)
            flag |= MS_BIND;

	if (!strncmp(fs, "vfat", 4))
	    mount_opt="check=relaxed";
	#ifdef __sparc__
	if (!strncmp(fs, "ufs", 3))
	    mount_opt="ufstype=sun";
	#endif

	/*logMessage("calling mount(%s, %s, %s, %ld, %p)", buf, where, fs, 
			flag, mount_opt);*/

	if (mount(buf, where, fs, flag, mount_opt)) {
 	    return IMOUNT_ERR_ERRNO;
	}
    }

    return 0;
}

int mkdirChain(char * origChain) {
    char * chain;
    char * chptr;

    chain = alloca(strlen(origChain) + 1);
    strcpy(chain, origChain);
    chptr = chain;

    while ((chptr = strchr(chptr, '/'))) {
	*chptr = '\0';
	if (mkdirIfNone(chain)) {
	    *chptr = '/';
	    return IMOUNT_ERR_ERRNO;
	}

	*chptr = '/';
	chptr++;
    }

    if (mkdirIfNone(chain))
	return IMOUNT_ERR_ERRNO;

    return 0;
}

static int mkdirIfNone(char * directory) {
    int rc, mkerr;
    char * chptr;

    /* If the file exists it *better* be a directory -- I'm not going to
       actually check or anything */
    if (!access(directory, X_OK)) return 0;

    /* if the path is '/' we get ENOFILE not found" from mkdir, rather
       then EEXIST which is weird */
    for (chptr = directory; *chptr; chptr++)
        if (*chptr != '/') break;
    if (!*chptr) return 0;

    rc = mkdir(directory, 0755);
    mkerr = errno;

    if (!rc || mkerr == EEXIST) return 0;

    return IMOUNT_ERR_ERRNO;
}

/* Borrowed from util-linux 2.12r and hack
 * check_special_mountprog()
 *      If there is a special mount program for this type, exec it.
 * returns: 0: no exec was done, 1: exec was done, status has result
 */

static int check_special_mountprog(char * dev, char * where, char * fs,
				   char * filteropts, int *status)
{
	char mountprog[120];
	struct stat statbuf;
	pid_t pid;

	if (fs && strlen(fs) < 100) {
		sprintf(mountprog, "/sbin/mount.%s", fs);
		if (stat(mountprog, &statbuf) == 0) {
			pid = fork();
			if (pid == 0) {
				const char *mountargs[10];
				int i = 0;

				mountargs[i++] = mountprog;
				mountargs[i++] = dev;
				mountargs[i++] = where;
				/* (ignore)
				   if (nomtab)
				   mountargs[i++] = "-n";
				   if (verbose)
				   mountargs[i++] = "-v";
				*/
				if (filteropts && *filteropts) {
					mountargs[i++] = "-o";
					mountargs[i++] = filteropts;
				}
				mountargs[i] = NULL;
				execv(mountprog, (char **) mountargs);
				exit(1);       /* exec failed */
			} else if (pid != -1) {
				waitpid(pid, status, 0);
				*status = (WIFEXITED(*status) ? \
					   WEXITSTATUS(*status) : -1);
				return 1;
			} else {
				//bb_perror_msg_and_die("fork failed");
				*status = -1;
				return 1;
			}
		}
	}
	return 0;
}

