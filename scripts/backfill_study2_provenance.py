"""Backfill cryptographic and configuration provenance for Study 2.

This is intentionally explicit about retrospective metadata. It does not
claim that ``generation_config`` was present when the API calls ran; the
source label records that the value was reconstructed from the frozen code,
the deviation ledger, and the retained session log.

Usage:
    python scripts/backfill_study2_provenance.py
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from study2.clients import ANTHROPIC_CONFIGS, OPENAI_CONFIGS  # noqa: E402


PUBLIC_ROOT = PROJECT_ROOT / "data" / "public_study2"
EXPECTED_REPS = 130
BACKFILL_SOURCE = "retrospective_backfill_2026-07-18"


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_config(model: str) -> Dict:
    if model in ANTHROPIC_CONFIGS:
        return ANTHROPIC_CONFIGS[model]
    if model in OPENAI_CONFIGS:
        return OPENAI_CONFIGS[model]
    raise ValueError(f"no frozen config for model {model}")


def resolve_project_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def update_manifest(path: Path) -> int:
    entries = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(entries) != EXPECTED_REPS:
        raise ValueError(f"{path}: expected {EXPECTED_REPS} entries, got {len(entries)}")

    model = path.parent.name
    config_json = json.dumps(expected_config(model), sort_keys=True)
    reps = set()
    changed = 0
    for entry in entries:
        if entry["model"] != model:
            raise ValueError(f"{path}: model mismatch in rep {entry.get('rep')}")
        rep = int(entry["rep"])
        if rep in reps:
            raise ValueError(f"{path}: duplicate rep {rep}")
        reps.add(rep)

        public_path = resolve_project_path(entry["public_path"])
        attempts_path = resolve_project_path(entry["attempts_path"])
        if sha256_of(public_path) != entry["public_sha256"]:
            raise ValueError(f"{path}: public hash mismatch for rep {rep}")

        updates = {
            "attempts_sha256": sha256_of(attempts_path),
            "generation_config": config_json,
            "generation_config_source": BACKFILL_SOURCE,
            "manifest_schema_version": "2",
        }
        for key, value in updates.items():
            if entry.get(key) != value:
                entry[key] = value
                changed += 1

    if reps != set(range(1, EXPECTED_REPS + 1)):
        raise ValueError(f"{path}: repetition grid is incomplete")

    rendered = "".join(
        json.dumps(entry, sort_keys=True) + "\n" for entry in entries
    )
    fd, tmp_name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(rendered)
        Path(tmp_name).replace(path)
    except Exception:
        Path(tmp_name).unlink(missing_ok=True)
        raise
    return changed


def main() -> None:
    manifests = sorted(PUBLIC_ROOT.glob("*/generation_manifest.jsonl"))
    if not manifests:
        raise SystemExit("no Study 2 generation manifests found")
    changed = 0
    for path in manifests:
        count = update_manifest(path)
        changed += count
        print(f"{path.relative_to(PROJECT_ROOT)}: {count} field updates")
    print(f"provenance backfill complete: {len(manifests)} manifests, {changed} updates")


if __name__ == "__main__":
    main()
