#!/usr/bin/env python3
"""
Git Pull Update Script
Pulls the latest code into this repository, runs `uv sync` when dependencies
changed, and reports whether the runner service needs a restart.

It never restarts the service itself: restarting would kill the runner before
it could record SUCCESS, leaving the Config row stuck on RUNNING.

No parameters.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEPENDENCY_FILES = ("pyproject.toml", "uv.lock")
RESTART_PREFIXES = ("scripts/runner.py", "scripts/utils/")
MAX_LISTED_FILES = 40


def _git(*args: str, timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, timeout=timeout
    )


def _find_uv() -> str | None:
    venv_bin = str(Path(sys.executable).parent)
    search_path = venv_bin + os.pathsep + os.environ.get("PATH", "")
    return shutil.which("uv", path=search_path)


def main():
    """
    Returns:
        Tuple of (success: bool, message: str, details: str)
    """
    try:
        head = _git("rev-parse", "HEAD")
        if head.returncode != 0:
            return (False, "Not a git repository", head.stderr.strip())
        old_sha = head.stdout.strip()

        pull = _git("pull", "--ff-only", timeout=120)
        if pull.returncode != 0:
            return (False, "git pull failed", (pull.stderr or pull.stdout).strip())

        new_sha = _git("rev-parse", "HEAD").stdout.strip()
        if new_sha == old_sha:
            return (True, "Already up to date", f"HEAD at {new_sha[:7]}")

        diff = _git("diff", "--name-only", old_sha, new_sha)
        changed = diff.stdout.split()

        notes = []
        if any(f in DEPENDENCY_FILES for f in changed):
            uv = _find_uv()
            if uv is None:
                return (False, "Pulled, but uv not found", "Run `uv sync` manually")
            sync = subprocess.run(
                [uv, "sync"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=600
            )
            if sync.returncode != 0:
                return (False, "Pulled, but uv sync failed", sync.stderr.strip()[-1500:])
            notes.append("Dependencies synced")

        restart_needed = any(f.startswith(RESTART_PREFIXES) for f in changed)
        if restart_needed:
            notes.append("RESTART NEEDED: runner or ControlPanel changed")

        message = f"Updated {old_sha[:7]} -> {new_sha[:7]} ({len(changed)} files)"
        if restart_needed:
            message += ", restart needed"

        listed = changed[:MAX_LISTED_FILES]
        if len(changed) > MAX_LISTED_FILES:
            listed.append(f"... and {len(changed) - MAX_LISTED_FILES} more")
        details = "\n".join(notes + ["Changed files:"] + listed)
        return (True, message, details)

    except subprocess.TimeoutExpired as e:
        return (False, "Command timed out", f"{e.cmd} after {e.timeout}s")
    except Exception as e:
        return (False, "Error during update", f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    success, message, details = main()
    print(message)
    print(details)
    raise SystemExit(0 if success else 1)
