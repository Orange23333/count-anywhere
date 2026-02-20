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
            'paths': {
                'app_path': Path(__file__).resolve().parent,
            },
            'version': '0.1.0'  # TODO: Get version from setup.py
        }


_init_global()


def get_global() -> PathDict:
    return PathDict(globals()[GLOBAL_NAME])
