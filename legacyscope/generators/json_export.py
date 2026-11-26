from __future__ import annotations

import json
from pathlib import Path

from ..models import AnalysisResult


def generate_json(result: AnalysisResult, output: Path) -> str:
    output.mkdir(parents=True, exist_ok=True)
    path = output / "analysis.json"
    path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)
