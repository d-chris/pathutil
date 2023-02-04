import distutils.file_util as dfutil
import hashlib
import os
import pathlib
import shutil
from typing import Any, Optional, Tuple, Union, Self


class Path(pathlib.Path):
    _flavour = pathlib._windows_flavour if os.name == 'nt' else pathlib._posix_flavour

    _digest_length = {
        'shake_128': 128,
        'shake_256': 256
    }

    _digest_default = 'md5'

    _digest_chunk = 2**20

    @property
    def default_digest(self) -> str:
        return self._digest_default

    def iter_lines(self, encoding: str = None) -> str:
        ''' read the content of a file line by line without the line-ending char '''
        with super().open(mode='rt', encoding=encoding) as f:
            while True:
                line = f.readline()

                if line:
                    yield line.rstrip('\n')
                else:
                    break

    def iter_bytes(self, size: int = None) -> bytes:
        ''' return a chunk of bytes '''
        if not size:
            size = self._digest_chunk

        with super().open(mode='rb') as f:
            while True:
                chunk = f.read(size)

                if chunk:
                    yield chunk
                else:
                    break

    def with_suffix(self: Self, suffix: str, delimiter: str = None) -> Self:
        if delimiter:
            suffix = f"{delimiter}{suffix.lstrip(delimiter)}"

        return super().with_suffix(suffix)

    def hexdigest(self, algorithm: str = None, *, size: int = None, length: int = None) -> str:
        ''' calculate a hashsum using an algorithm '''
        h = self.digest(algorithm, size=size)

        if h.digest_size != 0:
            kwargs = dict()
        else:
            if length:
                kwargs = {'length': length}
            else:
                try:
                    key = self.algorithm(algorithm)
                    kwargs = {'length': self._digest_length[key]}
                except KeyError:
                    raise TypeError(
                        "hexdigest() missing required argument 'length'")

            if kwargs['length'] < 0:
                raise ValueError(
                    "hexdigest() required argument 'length' has to be a positive integer")

        return h.hexdigest(**kwargs)

    def digest(self, algorithm: str = None, *, size: int = None) -> 'hashlib._Hash':
        ''' digest of the binary file-content '''
        if not size or size < 0:
            size = self._digest_chunk

        return self._file_digest(self.algorithm(algorithm), _bufsize=size)

    def _file_digest(self, algorithm: str, /, *, _bufsize: int) -> 'hashlib._Hash':
        digest = (lambda: hashlib.new(algorithm))

        with self.open(mode='rb') as f:
            h = hashlib.file_digest(f, digest, _bufsize=_bufsize)

        return h

    @staticmethod
    def algorithms_available() -> set[str]:
        ''' names of available hash algorithms '''
        return hashlib.algorithms_available

    @classmethod
    def algorithm(cls, value: Union[str, Any]) -> Union[str, Any]:
        ''' converts file suffix into a valid algorithm string '''
        try:
            return value.strip().lstrip('.').lower()
        except AttributeError:
            return cls._digest_default

    def eol_count(self, eol: str = None, size: int = None) -> int:
        ''' return the number of end-of-line characters'''
        try:
            substr = eol.encode()
        except AttributeError as e:
            substr = '\n'.encode()

        if not size:
            size = self._digest_chunk

        return self._count(substr, size=size)

    def _count(self, substr: str, /, *, size: int) -> int:
        return sum(chunk.count(substr) for chunk in self.iter_bytes(size))

    def copy(self, dst: Union[str, 'Path'], *, parents: bool = True, **kwargs) -> Tuple['Path', int]:
        ''' copies self into a new destination, check distutils.file_util::copy_file for kwargs '''

        if parents is True:
            Path(dst).mkdir(parents=True, exist_ok=True)

        destination, result = dfutil.copy_file(self, dst, **kwargs)

        return (Path(destination), result)

    def move(self, dst: Union[str, 'Path'], *, parents: bool = True, prune: bool = True, **kwargs) -> Tuple['Path', int]:
        ''' moves self into a new destination '''

        destination, result = self.copy(dst, parents=parents, **kwargs)

        if result:
            prune = False if not prune else 'try'
            self.unlink(missing_ok=True, prune=prune)

        return (Path(destination), result)

    def delete(self, recursive: bool = False, missing_ok: bool = False, **kwargs):
        try:
            if self.is_file():
                self.unlink(prune=recursive)
            elif self.is_dir():
                self.rmdir(recursive=True if recursive else False, **kwargs)
            else:
                raise FileNotFoundError
        except FileNotFoundError as e:
            if not missing_ok:
                raise

    def rmdir(self, *, recursive=False, **kwargs):
        ''' deletes a directory with all files, check shutil::rmtree for kwargs '''

        if not recursive:
            super().rmdir()
        else:
            shutil.rmtree(self, **kwargs)

    def unlink(self, missing_ok: bool = False, *, prune: Union[bool, str] = False):
        ''' deletes a file and prune an empty directory '''
        super().unlink(missing_ok)

        if prune:
            try:
                self.parent.rmdir(recursive=False)
            except OSError as e:
                if str(prune).casefold() != 'try':
                    raise

    def touch(self, mode=0o666, exist_ok=True, *, parents: bool = False):
        ''' creates a file and parent directories '''
        if parents is True:
            self.parent.mkdir(parents=True, exist_ok=True)

        super().touch(mode=mode, exist_ok=exist_ok)

    @property
    def mtime(self) -> int:
        ''' time of the last modification in nanoseconds '''
        return self.stat().st_mtime_ns

    def verify(self, hexdigest: str, algorithm: Optional[str] = None, *, size: Optional[int] = None) -> Union[str, None]:
        ''' verify if file has the correct hash '''
        hexdigest = hexdigest.strip().lower()
        digest_size = int(len(hexdigest) / 2)

        if algorithm:
            result = self.hexdigest(algorithm, length=digest_size, size=size)
            return algorithm if result == hexdigest else None

        for algorithm in self.algorithms_available():
            h = hashlib.new(algorithm)

            if h.digest_size not in (digest_size, 0):
                continue

            result = self.hexdigest(algorithm, length=digest_size, size=size)

            if result == hexdigest:
                break
        else:
            return None

        return algorithm
