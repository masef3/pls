"""Pytest tests for the "clean" feature of the folder cleaner.

Covers: Cleaner.get_ext, Cleaner.package, clean(), confirmation() and the
"clean" command flow (confirmation -> get_ext -> package).

If your module is not called `folder_cleaner.py`, change MODULE below.
Run with:  pytest -v
"""
import builtins
import json
import sys
from pathlib import Path

import pytest

# The module lives one directory above this test file (../folder_cleaner.py)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

MODULE = "dir_cleaner"
mod = __import__(MODULE)
Cleaner = mod.Cleaner
clean = mod.clean
confirmation = mod.confirmation


# --------------------------------------------------------------------------- #
# Fixtures and helpers
# --------------------------------------------------------------------------- #
@pytest.fixture
def env(tmp_path, monkeypatch):
    """Isolated environment: fake HOME, fake config file, separate work dir.

    The config file lives OUTSIDE the work dir, otherwise it would be a .json
    file that gets sorted together with the test files.
    """
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))

    conf_dir = tmp_path / "conf"
    conf_dir.mkdir()
    conf = conf_dir / "pls_conf.json"
    monkeypatch.setattr(Cleaner, "conf", conf)

    work = tmp_path / "work"
    work.mkdir()

    return {"home": home, "conf": conf, "work": work, "tmp": tmp_path}


@pytest.fixture
def work(env):
    return env["work"]


@pytest.fixture
def cleaner(env):
    """A Cleaner pointed at the empty work directory via the config file."""
    env["conf"].write_text(json.dumps({"path": str(env["work"])}))
    return Cleaner()


def touch(directory: Path, *names: str, content: str = "x") -> None:
    for name in names:
        (directory / name).write_text(content)


def listing(directory: Path) -> set[str]:
    return {p.name for p in directory.iterdir()}


# --------------------------------------------------------------------------- #
# get_ext
# --------------------------------------------------------------------------- #
class TestGetExt:
    def test_empty_directory(self, cleaner):
        assert dict(cleaner.get_ext()) == {}

    def test_single_file(self, cleaner, work):
        touch(work, "report.pdf")
        assert dict(cleaner.get_ext()) == {Path("report"): [Path(".pdf")]}

    def test_same_stem_different_extensions_are_grouped(self, cleaner, work):
        touch(work, "a.txt", "a.pdf")
        res = cleaner.get_ext()
        assert set(res) == {Path("a")}
        assert {e.name for e in res[Path("a")]} == {".txt", ".pdf"}

    def test_directories_are_ignored(self, cleaner, work):
        (work / "folder").mkdir()
        (work / "archive.zip").mkdir()  # a directory that looks like a file
        touch(work, "real.txt")
        assert set(cleaner.get_ext()) == {Path("real")}

    def test_multi_dot_name_uses_last_suffix(self, cleaner, work):
        touch(work, "archive.tar.gz")
        assert dict(cleaner.get_ext()) == {Path("archive.tar"): [Path(".gz")]}

    def test_file_without_extension_has_empty_suffix(self, cleaner, work):
        touch(work, "README")
        res = cleaner.get_ext()
        assert res[Path("README")] == [Path("")]

    def test_does_not_modify_filesystem(self, cleaner, work):
        touch(work, "a.txt", "b.pdf")
        before = listing(work)
        cleaner.get_ext()
        assert listing(work) == before


