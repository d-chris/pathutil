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

    @property
    def default_digest(self) -> 'hashlib._Hash':
        return self._digest_default

    def iter_lines(self, encoding: str = None) -> str:
        with super().open(mode='rt', encoding=encoding) as f:
            while True:
                line = f.readline()

                if line:
                    yield line.rstrip('\n')
                else:
                    break

    def iter_bytes(self, size: int = None) -> bytes:
        with super().open(mode='rb') as f:
            while True:
                chunk = f.read(size)

                if chunk:
                    yield chunk
                else:
                    break

    def hexdigest(self, algorithm: str = None, *, size: int = None, length: int = None) -> str:
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

        if size is None:
            kwargs = dict()
        else:
            kwargs = {'_bufsize': size}

        if digest is None:
            digest = self._digest_default

        with self.open(mode='rb') as f:
            h = hashlib.file_digest(f, digest, **kwargs)

        return h

    @property
    def algorithms_available(self) -> set[str]:
        return hashlib.algorithms_available

    def eol_count(self, eol: str = None, size: int = None) -> int:
        try:
            substr = eol.encode()

        except AttributeError as e:
            substr = '\n'.encode()

        return sum(chunk.count(substr) for chunk in self.iter_bytes(size))

    def copy(self, dst: Union[str, 'Path'], *, mkdir: bool = None, **kwargs) -> Tuple['Path', int]:
        ''' copies self into a new destination, check distutils.file_util::copy_file for kwargs '''

        if mkdir is True:
            Path(dst).mkdir(parents=True, exist_ok=True)
        elif mkdir is False:
            Path(dst).mkdir(parents=False, exist_ok=False)

        destination, result = dfutil.copy_file(self, dst, **kwargs)

        return (self.__class__(destination), result)

    def move(self, dst: Union[str, 'Path'], **kwargs) -> Tuple['Path', int]:
        ''' moves self into a new destination, check shutil::move for kwargs '''

        destination = shutil.move(self, dst, **kwargs)

        dest = self.__class__(destination)

        return (dest, dest.exists())

    def rmdir(self, *, file_ok: bool = False, **kwargs) -> bool:
        ''' deletes a directory with all files, check shutil::rmtree for kwargs '''

        try:
            shutil.rmtree(self, **kwargs)
        except NotADirectoryError as e:
            if file_ok != True:
                raise NotADirectoryError(f"'{self}' is not a directory")

        return self.exists() == False


if __name__ == '__main__':
    pass
