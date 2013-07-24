#define _XOPEN_SOURCE 500
#include <iostream>
#include <ftw.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <limits.h>
#include <stdarg.h>
using namespace std;

typedef struct Log_s {
    FILE *logd;
    char logfpath[PATH_MAX];
} Log_t;

Log_t* log;

int Log_Construct(Log_t** _self){
    Log_t *self;
    if ( ((*_self) = (Log_t*)malloc(sizeof(Log_t))) == NULL ) {
        goto err1;
    }
    self = *_self;
    self->logd = NULL;
    strcpy(self->logfpath, "/var/log/fnotify.log");
    return 0;
err1:
    printf("ConstructLog failed");
    return -1;
}

void Log_Destruct(Log_t** _self){
    if (*_self) {
        free(*_self);
        *_self = NULL;
    }
}

int Log_Open(Log_t* self){
    if ( (self->logd = fopen(self->logfpath, "a+")) == NULL ){
        printf("open log %s failed", self->logfpath);
        goto err1;
    }
    return 0;
err2:
    fclose(self->logd);
err1:
    return -1;
}

void Log_Close(Log_t* self){
    if (self->logd) {
        fclose(self->logd);
        self->logd = NULL;
    }
}

void Log_Write(Log_t* self, const char* fmt, ...){
    va_list args;
    char buf[4096];
    va_start(args, fmt);
    vsnprintf(buf, sizeof(buf), fmt, args);
    va_end(args);
    if (self->logd) {
        fwrite(buf, strlen(buf), 1, self->logd);
        fflush(self->logd);
    } else {
        printf(buf);
    }
}

typedef struct NotifyFile_s
{
    int ifd;
    char *path;
    bool isdir;
} NotifyFile_t;

NotifyFile_t* NotifyFile_Instance() {
    NotifyFile_t* nfile = (NotifyFile_t*)malloc(sizeof(NotifyFile_t));
    memset(nfile, 0, sizeof(NotifyFile_t));
    return nfile;
}

void NotifyFile_Desctruct(NotifyFile_t** self) {
    if ((*self)->path){
        free((*self)->path);
    }
    free(*self);
    *self = NULL;
}

#include <list>
list<NotifyFile_t*> dlist;

static int
display_info(const char *fpath, const struct stat *sb,
             int tflag, struct FTW *ftwbuf)
{
    NotifyFile_t * tmpf;
    if (tflag == FTW_D || tflag == FTW_DNR || tflag == FTW_DP){
        tmpf = NotifyFile_Instance();
        dlist.push_back(tmpf);
        tmpf->path = (char*)malloc(PATH_MAX);
        strncpy(tmpf->path, fpath, PATH_MAX);
    } else if (tflag == FTW_SLN) {
        printf("[EE] %s\n", fpath);
    }
    //printf("%-3s %2d %7jd   %-40s %d %s\n",
    //    (tflag == FTW_D) ?   "d"   : (tflag == FTW_DNR) ? "dnr" :
    //    (tflag == FTW_DP) ?  "dp"  : (tflag == FTW_F) ?   "f" :
    //    (tflag == FTW_NS) ?  "ns"  : (tflag == FTW_SL) ?  "sl" :
    //    (tflag == FTW_SLN) ? "sln" : "???",
    //    ftwbuf->level, (intmax_t) sb->st_size,
    //    fpath, ftwbuf->base, fpath + ftwbuf->base);
    return 0;           /* To tell nftw() to continue */
}

#include <sys/inotify.h>
#include <error.h>
#include <errno.h>
#define ERROR(text) error(1, errno, "%s", text)

typedef struct EventMask_s {
    int        flag;
    const char *name;

} EventMask;

int freadsome(void *dest, size_t remain, FILE *file)
{
    char *offset = (char*)dest;
    while (remain) {
        int n = fread(offset, 1, remain, file);
        if (n==0) {
            return -1;
        }

        remain -= n;
        offset += n;
    }
    return 0;
}


char *find_ifd_path(int ifd)
{
    list<NotifyFile_t*>::iterator i;
    for (i = dlist.begin(); i != dlist.end(); ++i) {
        if ((*i)->ifd == ifd) {
            return (*i)->path;
        }
    }
    return NULL;
}

