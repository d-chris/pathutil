import pytest
import hashlib
import inspect
import pathlib
import subprocess

from pathlibutil import Path

CONTENT = 'foo\nbar!\n'


@pytest.fixture()
def tmp_file(tmp_path: pathlib.Path) -> str:
    ''' returns a filename to a temporary testfile'''
    txt = tmp_path / 'test_file.txt'

    txt.write_text(CONTENT, encoding='utf-8', newline='')
    return str(txt)


@pytest.fixture()
def dst_path(tmp_path: pathlib.Path) -> str:
    dest = tmp_path / 'destination'

    return str(dest)


def test_eol_count(tmp_file):
    p = Path(tmp_file)
    assert p.eol_count() == 2
    assert p.eol_count(eol='\n') == 2
    assert p.eol_count(eol='\r') == 0


def test_hexdigest(tmp_file):
    p = Path(tmp_file)

    my_bytes = pathlib.Path(tmp_file).read_bytes()
    md5 = hashlib.new('md5', my_bytes).hexdigest()
    sha1 = hashlib.new('sha1', my_bytes).hexdigest()

    assert p.hexdigest() == md5
    assert p.hexdigest(p.default_digest) == md5
    assert p.hexdigest(algorithm='md5', size=4) == md5
    assert p.hexdigest(algorithm='sha1') == sha1

    with pytest.raises(ValueError):
        p.hexdigest(algorithm='fubar')

    with pytest.raises(TypeError):
        p.hexdigest(size='fubar')


def test_shake(tmp_file):
    p = Path(tmp_file)

    assert len(p.hexdigest('shake_128')) == 128*2

    length = 10

    assert len(p.hexdigest('shake_128', length=length)) == length * 2

    with pytest.raises(TypeError):
        p.hexdigest('shake_128', length)

    with pytest.raises(ValueError):
        p.hexdigest('shake_256', length=-1)


def test_digest(tmp_file):
    p = Path(tmp_file)

    my_bytes = pathlib.Path(tmp_file).read_bytes()
    md5 = hashlib.new('md5', my_bytes)

    assert p.digest('md5').digest() == md5.digest()


def test_available_algorithm():
    p = Path()

    assert isinstance(p.algorithms_available, set)

    for a in p.algorithms_available:
        assert a in hashlib.algorithms_available


def test_iter_lines(tmp_file):
    with pytest.raises(FileNotFoundError):
        for line in Path('file_not_available.txt').iter_lines():
            pass

    my_generator = Path(tmp_file).iter_lines()

    assert inspect.isgenerator(my_generator)
    assert list(my_generator) == str(CONTENT).splitlines()


def test_iter_bytes(tmp_file):
    with pytest.raises(FileNotFoundError):
        for chunk in Path('file_not_available.txt').iter_bytes():
            pass

    my_generator = Path(tmp_file).iter_bytes()

    assert inspect.isgenerator(my_generator)
    assert list(my_generator)[0] == str(CONTENT).encode()


def test_main():
    ''' run script in virtual environment '''
    p = subprocess.run(r'pipenv run src\pathlibutil\pathutil.py', shell=True)

    assert p.returncode == 0


def test_copy(tmp_file, dst_path):
    src = Path(tmp_file)

    result = src.copy(dst_path, mkdir=True)

    assert isinstance(result, tuple)

    dst, copied = result

    assert copied == True
    assert pathlib.Path(src).is_file() == True
    assert dst == pathlib.Path(dst_path).joinpath(pathlib.Path(tmp_file).name)


def test_move(tmp_file, dst_path):
    src = Path(tmp_file)

    result = src.move(dst_path)

    assert isinstance(result, tuple)

    dst, moved = result

    assert moved == True
    assert pathlib.Path(src).is_file() == False
