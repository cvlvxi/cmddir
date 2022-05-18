from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import partial
from importlib import import_module
from pathlib import Path
from typing import TypeAlias, List, Callable, Optional


PathLike: TypeAlias = str | Path

# class PythonScript(Callable):
#     """
#     Allow for Python Scripts that have a main function in them
#     The def main function can take *args, **kwargs such that
#     things can be passed from a previous step to this

#     Optionally return whatever the function produces
#     """

#     def __init__(self, path_struct: List[str]):
#         py_file = path_struct[-1].replace(".py", "")
#         path_struct[-1] = py_file
#         self.fn = partial(import_module, ".".join(path_struct))

#     def __call__(self, *args, **kwargs) -> Optional[K]:
#         return self.fn(*args, **kwargs)


@dataclass(init=False)
class CmdPaths:
    root: str
    dirs: List[str] = field(default_factory=list)
    files: List[str] = field(default_factory=list)

    @staticmethod
    def create(root: str, dirs: List[str], files: List[str]) -> CmdPaths:
        paths = CmdPaths()
        paths.root = root
        breakpoint()
        paths.dirs = [d for d in dirs if not CmdPaths.path_to_ignore(d)]
        paths.files = [f for f in files if not CmdPaths.path_to_ignore(f)]
        return paths

    @staticmethod
    def path_to_ignore(path: PathLike):
        invalid_contains = ["__pycache__", "__init__.py"]
        return any([x in str(path) for x in invalid_contains])


for root, dirs, files in os.walk("subdir/test_cmds"):
    if CmdPaths.path_to_ignore(root):
        continue
    paths = CmdPaths.create(root, dirs, files)
    print(paths)
