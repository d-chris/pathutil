from . import Path
import functools
from typing import Optional, Union, Callable
import hashlib


def cache(func):
    @functools.wraps(func)
    def cached(self, *args, **kwargs):
        try:
            lock = (self.mtime, self)
        except AttributeError:
            lock = self

        try:
            func_cache = self.__cache__[lock]
        except (AttributeError, KeyError):
            func_cache = dict()
            self.__cache__ = {lock: func_cache}

        try:
            args_cache = func_cache[func.__name__]
        except KeyError:
            args_cache = dict()
            self.__cache__[lock][func.__name__] = args_cache

        # key = args + tuple(sorted(kwargs.items()))
        key = args
        try:
            value = args_cache[key]
        except KeyError:
            value = func(self, *args, **kwargs)
            args_cache[key] = value

        return value

    return cached


class Path(Path):

    @cache
    def _count(self, substr: str, /, *, size: int) -> int:
        return super()._count(substr, size=size)

    @cache
    def _file_digest(self, algorithm: str, /, *, _bufsize: int) -> 'hashlib._Hash':
        return super()._file_digest(algorithm, _bufsize=_bufsize)
