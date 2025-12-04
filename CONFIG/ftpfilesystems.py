from pyftpdlib.filesystems import AbstractedFS
from django.core.files.storage import default_storage as default_storage_lazy
from django.core.files.base import ContentFile
from django.conf import settings
import posixpath
import time
import stat as stat_module


class SimpleStat:
    def __init__(self, st_mode=0, st_size=0, st_mtime=0, st_uid=0, st_gid=0):
        self.st_mode = st_mode
        self.st_size = st_size
        self.st_mtime = st_mtime
        self.st_uid = st_uid
        self.st_gid = st_gid


class DjangoStorageAbstractedFS(AbstractedFS):
    """AbstractedFS that uses Django's DEFAULT_FILE_STORAGE backend.

    This implementation provides a minimal file-system interface backed
    by Django's storage engine (S3 when configured via django-storages).

    Limitations:
    - S3 is object storage so directory semantics are driven by prefixes.
    - Some operations (rename directories, utime) are implemented in a
      simple way and may be expensive or partial.
    """

    def __init__(self, root, cmd_channel):
        # root is not used for S3, but keep the same interface as AbstractedFS
        super().__init__(root, cmd_channel)
        self._root = '/'

    # --- path translation utilities
    def ftp2fs(self, ftppath):
        """Map an ftp path to a storage name/key.

        This returns a normalized key relative to the storage location: e.g.
        ftppath='/shahed/myfile.txt' -> 'shahed/myfile.txt'.
        """
        p = self.ftpnorm(ftppath)
        key = p.lstrip('/')
        return key

    def fs2ftp(self, fspath):
        if fspath.startswith('/'):
            return fspath
        return '/' + fspath

    # --- list and stat
    def listdir(self, path):
        key = self.ftp2fs(path)
        from django.core.files.storage import default_storage
        return default_storage.listdir(key)

    def listdirinfo(self, path):
        key = self.ftp2fs(path)
        directories, files = self.listdir(path)
        listing = []
        for d in directories:
            listing.append((d, self._make_stat(key, d, is_dir=True)))
        for f in files:
            listing.append((f, self._make_stat(key, f, is_dir=False)))
        return listing

    def _make_stat(self, prefix, name, is_dir=False):
        st = SimpleStat()
        if is_dir:
            st.st_mode = stat_module.S_IFDIR | 0o755
            st.st_size = 0
            st.st_mtime = int(time.time())
        else:
            key = posixpath.join(prefix, name) if prefix else name
            try:
                from django.core.files.storage import default_storage
                st.st_size = int(default_storage.size(key))
            except Exception:
                st.st_size = 0
            try:
                from django.core.files.storage import default_storage
                mtime = default_storage.get_modified_time(key)
                try:
                    st.st_mtime = int(mtime.timestamp())
                except Exception:
                    st.st_mtime = int(time.mktime(mtime.timetuple()))
            except Exception:
                st.st_mtime = int(time.time())
            st.st_mode = stat_module.S_IFREG | 0o644
        st.st_uid = 1000
        st.st_gid = 1000
        return st

    # --- file operations
    def open(self, filename, mode='r'):
        key = self.ftp2fs(filename)
        # Default storage expects bytes mode for read/write where appropriate
        from django.core.files.storage import default_storage
        return default_storage.open(key, mode)

    def remove(self, path):
        key = self.ftp2fs(path)
        from django.core.files.storage import default_storage
        return default_storage.delete(key)

    def mkdir(self, path):
        # S3 directories are pseudo; create a zero-byte object with trailing slash
        key = self.ftp2fs(path).rstrip('/') + '/'
        from django.core.files.storage import default_storage
        default_storage.save(key, ContentFile(b''))

    def rmdir(self, path):
        # Remove the placeholder object if present; does not remove objects underneath.
        key = self.ftp2fs(path).rstrip('/') + '/'
        from django.core.files.storage import default_storage
        default_storage.delete(key)

    def isfile(self, path):
        key = self.ftp2fs(path)
        if not key:
            return False
        from django.core.files.storage import default_storage
        return default_storage.exists(key)

    def isdir(self, path):
        key = self.ftp2fs(path)
        if not key:
            return True
        from django.core.files.storage import default_storage
        try:
            directories, files = default_storage.listdir(key)
            return True
        except Exception:
            return False

    def exists(self, path):
        key = self.ftp2fs(path)
        if not key:
            return True
        from django.core.files.storage import default_storage
        return default_storage.exists(key)

    def getsize(self, path):
        key = self.ftp2fs(path)
        from django.core.files.storage import default_storage
        return default_storage.size(key)

    def getmtime(self, path):
        key = self.ftp2fs(path)
        from django.core.files.storage import default_storage
        mtime = default_storage.get_modified_time(key)
        try:
            return int(mtime.timestamp())
        except Exception:
            return int(time.mktime(mtime.timetuple()))

    def rename(self, src, dst):
        # Move a single object (file). For directories we copy objects with the prefix.
        src_key = self.ftp2fs(src)
        dst_key = self.ftp2fs(dst)
        if not src_key:
            raise ValueError('Cannot rename root')
        # Copy content and delete old one
        from django.core.files.storage import default_storage
        f = default_storage.open(src_key, 'rb')
        default_storage.save(dst_key, f)
        try:
            f.close()
        except Exception:
            pass
        default_storage.delete(src_key)
