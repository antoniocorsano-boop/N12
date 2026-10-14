from __future__ import annotations

import subprocess
from pathlib import Path

from .contracts import ControlPlaneError


def _run(args: list[str], *, cwd: Path | None = None) -> str:
    try:
        cp = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ControlPlaneError("CANDIDATE_REF_FETCH_FAILED") from exc
    return cp.stdout.strip()


def fetch_candidate(base_repository_url: str, pr_number: int, requested_sha: str, destination: Path) -> str:
    destination = Path(destination)
    if destination.exists():
        raise ControlPlaneError("CANDIDATE_REF_FETCH_FAILED")
    destination.parent.mkdir(parents=True, exist_ok=True)
    hooks = destination.parent / f"{destination.name}.hooks-disabled"
    hooks.mkdir(parents=True, exist_ok=True)
    _run(["git", "init", "--bare", str(destination)])
    _run(["git", "--git-dir", str(destination), "config", "core.hooksPath", str(hooks)])
    _run([
        "git", "--git-dir", str(destination), "fetch", "--no-tags", "--depth=1",
        base_repository_url, f"refs/pull/{pr_number}/head",
    ])
    obj_type = _run(["git", "--git-dir", str(destination), "cat-file", "-t", "FETCH_HEAD"])
    if obj_type != "commit":
        raise ControlPlaneError("CANDIDATE_REF_FETCH_FAILED")
    fetched = _run(["git", "--git-dir", str(destination), "rev-parse", "FETCH_HEAD"])
    if fetched != requested_sha:
        raise ControlPlaneError("CANDIDATE_FETCHED_SHA_MISMATCH")
    return fetched
