import pytest
from pathlib import Path

from pathutil import PathUtil


@pytest.fixture()
def my_file(tmp_path: Path) -> str:
    ''' returns a filename to a temporary testfile'''
    txt = tmp_path / 'test_file.txt'

    txt.write_text('Hallo\nWelt!\n')
    return str(txt)

def test_eol_count(my_file):
    p = PathUtil(my_file)
    assert p.eol_count() == 2

def test_hexdigest(my_file):
    p = PathUtil(my_file)

    md5 = '967ea98d8ee95e19a7ade44e778ac1d3'
    sha1 = '0a8115d4699743050c40a4298e9c93e3a2b5485f'

    assert p.hexdigest() == md5
    assert p.hexdigest(algorithm='md5') == md5
    assert p.hexdigest(algorithm='sha1') == sha1

def test_available_algorithm():
    import hashlib

    p = PathUtil()

    for a in p.algorithms_available:
        assert a in hashlib.algorithms_available

def test_iter_lines(my_file):
    with pytest.raises(FileNotFoundError):
        for line in PathUtil('test.txt').iter_lines():
            pass
