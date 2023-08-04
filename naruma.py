import cmd
from collections import deque
from pathlib import Path
from typing import Optional
from requests import Session, Response, codes


class NarumaShell(cmd.Cmd):
    intro: str = "Welcome to naruma. Type help or ? to list commands.\n"
    prompt: str = "(naruma) "
    session: Session
    remote: str
    cache: Optional[tuple[str, str]]
    cwd: Path

    def __init__(self):
        self.cwd = Path.cwd()
        self.cache = None
        super().__init__()

    def do_connect(self, remote_url: str) -> None:
        """Connect to a remote HedgeDoc instance.

        Args:
            remote_url (str): root url of the instance
        """
        if hasattr(self, "remote"):
            return

        self.session = Session()
        self.remote = remote_url

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

    def do_cache(self):
        """Shows current cache."""
        if self.cache:
            note_id, content = self.cache
            print(f"{note_id} {len(content)}")
        else:
            print("empty")

    def do_clear(self):
        """Clears the cache."""
        print("cache was cleared")
        self.cache = None

    def do_bye(self, arg) -> bool:
        """Closes program."""
        if hasattr(self, "session"):
            self.session.close()
        if self.cache is not None:
            print("Cache is not empty, please save cache to file")
            return

        return True


if __name__ == "__main__":
    NarumaShell().cmdloop()
