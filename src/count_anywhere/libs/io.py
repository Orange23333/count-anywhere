from pathlib import Path
from typing import Any

import ruamel.yaml

# TODO: Using QFile 来确保文件读写的一致性。

def read_all_from_file(path: str) -> Any:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content

def load_yaml_from_file(path: str) -> Any:
    y = ruamel.yaml.YAML(typ='safe', pure=False)
    doc = read_all_from_file(path)
    t = y.load(doc)
    return t

def save_yaml_to_file(path: str, data: Any) -> None:
    # TODO: format: null -> ~, tending = 2

    y = ruamel.yaml.YAML(typ='safe', pure=False)
    with open(path, 'w', encoding='utf-8') as f:
        y.dump(data, f)
