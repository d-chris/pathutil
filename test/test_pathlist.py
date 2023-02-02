import pytest

from pathlibutil.pathlist import PathList
from pathlibutil import Path


def test_pathlist():
    p = PathList()

    assert len(p) == 0

    p = PathList([])

    assert len(p) == 0

    p = PathList(['file1.txt', './test/', Path('file3.txt')])

    assert len(p) == 3

    for item in p:
        assert isinstance(item, Path)


def test_apply():
    p = PathList(['file1.txt', 'file2.txt'])

    def suffix(x: Path):
        return x.suffix

    suffixes = p.apply(suffix)

    assert len(suffixes) == 2

    for item in suffixes:
        assert item == '.txt'

    names = p.apply(lambda x: x.stem)

    assert names[0] == 'file1'
    assert names[-1] == 'file2'
