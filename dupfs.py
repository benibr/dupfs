#!/usr/bin/env python

from __future__ import with_statement

import os
import sys
import errno
import argparse

from fuse import FUSE, FuseOSError, Operations, fuse_get_context


class dupfs(Operations):

    fh_dup_lookup = {}

    def __init__(self, root1, root2):
        self.root1 = root1
        self.root2 = root2

    # Helpers
    # =======
    def _full_path_root1(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root1, partial)
        return path

    def _full_path_root2(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root2, partial)
        return path

    # Filesystem methods
    # ==================

    # read function, single fs access

    def getattr(self, path, fh=None):
        # get method doesn't need root1
        full_path = self._full_path_root2(path)
        st = os.lstat(full_path)
        return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                     'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))

    def readdir(self, path, fh):
        # read method doesn't need root1
        full_path = self._full_path_root2(path)
        dirents = ['.', '..']
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        for r in dirents:
            yield r

    def readlink(self, path):
        # read method doesn't need root1
        pathname = os.readlink(self._full_path_root2(path))
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            return os.path.relpath(pathname, self.root)
        else:
            return pathname

    # write functions, double fs access
    def access(self, path, mode):
        full_path = self._full_path_root1(path)
        if not os.access(full_path, mode):
            raise FuseOSError(errno.EACCES)
        full_path = self._full_path_root2(path)
        if not os.access(full_path, mode):
            raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        full_path = self._full_path_root1(path)
        os.chmod(full_path, mode)
        full_path = self._full_path_root2(path)
        return os.chmod(full_path, mode)

    def chown(self, path, uid, gid):
        full_path = self._full_path_root1(path)
        os.chown(full_path, uid, gid)
        full_path = self._full_path_root2(path)
        return os.chown(full_path, uid, gid)

    def mknod(self, path, mode, dev):
        os.mknod(self._full_path_root1(path), mode, dev)
        return os.mknod(self._full_path_root2(path), mode, dev)

    def rmdir(self, path):
        full_path = self._full_path_root1(path)
        os.rmdir(full_path)
        full_path = self._full_path_root2(path)
        return os.rmdir(full_path)

    def mkdir(self, path, mode):
        os.mkdir(self._full_path_root1(path), mode)
        return os.mkdir(self._full_path_root2(path), mode)

    def statfs(self, path):
        # stat method doesn't need root1
        full_path = self._full_path_root2(path)
        stv = os.statvfs(full_path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))

    def unlink(self, path):
        os.unlink(self._full_path_root1(path))
        return os.unlink(self._full_path_root2(path))

    def symlink(self, name, target):
        os.symlink(target, self._full_path_root1(name))
        return os.symlink(target, self._full_path_root2(name))

    def rename(self, old, new):
        os.rename(self._full_path_root1(old), self._full_path_root1(new))
        return os.rename(self._full_path_root2(old), self._full_path_root2(new))

    def link(self, target, name):
        os.link(self._full_path_root1(name), self._full_path_root1(target))
        return os.link(self._full_path_root2(name), self._full_path_root2(target))

    def utimens(self, path, times=None):
        return os.utime(self._full_path_root2(path), times)

    # File methods
    # ============

    def open(self, path, flags):
        # read method doesn't need root1
        full_path = self._full_path_root1(path)
        fh_r1 = os.open(full_path, flags)
        full_path = self._full_path_root2(path)
        fh_r2 = os.open(full_path, flags)
        self.fh_dup_lookup[fh_r2] = fh_r1
        return fh_r2

    def create(self, path, mode, fi=None):
        uid, gid, pid = fuse_get_context()
        full_path = self._full_path_root1(path)
        fd = os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)
        os.chown(full_path,uid,gid) #chown to context uid & gid
        full_path = self._full_path_root2(path)
        fd = os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)
        os.chown(full_path,uid,gid) #chown to context uid & gid
        return fd

    def read(self, path, length, offset, fh):
        # read method doesn't need root1
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        # FIXME: this is probably super racy
        fh1=fh-1
        print(fh1)
        os.lseek(fh1, offset, os.SEEK_SET)
        os.write(fh1, buf)
        print(fh)
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    def truncate(self, path, length, fh=None):
        full_path = self._full_path_root1(path)
        with open(full_path, 'r+') as f:
            f.truncate(length)
        full_path = self._full_path_root2(path)
        with open(full_path, 'r+') as f:
            f.truncate(length)

    def flush(self, path, fh):
        # FIXME: how relevant is the root1 here?
        return os.fsync(fh)

    def release(self, path, fh):
        # FIXME: how relevant is the root1 here?
        return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        # FIXME: how relevant is the root1 here?
        return self.flush(path, fh)


def main():
    parser = argparse.ArgumentParser(description='duplicate filesystem I/O to a secondary location')

    # Optional parameter
    parser.add_argument('--primary', type=str, help='The primary directory where the I/O is written to.')
    parser.add_argument('--secondary', type=str, help='The directory where the I/O is duplicated to.')
    #parser.add_argument('--mirror', type=str, required=True, help='Same as --secondary')
    parser.add_argument('--mountpoint', type=str, help='The mountpoint where dupfs is mounted to.')

    # Positional parameter

    args = parser.parse_args()

    # Print the arguments for demonstration purposes
    print(f"primary: {args.primary}")
    print(f"secondary: {args.secondary}")
    print(f"mountpoint: {args.mountpoint}")

    FUSE(dupfs(args.primary, args.secondary), args.mountpoint, nothreads=True, foreground=True, allow_other=True, nonempty=True)

if __name__ == '__main__':
    main()
