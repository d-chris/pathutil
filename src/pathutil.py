import pathlib
import hashlib
import os
import shutil
import distutils.file_util as dfutil


class PathUtil(pathlib.Path):
    _flavour = pathlib._windows_flavour if os.name == 'nt' else pathlib._posix_flavour

    def iter_lines(self, encoding: str = None):
        with super().open(mode='rt', encoding=encoding) as f:
            while True:
                line = f.readline()

                if line:
                    yield line.rstrip('\n')
                else:
                    break

    def iter_bytes(self, size: int = None):
        with super().open(mode='rb') as f:
            while True:
                chunk = f.read(size)

                if chunk:
                    yield chunk
                else:
                    break

    def hexdigest(self, algorithm: str = None, size: int = None) -> str:
        try:
            h = hashlib.new(algorithm)

        except TypeError as e:
            h = hashlib.md5()

        for chunk in self.iter_bytes(size):
            h.update(chunk)

        return h.hexdigest()

    @property
    def algorithms_available(self) -> set:
        return hashlib.algorithms_available

    def eol_count(self, eol: str = None, size: int = None) -> int:
        try:
            substr = eol.encode()

        except AttributeError as e:
            substr = '\n'.encode()

        return sum(chunk.count(substr) for chunk in self.iter_bytes(size))

    def copy(self, dst: str, mkdir: bool = None, **kwargs) -> tuple:
        ''' copies self into a new destination, check distutils.file_util::copy_file for kwargs '''

        if mkdir is True:
            PathUtil(dst).mkdir(parents=True, exist_ok=True)
        elif mkdir is False:
            PathUtil(dst).mkdir(parents=False, exist_ok=False)

        destination, result = dfutil.copy_file(str(self), dst, **kwargs)

        return (self.__class__(destination), result)

    def move(self, dst: str, **kwargs) -> tuple:
        ''' moves self into a new destination, check shutil::move for kwargs '''

        destination = shutil.move(self, dst, **kwargs)

        dest = self.__class__(destination)

        return (dest, dest.is_file())


if __name__ == '__main__':
    pass
