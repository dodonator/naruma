import cmd
import json
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from requests import Session, Response, codes
import time

# TODO: separate profile cwd and download cwd


def url_to_profile_path(url: str) -> Path:
    parse_url = urlparse(url)
    filename: str = f"{parse_url.netloc}.json"
    path = Path(filename)
    return path


class NarumaShell(cmd.Cmd):
    intro: str = "Welcome to naruma. Type help or ? to list commands.\n"
    prompt: str = "(naruma) "
    session: Session
    remote: str
    cache: Optional[tuple[str, str]]
    cwd: Path
    _profile: dict

    def __init__(self):
        self.cwd = Path.cwd()
        self.cache = None
        super().__init__()

    @property
    def profile(self):
        remote = self.remote if hasattr(self, "remote") else None
        cwd: str = self.cwd.as_posix()
        profile = {"remote": remote, "cwd": cwd}
        return profile

    @profile.setter
    def profile(self, other: dict):
        self.remote = other["remote"]
        self.cwd = Path(other["cwd"])

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
        """Downloads note and saves it to the stack.

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
        print("saved note content to stack")

    def do_save(self, filename: str):
        """Saves last entry of the stack.

        Args:
            filename (str): target path
        """
        path = self.cwd / Path(f"{filename}.md")
        if path.exists():
            print(f"Path {path} already exists.")
            return

        if self.cache is None:
            print("Nothing to save")
            return

        note_id, content = self.cache

        with path.open("w", encoding="UTF-8") as stream:
            stream.write(content)

        print(f"written {note_id} to {path}")
        self.cache = None

    def do_cwd(self, new_path: str):
        """Returns cwd or sets new cwd.

        Args:
            new_path (str): new path for cwd
        """
        if not new_path:
            print(f"current working directory: {self.cwd}")
            return

        cwd = Path(new_path)
        print(f"set current working directory to: {cwd}")
        self.cwd = cwd

    def do_list(self, arg):
        """Lists content of cwd."""
        print(f"cwd: {self.cwd}")
        path: Path
        for path in self.cwd.glob("*.md"):
            stat = path.stat()
            print(f"{stat.st_size:>10} | {time.ctime(stat.st_ctime)} | {path.name}")

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

    def do_profile(self, sub_cmd: str):
        match sub_cmd:
            case "save":
                if hasattr(self, "remote"):
                    profile_path = self.cwd / url_to_profile_path(self.remote)
                else:
                    filename = input("Please enter filename: ")
                    profile_path = self.cwd / Path(f"{filename}.json")

                if not profile_path.exists():
                    profile_path.touch()

                with profile_path.open("w", encoding="UTF-8") as stream:
                    json.dump(self.profile, stream)

                print(f"saved profile to {profile_path}")

            case "load":
                filename: str = input("please enter filename: ")
                profile_path: Path = self.cwd / f"{filename}.json"

                with profile_path.open("r", encoding="UTF-8") as stream:
                    profile = json.load(stream)

                print(f"loaded profile {profile}")
                self.profile = profile

            case "list":
                for path in self.cwd.glob("*.json"):
                    print(path.name)

            case "show" | "":
                print(self.profile)

    def do_bye(self, arg) -> bool:
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
