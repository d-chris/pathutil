import re

from .pathutil import Path


class JobFile:
    regex = re.compile(
        r"(?P<quote>[\"']?)(?P<value>.*?)(?P=quote)(?:$|\s+)")

    def __init__(self, filename):
        self._job = Path(filename)

    @staticmethod
    def strip_comment(comment: str) -> str:
        return comment.lstrip('# ')

    @property
    def comments(self):
        try:
            return self._comments
        except AttributeError:
            _ = self.lines

        return self._comments

    @property
    def lines(self):
        try:
            return self._lines
        except AttributeError:
            lines = list()
            comments = list()

            for line in self._job.iter_lines('utf-8'):
                if line.startswith('#'):
                    comments.append(self.strip_comment(line))
                    continue

                match = self.regex.finditer(line)

                try:
                    glob = next(match).group('value')
                except StopIteration:
                    continue
                try:
                    dest = next(match).group('value')
                except StopIteration:
                    dest = '.'

                lines.append((glob, dest))
            else:
                self._lines = lines
                self._comments = comments

        return self._lines

    def __iter__(self):
        for item in self.lines:
            yield item

    def __repr__(self):
        return f"{self.__class__.__name__}('{self._job}')"

    def __len__(self):
        return len(self.lines)


class JobSearch(JobFile):
    def __init__(self, jobfile, rootdir=None, skip=None, recusrive=True):
        super().__init__(jobfile)

        self._skip = skip
        if rootdir:
            self._root = Path(rootdir)
        else:
            self._root = self._job.parent

        if recusrive:
            self._pathglob = self._root.rglob
        else:
            self._pathglob = self._root.glob

    def __repr__(self):
        return f"{self.__class__.__name__}('{self._job}', rootdir='{self._root}')"

    def __iter__(self):
        for pattern, path in super().__iter__():
            pathglob = self._pathglob(pattern)
            if self._skip:
                files = [
                    file.resolve()
                    for file in pathglob
                    if not file.is_relative_to(self._root)
                ]
            else:
                files = [file.resolve() for file in pathglob]

            yield path, files
