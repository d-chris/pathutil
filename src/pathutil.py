import pathlib
import hashlib
import os


class PathUtil(pathlib.Path):
    _flavour = pathlib._windows_flavour if os.name == 'nt' else pathlib._posix_flavour

    def iter_lines(self, encoding=None):
        with super().open(mode='rt', encoding=encoding) as f:
            while True:
                line = f.readline()

                if line:
                    yield line.rstrip('\n')
                else:
                    break

    def iter_bytes(self, size=None):
        with super().open(mode='rb') as f:
            while True:
                chunk = f.read(size)

                if chunk:
                    yield chunk
                else:
                    break

    def hexdigest(self, algorithm=None, size=None) -> str:
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


if __name__ == '__main__':
    pass
