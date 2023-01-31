from pathlibutil.pathlist import PathList
from pathlibutil.hashsum import HashFile, hashsum
from pathlibutil import Path


def test_hashsum():
    hashsum(['Pipfile', 'LICENSE', 'README.md', '../pstester.7z'],
            'files.md5')


def test_hexdigest():
    p = PathList(['file1.txt', 'file2.txt', 'file4.txt'])

    def hexdigest(item: Path) -> str:
        return item.hexdigest('md5')

    h = p.apply(hexdigest)

    pass


def test_pathlist():
    file_list = ['file1.txt', 'file2.txt', 'file3.txt']

    p = PathList(file_list)

    p.append(Path('file4.txt'))
    p.append('file5.txt')

    p.extend(['file6.txt', 'file7.txt'])
    p.extend([Path('file7.txt'), 'file8.txt'])
    p.extend(PathList(['file9.txt', 'file10.txt']))

    del p[-1]

    p9 = Path('file10.txt')
    p[9] = p9
    assert id(p[9]) == id(p9)

    pass


def test_pashclass():
    p = HashFile('pathutil.md5')
    l = p.verify()
    p.all('md5')

    pass
