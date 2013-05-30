#!/bin/bash

die() { error "$@"; exit 1; }

track_mount() {
  mount "$@" && CHROOT_ACTIVE_MOUNTS=("$2" "${CHROOT_ACTIVE_MOUNTS[@]}")
}

api_fs_mount() {
  CHROOT_ACTIVE_MOUNTS=()
  { mountpoint -q "$1" || track_mount "$1" "$1" --bind; } &&
  track_mount proc "$1/proc" -t proc -o nosuid,noexec,nodev &&
  track_mount sys "$1/sys" -t sysfs -o nosuid,noexec,nodev &&
  track_mount udev "$1/dev" -t devtmpfs -o mode=0755,nosuid &&
  track_mount devpts "$1/dev/pts" -t devpts -o mode=0620,gid=5,nosuid,noexec &&
  track_mount shm "$1/dev/shm" -t tmpfs -o mode=1777,nosuid,nodev &&
  track_mount run "$1/run" -t tmpfs -o nosuid,nodev,mode=0755 &&
  track_mount tmp "$1/tmp" -t tmpfs -o mode=1777,strictatime,nodev,nosuid
}

api_fs_umount() {
  umount "${CHROOT_ACTIVE_MOUNTS[@]}"
}

usage() {
  cat <<EOF
usage: ${0##*/} chroot-dir [command]

    -h             Print this help message

If 'command' is unspecified, ${0##*/} will launch /bin/sh.

EOF
}

if [[ -z $1 || $1 = @(-h|--help) ]]; then
  usage
  exit $(( $# ? 0 : 1 ))
fi

(( EUID == 0 )) || die 'This script must be run with root privileges'
chrootdir=$1
shift

[[ -d $chrootdir ]] || die "Can't create chroot on non-directory %s" "$chrootdir"

trap '{ api_fs_umount "$chrootdir"; umount "$chrootdir/etc/resolv.conf"; } 2>/dev/null' EXIT

api_fs_mount "$chrootdir" || die "failed to setup API filesystems in chroot %s" "$chrootdir"
track_mount /etc/resolv.conf "$chrootdir/etc/resolv.conf" --bind

SHELL=/bin/sh chroot "$chrootdir" "$@"

