from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from legacyscope.pipeline import BASE_DIR, DEFAULT_OUTPUT, artifact_urls, run_pipeline

app = FastAPI(title="LegacyScope", version="1.0.0")
WEB_DIR = BASE_DIR / "legacyscope" / "web"
SAMPLE_DIR = BASE_DIR / "sample_legacy"
OUTPUT_DIR = DEFAULT_OUTPUT
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")

CACHE: dict[str, dict[str, Any]] = {}

SAMPLES = [
    {
        "id": "library_legacy",
        "name": "Hệ thống Quản lý Thư viện",
        "description": "Java Servlet + JDBC + MySQL, mã nguồn kiểu cũ, nhiều đoạn SQL nối chuỗi và JSP scriptlet.",
        "languages": ["Java", "SQL"],
        "year": "2014",
        "scale": "19 lớp · 5 bảng · 10 API",
    }
]


class AnalyzeRequest(BaseModel):
    sample: str


def sample_path(sample_id: str) -> Path:
    if sample_id not in {sample["id"] for sample in SAMPLES}:
        raise HTTPException(status_code=404, detail="Không tìm thấy mẫu mã nguồn.")
    return SAMPLE_DIR / sample_id


def build_payload(result) -> dict[str, Any]:
    payload = result.to_dict()
    urls = artifact_urls(result)
    payload["diagrams"] = urls["diagrams"]
    payload["artifacts"] = urls["artifacts"]
    payload["root"] = str(result.root)
    return payload


def save_result(result) -> dict[str, Any]:
    payload = build_payload(result)
    CACHE[result.analysis_id] = payload
    return payload


def load_payload(analysis_id: str) -> dict[str, Any]:
    if analysis_id in CACHE:
        return CACHE[analysis_id]
    analysis_file = OUTPUT_DIR / analysis_id / "analysis.json"
    if not analysis_file.exists():
        raise HTTPException(status_code=404, detail="Không tìm thấy kết quả phân tích.")
    payload = json.loads(analysis_file.read_text(encoding="utf-8"))
    prefix = f"/outputs/{analysis_id}"
    payload["diagrams"] = {
        key: f"{prefix}/{Path(value).name}"
        for key, value in payload.get("diagrams", {}).items()
    }
    payload["artifacts"] = {
        key: f"{prefix}/{Path(value).name}"
        for key, value in payload.get("artifacts", {}).items()
    }
    if not payload["artifacts"]:
        output = OUTPUT_DIR / analysis_id
        payload["artifacts"] = {
            "docx": f"{prefix}/Dac_ta_ky_thuat.docx",
            "markdown": f"{prefix}/Dac_ta_ky_thuat.md",
            "json": f"{prefix}/analysis.json",
        }
        packages = list(output.glob("LegacyScope_*.zip"))
        if packages:
            payload["artifacts"]["package"] = f"{prefix}/{packages[0].name}"
    CACHE[analysis_id] = payload
    return payload


@app.get("/")
def index():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "LegacyScope"}


@app.get("/api/samples")
def get_samples():
    return {"samples": SAMPLES}


@app.post("/api/analyze")
def analyze_sample(request: AnalyzeRequest):
    root = sample_path(request.sample)
    try:
        result = run_pipeline(root, name_for_sample(request.sample))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Phân tích thất bại: {exc}") from exc
    return save_result(result)


@app.post("/api/analyze-upload")
async def analyze_upload(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ tệp ZIP.")
    data = await file.read()
    if len(data) > 30 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Tệp ZIP vượt quá 30 MB.")
    temp_dir = Path(tempfile.mkdtemp(prefix="legacyscope_"))
    archive_path = temp_dir / "source.zip"
    archive_path.write_bytes(data)
    extract_dir = temp_dir / "source"
    extract_dir.mkdir()
    try:
        with zipfile.ZipFile(archive_path) as archive:
            for member in archive.infolist():
                if member.filename.startswith("__MACOSX"):
                    continue
                target = (extract_dir / member.filename).resolve()
                if not str(target).startswith(str(extract_dir.resolve())):
                    raise HTTPException(status_code=400, detail="Tệp ZIP chứa đường dẫn không hợp lệ.")
                archive.extract(member, extract_dir)
        roots = [path for path in extract_dir.iterdir() if path.is_dir()]
        root = roots[0] if len(roots) == 1 and not any(extract_dir.glob("*.*")) else extract_dir
        project_name = Path(file.filename).stem.replace("_", " ").replace("-", " ").title()
        result = run_pipeline(root, project_name)
        return save_result(result)
    except HTTPException:
        raise
    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=400, detail="Tệp ZIP không hợp lệ.") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Phân tích thất bại: {exc}") from exc
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.get("/api/analyses/{analysis_id}")
def get_analysis(analysis_id: str):
    return load_payload(analysis_id)


def name_for_sample(sample_id: str) -> str:
    for sample in SAMPLES:
        if sample["id"] == sample_id:
            return sample["name"]
    return sample_id


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
