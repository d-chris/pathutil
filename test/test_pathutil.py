import hashlib
import inspect
import pathlib
import time

import pytest

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
    files = [
        'dir1/file1.txt',
        'dir1/file2.txt'
    ]

    for f in map(lambda x: pathlib.Path(tmp_path, x), files):
        f.parent.mkdir(exist_ok=True)
        f.touch(exist_ok=True)

    return str(f.parent)


@pytest.fixture()
def tmp_dir(tmp_path: pathlib.Path):
    files = [
        'fileA.txt',
        'file1.py',
        '.git/HEAD',
        '.git/index',
        '.venv/index'
    ]

    for f in map(lambda x: pathlib.Path(tmp_path, x), files):
        f.parent.mkdir(parents=True, exist_ok=True)
        f.touch(exist_ok=True)

    return str(tmp_path)


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
    p = Path.algorithms_available()

    assert isinstance(p, set)

    for a in p:
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


def test_suffix(tmp_file):
    p = Path(tmp_file)

    assert str(p).endswith('.txt')

    with pytest.raises(ValueError):
        a = p.with_suffix('log')

    with pytest.raises(ValueError):
        a = p.with_suffix('log', separator=False)

    a = p.with_suffix('log', True)
    assert str(a).endswith('.log')

    a = p.with_suffix('log', separator=True)
    assert str(a).endswith('.log')

    a = p.with_suffix('.log')
    assert str(a).endswith('.log')

    a = p.with_suffix('', True)
    assert str(a).endswith(p.stem)

    a = p.with_suffix('')
    assert str(a).endswith(p.stem)


def test_relative(tmp_file, dst_path):
    dst = Path(tmp_file).resolve()
    src = Path(dst_path).resolve()

    with pytest.raises(ValueError):
        src.relative_to(dst)

    z = src.relative_to(dst, uptree=True)
    assert str(z).startswith('..')

    # with pytest.raises(ValueError):
    #     dst.relative_to(src, uptree=True)

    src = src.joinpath('subdir')

    # with pytest.raises(ValueError):
    #    z = dst.relative_to(src, uptree=True)

    z = src.relative_to(dst, uptree=2)
    assert str(z).startswith('..\\..\\')


def test_fnmatch():
    def generator():
        files = [
            'fileA.txt', 'fileB.txt', 'fileC.txt',
            'file1.py', 'file2.py'
        ]

        for f in files:
            yield f

    for i in Path.fnmatch(generator, exclude=['*.py']):
        assert str(i).endswith('.txt')

    result = list(Path.fnmatch(generator))
    assert len(result) == 5


def test_iterdir(tmp_dir):

    p = Path(tmp_dir)

    result = list(p.iterdir())
    assert len(result) == 4

    result = list(p.iterdir(recursive=True))
    assert len(result) == 5

    result = list(p.iterdir(exclude=['*/file?.*']))
    assert len(result) == 2

    result = list(p.iterdir(recursive=True, exclude=['*/file?.txt']))
    assert len(result) == 4


def test_iterdirempty(tmp_dir):
    p = Path(tmp_dir)
    i = p.joinpath('empty')
    i.mkdir()

    result = list(p.iterdir(recursive=True))
    assert len(result) == 6


def test_glob(tmp_dir):

    p = Path(tmp_dir)

    result = list(p.glob('file*'))
    assert len(result) == 2

    result = list(p.glob('file*', exclude=['*.txt']))
    assert len(result) == 1


def test_rglob(tmp_dir):

    p = Path(tmp_dir)

    result = list(p.rglob('index'))
    assert len(result) == 2

    result = list(p.rglob('index', exclude=['*/.venv/*']))
    assert len(result) == 1
