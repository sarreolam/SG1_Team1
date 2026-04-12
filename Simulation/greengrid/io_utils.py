from __future__ import annotations

import csv
import shutil
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping

from .config import OUTPUT_DIR


def create_run_directories(scenario_name: str) -> tuple[Path, Path]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    run_dir = OUTPUT_DIR / f"{scenario_name}_{timestamp}"
    latest_dir = OUTPUT_DIR / "latest"

    run_dir.mkdir(parents=True, exist_ok=True)

    if latest_dir.exists():
        shutil.rmtree(latest_dir)
    latest_dir.mkdir(parents=True, exist_ok=True)

    return run_dir, latest_dir


def write_csv(path: Path, rows: Iterable[Mapping[str, object]]) -> None:
    rows = list(rows)
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)