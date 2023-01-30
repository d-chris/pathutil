import re
from . import Path
from typing import Any, Callable, Iterable
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

    def apply(self, func: Callable[[Path], Any], **kwargs) -> list[Any]:
        results = list()
        with cf.ThreadPoolExecutor(**kwargs) as exec:
            for thread in [exec.submit(func, file) for file in self]:
                try:
                    results.append(thread.result())
                except (FileNotFoundError, PermissionError) as e:
                    results.append(None)

        return results


def hashsum(infiles: Iterable, outfile: str, header: str = None, *, algorithm: str = None, length: int = None) -> Path:
    root = Path(outfile).resolve()
    if not algorithm:
        algorithm = root.suffix

    def hexdigest(file: Path) -> str:
        return file.hexdigest(algorithm, length=length)

    def format(tuple):
        hash, file = tuple
        return (hash.upper(), file.resolve())

    def comment(line: str):
        return f"# {line.lstrip('# ')}\n"

    files = PathList(infiles)  # convert files to a List[Path]
    hashes = files.apply(hexdigest)  # List[str] contains file-hashes

    if all(hashes) == False:
        args = [file.as_posix()
                for file, hash in zip(files, hashes) if not hash]
        msg = f"{len(args)} file(s) inaccessable"
        raise FileNotFoundError(msg, args)

    with root.open(mode='wt', encoding='utf-8') as f:
        if header:
            for line in map(comment, header.split('\n')):
                f.write(line)

            f.write('\n')

        for hash, file in map(format, zip(hashes, files)):
            if file.is_relative_to(root.parent):
                file = file.relative_to(root.parent)

            f.write(f"{hash} *{file}\n")

    return root


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