# --------------------------------------------------------------------------- #
# clean(): the happy path
# --------------------------------------------------------------------------- #
class TestCleanBasics:
    def test_moves_file_into_extension_folder(self, cleaner, work):
        touch(work, "report.pdf", content="hello")
        clean(cleaner)
        assert not (work / "report.pdf").exists()
        assert (work / "pdf" / "report.pdf").read_text() == "hello"

    @pytest.mark.parametrize(
        "filename, folder",
        [
            ("song.mp3", "mp3"),
            ("photo.jpg", "jpg"),
            ("script.py", "py"),
            ("data.json", "json"),
            ("installer.exe", "exe"),
            ("doc.docx", "docx"),
            ("a.b", "b"),
            ("x.7z", "7z"),
        ],
    )
    def test_various_extensions(self, cleaner, work, filename, folder):
        touch(work, filename)
        clean(cleaner)
        assert (work / folder / filename).is_file()
        assert not (work / filename).exists()

    def test_multiple_files_same_extension_share_a_folder(self, cleaner, work):
        touch(work, "a.txt", "b.txt", "c.txt")
        clean(cleaner)
        assert listing(work) == {"txt"}
        assert listing(work / "txt") == {"a.txt", "b.txt", "c.txt"}

    def test_multiple_extensions_get_separate_folders(self, cleaner, work):
        touch(work, "a.txt", "b.pdf", "c.png")
        clean(cleaner)
        assert listing(work) == {"txt", "pdf", "png"}
        assert (work / "txt" / "a.txt").is_file()
        assert (work / "pdf" / "b.pdf").is_file()
        assert (work / "png" / "c.png").is_file()

    def test_same_stem_different_extensions(self, cleaner, work):
        touch(work, "a.txt", "a.pdf")
        clean(cleaner)
        assert (work / "txt" / "a.txt").is_file()
        assert (work / "pdf" / "a.pdf").is_file()

    def test_binary_content_is_preserved(self, cleaner, work):
        data = bytes(range(256)) * 100
        (work / "blob.bin").write_bytes(data)
        clean(cleaner)
        assert (work / "bin" / "blob.bin").read_bytes() == data

    def test_empty_file_is_moved(self, cleaner, work):
        (work / "empty.log").touch()
        clean(cleaner)
        assert (work / "log" / "empty.log").is_file()
        assert (work / "log" / "empty.log").stat().st_size == 0

    def test_empty_directory_is_a_noop(self, cleaner, work):
        clean(cleaner)
        assert listing(work) == set()

    def test_multi_dot_name_goes_by_last_suffix(self, cleaner, work):
        touch(work, "archive.tar.gz")
        clean(cleaner)
        assert (work / "gz" / "archive.tar.gz").is_file()

    def test_spaces_and_unicode_in_names(self, cleaner, work):
        touch(work, "moja fotka č.jpg", "súbor ľščťžýáíé.txt", "日本語.md")
        clean(cleaner)
        assert (work / "jpg" / "moja fotka č.jpg").is_file()
        assert (work / "txt" / "súbor ľščťžýáíé.txt").is_file()
        assert (work / "md" / "日本語.md").is_file()

    def test_many_files(self, cleaner, work):
        for i in range(200):
            touch(work, f"file{i}.txt" if i % 2 else f"file{i}.log")
        clean(cleaner)
        assert len(listing(work / "txt")) == 100
        assert len(listing(work / "log")) == 100
        assert listing(work) == {"txt", "log"}


# --------------------------------------------------------------------------- #
# clean(): things that must NOT be touched
# --------------------------------------------------------------------------- #
class TestCleanLeavesThingsAlone:
    def test_file_without_extension_is_not_moved(self, cleaner, work):
        touch(work, "README", "Makefile")
        clean(cleaner)
        assert listing(work) == {"README", "Makefile"}

    def test_hidden_file_without_extension_is_not_moved(self, cleaner, work):
        touch(work, ".bashrc")
        clean(cleaner)
        assert listing(work) == {".bashrc"}

    def test_files_without_extension_do_not_block_others(self, cleaner, work):
        touch(work, "README", "a.txt")
        clean(cleaner)
        assert (work / "README").is_file()
        assert (work / "txt" / "a.txt").is_file()

    def test_existing_subdirectories_are_not_recursed_into(self, cleaner, work):
        sub = work / "projects"
        sub.mkdir()
        touch(sub, "inner.txt")
        touch(work, "top.txt")
        clean(cleaner)
        assert (sub / "inner.txt").is_file()
        assert (work / "txt" / "top.txt").is_file()
        assert not (work / "txt" / "inner.txt").exists()

    def test_directory_with_file_like_name_is_not_moved(self, cleaner, work):
        (work / "archive.zip").mkdir()
        touch(work / "archive.zip", "inside.txt")
        clean(cleaner)
        assert (work / "archive.zip" / "inside.txt").is_file()
        assert not (work / "zip").exists()

    def test_only_configured_path_is_cleaned_not_cwd(
        self, cleaner, work, env, monkeypatch
    ):
        elsewhere = env["tmp"] / "elsewhere"
        elsewhere.mkdir()
        touch(elsewhere, "keep.txt")
        monkeypatch.chdir(elsewhere)
        touch(work, "move.txt")
        clean(cleaner)
        assert (elsewhere / "keep.txt").is_file()
        assert (work / "txt" / "move.txt").is_file()


