from __future__ import annotations

import sys
from dataclasses import field
from enum import Enum
from pathlib import Path
from typing import Callable, List, Optional, TypeAlias, Tuple

from box import Box
from bullet import Bullet, Check, keyhandler
from bullet.charDef import NEWLINE_KEY
from pydantic.dataclasses import dataclass

from cmddir.types import Bg, Fg, K
from cmddir.utils import clear_screen, getjson, notify, style

VIM_SHORTCUTS = ["j", "k"]


class HotkeyError(Exception):
    def __init__(self, cmd_name, key):
        self.message = f"Invalid hotkey: {key} supplied to {cmd_name}"
        super().__init__(self.message)


@dataclass
class Command:
    name: Optional[str]
    shortcuts: Optional[List[str]] = None
    orig_name: Optional[str] = None
    desc: str = ""
    fn: Optional[Callable] = None
    custom_shortcuts: List[str]= field(default_factory=list)
    aliases: List[str] = field(default_factory=list)

    def __post_init__(self):
        """
        Check that our shortcuts/aliases are correct
        """
        if self.aliases:
            for k in self.aliases:
                if len(k) == 1:
                    raise HotkeyError(self.name, k)

        if self.shortcuts:
            for k in self.shortcuts:
                if len(k) > 1:
                    raise HotkeyError(self.name, k)
                # Disallow j,k so we can use vim keys
                if k in VIM_SHORTCUTS:
                    raise HotkeyError(self.name, k)

    def update(self, other: Command):
        self.name = other.name or self.name
        self.desc = other.desc or self.desc
        if other.shortcuts:
            self.shortcuts += other.shortcuts 
            self.custom_shortcuts = other.shortcuts

    def match(self, matcher: Optional[str]) -> Optional[Command]:
        if not matcher:
            return None
        return (
            any([matcher == k for k in self.aliases + self.shortcuts])
            or matcher == self.name
        )

    def hotkey_str(self) -> str:
        val = ""
        if [x for x in self.shortcuts if x]:
            val += "["
            val += ",".join(self.shortcuts)
            val += "]"
        if [x for x in self.aliases if x]:
            val += "("
            val += ",".join(self.aliases)
            val += ")"
        return val

    def str(self, max_align: Optional[MaxAlign] = None) -> str:
        buffer = 10
        # Format
        hotkey_str = self.hotkey_str()
        diff = max_align.aliases + buffer - len(hotkey_str)
        hotkey_str += " " * diff if diff > 0 else " "
        name_str = self.name
        diff = max_align.name + buffer - len(name_str)
        name_str += " " * diff if diff > 0 else ""
        val = hotkey_str + name_str
        if self.desc:
            val += f": {self.desc}"
        return val

    @staticmethod
    def str_to_cmdname(cmd_str) -> str:
        # Check Format above as to how this works
        name = [x for x in cmd_str.split(" ") if x][1]
        if ":" in name:
            name = name.split(":")[0].strip()
        return name


class CommandsType(Enum):
    Dropdown = 0
    Selectable = 1


