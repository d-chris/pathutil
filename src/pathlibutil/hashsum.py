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


def hashparse(
    hashfile: str,
) -> Generator[Tuple[str, Path], None, None]:

    hashfile = Path(hashfile)

    root = hashfile.resolve().parent

    regex = re.compile(
        r'^(?P<hash>[a-f0-9]{8,}) \*(?P<filename>.*?)$',
        re.IGNORECASE
    )

    for match in map(lambda line: regex.match(line.strip()), hashfile.iter_lines(encoding='utf-8')):
        if match is None:
            continue

        try:
            hash, filename = match.group('hash'), Path(match.group('filename'))
        except IndexError:
            continue

        if not filename.is_absolute():
            filename = root.joinpath(filename)

        yield (hash, filename)


def hashcheck(
    hashfile: str,
    algorithm: str = None,
    *,
    size: int = None
) -> Dict[Union[bool, None], List[Path]]:

    kwargs = {
        'algorithm': algorithm,
        'size': size
    }

    result = {True: [], False: [], None: []}

    for hash, file in hashparse(hashfile):
        try:
            key = bool(file.verify(hash, **kwargs))
        except (FileNotFoundError, PermissionError) as e:
            result[None].append(file)
        else:
            result[key].append(file)

    return result


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
