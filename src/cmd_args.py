import argparse


def help_() -> None:
    msg = """
    pls is an automatization utility for linux.

    Usage:
        pls [command] [flags]

    Commands:
        clean       Recycles files into directories that differ by extension
        change      Changes working directory of the program
        watch       Watches and prints all modifications of wanted directory
        cleanbg     Runs online cleaner
        show        Shows working directory
        print_exts  Prints mapping of filename -> extensions

    Flags:
        -h, --help, help
    """
    print(msg)

