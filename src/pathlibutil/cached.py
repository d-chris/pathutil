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

        key = args + tuple(sorted(kwargs.items()))
        try:
            value = args_cache[key]
        except KeyError:
            value = func(self, *args, **kwargs)
            args_cache[key] = value

        return value

    return cached


class Path(Path):

    @cache
    def hexdigest(self, algorithm: str = None, *, size: int = None, length: int = None) -> str:
        return super().hexdigest(algorithm=algorithm, size=size, length=length)

    @cache
    def digest(self, digest: Union[str, Callable] = None, *, size: int = None) -> 'hashlib._Hash':
        return super().digest(digest, size=size)

    @cache
    def eol_count(self, eol: str = None, size: int = None) -> int:
        return super().eol_count(eol=eol, size=size)

    @cache
    def verify(self, hexdigest: str, algorithm: Optional[str] = None, size: Optional[int] = None) -> Union[str, None]:
        return super().verify(hexdigest, algorithm=algorithm, size=size)
