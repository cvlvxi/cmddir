import contextlib
import importlib
import json
import os
import sys
import traceback
from pathlib import Path

from box import Box
from bullet import colors

from .types import Color, Fg, PathLike

_colors = Box(
    {"notify": Fg.yellow, "notify_kv": {
        "k": Fg.green, "v": Fg.yellow, "sep": Fg.green}}
)


def to_ansi_art(word: str, indent_right: int = 0) -> str:
    final_parts = {}
    final_string = r""
    for letter in word:
        if letter == " ":
            parts = [" "] * 6
        else:
            curr = alphabet[letter]
            parts = [x for x in curr.split("\n") if x]
        assert len(parts) == 6
        for idx, ansi_part in enumerate(parts):
            if idx not in final_parts:
                final_parts[idx] = []
            final_parts[idx].append(ansi_part)
    for idx, parts in final_parts.items():
        final_string += " " * indent_right + " ".join(parts) + "\n"
    return final_string


def style(msg: str, col: Color):
    return col + msg + colors.RESET


def notify(
    msg: str,
    col: Color = None,
    sep: str = False,
    lines_after: int = 0,
    lines_before: int = 0,
):
    total_len = len(msg)
    col = col or _colors.notify
    val = "\n" * lines_before
    val += style(str(msg), col) + "\n"
    val += "" if not sep else style("-" * total_len, col)
    val += "\n" * lines_after
    print(val)


def notify_kv(k: str, v: str, no_print: bool = False, sep: bool = False):
    k = str(k)
    v = str(v)
    total_len = len(k + v) + 2
    val = style(f"{k}: ", _colors.notify_kv.k)
    val += style(v, _colors.notify_kv.v)
    if sep:
        val += "\n"
        val += style("-" * total_len, _colors.notify_kv.sep)
        val += "\n"
    if not no_print:
        print(val)
    else:
        return val


def notify_d(d: dict, no_print=False, level=0):
    val = ""
    for k, v in d.items():
        if isinstance(v, dict):
            val += style(f"{str(k)}:\n", _colors.notify_kv.k)
            val += notify_d(v, no_print, level + 1)
        else:
            if level > 0:
                val += "  " * level
            val += style(f"{str(k)}: ", _colors.notify_kv.k)
            val += style(str(v), _colors.notify_kv.v)
            val += "\n"
    if no_print:
        return val
    else:
        print("\n" + val + "\n")


def clear_screen():
    os.system("cls||clear")


@contextlib.contextmanager
def cd(path: PathLike):
    CWD = os.getcwd()
    os.chdir(path)
    try:
        yield
    except:
        print("Exception caught: ", sys.exc_info()[0])
        print(traceback.format_exc())
    finally:
        os.chdir(CWD)


def getjson(path: PathLike) -> dict:
    path = Path(path)
    assert path.exists()
    data = json.load(open(path))
    return data


