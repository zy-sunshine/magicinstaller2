#include <stdio.h>
#include "imount.h"

//mountCommandWrapper()
int main()
{
    char *err = NULL, * fs, * device, * mntpoint, *flags = NULL;
    int rc;
    //int doPwMount(char *dev, char *where, char *fs, char *options, char **err);
    //device = "/mnt/sda12/MagicLinux-2.5-1.iso";
    device = "/dev/sda12";
    mntpoint = "/tmpfs/sda12";
    fs = "ntfs";
    //fs = "iso9660";
    rc = doPwMount(device, mntpoint, fs, flags, &err);
    printf("%s", err);
}
