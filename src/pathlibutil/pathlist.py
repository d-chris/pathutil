import concurrent.futures as cf
from typing import Any, Callable

from .pathutil import Path


class PathList(list):
    @staticmethod
    def Path(item: Any) -> Path:
        if isinstance(item, Path):
            return item

        return Path(item)

    def __init__(self, iterable=None):
        try:
            items = [self.Path(item) for item in iterable]
        except TypeError:
            items = []

        super().__init__(items)

    def __setitem__(self, index, item):
        super().__setitem__(index, self.Path(item))

    def insert(self, index, item):
        super().insert(index, self.Path(item))

    def append(self, item):
        super().append(self.Path(item))

    def extend(self, other):
        if isinstance(other, type(self)):
            super().extend(other)
        else:
            super().extend(self.Path(item) for item in other)

    def apply(self, func: Callable[[Path], Any], **kwargs) -> list[Any]:
        results = list()
        with cf.ThreadPoolExecutor(**kwargs) as exec:
            for thread in [exec.submit(func, file) for file in self]:
                try:
                    results.append(thread.result())
                except (FileNotFoundError, PermissionError) as e:
                    results.append(None)

        return results
