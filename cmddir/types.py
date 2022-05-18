import subprocess
from dataclasses import dataclass, field
from functools import partial
from importlib import import_module
from pathlib import Path
from typing import Callable, List, Optional, TypeAlias, TypeVar

from box import Box
from bullet import colors

K = TypeVar("K")
PathLike: TypeAlias = str | Path
Fg = Box(colors.foreground)
Bg = Box(colors.background)
Color: TypeAlias = Fg | Bg


@dataclass
class BashOut:
    stdout: Optional[str]
    stderr: Optional[str]


class InvalidScriptError(Exception):
    def __init__(self, msg: str):
        self.message = f"Invalid Script found. {msg}"
        super().__init__(self.message)


class PythonScript(Callable):
    """
    Allow for Python Scripts that have a main function in them
    The def main function can take *args, **kwargs such that
    things can be passed from a previous step to this

    Optionally return whatever the function produces
    """

    def __init__(self, path_struct: List[str], *args, **kwargs):
        py_file = path_struct[-1].replace(".py", "")
        path_struct[-1] = py_file
        module_path = ".".join(path_struct)
        try:
            imported_module = import_module(module_path)
        except ModuleNotFoundError:
            raise InvalidScriptError(f"Does the script: {module_path} exist?")
        # Check for main method
        if "main" not in dir(imported_module):
            raise InvalidScriptError(f"No main method in script: {module_path}?")
        main_method = imported_module.main
        if not callable(main_method):
            raise InvalidScriptError(f"Is main a method in {module_path}?")
        self.fn = partial(main_method, *args, **kwargs)

    def __call__(self) -> Optional[K]:
        return self.fn()


class BashScript(Callable):
    """
    Allow for Bash scripts that are defined to be executed
    Allowed is the ability to pass arguments *args, **kwargs
    such that things can be passed from a previous step to this

    Optionally return whatever the bash script produces
    seperating the stdout and stderr within the BashOut container
    """

    def __init__(self, path: PathLike, *args, **kwargs):
        self.path = Path(path)
        assert self.path.exists()
        self.cmd = ["bash", self.path]
        if args:
            self.cmd += [str(x) for x in args]
        if kwargs:
            for k, v in kwargs.items():
                self.cmd.append(f"--{str(k)}")
                self.cmd.append(str(v))

    def __call__(self) -> BashOut:
        ps = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        o = BashOut()
        o.stdout = ps.stdout.read().decode()
        o.stderr = ps.stderr.read().decode()
        return o
