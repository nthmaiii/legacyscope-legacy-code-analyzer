from __future__ import annotations

from pathlib import Path

from ..models import AnalysisResult


def _img(result: AnalysisResult, key: str, caption: str) -> str:
    value = result.diagrams.get(key, "")
    if not value:
        return ""
    return f"![{caption}]({Path(value).name})\n"


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(item).replace("|", "\\|") for item in row) + " |")
    return "\n".join(lines)


def generate_markdown(result: AnalysisResult, output: Path) -> str:
    output.mkdir(parents=True, exist_ok=True)
    m = result.metrics
    lines = [
        f"# Đặc tả kỹ thuật: {result.project_name}",
        "",
        f"> Sinh tự động bởi LegacyScope lúc {result.generated_at}  ",
        f"> Mã phân tích: `{result.analysis_id}`  ",
        f"> Nguồn: `{result.root}`",
        "",
        "## 1. Thông tin chung",
        "",
        _md_table(
            ["Thuộc tính", "Giá trị"],
            [
                ["Tên dự án", result.project_name],
                ["Số tệp", str(m["files"])],
                ["Dòng mã", str(m["loc"])],
                ["Lớp", str(m["classes"])],
                ["Phương thức", str(m["methods"])],
                ["API", str(m["endpoints"])],
                ["Bảng dữ liệu", str(m["tables"])],
                ["Quy tắc nghiệp vụ", str(m.get("business_rules", 0))],
                ["Chỉ số rủi ro", f"{m['legacy_score']}/100 ({m['legacy_grade']})"],
            ],
        ),
        "",
        "## 2. Tổng quan kiến trúc",
        "",
        result.overview.get("summary", ""),
        "",
        _md_table(
            ["Tầng", "Số lớp", "Phương thức", "Dòng mã", "Mô tả"],
            [[layer.name, str(layer.class_count), str(layer.methods), str(layer.loc), layer.description] for layer in result.layers],
        ),
        "",
        _img(result, "architecture", "Kiến trúc phân tầng"),
        "",
        "## 3. Danh mục module",
        "",
        _md_table(
            ["Tầng", "Lớp tiêu biểu", "Trách nhiệm"],
            [[layer.name, ", ".join(layer.classes[:6]), layer.description] for layer in result.layers],
        ),
        "",
        "## 4. Danh mục lớp",
        "",
    ]
    class_rows = []
    for cls in result.classes:
        deps = sum(1 for d in result.dependencies if d.source == cls.name)
        class_rows.append([cls.name, cls.layer, cls.kind, str(len(cls.methods)), str(len(cls.fields)), str(deps), str(cls.loc), cls.file])
    lines.append(_md_table(["Lớp", "Tầng", "Loại", "Phương thức", "Thuộc tính", "Phụ thuộc", "Dòng", "Tệp"], class_rows))
    lines.extend(["", "## 5. Danh mục API", ""])
    if result.endpoints:
        lines.append(_md_table(
            ["HTTP", "Đường dẫn", "Handler", "Lớp", "Tệp", "Dòng"],
            [[e.http_method, e.path, e.handler, e.class_name, e.file, str(e.line)] for e in result.endpoints],
        ))
    else:
        lines.append("Không phát hiện endpoint.")
    lines.extend(["", "## 6. Mô hình dữ liệu", ""])
    if result.tables:
        lines.append(_img(result, "erd", "Mô hình dữ liệu quan hệ"))
        lines.append("")
        lines.append(_md_table(
            ["Bảng", "Số cột", "Khóa chính", "Khóa ngoại", "Nguồn"],
            [[t.name, str(len(t.columns)), t.primary_key or "-", "; ".join(t.foreign_keys) or "-", t.source] for t in result.tables],
        ))
    else:
        lines.append("Không phát hiện bảng dữ liệu.")
    lines.extend(["", "## 7. Quy tắc nghiệp vụ", ""])
    if result.business_rules:
        lines.append(_md_table(
            ["STT", "Vị trí", "Điều kiện", "Hành vi / thông báo"],
            [[str(i + 1), rule.title, rule.condition, rule.action] for i, rule in enumerate(result.business_rules)],
        ))
    else:
        lines.append("Không phát hiện quy tắc nghiệp vụ từ mã nguồn.")
    lines.extend(["", "## 8. Đánh giá chất lượng", ""])
    lines.append(_img(result, "quality", "Bảng điều khiển chất lượng"))
    lines.append("")
    lines.append(_md_table(
        ["Chỉ số", "Giá trị"],
        [
            ["Độ phức tạp trung bình", str(m["avg_complexity"])],
            ["Độ phức tạp lớn nhất", str(m["max_complexity"])],
            ["Phương thức dài/phức tạp", str(m["long_methods"])],
            ["TODO/FIXME", str(m["todos"])],
            ["Chu trình phụ thuộc", str(m["cycles"])],
            ["Vấn đề mức cao", str(m["findings_high"])],
            ["Vấn đề mức trung bình", str(m["findings_medium"])],
        ],
    ))
    lines.extend(["", "### Phát hiện chính", ""])
    if result.findings:
        for finding in result.findings:
            location = f" (`{finding.file}`)" if finding.file else ""
            lines.append(f"- **[{finding.severity}] {finding.title}**{location}: {finding.description}")
    else:
        lines.append("- Không phát hiện vấn đề đáng chú ý.")
    lines.extend([
        "",
        "## 9. Phụ lục tệp",
        "",
        _md_table(
            ["Tệp", "Ngôn ngữ", "Dòng", "Code", "Comment", "TODO"],
            [[f.path, f.language, str(f.loc), str(f.code_lines), str(f.comment_lines), str(f.todos)] for f in result.files],
        ),
        "",
        "## 10. Sơ đồ Mermaid",
        "",
        "Các tệp `.mmd` đi kèm có thể mở bằng Mermaid Live Editor hoặc tích hợp vào tài liệu Markdown hỗ trợ Mermaid.",
        "",
        f"- Kiến trúc: `{Path(result.diagrams.get('mermaid_architecture', '')).name}`",
        f"- Phụ thuộc: `{Path(result.diagrams.get('mermaid_dependency', '')).name}`",
        f"- Lớp: `{Path(result.diagrams.get('mermaid_class', '')).name}`",
        f"- ERD: `{Path(result.diagrams.get('mermaid_erd', '')).name}`",
        f"- Tuần tự: `{Path(result.diagrams.get('mermaid_sequence', '')).name}`",
        "",
    ])
    path = output / "Dac_ta_ky_thuat.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)
