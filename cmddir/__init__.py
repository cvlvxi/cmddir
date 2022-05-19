from __future__ import annotations

import os
import sys

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel as PydanticBaseModel

from cmddir.cmds import Command, SubMenu
from cmddir.types import BashScript, PythonScript, PathLike
from cmddir.utils import to_ansi_art


class BaseModel(PydanticBaseModel):
    """
    Restrict pydantic to only allow declared fields
    """

    class Config:
        extra = "forbid"


@dataclass(init=False)
class CmdPaths:
    """
    os.walk transformer -> SubMenu
    """

    cmd_path_stem: str
    root: str
    root_stem: str
    dirs: List[str] = field(default_factory=list)
    fullpaths: List[Path] = field(default_factory=list)

    @staticmethod
    def create(
        cmd_path_stem: str, root: str, dirs: List[str], files: List[str]
    ) -> CmdPaths:
        root_path = Path(root)
        assert root_path.exists()
        paths = CmdPaths()
        paths.root = root
        paths.cmd_path_stem = cmd_path_stem
        paths.root_stem = root_path.stem
        paths.dirs = []
        for d in dirs:
            CmdPaths.add_init(root_path / d)
            if CmdPaths.path_to_ignore(d):
                paths.dirs.append(d)
        paths.fullpaths = [
            (root_path / f).resolve()
            for f in files
            if not CmdPaths.path_to_ignore(f) and CmdPaths.file_to_include(f)
        ]
        return paths

    @staticmethod
    def path_to_ignore(path: PathLike) -> bool:
        invalid_contains = ["__pycache__", "__init__.py"]
        return any([x in str(path) for x in invalid_contains])

    @staticmethod
    def file_to_include(path: PathLike) -> bool:
        path = Path(path)
        include_suffixes = [".py", ".sh", ".json"]
        return path.suffix in include_suffixes

    @staticmethod
    def add_init(dir_path: PathLike):
        dir_path = Path(dir_path)
        assert dir_path.exists() and dir_path.is_dir()
        init_path = dir_path / "__init__.py"
        if not init_path.exists():
            with open(init_path, "w") as f:
                f.write("")

    def create_menu(self, *args, **kwargs) -> SubMenu:
        cmds = []
        other_cmds = None
        for path in self.fullpaths:
            assert path.exists()
            path_struct = str(path).split(os.sep)
            path_struct = path_struct[path_struct.index(self.cmd_path_stem) + 1 :]
            name = path.stem
            cmd = Command(name=name, orig_name=name, shortcuts=[name[0]])
            add_cmd = True
            match Path(path_struct[-1]).suffix:
                case ".py":
                    cmd.fn = PythonScript(path_struct, *args, **kwargs)
                case ".sh":
                    cmd.fn = BashScript(path, *args, **kwargs)
                case ".json":
                    other_cmds = SubMenu.from_json(path)
                    add_cmd = False
            if add_cmd:
                cmds.append(cmd)
        c = SubMenu(
            name=self.root_stem, 
            orig_name=self.root_stem, 
            cmds=cmds,
            title=to_ansi_art(self.root_stem),
            shortcuts=[self.root_stem[0]]
        )
        if other_cmds:
            c.update(other_cmds)
        return c


def add_modules(root: Path, modules: PathLike | List[PathLike] = None):
    root = Path(root)
    assert root.exists()
    if not isinstance(modules, list):
        modules = [Path(modules)]
    if modules:
        for m in modules:
            append_module(m)
    append_module(str(root))


def append_module(path: PathLike):
    path = Path(path)
    if CmdPaths.path_to_ignore(path):
        return
    assert path.exists()
    if str(path.resolve()) not in sys.path:
        sys.path.append(str(path.resolve()))


def cmd_tree_builder(
    cmd_path: PathLike, modules: PathLike | List[PathLike] = None, *args, **kwargs
) -> List[SubMenu]:
    """
    Build a SubMenu from a directory path

    :root Path to the Command Structure
    :modules Path or Paths to modules to include for use within
    the Command Structure

    A SubMenu will import the root command as a module
    such that inside the tree's subfolders if a python
    file exists it can reference the root as a module

    The first item in the List[SubMenu] will always be the root of the tree
    """

    cmd_path = Path(cmd_path)

    add_modules(cmd_path, modules)

    trees = {}
    tree_list = []
    for root, dirs, files in os.walk(cmd_path):
        if CmdPaths.path_to_ignore(root):
            continue
        print(root, dirs, files)
        # os.walk will duplicate paths so let's not do that
        parts = root.split(os.sep)
        parts_from_stem: List[str] = parts[parts.index(cmd_path.stem):]
        path: str = os.sep.join(parts_from_stem)
        if path not in trees:
            cmds: SubMenu = CmdPaths.create(cmd_path.stem, root, dirs, files).create_menu()
            trees[path] = cmds

    # For every tree find the children and parent
    for tree_root, curr_tree in trees.items():
        p = Path(tree_root)
        parent = str(p.parent) 
        parent_tree = trees[parent] if parent != '.' else None
        if parent_tree:
            parent_tree.children.append(curr_tree)
        curr_tree.parent = parent_tree
        curr_tree.level = len(tree_root.split(os.sep))
        tree_list.append(curr_tree)
    tree_list = sorted(tree_list, key=lambda t: t.level)
    return tree_list



# trees = cmd_tree_builder("test/subdir/test_cmds", "test/helpers")
# print(trees)
