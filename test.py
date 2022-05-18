from cmddir import cmd_tree_builder
from pprint import pprint
from cmddir.cmds import cli

trees = cmd_tree_builder("test/subdir/test_cmds", "test/helpers")


@cli(cmds=trees[0].commands)
def main():
    pass

main()
