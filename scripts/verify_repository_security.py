"""Fail-closed repository security and provenance checks.

The checker never prints matched secret values. It reports only a category
and path so CI logs cannot become a second leak.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from study2.clients import ANTHROPIC_CONFIGS, OPENAI_CONFIGS  # noqa: E402


MAX_BLOB_SIZE = 10_000_000
ALLOWED_TRACKED_ENV = {".env.example"}
# 260 = Study 2 confirmatory (reps 1-130, study2-freeze) + Study 2b
# confirmatory (reps 131-260, study2b-freeze; STUDY2B_PLAN.md §4). Both
# generations share one manifest per model; every rep must appear exactly
# once with the frozen generation config.
# 260 = Study 2 확증 (rep 1-130) + Study 2b 확증 (rep 131-260). 두 생성이
# 모델당 하나의 manifest를 공유하며, 모든 rep은 동결 생성 설정과 함께
# 정확히 한 번씩 나타나야 한다.
EXPECTED_STUDY2_REPS = 260

SECRET_PATTERNS = {
    "openai_api_key": re.compile(rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    "anthropic_api_key": re.compile(rb"\bsk-ant-[A-Za-z0-9_-]{20,}\b"),
    "github_token": re.compile(
        rb"\b(?:ghp_|github_pat_|gho_|ghu_|ghs_|ghr_)[A-Za-z0-9_-]{20,}\b"
    ),
    "aws_access_key": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "google_api_key": re.compile(rb"\bAIza[0-9A-Za-z_-]{30,}\b"),
    "slack_token": re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    "private_key": re.compile(
        b"-----BEGIN " + b"(?:RSA |EC |OPENSSH )?" + b"PRIVATE KEY-----"
    ),
}

LOCAL_PATH_PATTERNS = {
    "windows_user_path": re.compile(rb"(?i)\b[A-Z]:[\\/]+Users[\\/]+"),
    "mac_user_path": re.compile(b"/" + b"Users" + b"/"),
    "linux_home_path": re.compile(b"/" + b"home" + b"/"),
}


def git(*args: str, input_text: str | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        input=input_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return result.stdout


def pattern_hits(data: bytes, patterns: Dict[str, re.Pattern]) -> List[str]:
    return [name for name, pattern in patterns.items() if pattern.search(data)]


def tracked_paths() -> List[Path]:
    return [
        PROJECT_ROOT / value
        for value in git("ls-files", "-z").split("\0")
        if value
    ]


def check_tracked_env_files(failures: List[str]) -> None:
    tracked = {
        path.relative_to(PROJECT_ROOT).as_posix()
        for path in tracked_paths()
        if path.name == ".env" or path.name.endswith(".env") or ".env." in path.name
    }
    unexpected = tracked - ALLOWED_TRACKED_ENV
    if unexpected:
        failures.append(f"tracked env files: {sorted(unexpected)}")


def check_worktree(failures: List[str]) -> None:
    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(PROJECT_ROOT)
        if ".git" in relative.parts or ".venv" in relative.parts:
            continue
        if relative.as_posix() == ".env" or "__pycache__" in relative.parts:
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        hits = pattern_hits(data, SECRET_PATTERNS)
        if hits:
            failures.append(f"worktree secret pattern {','.join(hits)}: {relative}")


def check_tracked_privacy_paths(failures: List[str]) -> None:
    for path in tracked_paths():
        if not path.is_file():
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        hits = pattern_hits(data, LOCAL_PATH_PATTERNS)
        if hits:
            relative = path.relative_to(PROJECT_ROOT)
            failures.append(f"local workstation path {','.join(hits)}: {relative}")


def reachable_blob_ids() -> Iterable[Tuple[str, str]]:
    objects = git("rev-list", "--objects", "--all")
    path_by_oid = {}
    oids = []
    for line in objects.splitlines():
        oid, separator, path = line.partition(" ")
        oids.append(oid)
        if separator and oid not in path_by_oid:
            path_by_oid[oid] = path
    check = subprocess.run(
        ["git", "cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)"],
        cwd=PROJECT_ROOT,
        input="\n".join(oids) + "\n",
        capture_output=True,
        text=True,
        encoding="ascii",
        errors="replace",
        check=True,
    )
    for line in check.stdout.splitlines():
        fields = line.split()
        if len(fields) == 3 and fields[1] == "blob":
            yield fields[0], path_by_oid.get(fields[0], "(path unavailable)")


def check_git_history(failures: List[str]) -> int:
    blobs = list(reachable_blob_ids())
    process = subprocess.Popen(
        ["git", "cat-file", "--batch"],
        cwd=PROJECT_ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    assert process.stdin is not None and process.stdout is not None
    scanned = 0
    try:
        for oid, path in blobs:
            process.stdin.write((oid + "\n").encode("ascii"))
            process.stdin.flush()
            header = process.stdout.readline().decode("ascii", "replace").split()
            if len(header) < 3 or header[1] != "blob":
                failures.append(f"unable to read git blob metadata: {oid[:12]}")
                continue
            size = int(header[2])
            data = process.stdout.read(size)
            process.stdout.read(1)
            if size > MAX_BLOB_SIZE:
                failures.append(f"git blob exceeds scan limit: {oid[:12]} {path}")
                continue
            scanned += 1
            hits = pattern_hits(data, SECRET_PATTERNS)
            if hits:
                failures.append(
                    f"git-history secret pattern {','.join(hits)}: {oid[:12]} {path}"
                )
    finally:
        process.stdin.close()
        process.terminate()
    return scanned


def check_remote_urls(failures: List[str]) -> None:
    try:
        urls = git("remote", "-v")
    except subprocess.CalledProcessError:
        return
    credential_url = re.compile(r"://[^/\s:@]+:[^/\s@]+@")
    token_url = re.compile(r"(?:ghp_|github_pat_|glpat-)[A-Za-z0-9_-]+")
    for line in urls.splitlines():
        if credential_url.search(line) or token_url.search(line):
            failures.append("git remote URL contains embedded credentials")


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_project_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def frozen_config(model: str) -> Dict:
    if model in ANTHROPIC_CONFIGS:
        return ANTHROPIC_CONFIGS[model]
    if model in OPENAI_CONFIGS:
        return OPENAI_CONFIGS[model]
    raise KeyError(model)


def check_study2_manifests(failures: List[str]) -> int:
    entries_checked = 0
    manifests = sorted((PROJECT_ROOT / "data" / "public_study2").glob(
        "*/generation_manifest.jsonl"
    ))
    for manifest in manifests:
        entries = [
            json.loads(line)
            for line in manifest.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        model = manifest.parent.name
        reps = set()
        if len(entries) != EXPECTED_STUDY2_REPS:
            failures.append(f"{manifest}: expected {EXPECTED_STUDY2_REPS} entries")
        for entry in entries:
            entries_checked += 1
            rep = int(entry["rep"])
            if rep in reps:
                failures.append(f"{manifest}: duplicate rep {rep}")
            reps.add(rep)
            if entry.get("manifest_schema_version") != "2":
                failures.append(f"{manifest}: rep {rep} has old manifest schema")
            if entry.get("generation_config_source") not in {
                "runtime",
                "retrospective_backfill_2026-07-18",
            }:
                failures.append(f"{manifest}: rep {rep} config source missing")
            expected = frozen_config(model)
            try:
                actual = json.loads(entry["generation_config"])
            except (KeyError, json.JSONDecodeError):
                failures.append(f"{manifest}: rep {rep} generation config invalid")
            else:
                if actual != expected:
                    failures.append(f"{manifest}: rep {rep} generation config mismatch")
            for path_key, hash_key in (
                ("public_path", "public_sha256"),
                ("attempts_path", "attempts_sha256"),
            ):
                try:
                    path = resolve_project_path(entry[path_key])
                    expected_hash = entry[hash_key]
                except KeyError:
                    failures.append(f"{manifest}: rep {rep} missing {hash_key}")
                    continue
                if not path.is_file() or sha256_of(path) != expected_hash:
                    failures.append(f"{manifest}: rep {rep} {path_key} hash mismatch")
        if reps != set(range(1, EXPECTED_STUDY2_REPS + 1)):
            failures.append(f"{manifest}: incomplete repetition grid")
    if len(manifests) != 4:
        failures.append(f"expected 4 Study 2 manifests, found {len(manifests)}")
    return entries_checked


def check_study1_manifest_paths(failures: List[str]) -> None:
    manifest = PROJECT_ROOT / "data" / "manifest.csv"
    text = manifest.read_bytes()
    hits = pattern_hits(text, LOCAL_PATH_PATTERNS)
    if hits:
        failures.append(f"Study 1 manifest contains local paths: {','.join(hits)}")


def main() -> int:
    failures: List[str] = []
    check_tracked_env_files(failures)
    check_worktree(failures)
    check_tracked_privacy_paths(failures)
    check_remote_urls(failures)
    check_study1_manifest_paths(failures)
    entries = check_study2_manifests(failures)
    blobs = check_git_history(failures)

    if failures:
        print("repository security gate FAILED / 저장소 보안 게이트 실패")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print(
        "repository security gate passed / 저장소 보안 게이트 통과 "
        f"(git blobs={blobs}, Study 2 manifest entries={entries})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