# --------------------------------------------------------------------------- #
# clean(): repeated runs and pre-existing folders
# --------------------------------------------------------------------------- #
class TestCleanRepeatedRuns:
    def test_idempotent(self, cleaner, work):
        touch(work, "a.txt", "b.pdf")
        clean(cleaner)
        snapshot = {p.relative_to(work) for p in work.rglob("*")}
        clean(cleaner)
        assert {p.relative_to(work) for p in work.rglob("*")} == snapshot

    def test_new_files_after_first_run_are_sorted(self, cleaner, work):
        touch(work, "a.txt")
        clean(cleaner)
        touch(work, "b.txt", "c.pdf")
        clean(cleaner)
        assert listing(work / "txt") == {"a.txt", "b.txt"}
        assert listing(work / "pdf") == {"c.pdf"}

    def test_existing_extension_folder_is_reused(self, cleaner, work):
        (work / "txt").mkdir()
        touch(work / "txt", "old.txt", content="old")
        touch(work, "new.txt", content="new")
        clean(cleaner)
        assert (work / "txt" / "old.txt").read_text() == "old"
        assert (work / "txt" / "new.txt").read_text() == "new"

    def test_extension_case_is_kept_in_folder_name(self, cleaner, work):
        """Documents CURRENT behaviour: 'jpg' and 'JPG' are different folders."""
        touch(work, "a.jpg", "B.JPG")
        clean(cleaner)
        assert (work / "jpg" / "a.jpg").is_file()
        assert (work / "JPG" / "B.JPG").is_file()


# --------------------------------------------------------------------------- #
# clean(): symlinks
# --------------------------------------------------------------------------- #
class TestCleanSymlinks:
    def test_symlink_to_file_is_moved_as_a_link(self, cleaner, work, env):
        target = env["tmp"] / "target.txt"
        target.write_text("real")
        (work / "link.txt").symlink_to(target)
        clean(cleaner)
        moved = work / "txt" / "link.txt"
        assert moved.is_symlink()
        assert target.read_text() == "real"  # real file untouched

    def test_broken_symlink_is_ignored(self, cleaner, work, env):
        (work / "broken.txt").symlink_to(env["tmp"] / "does_not_exist")
        clean(cleaner)
        assert (work / "broken.txt").is_symlink()
        assert not (work / "txt").exists()


# --------------------------------------------------------------------------- #
# clean(): path selection (config / defaults)
# --------------------------------------------------------------------------- #
class TestCleanPathSelection:
    def test_default_path_is_home_downloads(self, env):
        downloads = env["home"] / "Downloads"
        downloads.mkdir()
        touch(downloads, "a.txt")
        c = Cleaner()  # no config file
        assert c.access_path() == downloads
        clean(c)
        assert (downloads / "txt" / "a.txt").is_file()

    def test_corrupted_config_falls_back_to_downloads(self, env):
        env["conf"].write_text("{ this is not json")
        c = Cleaner()
        assert c.access_path() == env["home"] / "Downloads"

    def test_config_without_path_key_falls_back_to_downloads(self, env):
        env["conf"].write_text(json.dumps({"something": "else"}))
        c = Cleaner()
        assert c.access_path() == env["home"] / "Downloads"

    def test_clean_uses_path_set_by_change_path(self, env):
        c = Cleaner()
        c.change_path(env["work"])
        touch(env["work"], "a.md")
        clean(c)
        assert (env["work"] / "md" / "a.md").is_file()

    def test_nonexistent_directory_raises(self, env):
        env["conf"].write_text(json.dumps({"path": str(env["tmp"] / "nope")}))
        c = Cleaner()
        with pytest.raises(FileNotFoundError):
            clean(c)


# --------------------------------------------------------------------------- #
# package() called directly
# --------------------------------------------------------------------------- #
class TestPackage:
    def test_empty_mapping_is_a_noop(self, cleaner, work):
        touch(work, "a.txt")
        cleaner.package({})
        assert listing(work) == {"a.txt"}

    def test_explicit_mapping_moves_only_listed_files(self, cleaner, work):
        touch(work, "a.txt", "b.txt")
        cleaner.package({Path("a"): [Path(".txt")]})
        assert (work / "txt" / "a.txt").is_file()
        assert (work / "b.txt").is_file()

    def test_stale_snapshot_raises(self, cleaner, work):
        """File deleted between get_ext() and package()."""
        touch(work, "a.txt")
        snapshot = cleaner.get_ext()
        (work / "a.txt").unlink()
        with pytest.raises(FileNotFoundError):
            cleaner.package(snapshot)

    def test_entry_with_empty_suffix_is_skipped(self, cleaner, work):
        touch(work, "README")
        cleaner.package({Path("README"): [Path("")]})
        assert listing(work) == {"README"}


