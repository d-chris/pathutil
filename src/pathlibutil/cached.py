from . import Path
from functools import cache


class Path(Path):

    def _check_cache_integrity(self):
        ''' clear caches if file was modified '''
        if self.modified:
            self._cached_hexdigest.clear()
            self._cached_eol_count.clear()

    @cache
    def _cached_eol_count(self, **kwargs):
        return super().eol_count(**kwargs)

    @cache
    def _cached_hexdigest(self, **kwargs):
        return super().hexdigest(**kwargs)

    def hexdigest(self, algorithm: str = None, *, size: int = None, length: int = None) -> str:
        ''' return a cached hexdigest from the file '''
        self._check_cache_integrity()

        if algorithm:
            algorithm = algorithm.casefold()

        return self._cached_hexdigest(algorithm=algorithm, size=size, length=length)

    def eol_count(self, eol: str = None, size: int = None) -> int:
        ''' return a cached eol count from the file '''
        self._check_cache_integrity()

        return self._cached_eol_count(eol=eol, size=size)
