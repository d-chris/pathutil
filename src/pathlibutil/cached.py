import functools
import hashlib

from .pathlist import PathList as _PathList
from .pathutil import Path as _Path


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


class Path(_Path):

    def cached(self, func: str = None) -> dict:
        try:
            cache, *_ = self.__cache__.values()

            if func:
                return cache[func]
            else:
                return cache
        except (AttributeError, KeyError) as e:
            return dict()

    @cache
    def _count(self, substr: str, /, *, size: int) -> int:
        return super()._count(substr, size=size)

    @cache
    def _file_digest(self, algorithm: str, /, *, _bufsize: int) -> 'hashlib._Hash':
        return super()._file_digest(algorithm, _bufsize=_bufsize)


class PathList(_PathList):
    @staticmethod
    def Path(item):
        if isinstance(item, Path):
            return item

        return Path(item)
