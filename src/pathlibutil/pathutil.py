import pathlib
import hashlib
import os
import shutil
import distutils.file_util as dfutil
from typing import Tuple, Union, Callable


class Path(pathlib.Path):
    _flavour = pathlib._windows_flavour if os.name == 'nt' else pathlib._posix_flavour

    _digest_length = {
        'shake_128': 128,
        'shake_256': 256
    }

    _digest_default = hashlib.md5

    _digest_chunk = 2**20

    def __init__(self, *args):
        super().__init__()

        _ = self.modified

    @property
    def default_digest(self) -> 'hashlib._Hash':
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

    def hexdigest(self, algorithm: str = None, *, size: int = None, length: int = None) -> str:
        ''' calculate a hashsum using an algorithm '''
        try:
            h = hashlib.new(algorithm)

        except TypeError as e:
            h = self._digest_default()

        for chunk in self.iter_bytes(size):
            h.update(chunk)

        try:
            bits = self._digest_length[algorithm]

            if length <= 0:
                raise ValueError(
                    'length for digest needs do be a positive integer')

            kwargs = {'length': length}

        except KeyError as e:
            kwargs = dict()
        except TypeError as e:
            kwargs = {'length': bits}

        return h.hexdigest(**kwargs)

    def digest(self, digest: Union[str, Callable] = None, *, size: int = None) -> 'hashlib._Hash':
        ''' digest of the binary file-content '''
        if not size:
            size = self._digest_chunk

        if digest is None:
            digest = self._digest_default

        with self.open(mode='rb') as f:
            h = hashlib.file_digest(f, digest, _bufsize=size)

        return h

    @property
    def algorithms_available(self) -> set[str]:
        ''' names of available hash algorithms '''
        return hashlib.algorithms_available

    def eol_count(self, eol: str = None, size: int = None) -> int:
        ''' return the number of end-of-line characters'''
        try:
            substr = eol.encode()

        except AttributeError as e:
            substr = '\n'.encode()

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

    @property
    def modified(self) -> bool:
        ''' returns true when file was modified after initialization from class instance '''
        try:
            lock = (self.mtime, self)

            if self._lock != lock:
                self._lock = lock
                return True
        except AttributeError as e:
            self._lock = lock
        except FileNotFoundError as e:
            pass

        return False


if __name__ == '__main__':
    pass
