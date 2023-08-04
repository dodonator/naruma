import cmd
from collections import deque
from pathlib import Path
from requests import Session, Response, codes


class NarumaShell(cmd.Cmd):
    intro: str = "Welcome to naruma. Type help or ? to list commands.\n"
    prompt: str = "(naruma) "
    session: Session
    remote: str
    stack: deque
    cwd: Path

    def __init__(self):
        self.stack = deque()
        self.cwd = Path.cwd()
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
        else:
            self.stack.append(response.text)
            print("saved note content to stack")

    def do_save(self, filename: str):
        """Saves last entry of the stack.

        Args:
            filename (str): target path
        """
        path = Path(filename)
        if path.exists():
            print(f"Path {path} already exists.")
            return

        if not self.stack:
            print("Nothing to save")
            return

        content = self.stack.pop()
        with path.open("w", encoding="UTF-8") as stream:
            stream.write(content)

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

    def do_bye(self, arg) -> bool:
        """Closes program."""
        if hasattr(self, "session"):
            self.session.close()
        return True


if __name__ == "__main__":
    NarumaShell().cmdloop()
