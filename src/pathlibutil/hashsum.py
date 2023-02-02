import os
import re
from typing import Dict, Generator, Iterable, List, Tuple, Union

from .pathlist import PathList
from .pathutil import Path


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


class _Hasher:
    regex = re.compile(
        r'^(?P<hash>[a-f0-9]{8,}) \*(?P<filename>.*?)$',
        re.IGNORECASE
    )

    def __init__(self, infile):
        self.root = Path(infile).resolve()

        self._comments = list()
        self._lines = dict()

        for line in self.root.iter_lines(encoding='utf-8'):
            if not line:
                continue

            if line.startswith('#'):
                self._comments.append(line)
                continue

            match = self.regex.match(line)

            try:
                file = Path(match.group('filename'))
                hash = match.group('hash')
            except (AttributeError, IndexError) as e:
                continue

            if not file.is_absolute():
                file = self.root.parent.joinpath(file)

            self._lines[file] = hash.upper()

    @property
    def files(self) -> PathList:
        return PathList(self._lines.keys())

    @property
    def hashes(self) -> List[str]:
        return list(self._lines.values())

    @property
    def comments(self) -> List[str]:
        return self._comments

    @property
    def lines(self) -> Dict[Path, str]:
        return self._lines

    def hexdigest(self, algorithm=None):
        if not algorithm:
            algorithm = self.root.suffix

        def _hexdigest(x: Path):
            try:
                h = x.hexdigest(algorithm=algorithm).upper()

                if not h:
                    h = False
            except (FileNotFoundError, PermissionError) as e:
                return None

            return h

        return self.files.apply(_hexdigest)

    def verify(self, algorithm = None):
        if not algorithm:
            algorithm = self.root.suffix

        result = dict()

        for (k, v), h in zip(self.lines.items(), self.hexdigest(algorithm)):
            if v == h:
                result[k] = True
            else:
                result[k] = h

        return result


