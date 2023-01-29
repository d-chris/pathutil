import re
from . import Path
from typing import Any, Callable
import concurrent.futures as cf


class PathList(list):
    @staticmethod
    def Path(item: Any) -> Path:
        if isinstance(item, Path):
            return item

        return Path(item)

    def __init__(self, iterable):
        super().__init__([self.Path(item) for item in iterable])

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

    def apply(self, func: Callable[[Path], Any]) -> list[Any]:
        results = list()
        with cf.ThreadPoolExecutor() as exec:
            for result in [exec.submit(func, file) for file in self]:
                try:
                    results.append(result.result())
                except (FileNotFoundError, PermissionError) as e:
                    results.append(None)

        return results


class HashFile:
    regex = regex = re.compile(
        r'^(?:(?P<comment>#.*?)|(?:(?P<hash>[a-f0-9]{8,}) \*(?P<filename>.*?)))$', re.IGNORECASE)

    def __init__(self, filename: str, encoding='utf-8'):
        self.filename = Path(filename)
        self.comments = list()
        self.hashes = list()
        self.files = PathList([])

        for line in self.filename.iter_lines(encoding=encoding):
            match = self.regex.match(line)

            if not match:
                continue

            match = match.groupdict()

            if match['comment']:
                self.comments.append(match['comment'])
            else:
                filename = match['filename']
                hash = match['hash']

                if not filename or not hash:
                    continue

                self.files.append(filename)
                self.hashes.append(hash)

    def verify(self, algorithm=None):
        result = list()
        for file, hash in zip(self.files, self.hashes):
            try:
                h = file.verify(hash, algorithm)
                if not h:
                    hash = False

            except (FileNotFoundError, PermissionError) as e:
                hash = None
            finally:
                result.append(hash)

        return result