alphabet = {
    "a": r"""
 █████╗ 
██╔══██╗
███████║
██╔══██║
██║  ██║
╚═╝  ╚═╝
""",
    "b": r"""
██████╗ 
██╔══██╗
██████╔╝
██╔══██╗
██████╔╝
╚═════╝ 
""",
    "c": r"""
 ██████╗
██╔════╝
██║     
██║     
╚██████╗
 ╚═════╝
""",
    "d": r"""
██████╗ 
██╔══██╗
██║  ██║
██║  ██║
██████╔╝
╚═════╝ 
""",
    "e": r"""
███████╗
██╔════╝
█████╗  
██╔══╝  
███████╗
╚══════╝
""",
    "f": r"""
███████╗
██╔════╝
█████╗  
██╔══╝  
██║     
╚═╝     
""",
    "g": r"""
 ██████╗ 
██╔════╝ 
██║  ███╗
██║   ██║
╚██████╔╝
 ╚═════╝ 
""",
    "h": r"""
██╗  ██╗
██║  ██║
███████║
██╔══██║
██║  ██║
╚═╝  ╚═╝
""",
    "i": r"""
██╗
██║
██║
██║
██║
╚═╝
""",
    "j": r"""
     ██╗
     ██║
     ██║
██   ██║
╚█████╔╝
 ╚════╝ 
""",
    "k": r"""
██╗  ██╗
██║ ██╔╝
█████╔╝ 
██╔═██╗ 
██║  ██╗
╚═╝  ╚═╝
""",
    "l": r"""
██╗     
██║     
██║     
██║     
███████╗
╚══════╝
""",
    "m": r"""
███╗   ███╗
████╗ ████║
██╔████╔██║
██║╚██╔╝██║
██║ ╚═╝ ██║
╚═╝     ╚═╝
""",
    "n": r"""
███╗   ██╗
████╗  ██║
██╔██╗ ██║
██║╚██╗██║
██║ ╚████║
╚═╝  ╚═══╝
""",
    "o": r"""
 ██████╗ 
██╔═══██╗
██║   ██║
██║   ██║
╚██████╔╝
 ╚═════╝ 
""",
    "p": r"""
██████╗ 
██╔══██╗
██████╔╝
██╔═══╝ 
██║     
╚═╝     
""",
    "q": r"""
 ██████╗ 
██╔═══██╗
██║   ██║
██║▄▄ ██║
╚██████╔╝
 ╚══▀▀═╝ 
""",
    "r": r"""
██████╗ 
██╔══██╗
██████╔╝
██╔══██╗
██║  ██║
╚═╝  ╚═╝
""",
    "s": r"""
███████╗
██╔════╝
███████╗
╚════██║
███████║
╚══════╝
""",
    "t": r"""
████████╗
╚══██╔══╝
   ██║   
   ██║   
   ██║   
   ╚═╝   
""",
    "u": r"""
██╗   ██╗
██║   ██║
██║   ██║
██║   ██║
╚██████╔╝
 ╚═════╝ 
""",
    "v": r"""
██╗   ██╗
██║   ██║
██║   ██║
╚██╗ ██╔╝
 ╚████╔╝ 
  ╚═══╝  
""",
    "w": r"""
██╗    ██╗
██║    ██║
██║ █╗ ██║
██║███╗██║
╚███╔███╔╝
 ╚══╝╚══╝ 
""",
    "x": r"""
██╗  ██╗
╚██╗██╔╝
 ╚███╔╝ 
 ██╔██╗ 
██╔╝ ██╗
╚═╝  ╚═╝
""",
    "y": r"""
██╗   ██╗
╚██╗ ██╔╝
 ╚████╔╝ 
  ╚██╔╝  
   ██║   
   ╚═╝   
""",
    "z": r"""
███████╗
╚══███╔╝
  ███╔╝ 
 ███╔╝  
███████╗
╚══════╝
""",
    "!": r"""
██╗
██║
██║
╚═╝
██╗
╚═╝
""",
    "@": r"""
 ██████╗ 
██╔═══██╗
██║██╗██║
██║██║██║
╚█║████╔╝
 ╚╝╚═══╝ 
""",
    "#": r"""
 ██╗ ██╗ 
████████╗
╚██╔═██╔╝
████████╗
╚██╔═██╔╝
 ╚═╝ ╚═╝ 
""",
    "$": r"""
▄▄███▄▄·
██╔════╝
███████╗
╚════██║
███████║
╚═▀▀▀══╝
""",
    "%": r"""
██╗ ██╗
╚═╝██╔╝
  ██╔╝ 
 ██╔╝  
██╔╝██╗
╚═╝ ╚═╝
""",
    "^": r"""
 ███╗ 
██╔██╗
╚═╝╚═╝
      
      
      
""",
    "&": r"""
   ██╗   
   ██║   
████████╗
██╔═██╔═╝
██████║  
╚═════╝  
""",
    "*": r"""
      
▄ ██╗▄
 ████╗
▀╚██╔▀
  ╚═╝ 
      
""",
    "(": r"""
 ██╗
██╔╝
██║ 
██║ 
╚██╗
 ╚═╝
""",
    ")": r"""
██╗ 
╚██╗
 ██║
 ██║
██╔╝
╚═╝ 
""",
    "-": r"""
      
      
█████╗
╚════╝
      
      
""",
    "_": r"""
        
        
        
        
███████╗
╚══════╝
""",
    "[": r"""
███╗
██╔╝
██║ 
██║ 
███╗
╚══╝
""",
    "]": r"""
███╗
╚██║
 ██║
 ██║
███║
╚══╝
""",
    ";": r"""
   
██╗
╚═╝
▄█╗
▀═╝
   
""",
    ":": r"""
   
██╗
╚═╝
██╗
╚═╝
   
""",
    "<": r"""
  ██╗
 ██╔╝
██╔╝ 
╚██╗ 
 ╚██╗
  ╚═╝
""",
    ">": r"""
██╗  
╚██╗ 
 ╚██╗
 ██╔╝
██╔╝ 
╚═╝  
""",
    "?": r"""
██████╗ 
╚════██╗
  ▄███╔╝
  ▀▀══╝ 
  ██╗   
  ╚═╝   
""",
    "1": r"""
 ██╗
███║
╚██║
 ██║
 ██║
 ╚═╝
""",
    "2": r"""
██████╗ 
╚════██╗
 █████╔╝
██╔═══╝ 
███████╗
╚══════╝
""",
    "3": r"""
██████╗ 
╚════██╗
 █████╔╝
 ╚═══██╗
██████╔╝
╚═════╝ 
""",
    "4": r"""
██╗  ██╗
██║  ██║
███████║
╚════██║
     ██║
     ╚═╝
""",
    "5": r"""
███████╗
██╔════╝
███████╗
╚════██║
███████║
╚══════╝
""",
    "6": r"""
 ██████╗ 
██╔════╝ 
███████╗ 
██╔═══██╗
╚██████╔╝
 ╚═════╝ 
""",
    "7": r"""
███████╗
╚════██║
    ██╔╝
   ██╔╝ 
   ██║  
   ╚═╝  
""",
    "8": r"""
 █████╗ 
██╔══██╗
╚█████╔╝
██╔══██╗
╚█████╔╝
 ╚════╝ 
""",
    "9": r"""
 █████╗ 
██╔══██╗
╚██████║
 ╚═══██║
 █████╔╝
 ╚════╝ 
""",
    "0": r"""
 ██████╗ 
██╔═████╗
██║██╔██║
████╔╝██║
╚██████╔╝
 ╚═════╝ 
"""
}
