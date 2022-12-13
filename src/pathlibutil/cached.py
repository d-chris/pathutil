from . import Path
import functools


def cache(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            lock = (self.mtime, self)
        except AttributeError:
            lock = self

        try:
            func_cache = self.__cache[lock]
        except (AttributeError, KeyError):
            func_cache = dict()
            self.__cache = {lock: func_cache}

        try:
            args_cache = func_cache[func.__name__]
        except KeyError:
            args_cache = dict()
            self.__cache[lock][func.__name__] = args_cache

        key = args + tuple(sorted(kwargs.items()))
        try:
            value = args_cache[key]
        except KeyError:
            value = func(self, *args, **kwargs)
            args_cache[key] = value

        return value

    return wrapper


class Path(Path):

    @cache
    def hexdigest(
        self, algorithm: str = None, *, size: int = None, length: int = None
    ) -> str:
        return super().hexdigest(algorithm=algorithm, size=size, length=length)

    @cache
    def eol_count(self, eol: str = None, size: int = None) -> int:
        return super().eol_count(eol=eol, size=size)
