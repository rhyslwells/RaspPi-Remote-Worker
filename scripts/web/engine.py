#!/usr/bin/env python3
"""
Web UI engine: finds task scripts, runs and stops them, keeps their state.

No web code here (see app.py). A script is started as its own process through
scripts/run_script.py, so it can be stopped and its output read while it runs.

Folders (optionally overridable with environment variables):
    PI_CONTROL_DATA         per-script databases + state    (default: data/)
    PI_CONTROL_LOGS         one log file per run            (default: logs/)
    PI_CONTROL_SHEET_LOG    "1" (default) mirrors each finished run to the Sheet's
                            Log tab, best effort; "0" never contacts the Sheet

State lives in <data>/pi_control/ (a subfolder so db_report does not list it):
    state.db       saved parameter values and the history of web runs
    locks/<name>.lock   holds the PID while a script runs
"""

import ast
import json
import logging
import os
import signal
import sqlite3
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from utils import script_db  # noqa: E402
from utils.params import coerce_params  # noqa: E402

log = logging.getLogger("pi_control")

TASK_DIR = SCRIPTS_DIR  # task scripts live next to run_script.py
if os.environ.get("PI_CONTROL_DATA"):
    # Same module object that run_script.py and the scripts use, so the whole app
    # agrees on where per-script databases live.
    script_db.DATA_DIR = Path(os.environ["PI_CONTROL_DATA"])
DATA_DIR = script_db.DATA_DIR
LOG_DIR = Path(os.environ.get("PI_CONTROL_LOGS") or REPO_ROOT / "logs")
STATE_DIR = DATA_DIR / "pi_control"
LOCK_DIR = STATE_DIR / "locks"

# Files in the scripts folder that are not task scripts.
EXCLUDED = {"runner", "run_script"}
KEEP_RUNS = 20            # logs and history kept per script
DEFAULT_TIMEOUT_S = 1800  # a script can override with TIMEOUT_S
STOP_GRACE_S = 5          # SIGTERM first, SIGKILL after this (Linux)
ENTRY_POINTS = ("main", "test_sheet_connection")  # the second is test_connection's

SCHEMA = """
CREATE TABLE IF NOT EXISTS saved_params (
    script TEXT PRIMARY KEY,
    params TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS web_runs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    script     TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at   TEXT,
    status     TEXT NOT NULL,
    exit_code  INTEGER,
    params     TEXT,
    log_path   TEXT,
    pid        INTEGER
);
"""


class EngineError(Exception):
    """An error the API reports to the user: an HTTP-like status and readable text."""

    def __init__(self, status: int, message: str, errors: Optional[List[str]] = None):
        super().__init__(message)
        self.status = status
        self.message = message
        self.errors = errors or []


