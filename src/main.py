import sys
from dir_cleaner import Cleaner, confirmation, Trigger
from pathlib import Path
import watch_module as wm
from cmd_args import help_


def main() -> None:
    args = sys.argv
    if len(args) > 3:
        print("Too many arguments")
        return

    cleaner = Cleaner()

    if (len(args) < 2):
        help_()
        return

    arg = args[1]

    match arg:
        case "--help" | "-h" | "help":
            help_()

        case "show":
            cleaner.show_path()

        case "change":
            if (len(args) < 3):
                cleaner.change_path(None)
            else:
                cleaner.change_path(Path(args[2]))

        case "clean":
            inp = confirmation("package")
            if inp:
                exts = cleaner.get_ext()
                cleaner.package(exts)

        case "cleanbg":
            runner = wm.Runner(cleaner.access_path(), Trigger.OFF_WATCH)
            runner.start()

        case "watch":
            runner = wm.Runner(cleaner.access_path(), Trigger.ON_WATCH)
            runner.start()

        case "recycle":
            cleaner.recycle()

        case _:
            print("No match for given argument")


if __name__ == "__main__":
    main()
