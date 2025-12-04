"""CONFIG>filesystems.py"""

import logging
import time
import os
import errno
from collections import namedtuple

from pyftpdlib.filesystems import AbstractedFS
from django.conf import settings

logger = logging.getLogger(__name__)

PseudoStat = namedtuple(
    "PseudoStat",
    [
        "st_size",
        "st_mtime",
        "st_nlink",
        "st_mode",
        "st_uid",
        "st_gid",
        "st_dev",
        "st_ino",
    ],
)


class StoragePatch:
    """Base class for patches to StorageFS."""
    patch_methods = ()

    @classmethod
    def apply(cls, fs):
        logger.debug("Patching %s with %s.", fs.__class__.__name__, cls.__name__)
        fs._patch = cls
        for method_name in cls.patch_methods:
            origin = getattr(fs, method_name)
            method = getattr(cls, method_name)
            bound_method = method.__get__(fs, fs.__class__)
            setattr(fs, method_name, bound_method)
            setattr(fs, "_origin_" + method_name, origin)


class FileSystemStoragePatch(StoragePatch):
    patch_methods = ("mkdir", "rmdir", "stat")

    def mkdir(self, path):
        # allow the path to be a filesystem path or ftp-style
        ftp_path = self._ensure_ftp_path(path) if hasattr(self, '_ensure_ftp_path') else path
        self.storage.save(self._storage_name(ftp_path).rstrip("/") + "/", b"")

    def rmdir(self, path):
        # local filesystem storage: delegate to os.rmdir if storage exposes path
        if hasattr(self.storage, "path"):
            ftp_path = self._ensure_ftp_path(path) if hasattr(self, '_ensure_ftp_path') else path
            os.rmdir(self.storage.path(self._storage_name(ftp_path)))
        else:
            # fallback: try deleting placeholder directory if any
            raise NotImplementedError("rmdir not supported for this storage")

    def stat(self, path):
        ftp_path = self._ensure_ftp_path(path) if hasattr(self, '_ensure_ftp_path') else path
        return os.stat(self.storage.path(self._storage_name(ftp_path)))


class S3Boto3StoragePatch(StoragePatch):
    patch_methods = ("_exists", "isdir", "getmtime")

    def _exists(self, path):
        ftp_path = self._ensure_ftp_path(path) if hasattr(self, '_ensure_ftp_path') else path
        if ftp_path.endswith("/"):
            return True
        return self.storage.exists(self._storage_name(ftp_path))

    def isdir(self, path):
        return not self.isfile(path)

    def getmtime(self, path):
        if self.isdir(path):
            return 0
        ftp_path = self._ensure_ftp_path(path) if hasattr(self, '_ensure_ftp_path') else path
        return self._origin_getmtime(self._storage_name(ftp_path))


class DjangoGCloudStoragePatch(StoragePatch):
    patch_methods = ("_exists", "isdir", "getmtime", "listdir")

    def _exists(self, path):
        ftp_path = self._ensure_ftp_path(path) if hasattr(self, '_ensure_ftp_path') else path
        if ftp_path.endswith("/"):
            return True
        return self.storage.exists(self._storage_name(ftp_path))

    def isdir(self, path):
        return not self.isfile(path)

    def getmtime(self, path):
        if self.isdir(path):
            return 0
        ftp_path = self._ensure_ftp_path(path) if hasattr(self, '_ensure_ftp_path') else path
        return self._origin_getmtime(ftp_path)

    def listdir(self, path):
        ftp_path = self._ensure_ftp_path(path) if hasattr(self, '_ensure_ftp_path') else path
        if not ftp_path.endswith("/"):
            ftp_path += "/"
        return self._origin_listdir(self._storage_name(ftp_path))


