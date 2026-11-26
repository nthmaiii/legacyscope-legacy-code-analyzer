from __future__ import annotations

import zipfile
from pathlib import Path

from .analysis import analyze_project
from .diagrams import generate_all_diagrams
from .generators.docx_spec import generate_docx
from .generators.json_export import generate_json
from .generators.markdown_spec import generate_markdown
from .models import AnalysisResult

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = BASE_DIR / "outputs"


def run_pipeline(root: Path, project_name: str | None = None, output_root: Path | None = None) -> AnalysisResult:
    root = Path(root).resolve()
    output_root = Path(output_root or DEFAULT_OUTPUT)
    result = analyze_project(root, project_name)
    output = output_root / result.analysis_id
    output.mkdir(parents=True, exist_ok=True)

    result.diagrams = generate_all_diagrams(result, output)
    markdown_path = generate_markdown(result, output)
    docx_path = generate_docx(result, output)
    result.artifacts = {
        "markdown": Path(markdown_path).name,
        "docx": Path(docx_path).name,
    }
    json_path = generate_json(result, output)
    result.artifacts["json"] = Path(json_path).name

    package_path = output / f"LegacyScope_{result.analysis_id}.zip"
    with zipfile.ZipFile(package_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(output.iterdir()):
            if path.is_file() and path.name != package_path.name:
                archive.write(path, arcname=path.name)
    result.artifacts["package"] = package_path.name
    result.artifacts["docx"] = Path(docx_path).name
    return result


def artifact_urls(result: AnalysisResult) -> dict[str, str]:
    prefix = f"/outputs/{result.analysis_id}"
    diagrams = {key: f"{prefix}/{Path(value).name}" for key, value in result.diagrams.items()}
    artifacts = {key: f"{prefix}/{value}" for key, value in result.artifacts.items()}
    return {"diagrams": diagrams, "artifacts": artifacts}
