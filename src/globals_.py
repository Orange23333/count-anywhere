from pathlib import Path

# TODO: Using dict to save values is too slow.
#       Originally, Using one global dict to save all values is
#       for solving the problem of confliction between different modules.
#       Shall we directly use global variables?

GLOBAL_NAME = '_count_anywhere'


def _init_global() -> None:
    if GLOBAL_NAME not in globals():
        globals()[GLOBAL_NAME] = {
            'paths': {
                'app_path': Path(__file__).resolve().parent,
            },
            'version': '0.1.0'
        }


_init_global()


def get_global() -> dict:
    return globals()[GLOBAL_NAME]