@dataclass
class Commands:
    cmds: Optional[List[Command]]
    name: Optional[str] = None
    orig_name: Optional[str] = None
    msg: str = ""
    title: str = ""
    title_col: str = Fg.yellow
    desc: str = ""
    msg_col: str = Fg.yellow
    level: int = 0
    indent_by: int = 2
    bullet: str = ">"
    check: str = "√"
    ordered_hotkeys: bool = True
    type: CommandsType = CommandsType.Dropdown
    fn: Optional[Callable] = None

    @staticmethod
    def from_json(j: str | Path | str) -> Commands:
        data = j
        if not isinstance(data, dict):
            data = getjson(data)
        subcmds: List[Command] = data.get("cmds") or []
        if subcmds:
            subcmds = [Command(**x) for x in subcmds]
            data["cmds"] = subcmds
        return Commands(**data)

    def update(self, other: Commands):
        self.name = other.name or self.name
        self.msg = other.msg or self.msg
        self.title = other.title or self.title
        self.title_col = other.title_col or self.title_col
        self.desc = other.desc or self.desc
        self.msg_col = other.msg_col or self.msg_col
        self.bullet = other.bullet or self.bullet
        self.check = other.check or other.check
        for cmd in self.cmds:
            for o_cmd in other.cmds:
                if o_cmd.orig_name == cmd.orig_name:
                    cmd.update(o_cmd)
        self.resolve_shortcut_conflicts()

    def resolve_shortcut_conflicts(self):
        while conflicts := self.conflicting_commands():
            self.bump_shortcut_conflicts(conflicts)

    def conflicting_commands(self) -> List[Tuple[Command, List[str], int]]:
        conflicting = []
        for cmd in self.cmds:
            for other_cmd in self.cmds:
                if cmd == other_cmd:
                    continue
                # Find violating shortcuts for cmd
                bad_shortcuts = [s for s in cmd.shortcuts if s in other_cmd.shortcuts]
                num_custom_bad = len([s for s in bad_shortcuts if s in cmd.custom_shortcuts])
                if bad_shortcuts:
                    conflicting.append((cmd, bad_shortcuts, num_custom_bad))
                continue
        conflicting = sorted(conflicting, key=lambda c: c[2])
        return conflicting

    def bump_shortcut_conflicts(self, conflicting: List[Tuple[Command, List[str], int]]):
        updated_shortcuts = []
        for cmd, bad_shortcuts, _ in conflicting:
            for s in bad_shortcuts:
                if s not in updated_shortcuts:
                    updated_shortcuts.append(s)
                    next_char = chr(ord(s) + 1)
                    cmd.shortcuts[cmd.shortcuts.index(s)] = next_char

    def prompt(self) -> Command | List[Command]:
        max_align = MaxAlign(
            aliases=max([len(cmd.hotkey_str()) for cmd in self.cmds]),
            name=max([len(cmd.name) for cmd in self.cmds]),
            desc=max([len(cmd.desc) for cmd in self.cmds]),
        )
        match self.type:
            case CommandsType.Dropdown:
                return self.dropdown(max_align)
            case CommandsType.Selectable():
                return self.selection(max_align)
            case _:
                raise NotImplementedError()

    def order_hotkeys(self):
        """Order by shortcuts"""
        self.cmds = sorted(self.cmds, key=lambda cmd: cmd.shortcuts)

    def all_shortcuts(self) -> List[str]:
        return [key for cmd in self.cmds for key in cmd.shortcuts]

    def dropdown(self, max_align: MaxAlign) -> Command:
        notify(self.msg, self.msg_col)
        if self.ordered_hotkeys:
            self.order_hotkeys()
        CBullet = generate_bullet(self)
        _cli = CBullet(
            prompt="",
            choices=[cmd.str(max_align) for cmd in self.cmds],
            indent=self.indent_by * self.level,
            align=2,
            margin=2,
            shift=0,
            bullet=self.bullet,
            bullet_color=Fg.magenta,
            word_color=Fg.blue,
            word_on_switch=Fg.green,
            background_color=Bg.default,
            background_on_switch=Bg.default,
            pad_right=5,
        )
        matcher = _cli.launch()
        matcher = Command.str_to_cmdname(matcher)
        chosen = self.find_command(matcher)
        assert chosen
        return chosen

    def selection(self, max_align: Optional[MaxAlign]) -> List[Command]:
        notify(self.msg, self.msg_col)
        _cli = MinMaxCheck(
            prompt="",
            indent=self.indent_by * self.level,
            choices=[cmd.str(max_align) for cmd in self.cmds],
            min_selections=1,
            max_selections=len(self.cmds),
            return_index=False,
            margin=2,
            pad_right=5,
            align=5,
            shift=0,
            check=self.check,
            check_color=Fg.red,
            check_on_switch=Fg.red,
            word_color=Fg.blue,
            word_on_switch=Fg.green,
            background_color=Bg.default,
            background_on_switch=Bg.default,
        )
        matcher = _cli.launch()
        matcher = Command.str_to_cmdname(matcher)
        chosen = self.find_commands(matcher)
        return chosen

    def find_command(self, matcher: Optional[str]) -> Optional[Command]:
        if not matcher:
            return None
        chosen = [cmd for cmd in self.cmds if cmd.match(matcher)]
        assert len(chosen) <= 1
        return chosen[0] if chosen else None

    def find_commands(self, matcher: str) -> List[Command]:
        return [cmd for cmd in self.cmds if cmd.match(matcher)]