int notify_directories(){
    EventMask event_masks[] = {
           {IN_ACCESS        , "IN_ACCESS"}        ,
           {IN_ATTRIB        , "IN_ATTRIB"}        ,
           {IN_CLOSE_WRITE   , "IN_CLOSE_WRITE"}   ,
           {IN_CLOSE_NOWRITE , "IN_CLOSE_NOWRITE"} ,
           {IN_CREATE        , "IN_CREATE"}        ,
           {IN_DELETE        , "IN_DELETE"}        ,
           {IN_DELETE_SELF   , "IN_DELETE_SELF"}   ,
           {IN_MODIFY        , "IN_MODIFY"}        ,
           {IN_MOVE_SELF     , "IN_MOVE_SELF"}     ,
           {IN_MOVED_FROM    , "IN_MOVED_FROM"}    ,
           {IN_MOVED_TO      , "IN_MOVED_TO"}      ,
           {IN_OPEN          , "IN_OPEN"}          ,

           {IN_DONT_FOLLOW   , "IN_DONT_FOLLOW"}   ,
           {IN_EXCL_UNLINK   , "IN_EXCL_UNLINK"}   ,
           {IN_MASK_ADD      , "IN_MASK_ADD"}      ,
           {IN_ONESHOT       , "IN_ONESHOT"}       ,
           {IN_ONLYDIR       , "IN_ONLYDIR"}       ,

           {IN_IGNORED       , "IN_IGNORED"}       ,
           {IN_ISDIR         , "IN_ISDIR"}         ,
           {IN_Q_OVERFLOW    , "IN_Q_OVERFLOW"}    ,
           {IN_UNMOUNT       , "IN_UNMOUNT"}       ,
    };

    int monitor = inotify_init();
    if ( -1 == monitor ) {
        ERROR("monitor");
    }

    list<NotifyFile_t*>::iterator i;
    for( i = dlist.begin(); i != dlist.end(); i++) {
        int watcher = inotify_add_watch(monitor, (*i)->path, IN_ALL_EVENTS);
        (*i)->ifd = watcher;
        if ( -1 == watcher  ) {
            ERROR("inotify_add_watch");
        } else {
            //printf("add directory %s", (*i)->path);
        }
    }

    FILE *monitor_file = fdopen(monitor, "r");
    char name[1024];
    char last_path[PATH_MAX];
    char abspath[PATH_MAX];
    char* tmpfp;
    /* event:inotify_event -> name:char[event.len] */
    printf("notify directories success!!\n");
    fflush(stdout);
    while (1) {
        inotify_event event;
        if ( -1 == freadsome(&event, sizeof(event), monitor_file) ) {
            ERROR("freadsome");
        }
        if (event.len) {
            freadsome(name, event.len, monitor_file);
            //printf("#@# %s", name);
        } else {
            //printf(name, "FD: %d\n", event.wd);
        }

        tmpfp = find_ifd_path(event.wd);
        strcpy(abspath, tmpfp);
        if (event.len) {
            strcat(abspath, "/");
            strcat(abspath, name);
        } else {
            // print path only
        }
        //printf("abspath: %s", abspath);
        if (strcmp(abspath, last_path) != 0) {
            Log_Write(log, "%s\n", abspath);
            puts(abspath);
            strcpy(last_path, abspath);
        }

        /* 显示event的mask的含义 */
        for (int i=0; i<sizeof(event_masks)/sizeof(EventMask); ++i) {
            if (event.mask & event_masks[i].flag) {
                printf("\t%s\n", event_masks[i].name);
            }
        }
    }
    // destruct dlist
    for( i = dlist.begin(); i != dlist.end(); i++) {
        NotifyFile_Desctruct(&(*i));
    }
}

int
main(int argc, char *argv[])
{
    int flags = 0;
    int i;
    Log_Construct(&log);
    if (Log_Open(log)) {
        goto err1;
    }

    //if (argc > 2 && strchr(argv[2], 'd') != NULL)
    //    flags |= FTW_DEPTH;
    //if (argc > 2 && strchr(argv[2], 'p') != NULL)
    //    flags |= FTW_PHYS;
    flags |= FTW_PHYS;
    if (argc < 2) {
        if (nftw(".", display_info, 20, flags)
                == -1) {
            perror("nftw");
            exit(EXIT_FAILURE);
        }
    } else {
        for (i = 1; i < argc; ++i) {
            if (nftw(argv[i], display_info, 20, flags)
                    == -1) {
                perror("nftw");
                exit(EXIT_FAILURE);
            }
        }
    }
    notify_directories();

    Log_Close(log);
    Log_Destruct(&log);

    return 0;
err1:
    Log_Destruct(&log);
    return -1;

}