_mutex = threading.RLock()
_stop_requested: set = set()
_panel = None
_panel_lock = threading.Lock()


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@contextmanager
def db():
    """Open the state database; commits on success and always closes."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(STATE_DIR / "state.db", timeout=10)
    con.row_factory = sqlite3.Row
    try:
        con.executescript(SCHEMA)
        with con:
            yield con
    finally:
        con.close()


# --- Finding scripts ------------------------------------------------------------

def _literal(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except (ValueError, SyntaxError):
        return None


def _describe(doc: str, name: str) -> tuple:
    lines = [ln.strip() for ln in doc.strip().splitlines()]
    title = lines[0] if lines else ""
    if title.endswith(" Script"):
        title = title[: -len(" Script")]
    label = title or name.replace("_", " ").title()
    body = []
    for line in lines[1:]:
        if not line:
            if body:
                break
            continue
        body.append(line)
    description = " ".join(body)
    if len(description) > 200:
        description = description[:197] + "..."
    return label, description


def discover() -> Dict[str, dict]:
    """
    Task scripts in TASK_DIR, read with ast so nothing is imported or executed.

    A script is listed if it defines main() (or the legacy test_sheet_connection())
    and is not on the exclusion list. PARAMS, CONFIRM, TIMEOUT_S and DESCRIPTION must be
    literals.
    """
    found: Dict[str, dict] = {}
    for path in sorted(TASK_DIR.glob("*.py")):
        name = path.stem
        if name in EXCLUDED or name.startswith("_"):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue

        has_entry = False
        params: List[dict] = []
        confirm = None
        timeout = None
        about = None
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in ENTRY_POINTS:
                has_entry = True
            elif (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
            ):
                key = node.targets[0].id
                value = _literal(node.value)
                if key == "PARAMS" and isinstance(value, list):
                    params = [
                        p for p in value if isinstance(p, dict) and isinstance(p.get("name"), str)
                    ]
                elif key == "CONFIRM" and value:
                    confirm = value if isinstance(value, str) else "Run this script?"
                elif key == "TIMEOUT_S" and isinstance(value, (int, float)) and value > 0:
                    timeout = int(value)
                elif key == "DESCRIPTION" and isinstance(value, str) and value.strip():
                    about = value.strip()
        if not has_entry:
            continue

        label, description = _describe(ast.get_docstring(tree) or "", name)
        if about:
            description = about  # the script's own plain-language explanation, in full
        found[name] = {
            "name": name,
            "label": label,
            "description": description,
            "params": params,
            "confirm": confirm,
            "timeout": timeout or DEFAULT_TIMEOUT_S,
        }
    return found


# --- Processes ------------------------------------------------------------------

def pid_alive(pid: Optional[int]) -> bool:
    if not pid:
        return False
    if sys.platform == "win32":
        # os.kill(pid, 0) would TERMINATE the process on Windows, so ask the OS.
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, int(pid))  # QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        code = ctypes.c_ulong()
        ok = kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
        kernel32.CloseHandle(handle)
        return bool(ok) and code.value == 259  # STILL_ACTIVE
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def kill_tree(pid: int, force: bool) -> None:
    """End a process and its children. The run was started in its own group/session."""
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, timeout=15
            )
        else:
            os.killpg(pid, signal.SIGKILL if force else signal.SIGTERM)
    except (ProcessLookupError, PermissionError, subprocess.SubprocessError, OSError):
        pass


def _terminate(pid: int) -> None:
    kill_tree(pid, force=False)
    deadline = time.monotonic() + STOP_GRACE_S
    while time.monotonic() < deadline:
        if not pid_alive(pid):
            return
        time.sleep(0.3)
    if pid_alive(pid):
        kill_tree(pid, force=True)


# --- Locks ----------------------------------------------------------------------

def _lock_path(name: str) -> Path:
    return LOCK_DIR / f"{name}.lock"


def _acquire_lock(name: str) -> None:
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    lock = _lock_path(name)
    if lock.exists():
        try:
            pid = int(lock.read_text().strip() or 0)
        except (OSError, ValueError):
            pid = 0
        if pid and pid_alive(pid):
            raise EngineError(409, f"{name} is already running")
        lock.unlink(missing_ok=True)  # left behind by a crash
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise EngineError(409, f"{name} is already running") from None
    with os.fdopen(fd, "w") as f:
        f.write(str(os.getpid()))  # placeholder until the script's own PID is known


def _release_lock(name: str) -> None:
    try:
        _lock_path(name).unlink(missing_ok=True)
    except OSError:
        pass


# --- Reading state ----------------------------------------------------------------

def _run_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "script": row["script"],
        "started_at": row["started_at"],
        "ended_at": row["ended_at"],
        "status": row["status"],
        "exit_code": row["exit_code"],
        "params": json.loads(row["params"] or "{}"),
    }


def _running_row(con: sqlite3.Connection, name: str) -> Optional[sqlite3.Row]:
    return con.execute(
        "SELECT * FROM web_runs WHERE script=? AND status='running' ORDER BY id DESC LIMIT 1",
        (name,),
    ).fetchone()


def _last_script_run(name: str) -> Optional[sqlite3.Row]:
    """Newest row of the script's own runs table (covers Sheet runs and web runs)."""
    try:
        rows = script_db.get_runs(name, 1)
    except (FileNotFoundError, sqlite3.Error):
        return None
    return rows[0] if rows else None


def list_scripts() -> dict:
    infos = discover()
    with db() as con:
        saved = {r["script"]: json.loads(r["params"]) for r in con.execute("SELECT * FROM saved_params")}
        out = []
        for name, info in infos.items():
            web = con.execute(
                "SELECT * FROM web_runs WHERE script=? ORDER BY id DESC LIMIT 1", (name,)
            ).fetchone()
            last = _last_script_run(name)

            if web is not None and web["status"] == "running":
                state = "running"
            elif web is not None and (last is None or web["started_at"] >= last["started_at"]):
                state = web["status"]
            elif last is not None:
                state = "success" if last["success"] else "failed"
            else:
                state = "never"

            values = saved.get(name, {})
            params = []
            for spec in info["params"]:
                p = dict(spec)
                p["value"] = values.get(spec["name"], spec.get("default"))
                params.append(p)

            out.append({
                "name": name,
                "label": info["label"],
                "description": info["description"],
                "params": params,
                "confirm": info["confirm"],
                "state": state,
                "run_id": web["id"] if web is not None else None,
                "last": None if last is None else {
                    "success": bool(last["success"]),
                    "message": (last["message"] or "")[:300],
                    "started_at": last["started_at"],
                    "duration_s": last["duration_s"],
                },
            })
    return {"server_time": now(), "scripts": out}


