from pathlib import Path

from path_dict import PathDict

# TODO: Using dict to save values is too slow.
#       Originally, Using one global dict to save all values is
#       for solving the problem of confliction between different modules,
#       and the most important - duplicated variables.
#       Shall we directly use global variables?

GLOBAL_NAME = '_count_anywhere'


def _init_global() -> None:
    if GLOBAL_NAME not in globals():
        globals()[GLOBAL_NAME] = {
            'paths': {},
            'version': '0.1.0'  # TODO: Get version from setup.py
        }


_init_global()


def get_global() -> PathDict:
    return PathDict(globals()[GLOBAL_NAME])

def get_paths() -> PathDict:
    return PathDict(get_global(), 'paths')

def set_app_path(path: str | Path) -> None:
    cfg = get_paths()
    cfg['app_path'] = path
