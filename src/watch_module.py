from watchdog.observers import Observer
from pathlib import Path
from watchdog.events import FileSystemEventHandler, FileSystemEvent
import time
from dir_cleaner import Cleaner, clean


class Logger(FileSystemEventHandler):

    def __init__(self, on_watch: bool) -> None:
        super().__init__()
        self.on_watch = on_watch
        self.call_flag: bool = False

    def on_any_event(self, event: FileSystemEvent) -> None:
        if self.on_watch:
            match event.event_type:
                case "created":
                    print("Created file/directory: ", event.src_path)
                case "modified":
                    print("Modified file/directory: ", event.src_path)
                case "deleted":
                    print("Deleted file/directory: ", event.src_path)
                case "moved":
                    print("Moved file/directory", event.src_path)

        elif not self.call_flag:
            self.call_flag = True
            try:
                cleaner = Cleaner()
                match event.event_type:
                    case "created" | "modified":
                        clean(cleaner)
            finally:
                self.call_flag = False

        elif self.call_flag:
            return


class Wd_(Logger):
    def __init__(self, wd_path: Path, on_watch: bool) -> None:
        super().__init__(on_watch)
        self.__wd_path = wd_path
        self.observer = Observer()

    def watch(self) -> None:
        """
        only spectates and reports the interactions with given directory.
        """
        self.observer.schedule(self, self.__wd_path, recursive=False)
        self.observer.start()

        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            self.observer.stop()


class Runner(Wd_):
    def __init__(self, wd_path: Path, on_watch: bool) -> None:
        super().__init__(wd_path, on_watch)

    def start(self) -> None:
        self.watch()
