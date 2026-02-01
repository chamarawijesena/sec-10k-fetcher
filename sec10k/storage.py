from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


def make_output_dir(base_dir: str | Path, cik_10: str, accession_number: str) -> Path:
    accession_no_dashes = accession_number.replace("-", "")
    out_dir = Path(base_dir) / cik_10 / accession_no_dashes
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    if is_dataclass(data):
        data = asdict(data)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
