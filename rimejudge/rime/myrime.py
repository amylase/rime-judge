#!/usr/bin/python
import subprocess
import sys

from rime.core import main

# Enable plugins, Do not remove this.
import rime.plugins.rime_plus
import rimejudge.rime.plugins.judge


def run_command(project_dir: str, command: str, *argv: str) -> subprocess.CompletedProcess:
    args = [
               sys.executable,
               __file__,
               command
           ] + list(argv)
    return subprocess.run(args, cwd=project_dir, capture_output=True, text=True)


if __name__ == '__main__':
    sys.exit(main.Main(sys.argv))
