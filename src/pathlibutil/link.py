from pathlib import Path
import LnkParse3
import struct
import warnings


def PathLnk(filename: str) -> Path:
    file = Path(filename)

    if not file.is_file():
        return file

    try:
        with warnings.catch_warnings(record=True) as w:
            with file.open(mode='rb') as f:
                lnk = LnkParse3.lnk_file(f)
    except struct.error as e:
        return file

    link_info = lnk.get_json().get('link_info', {})

    location = link_info.get('location', '')

    try:
        if location.casefold() == 'local':
            p = Path(link_info.get('local_base_path'))
        else:
            location_info = link_info.get('location_info', {})
            p = Path(location_info.get('net_name')).joinpath(
                link_info.get('common_path_suffix'))
    except TypeError as e:
        return file

    return p.resolve()
