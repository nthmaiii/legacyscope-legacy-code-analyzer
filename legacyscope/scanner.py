from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from .models import FileInfo

IGNORED_DIRS = {
    ".git", ".svn", ".hg", ".idea", ".vscode", "__pycache__", "node_modules",
    "target", "build", "out", "bin", "dist", "coverage", ".mvn", ".gradle",
    "vendor", "log", "logs", "tmp", "temp",
}

LANGUAGE_BY_EXT = {
    ".java": "Java",
    ".sql": "SQL",
    ".xml": "XML",
    ".jsp": "JSP",
    ".jspf": "JSP",
    ".properties": "Properties",
    ".md": "Markdown",
    ".txt": "Text",
    ".html": "HTML",
    ".css": "CSS",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".py": "Python",
    ".php": "PHP",
    ".cs": "C#",
    ".json": "JSON",
    ".yml": "YAML",
    ".yaml": "YAML",
}

CODE_LANGUAGES = {"Java", "SQL"}

COMMENT_MARKERS = {
    "Java": ("//", "/*", "*/"),
    "SQL": ("--", "/*", "*/"),
    "JavaScript": ("//", "/*", "*/"),
    "TypeScript": ("//", "/*", "*/"),
    "PHP": ("//", "/*", "*/"),
    "C#": ("//", "/*", "*/"),
    "Python": ("#", None, None),
    "Properties": ("#", None, None),
    "YAML": ("#", None, None),
}


@dataclass
class ScanResult:
    root: Path
    files: list[FileInfo] = field(default_factory=list)
    language_stats: dict[str, dict[str, int]] = field(default_factory=dict)
    total_loc: int = 0
    total_code: int = 0
    total_comments: int = 0
    total_blank: int = 0
    todo_count: int = 0
    ignored_files: int = 0

    def to_dict(self) -> dict:
        return {
            "root": str(self.root),
            "files": [f.to_dict() for f in self.files],
            "language_stats": self.language_stats,
            "total_loc": self.total_loc,
            "total_code": self.total_code,
            "total_comments": self.total_comments,
            "total_blank": self.total_blank,
            "todo_count": self.todo_count,
            "ignored_files": self.ignored_files,
        }


def detect_language(path: Path) -> str:
    return LANGUAGE_BY_EXT.get(path.suffix.lower(), "Other")


def detect_text_encoding(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1258", "windows-1252"):
        try:
            data.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    return "utf-8"


def count_lines(text: str, language: str) -> tuple[int, int, int]:
    """Trả về (blank, comment, code) theo cách đếm đơn giản nhưng ổn định."""
    if not text:
        return 0, 0, 0
    lines = text.splitlines()
    blank = 0
    comment = 0
    code = 0
    in_block = False
    line_comment, block_start, block_end = COMMENT_MARKERS.get(language, ("//", "/*", "*/"))
    for raw in lines:
        line = raw.strip()
        if not line:
            blank += 1
            continue
        if in_block:
            comment += 1
            if block_end and block_end in line:
                in_block = False
            continue
        if block_start and line.startswith(block_start):
            comment += 1
            if block_end not in line[2:]:
                in_block = True
            continue
        if line_comment and line.startswith(line_comment):
            comment += 1
            continue
        code += 1
    return blank, comment, code


def scan_project(root: Path) -> ScanResult:
    root = Path(root).resolve()
    result = ScanResult(root=root)
    for current, dirs, filenames in os.walk(root):
        dirs[:] = [d for d in dirs if d.lower() not in IGNORED_DIRS]
        for filename in filenames:
            path = Path(current) / filename
            language = detect_language(path)
            if language == "Other":
                result.ignored_files += 1
                continue
            try:
                data = path.read_bytes()
            except OSError:
                result.ignored_files += 1
                continue
            if b"\x00" in data[:4096]:
                result.ignored_files += 1
                continue
            encoding = detect_text_encoding(data)
            try:
                text = data.decode(encoding, errors="replace")
            except Exception:
                result.ignored_files += 1
                continue
            blank, comment, code_lines = count_lines(text, language)
            loc = len(text.splitlines())
            todos = len(re.findall(r"\b(TODO|FIXME|HACK|XXX)\b", text, flags=re.IGNORECASE))
            rel = path.relative_to(root).as_posix()
            info = FileInfo(
                path=rel,
                language=language,
                loc=loc,
                code_lines=code_lines,
                comment_lines=comment,
                blank_lines=blank,
                size_bytes=len(data),
                todos=todos,
            )
            result.files.append(info)
            result.total_loc += loc
            result.total_code += code_lines
            result.total_comments += comment
            result.total_blank += blank
            result.todo_count += todos
            stats = result.language_stats.setdefault(
                language, {"files": 0, "loc": 0, "code": 0, "comments": 0, "todos": 0}
            )
            stats["files"] += 1
            stats["loc"] += loc
            stats["code"] += code_lines
            stats["comments"] += comment
            stats["todos"] += todos
    result.files.sort(key=lambda f: f.path.lower())
    return result
