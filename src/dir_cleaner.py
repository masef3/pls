from pathlib import Path
import sys


class Target:
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


def main() -> None:
    target = Target()
    args = sys.argv
    if (len(args) < 2):
        print("Not enough arguments")  # DO HELP OUTPUT HERE
        return

    arg = args[1]
    match arg:
        case "show":
            target.show_path()
        case "change":
            if (len(args) < 3):
                target.change_path(None)
            else:
                target.change_path(Path(args[2]))

        case _:
            print("No match for given argument")


if __name__ == "__main__":
    main()
