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
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VERSION_PATTERN = re.compile(r'^version\s*=\s*"([^"]+)"', re.MULTILINE)
DEPENDENCY_FILES = ("pyproject.toml", "uv.lock")
RESTART_PREFIXES = ("scripts/runner.py", "scripts/utils/")
MAX_LISTED_FILES = 40
# The systemd unit sets PATH to the venv's bin only, so git in /usr/bin is not found
FALLBACK_DIRS = ("/usr/local/bin", "/usr/bin", "/bin")


def _search_path() -> str:
    parts = [str(Path(sys.executable).parent), os.environ.get("PATH", "")]
    parts.extend(FALLBACK_DIRS)
    return os.pathsep.join(p for p in parts if p)


def _run(args: list[str], timeout: int) -> subprocess.CompletedProcess:
    env = {**os.environ, "PATH": _search_path()}
    return subprocess.run(
        args, cwd=REPO_ROOT, capture_output=True, text=True, timeout=timeout, env=env
    )


def _git(*args: str, timeout: int = 30) -> subprocess.CompletedProcess:
    git = shutil.which("git", path=_search_path())
    if git is None:
        raise FileNotFoundError("git not found (searched venv bin, PATH, /usr/bin)")
    return _run([git, *args], timeout)


def _find_uv() -> str | None:
    return shutil.which("uv", path=_search_path())


def _read_version() -> str:
    try:
        text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    except OSError:
        return "unknown"
    match = VERSION_PATTERN.search(text)
    return match.group(1) if match else "unknown"


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
        old_version = _read_version()

        pull = _git("pull", "--ff-only", timeout=120)
        if pull.returncode != 0:
            return (False, "git pull failed", (pull.stderr or pull.stdout).strip())

        new_sha = _git("rev-parse", "HEAD").stdout.strip()
        new_version = _read_version()
        if new_sha == old_sha:
            return (
                True,
                f"Already up to date (v{new_version})",
                f"HEAD at {new_sha[:7]}",
            )

        diff = _git("diff", "--name-only", old_sha, new_sha)
        changed = diff.stdout.split()

        notes = []
        if any(f in DEPENDENCY_FILES for f in changed):
            uv = _find_uv()
            if uv is None:
                return (False, "Pulled, but uv not found", "Run `uv sync` manually")
            # --locked never rewrites uv.lock, so a stale lock fails loudly
            # instead of dirtying the checkout and breaking the next pull
            sync = _run([uv, "sync", "--locked"], timeout=600)
            if sync.returncode != 0:
                return (
                    False,
                    "Pulled, but uv sync failed (run `uv lock` and push?)",
                    sync.stderr.strip()[-1500:],
                )
            notes.append("Dependencies synced")

        restart_needed = any(f.startswith(RESTART_PREFIXES) for f in changed)
        if restart_needed:
            notes.append("RESTART NEEDED: runner or ControlPanel changed")

        if new_version == old_version:
            version_text = f"v{new_version} (version not bumped)"
        else:
            version_text = f"v{old_version} -> v{new_version}"
        message = (
            f"Updated {version_text} "
            f"({old_sha[:7]} -> {new_sha[:7]}, {len(changed)} files)"
        )
        if restart_needed:
            message += ", restart needed"

        listed = changed[:MAX_LISTED_FILES]
        if len(changed) > MAX_LISTED_FILES:
            listed.append(f"... and {len(changed) - MAX_LISTED_FILES} more")
        details = "\n".join(notes + ["Changed files:"] + listed)
        return (True, message, details)

    except FileNotFoundError as e:
        return (False, "Required tool not found", str(e))
    except subprocess.TimeoutExpired as e:
        return (False, "Command timed out", f"{e.cmd} after {e.timeout}s")
    except Exception as e:
        return (False, "Error during update", f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    success, message, details = main()
    print(message)
    print(details)
    raise SystemExit(0 if success else 1)