def list_runs(limit: int = 20, script: Optional[str] = None) -> List[dict]:
    limit = max(1, min(int(limit), 100))
    with db() as con:
        if script:
            rows = con.execute(
                "SELECT * FROM web_runs WHERE script=? ORDER BY id DESC LIMIT ?", (script, limit)
            ).fetchall()
        else:
            rows = con.execute(
                "SELECT * FROM web_runs ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
    return [_run_dict(r) for r in rows]


def get_run(run_id: int) -> dict:
    with db() as con:
        row = con.execute("SELECT * FROM web_runs WHERE id=?", (run_id,)).fetchone()
    if row is None:
        raise EngineError(404, "No such run")
    return _run_dict(row)


def read_log(run_id: int, tail: int = 60000) -> dict:
    with db() as con:
        row = con.execute("SELECT * FROM web_runs WHERE id=?", (run_id,)).fetchone()
    if row is None:
        raise EngineError(404, "No such run")
    text, truncated = "", False
    path = Path(row["log_path"] or "")
    try:
        # Only ever read inside the log folder, whatever the database says.
        if path.resolve().parent == LOG_DIR.resolve() and path.is_file():
            data = path.read_bytes()
            truncated = len(data) > tail
            text = data[-tail:].decode("utf-8", errors="replace")
    except OSError:
        pass
    return {"id": run_id, "status": row["status"], "text": text, "truncated": truncated}


# --- Running and stopping ---------------------------------------------------------

def start_run(name: str, raw_params: Optional[dict], confirm: bool) -> dict:
    info = discover().get(name)
    if info is None:
        raise EngineError(404, "Unknown script")
    if info["confirm"] and not confirm:
        raise EngineError(409, "Confirmation required", [info["confirm"]])
    values, errors = coerce_params(info["params"], raw_params or {})
    if errors:
        raise EngineError(400, "Invalid parameters", errors)

    with _mutex:
        with db() as con:
            stale = _running_row(con, name)
            if stale is not None:
                if pid_alive(stale["pid"]):
                    raise EngineError(409, f"{name} is already running")
                _finalize(stale["id"], name, None, False, False)  # died unnoticed
        _acquire_lock(name)

        LOG_DIR.mkdir(parents=True, exist_ok=True)
        started = now()
        with db() as con:
            run_id = con.execute(
                "INSERT INTO web_runs (script, started_at, status, params) VALUES (?, ?, 'running', ?)",
                (name, started, json.dumps(values, sort_keys=True)),
            ).lastrowid
            con.execute(
                "INSERT INTO saved_params (script, params) VALUES (?, ?) "
                "ON CONFLICT(script) DO UPDATE SET params=excluded.params",
                (name, json.dumps(values, sort_keys=True)),
            )
        log_path = LOG_DIR / f"{name}-{datetime.now():%Y%m%d-%H%M%S}-{run_id}.log"

        cmd = [
            sys.executable, "-u", str(SCRIPTS_DIR / "run_script.py"), name,
            "--params", json.dumps(values),
        ]
        env = {
            **os.environ,
            "PYTHONUNBUFFERED": "1",
            "PYTHONIOENCODING": "utf-8",
        }
        if os.environ.get("PI_CONTROL_DATA"):
            env["PI_CONTROL_DATA"] = str(DATA_DIR)
        kwargs: Dict[str, Any] = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = (
                subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
            )
        else:
            kwargs["start_new_session"] = True  # own process group so Stop reaches children

        logf = open(log_path, "wb")
        try:
            proc = subprocess.Popen(
                cmd, cwd=REPO_ROOT, env=env, stdin=subprocess.DEVNULL,
                stdout=logf, stderr=subprocess.STDOUT, **kwargs,
            )
        except OSError as e:
            logf.close()
            _release_lock(name)
            with db() as con:
                con.execute(
                    "UPDATE web_runs SET status='failed', ended_at=?, log_path=? WHERE id=?",
                    (now(), str(log_path), run_id),
                )
            raise EngineError(500, f"Could not start: {e}") from None

        with db() as con:
            con.execute(
                "UPDATE web_runs SET pid=?, log_path=? WHERE id=?",
                (proc.pid, str(log_path), run_id),
            )
        _lock_path(name).write_text(str(proc.pid))

    threading.Thread(
        target=_watch, args=(run_id, name, proc, logf, info["timeout"]), daemon=True
    ).start()
    return get_run(run_id)


def stop_run(name: str) -> dict:
    with _mutex:
        with db() as con:
            row = _running_row(con, name)
        if row is None:
            raise EngineError(409, f"{name} is not running")
        _stop_requested.add(row["id"])
    threading.Thread(target=_terminate, args=(row["pid"],), daemon=True).start()
    return {"id": row["id"], "stopping": True}


def _watch(run_id: int, name: str, proc: subprocess.Popen, logf, timeout: int) -> None:
    timed_out = False
    try:
        code = proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        kill_tree(proc.pid, force=True)
        code = proc.wait()
    finally:
        logf.close()
    _finalize(run_id, name, code, timed_out, run_id in _stop_requested, timeout)


def _watch_orphan(run_id: int, name: str, pid: int) -> None:
    """A run that outlived a restart of the web UI: wait for its PID to go away."""
    while pid_alive(pid):
        time.sleep(2)
    _finalize(run_id, name, None, False, run_id in _stop_requested)


def _finalize(run_id: int, name: str, code: Optional[int], timed_out: bool,
              stopped: bool, timeout: int = DEFAULT_TIMEOUT_S) -> None:
    """Record how a run ended, release the lock, tidy up, mirror to the Sheet."""
    with db() as con:
        row = con.execute("SELECT * FROM web_runs WHERE id=?", (run_id,)).fetchone()
    if row is None:
        return
    started_at = row["started_at"]
    params = json.loads(row["params"] or "{}")
    duration = max(0.0, (datetime.now() - datetime.strptime(started_at, "%Y-%m-%d %H:%M:%S")).total_seconds())

    note = None
    if stopped:
        status, success, message, details = "stopped", False, "Stopped by user", ""
        note = "[pi-control] stopped by user"
    elif timed_out:
        status, success, message, details = "timeout", False, f"Timed out after {timeout}s", ""
        note = f"[pi-control] killed after {timeout}s timeout"
    else:
        last = _last_script_run(name)
        if last is not None and last["started_at"] >= started_at:
            success = bool(last["success"])
            message, details = last["message"] or "", last["details"] or ""
        elif code == 0:
            success, message, details = True, "Finished", ""
        else:
            success = False
            message = "Could not start or ended without a result"
            details = f"Exit code {code}. See the log."
        status = "success" if success else "failed"

    if note and row["log_path"]:
        try:
            with open(row["log_path"], "a", encoding="utf-8") as f:
                f.write(f"\n{note}\n")
        except OSError:
            pass
    if status in ("stopped", "timeout"):
        # The killed process never got to record its own run.
        script_db.record_run(name, started_at, duration, False, params, message, details)

    with db() as con:
        con.execute(
            "UPDATE web_runs SET status=?, ended_at=?, exit_code=? WHERE id=?",
            (status, now(), code, run_id),
        )
    _stop_requested.discard(run_id)
    _release_lock(name)
    _prune(name)
    threading.Thread(
        target=mirror_to_sheet, args=(name, success, message, details), daemon=True
    ).start()


def _prune(name: str) -> None:
    """Keep the last KEEP_RUNS finished runs (rows and log files) per script."""
    with db() as con:
        old = con.execute(
            "SELECT id, log_path FROM web_runs WHERE script=? AND status!='running' "
            "ORDER BY id DESC LIMIT -1 OFFSET ?",
            (name, KEEP_RUNS),
        ).fetchall()
        for r in old:
            try:
                if r["log_path"]:
                    Path(r["log_path"]).unlink(missing_ok=True)
            except OSError:
                pass
            con.execute("DELETE FROM web_runs WHERE id=?", (r["id"],))


def mirror_to_sheet(name: str, success: bool, message: str, details: str) -> None:
    """Append the result to the Sheet's Log tab. Best effort: never raises."""
    global _panel
    if os.environ.get("PI_CONTROL_SHEET_LOG", "1") != "1":
        return
    try:
        from utils.control_panel import ControlPanel, ScriptStatus

        with _panel_lock:
            if _panel is None:
                _panel = ControlPanel(spreadsheet_name="RaspPI-Remote-Worker")
            panel = _panel
        panel.log_execution(
            f"{name}.py",
            ScriptStatus.SUCCESS if success else ScriptStatus.FAILED,
            f"[Web UI] {message}",
            (details or "")[:40000],
        )
    except Exception as e:  # noqa: BLE001 - the Sheet is a mirror, not a dependency
        log.warning("Could not write %s to the Sheet Log tab: %s", name, e)


def reconcile() -> None:
    """At startup: settle runs left 'running' by a previous web UI process."""
    with db() as con:
        rows = con.execute("SELECT * FROM web_runs WHERE status='running'").fetchall()
    for row in rows:
        if pid_alive(row["pid"]):
            threading.Thread(
                target=_watch_orphan, args=(row["id"], row["script"], row["pid"]), daemon=True
            ).start()
        else:
            _finalize(row["id"], row["script"], None, False, False)
