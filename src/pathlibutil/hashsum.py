import re
from typing import Dict, Generator, Iterable, List, Tuple

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


class HashFile:
    regex = re.compile(
        r'^(?P<hash>[a-f0-9]{8,}) \*(?P<filename>.*?)$',
        re.IGNORECASE
    )

    def __init__(self, infile: str, algorithm: str = None):
        self._root = Path(infile).resolve()

        self._algorithm = Path.algorithm(algorithm)

        if self._algorithm not in Path.algorithms_available():
            raise ValueError

        self._comments = list()
        self._lines = dict()

        for line in self._root.iter_lines(encoding='utf-8'):
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
                file = self._root.parent.joinpath(file)

            self._lines[file] = hash.upper()

    @property
    def files(self) -> PathList:
        return PathList(self._lines.keys())

    @property
    def hashes(self) -> List[str]:
        return list(self._lines.values())

    @property
    def comments(self) -> List[str]:
        return self._comments.copy()

    @property
    def lines(self) -> Dict[Path, str]:
        return self._lines.copy()

    def __hash__(self) -> int:
        return hash((self._root, self._algorithm))

    def __len__(self) -> int:
        return len(self._lines)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}('{self._root.as_posix()}', algorithm='{self._algorithm}')"

    def __getitem__(self, index) -> str:
        _, hash = self._get_result()[index]

        return hash

    def __iter__(self) -> Generator[Path, None, None]:
        for k, v in self._get_result().items():
            yield k, v

    def match(self) -> Generator[Path, None, None]:
        for file, (old, new) in self:
            if not new:
                continue

            if old == new:
                yield file

    def missing(self) -> Generator[Path, None, None]:
        for file, (_, new) in self:
            if new:
                continue

            yield file

    def modified(self) -> Generator[Path, None, None]:
        for file, (old, new) in self:
            if not new:
                continue

            if old != new:
                yield file

    @property
    def hexdigest(self) -> List[str]:
        return self._get_hexdigest().copy()

    def _get_hexdigest(self):
        try:
            return self._hexdigest
        except AttributeError:
            def _digest(x: Path):
                try:
                    return x.hexdigest(algorithm=self._algorithm).upper()
                except (FileNotFoundError, PermissionError) as e:
                    return None

            self._hexdigest = self.files.apply(_digest)

        return self._hexdigest

    @property
    def result(self) -> Dict[Path, Tuple[str, str]]:
        return self._get_result().copy()

    def _get_result(self):
        try:
            return self._result
        except AttributeError:
            self._result = dict()

            for (file, file_hash), new_hash in zip(self._lines.items(), self._get_hexdigest()):
                self._result[file] = (file_hash, new_hash)

        return self._result
