from pathlib import Path
import sys
import argparse as ap
from typing import Any


class Cleaner:
    def __init__(self) -> None:
        self.__path = Path.home().joinpath("Downloads")

    def show_path(self) -> None:
        print(self.__path)

    def change_path(self, new_path: Path | None) -> None:
        if new_path is None:
            self.__path = Path.home()
            print(f"Path has been set to {self.__path}")
            return

        assert new_path is not None
        self.__path = new_path
        print("Path has been set")

    def show_help(self) -> None:
        pass

    def scatter(self, opt: Any) -> None:
        pass

    def get_ext(self) -> set[str]:
        res = set()
        for file in self.__path.iterdir():
            if file.is_file() and file.suffix not in res:
                res.add(file.suffix)

        return res

    def package(self, extensions: set[str]) -> None:
        for ext in extensions:
            ext_p = self.__path.joinpath(ext[1:])
            if not ext_p.is_dir():
                ext_p.mkdir()


def confirmation(action: str) -> bool:
    count = 0
    while count < 5:
        inp = input(f"Do you really want to {action}: y/n")
        if inp == "yes" or inp == "y":
            return True
        elif inp == "n" or "no":
            return False
        count += 1

    return False


def main() -> None:
    args = sys.argv
    cleaner = Cleaner()
    if (len(args) < 2):
        # help
        return

    arg = args[1]
    match arg:
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
        case _:
            print("No match for given argument")


if __name__ == "__main__":
    main()
