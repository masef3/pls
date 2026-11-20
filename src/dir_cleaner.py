from pathlib import Path
from shutil import move
import json
from enum import Enum
from collections import defaultdict


class Trigger(Enum):
    ON_WATCH = True
    OFF_WATCH = False


class Cleaner:
    conf = Path.cwd() / "pls_conf.json"

    def __init__(self) -> None:
        if not self.conf.exists():
            self.__path = Path.home().joinpath("Downloads")
        else:
            try:
                with open(self.conf, "r") as cfg:
                    self.__path = Path(json.load(cfg)["path"])
            except Exception:
                self.__path = Path.home().joinpath("Downloads")

    def show_path(self) -> None:
        print(self.__path)

    def access_path(self) -> Path:
        return self.__path

    def change_path(self, new_path: Path | None) -> None:

        if new_path is None:
            self.__path = Path.home()
            print(f"Path has been set to {self.__path}")
            return

        assert new_path is not None
        if str(new_path) == "default":
            self.__path = Path.home() / "Downloads"
            print(f"Path has been set to {self.__path}")
            return

        assert new_path.exists()
        self.__path = new_path
        try:
            with open(self.conf, "w") as cfg:
                json.dump({"path": str(self.__path)}, cfg)
        except Exception:
            self.__path = Path.home()

        print(f"Path has been set to {self.__path}")

    def get_ext(self) -> dict[Path, list[Path]]:
        res: dict[Path, list[Path]] = defaultdict(list)
        for file in self.__path.iterdir():
            filename, file_ext = Path(file.stem), Path(file.suffix)
            if Path(file).is_file():
                res[filename].append(file_ext)

        return res

    @staticmethod
    def __check_for_duplicate_path(path_to_file: Path, directory: Path) \
            -> Path:
        target = directory / path_to_file.name
        if not target.exists():
            return target

        name = path_to_file.stem
        suff = path_to_file.suffix

        counter = 1
        while True:
            tmp = directory / f"{name}_{counter}{suff}"
            if not tmp.exists():
                return tmp
            counter += 1

    def package(self, files: dict[Path, list[Path]]) -> None:
        for name, ext_list in files.items():
            for ext in ext_list:

                suff = ext.name.lstrip(".")
                if suff:
                    suff_res = suff
                    file_name = f"{name.name}.{suff}"
                else:
                    suff_res = "other"
                    file_name = name.name

                ext_p = self.__path.joinpath(suff_res)
                full_path = self.__path.joinpath(file_name)

                if ext_p.exists() and not ext_p.is_dir():
                    continue
                ext_p.mkdir(parents=True, exist_ok=True)

                target = self.__check_for_duplicate_path(full_path, ext_p)
                move(full_path, target)

    def recycle(self) -> None:
        for elem in self.__path.iterdir():
            if elem.is_dir() and not any(elem.iterdir()):
                elem.rmdir()

    def print_exts(self, files: dict[Path, list[Path]]) -> None:
        for name, ext_list in files.items():
            print(f"{name.name}")
            for ext in ext_list:
                print(f"{ext.name}", end=" ")
            print("\n")
            print("-------------------")


def confirmation(action: str) -> bool:
    count = 0
    while count < 5:
        inp = input(f"Do you really want to {action}: y/n: ")
        if inp == "yes" or inp == "y":
            return True
        elif inp == "n" or inp == "no":
            return False
        count += 1

    return False


def clean(cleaner: Cleaner) -> None:
    files = cleaner.get_ext()
    cleaner.package(files)