# --------------------------------------------------------------------------- #
# Known problems (xfail = the test describes DESIRED behaviour, which the
# current code does not have yet). When you fix the bug, pytest reports XPASS.
# --------------------------------------------------------------------------- #
class TestKnownIssues:
    def test_name_collision_must_not_overwrite(self, cleaner, work):
        (work / "txt").mkdir()
        touch(work / "txt", "a.txt", content="OLD")
        touch(work, "a.txt", content="NEW")
        clean(cleaner)
        assert (work / "txt" / "a.txt").read_text() == "OLD"
        assert (work / "a.txt").read_text() == "NEW"  # left in place, nothing lost

    def test_file_named_like_extension_folder(self, cleaner, work):
        touch(work, "txt", "a.txt")
        clean(cleaner)
        assert (work / "txt").exists()


# --------------------------------------------------------------------------- #
# confirmation()
# --------------------------------------------------------------------------- #
@pytest.fixture
def answers(monkeypatch):
    """Feed scripted answers to input(); record the prompts."""

    def feed(*given: str):
        it = iter(given)
        prompts: list[str] = []

        def fake_input(prompt: str = "") -> str:
            prompts.append(prompt)
            return next(it)

        monkeypatch.setattr(builtins, "input", fake_input)
        return prompts

    return feed


class TestConfirmation:
    @pytest.mark.parametrize("reply", ["y", "yes"])
    def test_yes_variants(self, answers, reply):
        answers(reply)
        assert confirmation("package") is True

    @pytest.mark.parametrize("reply", ["n", "no"])
    def test_no_variants(self, answers, reply):
        answers(reply)
        assert confirmation("package") is False

    def test_prompt_contains_action(self, answers):
        prompts = answers("y")
        confirmation("package")
        assert "package" in prompts[0]

    def test_invalid_then_yes(self, answers):
        prompts = answers("maybe", "???", "y")
        assert confirmation("package") is True
        assert len(prompts) == 3

    def test_invalid_then_no(self, answers):
        answers("", "asdf", "no")
        assert confirmation("package") is False

    def test_five_invalid_answers_return_false_and_stop_asking(self, answers):
        prompts = answers("a", "b", "c", "d", "e", "y")  # the "y" is never read
        assert confirmation("package") is False
        assert len(prompts) == 5

    def test_yes_on_fifth_attempt_still_counts(self, answers):
        prompts = answers("a", "b", "c", "d", "y")
        assert confirmation("package") is True
        assert len(prompts) == 5

    @pytest.mark.parametrize("reply", ["Y", "YES", "N", "No", " y", "y "])
    def test_case_and_whitespace_are_not_normalised(self, answers, reply):
        """Documents CURRENT behaviour: only exact lowercase answers count."""
        prompts = answers(*([reply] * 5))
        assert confirmation("package") is False
        assert len(prompts) == 5


# --------------------------------------------------------------------------- #
# The "clean" command flow: confirmation -> get_ext -> package
# (mirrors the `case "clean":` branch of the command loop)
# --------------------------------------------------------------------------- #
def run_clean_command(cleaner) -> None:
    if confirmation("package"):
        exts = cleaner.get_ext()
        cleaner.package(exts)


class TestCleanCommandFlow:
    def test_confirmed_moves_files(self, cleaner, work, answers):
        touch(work, "a.txt", "b.pdf")
        answers("y")
        run_clean_command(cleaner)
        assert (work / "txt" / "a.txt").is_file()
        assert (work / "pdf" / "b.pdf").is_file()

    def test_declined_leaves_files_untouched(self, cleaner, work, answers):
        touch(work, "a.txt", "b.pdf")
        answers("n")
        run_clean_command(cleaner)
        assert listing(work) == {"a.txt", "b.pdf"}

    def test_too_many_invalid_answers_leaves_files_untouched(
        self, cleaner, work, answers
    ):
        touch(work, "a.txt")
        answers("x", "x", "x", "x", "x")
        run_clean_command(cleaner)
        assert listing(work) == {"a.txt"}

    def test_confirmed_on_empty_directory(self, cleaner, work, answers):
        answers("yes")
        run_clean_command(cleaner)
        assert listing(work) == set()