class StorageFS(AbstractedFS):
    """
    FileSystem bridging pyftpdlib's AbstractedFS and Django storage backends.

    Important: `_cwd` stores an FTP-style path (starts with '/'). All
    conversions to storage keys happen in _storage_name().
    """

    storage_class = None
    patches = {
        "FileSystemStorage": FileSystemStoragePatch,
        "S3Boto3Storage": S3Boto3StoragePatch,
        "DjangoGCloudStorage": DjangoGCloudStoragePatch,
    }

    def apply_patch(self):
        patch = self.patches.get(self.storage.__class__.__name__)
        if patch:
            patch.apply(self)

    def __init__(self, root, cmd_channel):
        super(StorageFS, self).__init__(root, cmd_channel)
        # set FTP cwd to root (FTP-style)
        self._cwd = "/"
        self.storage = self.get_storage()
        self.apply_patch()

    def get_storage_class(self):
        if self.storage_class is None:
            # lazy import via django's helper
            from django.core.files.storage import get_storage_class as _get_storage_class
            return _get_storage_class()
        return self.storage_class

    def get_storage(self):
        storage_class = self.get_storage_class()
        return storage_class()

    # --------------------- path helpers ---------------------

    def _make_ftp_path(self, path):
        """Return an FTP-style path (always begins with '/' except root '').

        Accepts either an absolute FTP path (starts with '/') or a
        relative name and joins with current _cwd.
        """
        if path is None or path == "":
            return "/"
        if path.startswith("/"):
            return path if path != "" else "/"
        # relative path
        base = self._cwd if self._cwd not in (None, "") else "/"
        if base.endswith("/"):
            return base + path.lstrip("/")
        return base + "/" + path.lstrip("/")

    def _ensure_ftp_path(self, path):
        """
        Accept either a real filesystem path (as passed by pyftpdlib
        handlers) or an FTP-style path and return an FTP-style path.

        - If `path` is a filesystem path under self.root, convert it
          to an FTP-style path using fs2ftp.
        - Otherwise assume the argument is already an FTP-style path
          and normalize it via _make_ftp_path.
        """
        # default: root and variants
        if path in (None, "", "/"):
            return "/"
        # If path looks like an absolute real filesystem path and starts
        # with the configured root, convert it back to ftp style.
        try:
            if os.path.isabs(path) and self.root and os.path.normpath(path).startswith(os.path.normpath(self.root)):
                # compute relative path to root without calling fs2ftp to avoid recursion
                rel = os.path.relpath(path, self.root)
                # rel may be '.' if path == root
                if rel in ('.', ''):
                    return "/"
                # Always return slash-prefixed ftp-style path with POSIX separators
                return "/" + rel.replace(os.sep, "/")
        except Exception:
            # fallback to ftp style
            pass
        return self._make_ftp_path(path)

    def _storage_name(self, ftp_path):
        """
        Convert an FTP-style path to a storage-relative key.

        - '' (root) -> '' (some storages expect empty string for root)
        - leading slash removed
        - if the ftp_path contains local MEDIA_ROOT segments, make it relative
          to MEDIA_ROOT so absolute local paths don't leak into S3 keys.
        """
        if ftp_path in (None, "", "/"):
            return ""

        # ensure ftp_path is ftp-style
        if not ftp_path.startswith("/"):
            ftp_path = "/" + ftp_path

        name = ftp_path.lstrip("/")

        # If MEDIA_ROOT appears inside the name, strip up to MEDIA_ROOT so that
        # keys are relative to media folder.
        try:
            media_root = getattr(settings, "MEDIA_ROOT", None)
            if media_root:
                media_root_base = os.path.basename(os.path.normpath(media_root))
                parts = name.split("/")
                if media_root_base in parts:
                    idx = parts.index(media_root_base)
                    # everything after MEDIA_ROOT basename is the real relative key
                    name = "/".join(parts[idx + 1 :]) or ""
        except Exception:
            # be conservative: if anything fails, fall back to the raw name
            pass

        return name

    # --------------------- FS operations ---------------------

    def chdir(self, path):
        """Change current directory. Keep as FTP-style path."""
        assert isinstance(path, str), path
        ftp_path = self._ensure_ftp_path(path)
        # normalize trailing slash: directories in FTP are represented with '/'
        if ftp_path != "/" and ftp_path.endswith("/"):
            ftp_path = ftp_path.rstrip("/")
        self._cwd = ftp_path

    def open(self, filename, mode="rb"):
        """Open a file using storage backend. filename may be absolute or relative."""
        assert isinstance(filename, str), filename
        ftp_path = self._ensure_ftp_path(filename)
        key = self._storage_name(ftp_path)
        try:
            return self.storage.open(key, mode)
        except FileNotFoundError:
            raise OSError(errno.ENOENT, "No such file or directory", filename)

    def mkstemp(self, suffix="", prefix="", dir=None, mode="wb"):
        raise NotImplementedError("mkstemp not implemented for StorageFS")

    def mkdir(self, path):
        """Create a pseudo-directory if backend supports it (S3 usually doesn't
        have real folders; many apps create zero-length object with trailing '/')."""
        ftp_path = self._ensure_ftp_path(path)
        key = self._storage_name(ftp_path)
        if not key.endswith("/"):
            key = key + "/"
        # Some storages accept save(...) for directories; try best-effort.
        try:
            # create an empty placeholder (some storages ignore zero-length saves)
            self.storage.save(key, b"")
        except Exception as e:
            logger.debug("mkdir fallback: %s", e)
            raise OSError(errno.EACCES, "Cannot create directory", path)

    def listdir(self, path):
        assert isinstance(path, str), path
        ftp_path = self._ensure_ftp_path(path)
        key = self._storage_name(ftp_path)
        logger.debug("StorageFS.listdir called with path=%r ftp_path=%r key=%r", path, ftp_path, key)
        # many storages expect '' for root
        if key != "" and not key.endswith("/"):
            key = key + "/"
        try:
            directories, files = self.storage.listdir(key)
            # normalize directories to FTP style (with trailing '/')
            dirs = [d.rstrip("/") + "/" for d in directories if d]
            files = [f for f in files if f]
            return dirs + files
        except FileNotFoundError:
            raise OSError(errno.ENOENT, "No such directory", path)

    def rmdir(self, path):
        ftp_path = self._ensure_ftp_path(path)
        key = self._storage_name(ftp_path)
        if not key.endswith("/"):
            key = key + "/"
        # attempt to delete placeholder object if present
        try:
            # Some storages don't provide delete for folders; simply try to delete
            self.storage.delete(key)
        except Exception as e:
            logger.debug("rmdir failed: %s", e)
            raise OSError(errno.EACCES, "Cannot remove directory", path)

    def remove(self, path):
        assert isinstance(path, str), path
        ftp_path = self._ensure_ftp_path(path)
        key = self._storage_name(ftp_path)
        try:
            self.storage.delete(key)
        except FileNotFoundError:
            raise OSError(errno.ENOENT, "No such file", path)

    def chmod(self, path, mode):
        raise NotImplementedError("chmod not supported for remote storage")

    def stat(self, path):
        """Return a PseudoStat. Raise OSError with errno when missing."""
        try:
            if self.isfile(path):
                st_mode = 0o0100770
            else:
                st_mode = 0o0040770
            size = self.getsize(path)
            mtime = int(self.getmtime(path))
            return PseudoStat(
                st_size=size,
                st_mtime=mtime,
                st_nlink=1,
                st_mode=st_mode,
                st_uid=1000,
                st_gid=1000,
                st_dev=0,
                st_ino=0,
            )
        except OSError:
            raise
        except FileNotFoundError:
            raise OSError(errno.ENOENT, "No such file or directory", path)

    lstat = stat

    def _exists(self, path):
        if path in (None, "", "/"):
            name = ""
        else:
            ftp_path = self._ensure_ftp_path(path)
            name = self._storage_name(ftp_path)
        try:
            return self.storage.exists(name)
        except Exception:
            return False

    def isfile(self, path):
        # file if exists and not endswith '/'
        if path in (None, "", "/"):
            return False
        ftp_path = self._ensure_ftp_path(path)
        if ftp_path.endswith("/"):
            return False
        return self._exists(path)

    def islink(self, path):
        return False

    def isdir(self, path):
        # '' or '/' is root directory
        ftp_path = self._ensure_ftp_path(path)
        if ftp_path in ("/", ""):
            return True
        # directory if exists with trailing slash or exists as prefix
        if ftp_path.endswith("/"):
            return self._exists(ftp_path)
        return self._exists(ftp_path + "/")

    def getsize(self, path):
        if self.isdir(path):
            return 0
        ftp_path = self._ensure_ftp_path(path)
        key = self._storage_name(ftp_path)
        try:
            return self.storage.size(key)
        except FileNotFoundError:
            raise OSError(errno.ENOENT, "No such file", path)

    def getmtime(self, path):
        # dirs -> 0; files -> use storage.get_modified_time
        if self.isdir(path):
            return 0
        ftp_path = self._ensure_ftp_path(path)
        key = self._storage_name(ftp_path)
        try:
            dt = self.storage.get_modified_time(key)
            # dt may be tz-aware; int timestamp is fine
            try:
                return int(dt.timestamp())
            except Exception:
                return int(time.mktime(dt.timetuple()))
        except FileNotFoundError:
            raise OSError(errno.ENOENT, "No such file", path)
        except Exception:
            # fallback: 0
            return 0

    def realpath(self, path):
        # return ftp-style path
        return self._ensure_ftp_path(path)

    def lexists(self, path):
        return self._exists(path)

    def get_user_by_uid(self, uid):
        return "owner"

    def get_group_by_gid(self, gid):
        return "group"
