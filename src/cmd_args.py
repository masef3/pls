def help() -> None:
    msg = """
    pls is an automatization utility for linux.

    Usage:
        pls [command] [flags]

    Commands:
        clean       Recycles files into directories that differ by extension
        change_path Changes working directory of the program

    Flags:
        -h, --help  help for pls
    """
    print(msg)
