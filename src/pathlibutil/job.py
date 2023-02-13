import itertools
import re
from typing import Dict

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
                    exclude = None
                else:
                    try:
                        exclude = next(match).group('value')
                    except StopIteration:
                        exclude = None

                lines.append((glob, dest, exclude))
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
    def __init__(self, jobfile, rootdir=None, exclude=None):
        super().__init__(jobfile)

        if not rootdir:
            self._root = self._job.parent
        else:
            self._root = Path(rootdir)

        self._exclude = exclude

    def __repr__(self):
        return f"{self.__class__.__name__}('{self._job}', rootdir='{self._root}', exclude={self._exclude})"

    def __iter__(self):
        self._hits = list()

        for pattern, path, exclude in super().__iter__():

            try:
                exclude = exclude.split(';')
                exclude.extend(self._exclude)
            except AttributeError:
                exclude = self._exclude
            except TypeError:
                pass

            i = 0
            for i, item in enumerate(Path(self._root).rglob(pattern, exclude), start=1):
                yield item, path
            else:
                self._hits.append(i)

    @property
    def hits(self):
        try:
            return self._hits
        except AttributeError:
            return [0] * len(self)
