import pytest
import hashlib
import inspect
import pathlib
import subprocess
import time

from pathlibutil import Path

CONTENT = 'foo\nbar!\n'
SEC = 0.02


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


@pytest.fixture()
def dir_tree(tmp_path: pathlib.Path) -> str:
    dir = tmp_path / 'dir1'
    dir.mkdir()

    file = dir / 'file1.txt'
    file.touch()

    file = dir / 'file2.txt'
    file.touch()

    return str(dir)


def test_delete_recursive(dir_tree: str):
    p = Path(dir_tree)

    assert p.exists() == True

    with pytest.raises(OSError):
        p.delete()

    assert p.exists() == True
    p.delete(recursive=True)
    assert p.exists() == False

    with pytest.raises(FileNotFoundError):
        p.delete(recursive=True)

    try:
        p.delete(recursive=True, missing_ok=True)
    except Exception:
        assert False


def test_delete(dir_tree: str):
    p = Path(dir_tree)

    files = [file for file in p.iterdir()]
    assert len(files) == 2

    assert files[0].exists() == True
    files[0].delete()
    assert files[0].exists() == False

    with pytest.raises(FileNotFoundError):
        files[0].delete()

    try:
        files[0].delete(missing_ok=True)
    except Exception:
        assert False

    assert files[1].exists() == True
    files[1].delete(recursive=True)
    assert p.exists() == False


def test_delete_try(dir_tree: str):
    p = Path(dir_tree)

    for file in p.iterdir():
        file.delete(recursive='try')

    assert p.exists() == False


def test_eol_count(tmp_file):
    p = Path(tmp_file)
    assert p.eol_count() == 2
    assert p.eol_count(eol='\n') == 2
    assert p.eol_count(eol='\r') == 0


def test_verify(tmp_file):
    p = Path(tmp_file)

    my_bytes = pathlib.Path(tmp_file).read_bytes()
    shake_128 = hashlib.new('shake_128', my_bytes).hexdigest(128)
    sha256 = hashlib.new('sha256', my_bytes).hexdigest()

    assert p.verify(sha256) == 'sha256'
    assert p.verify(sha256, algorithm='sha256') != None
    assert p.verify(sha256[:14]) == None
    assert p.verify(sha256[:14], algorithm='sha256') == None
    assert p.verify(sha256, algorithm='sha1') == None
    assert p.verify(sha256, algorithm=None, size=10) == 'sha256'

    assert p.verify(shake_128) != None
    assert p.verify(shake_128, algorithm='shake_128') == 'shake_128'
    assert p.verify(shake_128[:32]) != None
    assert p.verify(shake_128[:32], algorithm='shake_128') == 'shake_128'


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

    # test on a directory
    with pytest.raises(PermissionError):
        p.parent.hexdigest()

    # test none existing file
    p.unlink()
    with pytest.raises(FileNotFoundError):
        p.hexdigest()


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


def test_copy(tmp_file, dst_path):
    src = Path(tmp_file)

    result = src.copy(dst_path, parents=True)

    assert isinstance(result, tuple)

    dst, copied = result

    assert copied == True
    assert pathlib.Path(src).is_file() == True
    assert dst == pathlib.Path(dst_path).joinpath(pathlib.Path(tmp_file).name)


def test_move(tmp_file, dst_path):
    src = Path(tmp_file)

    result = src.move(dst_path)

    assert isinstance(result, tuple)

    _, moved = result

    assert moved == True
    assert pathlib.Path(src).is_file() == False


def test_unlink_prune(tmp_file):
    src = Path(tmp_file)

    src.unlink(prune=True)
    assert src.is_file() == False
    assert src.parent.exists() == False


def test_unlink(tmp_file):
    src = Path(tmp_file)

    src.unlink()
    assert src.is_file() == False
    assert src.parent.exists() == True


def test_unlink_missing(tmp_path):
    src = Path(tmp_path) / 'subdir' / 'file_not_found.txt'

    with pytest.raises(FileNotFoundError):
        src.unlink()

    src.parent.mkdir()

    src.unlink(missing_ok=True)
    assert src.parent.is_dir() == True

    src2 = Path(tmp_path) / 'subdir' / 'not_empty.txt'
    src2.touch()

    with pytest.raises(OSError):
        src.unlink(missing_ok=True, prune=True)
    assert src.parent.is_dir() == True

    src.unlink(missing_ok=True, prune='try')
    assert src.parent.is_dir() == True

    src2.unlink()
    src.unlink(missing_ok=True, prune=True)
    assert src.parent.is_dir() == False


def test_rmdir_isfile(tmp_file):
    src = Path(tmp_file)

    with pytest.raises(NotADirectoryError):
        src.rmdir()

    with pytest.raises(NotADirectoryError):
        src.rmdir(recursive=True)

    assert src.exists() == True


def test_rmdir_isdir(dst_path):
    dst = Path(dst_path)
    dst.mkdir()
    file = dst.joinpath('tmp.txt')
    file.touch()

    assert dst.is_dir() == True
    assert file.is_file() == True
    dst.rmdir(recursive=True)
    assert file.exists() == False
    assert dst.exists() == False


def test_touch(tmp_path):
    src = Path(tmp_path) / 'file_not_found.txt'

    src.touch()
    assert src.is_file() == True

    src2 = Path(tmp_path) / 'subdir' / 'file_not_found.txt'

    with pytest.raises(FileNotFoundError):
        src2.touch()

    assert src2.exists() == False

    src2.touch(parents=True)
    assert src2.parent.is_dir() == True
    assert src2.is_file() == True


def test_mtime(tmp_file, tmp_path):
    src = Path(tmp_file)

    start = src.mtime

    assert isinstance(start, int)

    with src.open(mode='at') as f:
        f.write('hallo welt')
        time.sleep(SEC)

    end = src.mtime
    assert (end - start) >= (SEC * 1e9)

    assert (src.mtime - end) == 0

    src2 = Path(tmp_path) / 'subdir_not_exists'

    with pytest.raises(FileNotFoundError):
        _ = src2.mtime

    src2.mkdir()
    assert src2.mtime > 0
