from pathlib import Path
import sys
import argparse as ap
from typing import Any
from shutil import move


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

    def get_ext(self) -> dict[Path, Path]:
        res: dict[Path, Path] = {}
        for file in self.__path.iterdir():
            filename, file_ext = Path(file.stem), Path(file.suffix)
            if Path(file).is_file() and file_ext not in res.values():
                res[filename] = file_ext

        return res

    def package(self, files: dict[Path, Path]) -> None:
        for name, ext in files.items():
            if ext.is_dir():
                continue

            suff = ext.name.lstrip(".")
            ext_p = self.__path.joinpath(suff)
            full_path = self.__path.joinpath(f"{name.name}.{suff}")

            ext_p.mkdir(parents=True, exist_ok=True)
            move(full_path, ext_p.joinpath(full_path.name))


def confirmation(action: str) -> bool:
    count = 0
    while count < 5:
        inp = input(f"Do you really want to {action}: y/n: \n")
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
