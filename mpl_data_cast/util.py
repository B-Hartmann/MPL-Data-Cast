"""Utility methods"""
import functools
import hashlib
import pathlib
import shutil
from typing import Callable


DEFAULT_BLOCK_SIZE = 4 * (1024 ** 2)


def copyhashfile(path_in: str | pathlib.Path,
                 path_out: str | pathlib.Path,
                 blocksize: int = DEFAULT_BLOCK_SIZE,
                 constructor: Callable = hashlib.md5) -> str:
    """Copy a file while computing its md5sum

    Parameters
    ----------
    path_in:
        Input path
    path_out:
        Output path
    blocksize: int
        Number of bytes to copy at once
    constructor:
        Which hash to use
    """
    hasher = constructor()
    with path_in.open('rb') as fd, path_out.open("wb") as fo:
        while buf := fd.read(blocksize):
            hasher.update(buf)
            fo.write(buf)
    shutil.copystat(path_in, path_out)
    return hasher.hexdigest()


def hashfile(fname: str | pathlib.Path,
             blocksize: int = DEFAULT_BLOCK_SIZE,
             count: int = 0,
             constructor: Callable = hashlib.md5) -> str:
    """Compute md5 hex-hash of a file

    Parameters
    ----------
    fname: str or pathlib.Path
        path to the file
    blocksize: int
        block size in bytes read from the file
        (set to `0` to hash the entire file)
    count: int
        number of blocks read from the file
    constructor: callable
        hash algorithm constructor
    """
    path = pathlib.Path(fname).resolve()
    path_stat = path.stat()
    return _hashfile_cached(
        path=path,
        path_stats=(path_stat.st_mtime_ns, path_stat.st_size),
        blocksize=blocksize,
        count=count,
        constructor=constructor
    )


@functools.lru_cache(maxsize=100)
def _hashfile_cached(path: pathlib.Path,
                     path_stats: tuple,
                     blocksize: int = DEFAULT_BLOCK_SIZE,
                     count: int = 0,
                     constructor: Callable = hashlib.md5) -> str:
    """Cached hashfile using stat tuple as cache

    This is a privat function. Please use `hashfile` instead!

    Parameters
    ----------
    path: pathlib.Path
        path to the file to be hashed
    path_stats: tuple
        tuple that contains information about the size and the
        modification time of `path`. This must be specified,
        so that caching of the result is done properly in case the user
        modified `path` (this function is wrapped with
        functools.lru_cache)
    blocksize: int
        block size in bytes read from the file
        (set to `0` to hash the entire file)
    count: int
        number of blocks read from the file
    constructor: callable
        hash algorithm constructor
    """
    assert path_stats, "We need stat for validating the cache"
    hasher = constructor()
    with path.open('rb') as fd:
        ii = 0
        while buf := fd.read(blocksize):
            hasher.update(buf)
            ii += 1
            if count and ii == count:
                break
    return hasher.hexdigest()


def is_dir_writable(path):
    """Check whether a directory is writable

    We could play around with os.access, but ultimately there will
    always be some use case where that does not work. So we just try
    to create a file in that directory and be done with it.
    """
    path = pathlib.Path(path)
    if not path.exists():
        writable = False
    elif path.is_file():
        writable = False
    else:
        test_file = path / ".write_test~"
        try:
            test_file.touch()
        except BaseException:
            writable = False
        else:
            writable = True
        finally:
            test_file.unlink(missing_ok=True)
    return writable