def generate_bullet(cmds: Commands):
    """
    Custom Bullet Generator

    Will generate a Bullet with allshortcuts
    within cmds being registered as keyable.

    This allows these hotkeys to be triggered whilst
    in a Menu system which currently is not supported
    via Bullet.

    """
    handlers = {"cmds": cmds}
    # Vim Key Bindings for Menu

    @keyhandler.register(ord("k"))
    def moveUp(self):
        self.moveUp()

    @keyhandler.register(ord("j"))
    def moveDown(self):
        self.moveDown()

    handlers["_moveUp"] = moveUp
    handlers["_moveDown"] = moveDown

    def register_key_handler(key):
        @keyhandler.register(ord(key))
        def f(self):
            chosen_cmd = self.cmds.find_command(key)
            choices = [Command.str_to_cmdname(x) for x in self.choices]
            if chosen_cmd:
                return self.choices[choices.index(chosen_cmd.name)]

        return f

    for key in cmds.all_shortcuts():
        handlers[key] = register_key_handler(key)
    CBullet = type("CBullet", (Bullet,), handlers)
    return CBullet


class MinMaxCheck(Check):
    def __init__(self, min_selections=0, max_selections=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.min_selections = min_selections
        self.max_selections = max_selections
        if max_selections is None:
            self.max_selections = len(self.choices)

    @keyhandler.register(NEWLINE_KEY)
    def accept(self):
        if self.valid():
            return super().accept()

    def valid(self):
        return (
            self.min_selections
            <= sum(1 for c in self.checked if c)
            <= self.max_selections
        )


@dataclass
class MaxAlign:
    aliases: int
    name: int
    desc: int


def cli(cmds: Commands):
    """
    When a method is wrapped with @cli(cmds)

    @cli(cmds=cmds)
    def my_method(some_param, other_param, out):
        pass

    This exposes to my_method an `out` variable.

    out: Out
    See: Out Type for what is contained without out
    This is a out variable that will contain the necessary
    components that you can use in your decorated method

    chosen: C
    You will still need to match on the out.chosen variable
    if you want to do some conditional behaviour

    skips: S
    This is used to pass a List[str] to avoid having
    to get prompted for a selection/dropdown

    args: A
    Since the *args, **kwargs passed to wrapper may have some
    overlap with the previous call we want to pop the kwargs
    You will need to retrieve the args supplied from out.args

    trace: T
    This is a trace of what the chosens were previously
    We also want to keep a trace of the args passed to each Commands
    layer in order for us to trace what's going on
    """

    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            clear_screen()
            if cmds.title:
                print(style(cmds.title, cmds.title_col))
            try:
                out: COutput = kwargs.pop("out")
            except:
                skips = sys.argv[1:] if len(sys.argv) > 1 else []
                out: COutput = COutput(skips=skips)
            skips: List[str] = out.skips
            matcher: Optional[str] = None
            rest: List[str] = []
            chosen: Optional[C] = None
            match skips:
                case [m, *ms]:
                    matcher = m
                    rest = ms
                case [m]:
                    matcher = m
            chosen = cmds.find_command(matcher)
            out.skips = rest
            if not chosen:
                chosen = cmds.prompt()
            out.chosen = chosen
            a = {}
            kwargs_keys = [k for k in kwargs.keys()]
            for k in kwargs_keys:
                a[k] = kwargs.pop(k)
            out.args = a
            out.args = Box(a)
            clear_screen()
            return func(out=out, *args, **kwargs)

        return wrapper

    return decorator


C: TypeAlias = Command | List[Command]


@dataclass
class COutput:
    chosen: Optional[C] = None
    skips: List[str] = field(default_factory=list)


Args: TypeAlias = Box[str, K]


@dataclass
class Trace:
    name: str
    fn: Callable
    args: Args
    out: COutput
