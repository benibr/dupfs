#!/usr/bin/env python

from __future__ import with_statement

import os
import sys
import errno

from fuse import FUSE, FuseOSError, Operations, fuse_get_context


class dupfs(Operations):
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

    def chown(self, path, path2, uid, gid):
        full_path = self._full_path_root1(path)
        os.chown(full_path, uid, gid)
        full_path = self._full_path_root2(path)
        return os.chown(full_path, uid, gid)

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
        full_path = self._full_path_root2(path)
        return os.open(full_path, flags)

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
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    def truncate(self, path, length, fh=None):
        full_path = self._full_path_root2(path)
        with open(full_path, 'r+') as f:
            f.truncate(length)

    def flush(self, path, fh):
        return os.fsync(fh)

    def release(self, path, fh):
        return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        return self.flush(path, fh)


def main(root1, root2, mountpoint):
    FUSE(dupfs(root1, root2), mountpoint, nothreads=True, foreground=True, allow_other=True)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
