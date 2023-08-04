import cmd
import json
from os import mkdir
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from requests import Session, Response, codes
import time

# TODO: separate profile cwd and download cwd


def url_to_profile_path(url: str) -> str:
    parse_url = urlparse(url)
    filename: str = f"{parse_url.netloc}.json"
    return filename


class NarumaShell(cmd.Cmd):
    intro: str = "Welcome to naruma. Type help or ? to list commands.\n"
    prompt: str = "(naruma) "
    session: Session
    remote: str
    cache: Optional[tuple[str, str]]
    profile_path: Path

    def __init__(self):
        cwd = Path.cwd()
        self.cache = None
        self.profile_path = cwd / "profiles"
        self.download_path = cwd / "notes"
        super().__init__()

    @property
    def profile(self):
        remote = self.remote if hasattr(self, "remote") else None
        profile_path: str = self.profile_path.as_posix()
        download_path: str = self.download_path.as_posix()
        profile = {
            "remote": remote,
            "profile_path": profile_path,
            "download_path": download_path,
        }
        return profile

    @profile.setter
    def profile(self, other: dict):
        self.remote = other["remote"]
        self.profile_path = Path(other["profile_path"])
        self.download_path = Path(other["download_path"])

    def do_connect(self, remote_url: str) -> None:
        """Connect to a remote HedgeDoc instance.

        Args:
            remote_url (str): root url of the instance
        """
        if hasattr(self, "remote"):
            return

        if not remote_url:
            remote_url = self.remote
        else:
            self.remote = remote_url

        self.session = Session()

        response = self.session.get(remote_url)
        if response.status_code != codes.ok:
            response.raise_for_status()
        else:
            print(response)

    def do_get(self, note_id: str) -> None:
        """Downloads note and saves it to the cache.

        Args:
            note_id (str): note id
        """
        download_url: str = f"{self.remote}/{note_id}/download"
        response = self.session.get(download_url)
        if response.status_code != codes.ok:
            response.raise_for_status()
            return
        if self.cache is not None:
            print("cache isn't empty, please save content to file")
            return

        self.cache = (note_id, response.text)
        print("saved note content to cache")

    def do_save(self, filename: str):
        """Saves last entry of the cache.

        Args:
            filename (str): target path
        """
        if self.cache is None:
            print("Nothing to save")
            return

        if not self.download_path.exists():
            self.download_path.mkdir()

        target_path = self.download_path / Path(f"{filename}.md")
        if target_path.exists():
            print(f"Path {target_path} already exists.")
            return

        note_id, content = self.cache

        with target_path.open("w", encoding="UTF-8") as stream:
            stream.write(content)

        print(f"written {note_id} to {target_path}")
        self.cache = None

    def do_cache(self, arg):
        """Shows current cache."""
        if self.cache:
            note_id, content = self.cache
            print(f"{note_id} {len(content)}")
        else:
            print("empty")

    def do_clear(self, arg):
        """Clears the cache."""
        print("cache was cleared")
        self.cache = None

    def do_local(self, sub_cmd: str):
        """
        Manipulate the local directory path.

        This is the directory where your downloaded notes will be saved.

        Subcommands:
            get: show the current local directory path
            set: change the current local directory path
            list: list notes in local directory
        """
        match sub_cmd.lower():
            case "list":
                print(f"local directory: {self.download_path}")
                path: Path
                for path in self.download_path.glob("*.md"):
                    stat = path.stat()
                    print(
                        f"{stat.st_size:>10} | {time.ctime(stat.st_ctime)} | {path.name}"
                    )

            case "set":
                new_path: Path = Path(input("Please enter new path: "))
                self.download_path = new_path
                print(f"set local directory to: {self.download_path}")

            case "get":
                print(f"current local directory: {self.download_path}")

            case _:
                print(self.do_local.__doc__)

    def do_profile(self, sub_cmd: str):
        match sub_cmd:
            case "save":
                if hasattr(self, "remote"):
                    filename = url_to_profile_path(self.remote)
                else:
                    filename = input("Please enter filename: ")

                target_path: Path = self.profile_path / filename

                if not self.profile_path.exists():
                    self.profile_path.mkdir()

                with target_path.open("w", encoding="UTF-8") as stream:
                    json.dump(self.profile, stream)

                print(f"saved profile to {target_path}")

            case "load":
                filename: str = input("please enter filename: ")
                target_path: Path = self.profile_path / f"{filename}.json"

                with target_path.open("r", encoding="UTF-8") as stream:
                    profile = json.load(stream)

                print(f"loaded profile {profile}")
                self.profile = profile

            case "list":
                for path in self.profile_path.glob("*.json"):
                    print(path.name)

            case "get":
                print(f"profile directory: {self.profile_path}")

            case "set":
                new_path = Path(input("new profiles path: "))
                self.profile_path = new_path

            case _:
                print(f"current: {self.profile}")

    def do_bye(self, arg):
        """Closes program."""
        if hasattr(self, "session"):
            self.session.close()
        if self.cache is not None:
            print("Cache is not empty, please save cache to file")
            return

        return True


if __name__ == "__main__":
    try:
        from rich import print as print
    except ImportError:
        pass

    NarumaShell().cmdloop()
