from __future__ import annotations

import re
import uuid
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import networkx as nx

from .models import (
    AnalysisResult,
    BusinessRuleInfo,
    ClassInfo,
    DependencyInfo,
    FindingInfo,
    LayerInfo,
    TableInfo,
)
from .parsers.java_parser import parse_java_file
from .parsers.sql_parser import find_sql_tables, parse_sql_file
from .scanner import scan_project

LAYER_DEFS = {
    "presentation": {
        "name": "Giao diện / API",
        "description": "Tiếp nhận yêu cầu từ người dùng, điều phối request và trả kết quả.",
        "color": "#2563EB",
    },
    "business": {
        "name": "Nghiệp vụ",
        "description": "Xử lý quy tắc nghiệp vụ, kiểm tra dữ liệu và điều phối các thao tác.",
        "color": "#D97706",
    },
    "persistence": {
        "name": "Truy cập dữ liệu",
        "description": "Truy vấn, ánh xạ và cập nhật dữ liệu trong cơ sở dữ liệu.",
        "color": "#059669",
    },
    "domain": {
        "name": "Mô hình miền",
        "description": "Biểu diễn thực thể, thuộc tính và quan hệ nghiệp vụ cốt lõi.",
        "color": "#7C3AED",
    },
    "infrastructure": {
        "name": "Hạ tầng dùng chung",
        "description": "Tiện ích, cấu hình, kết nối CSDL, bảo mật và các thành phần dùng chung.",
        "color": "#64748B",
    },
    "other": {
        "name": "Khác",
        "description": "Các lớp chưa xác định được tầng kiến trúc theo quy tắc hiện tại.",
        "color": "#94A3B8",
    },
}

LAYER_ORDER = ["presentation", "business", "persistence", "domain", "infrastructure", "other"]


def classify_layer(package: str, file_path: str, class_name: str = "") -> str:
    value = f"{package}/{file_path}".lower()
    if any(token in value for token in ("/controller", "/servlet", "/web", "/api", "/rest", ".controller.")):
        return "presentation"
    if any(token in value for token in ("/service", "/business", "/usecase", "/usecases")):
        return "business"
    if any(token in value for token in ("/dao", "/repository", "/mapper", "/persistence")):
        return "persistence"
    if any(token in value for token in ("/model", "/entity", "/domain", "/dto", "/bean")):
        return "domain"
    if any(token in value for token in ("/util", "/config", "/common", "/filter", "/security", "/helper")):
        return "infrastructure"
    return "other"


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def collect_tables(root: Path, files, java_sources: list[tuple[str, str]]) -> list[TableInfo]:
    tables: dict[str, TableInfo] = {}
    for file_info in files:
        if file_info.language == "SQL":
            for table in parse_sql_file(root / file_info.path, file_info.path):
                tables[table.name.lower()] = table
    for rel_path, text in java_sources:
        for table_name in find_sql_tables(text):
            key = table_name.lower()
            if key not in tables:
                tables[key] = TableInfo(
                    name=table_name,
                    columns=[],
                    source=f"Tham chiếu trong {rel_path}",
                )
    return sorted(tables.values(), key=lambda t: (t.name.lower(), t.source))


def build_layers(classes: list[ClassInfo]) -> list[LayerInfo]:
    layers = {
        key: LayerInfo(key=key, name=meta["name"], description=meta["description"], color=meta["color"])
        for key, meta in LAYER_DEFS.items()
    }
    for cls in classes:
        cls.layer = classify_layer(cls.package, cls.file, cls.name)
        layer = layers[cls.layer]
        layer.classes.append(cls.name)
        layer.loc += cls.loc
        layer.methods += len(cls.methods)
    result = [layers[key] for key in LAYER_ORDER if layers[key].classes]
    for layer in result:
        layer.classes.sort()
    return result


def build_dependencies(classes: list[ClassInfo], imports_by_file: dict[str, list[str]]) -> list[DependencyInfo]:
    by_name = {cls.name: cls for cls in classes}
    edges: dict[tuple[str, str], DependencyInfo] = {}

    def add(source: str, target: str, kind: str, weight: int = 1) -> None:
        if not target or target == source or target not in by_name:
            return
        key = (source, target)
        if key in edges:
            edges[key].weight += weight
        else:
            edges[key] = DependencyInfo(source=source, target=target, kind=kind, weight=weight)

    for cls in classes:
        if cls.extends:
            add(cls.name, cls.extends.split(".")[-1], "extends", 2)
        for interface in cls.implements:
            add(cls.name, interface.split(".")[-1], "implements", 2)
        for field_info in cls.fields:
            for candidate in re.findall(r"[A-Z][A-Za-z0-9_$]*", re.sub(r"<.*>", "", field_info.type)):
                add(cls.name, candidate, "field", 2)
        for method in cls.methods:
            for candidate in re.findall(r"[A-Z][A-Za-z0-9_$]*", method.return_type):
                add(cls.name, candidate, "return", 1)
            for candidate in re.findall(r"[A-Z][A-Za-z0-9_$]*", method.parameters):
                add(cls.name, candidate, "parameter", 1)
        for imported in imports_by_file.get(cls.file, []):
            add(cls.name, imported.split(".")[-1], "import", 1)
        # Gọi phương thức chỉ được nối khi tên phương thức là duy nhất trong dự án.
        for method in cls.methods:
            for called in method.calls:
                owners = [other for other in classes if any(m.name == called for m in other.methods)]
                if len(owners) == 1:
                    add(cls.name, owners[0].name, "call", 1)
    return sorted(edges.values(), key=lambda e: (-e.weight, e.source, e.target))


def detect_cycles(classes: list[ClassInfo], dependencies: list[DependencyInfo]) -> list[list[str]]:
    graph = nx.DiGraph()
    names = {cls.name for cls in classes}
    graph.add_nodes_from(names)
    for dependency in dependencies:
        if dependency.source in names and dependency.target in names and dependency.source != dependency.target:
            graph.add_edge(dependency.source, dependency.target)
    cycles = []
    try:
        for cycle in nx.simple_cycles(graph, length_bound=8):
            if 2 <= len(cycle) <= 8:
                cycles.append(cycle + [cycle[0]])
            if len(cycles) >= 8:
                break
    except Exception:
        cycles = []
    return cycles


def collect_findings(
    root: Path,
    files,
    classes: list[ClassInfo],
    dependencies: list[DependencyInfo],
    cycles: list[list[str]],
) -> list[FindingInfo]:
    findings: list[FindingInfo] = []
    java_sources = [(f.path, read_text(root / f.path)) for f in files if f.language == "Java"]
    all_sources = [(f.path, read_text(root / f.path)) for f in files if f.language in {"Java", "SQL", "JSP"}]
    has_tests = any(("test" in f.path.lower() or "spec" in f.path.lower()) and f.language == "Java" for f in files)

    for rel_path, text in all_sources:
        if not text:
            continue
        if re.search(r"(?i)(password|passwd|pwd)\s*=\s*[\"'][^\"']+[\"']", text) or re.search(r"getConnection\([^)]*[\"'][^\"']+[\"']", text):
            findings.append(FindingInfo(
                severity="Cao",
                category="Bảo mật",
                title="Thông tin đăng nhập hoặc mật khẩu bị hard-code",
                description="Phát hiện chuỗi mật khẩu/khóa kết nối nằm trực tiếp trong mã nguồn. Cần chuyển sang biến môi trường hoặc kho bí mật.",
                file=rel_path,
            ))
        if re.search(r"(?is)(SELECT|INSERT|UPDATE|DELETE)\b[^;]{0,300}[\"']\s*\+", text):
            findings.append(FindingInfo(
                severity="Cao",
                category="Bảo mật",
                title="SQL được nối chuỗi trực tiếp",
                description="Câu lệnh SQL ghép từ dữ liệu đầu vào có nguy cơ SQL Injection. Nên dùng PreparedStatement và tham số hóa.",
                file=rel_path,
            ))
        if re.search(r"\bcreateStatement\s*\(", text):
            findings.append(FindingInfo(
                severity="Trung bình",
                category="Bảo mật",
                title="Sử dụng Statement thay vì PreparedStatement",
                description="Statement không tham số hóa dễ dẫn tới lỗi injection và khó kiểm soát kiểu dữ liệu.",
                file=rel_path,
            ))
        if re.search(r"<\s*%.*?%>", text, flags=re.DOTALL):
            findings.append(FindingInfo(
                severity="Trung bình",
                category="Kiến trúc",
                title="JSP còn chứa scriptlet",
                description="Mã Java nhúng trong JSP làm trộn lẫn giao diện và nghiệp vụ, khó bảo trì và kiểm thử.",
                file=rel_path,
            ))
        if re.search(r"\b(TODO|FIXME|HACK)\b", text):
            findings.append(FindingInfo(
                severity="Thấp",
                category="Chất lượng mã",
                title="Còn ghi chú TODO/FIXME",
                description="Các ghi chú này cho thấy công việc chưa hoàn thiện hoặc khoản nợ kỹ thuật đã tồn tại lâu.",
                file=rel_path,
            ))

    for cls in classes:
        if cls.loc > 250:
            findings.append(FindingInfo(
                severity="Trung bình",
                category="Chất lượng mã",
                title=f"Lớp {cls.name} quá lớn",
                description=f"Lớp có {cls.loc} dòng, vượt ngưỡng 250 dòng; nên tách theo trách nhiệm.",
                file=cls.file,
                line=cls.start_line,
            ))
        for method in cls.methods:
            if method.loc > 35 or method.complexity > 10:
                findings.append(FindingInfo(
                    severity="Trung bình",
                    category="Chất lượng mã",
                    title=f"Phương thức {cls.name}.{method.name} quá dài/phức tạp",
                    description=f"{method.loc} dòng, độ phức tạp ước lượng {method.complexity}. Nên tách nhỏ và bổ sung kiểm thử.",
                    file=method.file,
                    line=method.start_line,
                ))
        out_degree = len([d for d in dependencies if d.source == cls.name])
        if out_degree > 7:
            findings.append(FindingInfo(
                severity="Thấp",
                category="Kiến trúc",
                title=f"Lớp {cls.name} phụ thuộc nhiều thành phần",
                description=f"Có {out_degree} phụ thuộc trực tiếp, làm tăng coupling và chi phí thay đổi.",
                file=cls.file,
                line=cls.start_line,
            ))

    if cycles:
        findings.append(FindingInfo(
            severity="Cao",
            category="Kiến trúc",
            title="Phát hiện chu trình phụ thuộc giữa các lớp",
            description="Chu trình phụ thuộc làm giảm khả năng tách module, kiểm thử độc lập và tái sử dụng.",
            file="",
        ))
    if not has_tests:
        findings.append(FindingInfo(
            severity="Cao",
            category="Kiểm thử",
            title="Không tìm thấy kiểm thử tự động",
            description="Dự án không có tệp kiểm thử Java. Việc thay đổi mã nguồn cũ không có lưới an toàn hồi quy.",
            file="",
        ))

    severity_order = {"Cao": 0, "Trung bình": 1, "Thấp": 2}
    findings.sort(key=lambda f: (severity_order.get(f.severity, 3), f.file, f.line, f.title))
    return findings


RULE_HINTS = ("create", "update", "delete", "borrow", "return", "validate", "check", "calculate", "login", "save", "process", "approve", "cancel")


def extract_if_returns(body: str) -> list[tuple[str, str, int]]:
    results: list[tuple[str, str, int]] = []
    for match in re.finditer(r"\bif\s*\(", body):
        open_index = body.find("(", match.start())
        depth = 0
        close_index = -1
        for index in range(open_index, len(body)):
            if body[index] == "(":
                depth += 1
            elif body[index] == ")":
                depth -= 1
                if depth == 0:
                    close_index = index
                    break
        if close_index < 0:
            continue
        condition = re.sub(r"\s+", " ", body[open_index + 1:close_index]).strip()
        tail = body[close_index + 1:]
        return_match = re.search(r"\breturn\s+\"([^\"]+)\"", tail)
        if not return_match:
            continue
        between = tail[:return_match.start()]
        if "}" in between:
            continue
        action = re.sub(r"\s+", " ", return_match.group(1)).strip()
        results.append((condition, action, match.start()))
    return results


def extract_business_rules(classes: list[ClassInfo], java_sources: list[tuple[str, str]], tables: list[TableInfo]) -> list[BusinessRuleInfo]:
    sources = dict(java_sources)
    rules: list[BusinessRuleInfo] = []
    seen: set[tuple[str, str]] = set()
    for cls in classes:
        if cls.layer not in {"business", "presentation"}:
            continue
        for method in cls.methods:
            lower = method.name.lower()
            if not any(hint in lower for hint in RULE_HINTS) and "nghiệp vụ" not in method.doc.lower():
                continue
            lines = sources.get(method.file, "").splitlines()
            if not lines:
                continue
            body = "\n".join(lines[max(0, method.start_line - 1): method.end_line])
            found_for_method = False
            for condition, action, offset in extract_if_returns(body):
                if "thành công" in action.lower():
                    continue
                key = (condition, action)
                if key in seen:
                    continue
                seen.add(key)
                rules.append(BusinessRuleInfo(
                    title=f"{cls.name}.{method.name}",
                    condition=condition,
                    action=action,
                    file=method.file,
                    line=method.start_line + body[:offset].count("\n"),
                ))
                found_for_method = True
            if method.doc and any(hint in lower for hint in RULE_HINTS):
                key = ("Javadoc", method.doc)
                if key not in seen:
                    seen.add(key)
                    rules.append(BusinessRuleInfo(
                        title=f"{cls.name}.{method.name}",
                        condition=method.doc,
                        action="Quy tắc được ghi nhận từ Javadoc của phương thức.",
                        file=method.file,
                        line=method.start_line,
                    ))
    for table in tables:
        for foreign_key in table.foreign_keys:
            if "->" not in foreign_key:
                continue
            child, target = foreign_key.split("->", 1)
            rules.append(BusinessRuleInfo(
                title=f"Ràng buộc dữ liệu {table.name}",
                condition=f"{child} tham chiếu {target}",
                action="Giá trị khóa ngoại phải tồn tại ở bảng được tham chiếu.",
                file=table.source,
            ))
    return rules[:40]


def compute_metrics(
    files,
    classes: list[ClassInfo],
    endpoints,
    tables: list[TableInfo],
    dependencies: list[DependencyInfo],
    cycles: list[list[str]],
    findings: list[FindingInfo],
    scan,
) -> dict:
    methods = [m for cls in classes for m in cls.methods]
    complexities = [m.complexity for m in methods] or [1]
    long_methods = [m for m in methods if m.loc > 35 or m.complexity > 10]
    high_findings = [f for f in findings if f.severity == "Cao"]
    medium_findings = [f for f in findings if f.severity == "Trung bình"]
    low_findings = [f for f in findings if f.severity == "Thấp"]
    has_tests = any("test" in f.path.lower() or "spec" in f.path.lower() for f in files)
    jsp_scriptlets = any(f.language == "JSP" for f in files)
    sql_concat = any("SQL được nối chuỗi" in f.title for f in findings)
    score = 25
    score += min(20, scan.todo_count * 2)
    score += min(20, len(cycles) * 5)
    score += min(15, len(long_methods) * 2)
    score += min(15, len(high_findings) * 4)
    score += min(10, max(0, max(complexities) - 8))
    score += 10 if not has_tests else 0
    score += 5 if jsp_scriptlets else 0
    score += 5 if sql_concat else 0
    legacy_score = min(100, int(round(score)))
    if legacy_score >= 80:
        grade = "Rủi ro rất cao"
    elif legacy_score >= 60:
        grade = "Rủi ro cao"
    elif legacy_score >= 40:
        grade = "Trung bình"
    else:
        grade = "Thấp"
    return {
        "files": len(files),
        "loc": scan.total_loc,
        "code_lines": scan.total_code,
        "comment_lines": scan.total_comments,
        "blank_lines": scan.total_blank,
        "classes": len(classes),
        "methods": len(methods),
        "fields": sum(len(cls.fields) for cls in classes),
        "endpoints": len(endpoints),
        "tables": len(tables),
        "dependencies": len(dependencies),
        "cycles": len(cycles),
        "avg_methods_per_class": round(len(methods) / max(1, len(classes)), 1),
        "avg_complexity": round(sum(complexities) / max(1, len(complexities)), 1),
        "max_complexity": max(complexities),
        "long_methods": len(long_methods),
        "todos": scan.todo_count,
        "findings_total": len(findings),
        "findings_high": len(high_findings),
        "findings_medium": len(medium_findings),
        "findings_low": len(low_findings),
        "legacy_score": legacy_score,
        "legacy_grade": grade,
        "maintainability": max(0, 100 - legacy_score),
        "has_tests": has_tests,
        "jsp_scriptlets": jsp_scriptlets,
        "sql_concat": sql_concat,
    }


def build_overview(project_name: str, classes: list[ClassInfo], endpoints, tables, layers, metrics) -> dict:
    technologies = []
    if any("servlet" in cls.package.lower() or "WebServlet" in " ".join(cls.annotations) for cls in classes):
        technologies.append("Java Servlet")
    if any("jdbc" in (cls.package + " " + " ".join(f.type for f in cls.fields)).lower() for cls in classes):
        technologies.append("JDBC")
    if any("spring" in cls.package.lower() or any("Mapping" in a for a in cls.annotations) for cls in classes):
        technologies.append("Spring MVC")
    if any(cls.kind == "interface" for cls in classes):
        technologies.append("Java Interface")
    if tables:
        technologies.append("Cơ sở dữ liệu quan hệ")
    if not technologies:
        technologies.append("Java")
    layer_names = [layer.name for layer in layers]
    return {
        "technologies": technologies,
        "layer_names": layer_names,
        "summary": (
            f"{project_name} là một hệ thống mã nguồn cũ gồm {metrics['classes']} lớp, "
            f"{metrics['methods']} phương thức, {metrics['endpoints']} điểm truy cập API và "
            f"{metrics['tables']} bảng dữ liệu. Mã nguồn được tổ chức thành "
            f"{len(layers)} tầng chính: {', '.join(layer_names)}. "
            f"Chỉ số rủi ro kỹ thuật ước lượng là {metrics['legacy_score']}/100 "
            f"({metrics['legacy_grade'].lower()})."
        ),
        "recommendations": [
            "Ưu tiên xử lý các điểm hard-code thông tin đăng nhập và SQL nối chuỗi.",
            "Bổ sung kiểm thử hồi quy trước khi tái cấu trúc các lớp nghiệp vụ.",
            "Tách các phương thức dài và giảm phụ thuộc vòng giữa các lớp.",
            "Chuẩn hóa tài liệu API và mô hình dữ liệu từ kết quả trích xuất.",
        ],
    }


def analyze_project(root: Path, project_name: str | None = None, analysis_id: str | None = None) -> AnalysisResult:
    root = Path(root).resolve()
    scan = scan_project(root)
    analysis_id = analysis_id or datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    classes: list[ClassInfo] = []
    endpoints = []
    imports_by_file: dict[str, list[str]] = {}
    java_sources: list[tuple[str, str]] = []
    for file_info in scan.files:
        if file_info.language != "Java":
            continue
        path = root / file_info.path
        text = read_text(path)
        java_sources.append((file_info.path, text))
        imports_by_file[file_info.path] = re.findall(r"\bimport\s+(?:static\s+)?([\w.*]+)\s*;", text)
        parsed_classes, parsed_endpoints = parse_java_file(path, file_info.path)
        classes.extend(parsed_classes)
        endpoints.extend(parsed_endpoints)
    classes.sort(key=lambda c: (c.package, c.name))
    endpoints.sort(key=lambda e: (e.path, e.http_method, e.class_name, e.handler))
    tables = collect_tables(root, scan.files, java_sources)
    layers = build_layers(classes)
    dependencies = build_dependencies(classes, imports_by_file)
    cycles = detect_cycles(classes, dependencies)
    findings = collect_findings(root, scan.files, classes, dependencies, cycles)
    business_rules = extract_business_rules(classes, java_sources, tables)
    metrics = compute_metrics(scan.files, classes, endpoints, tables, dependencies, cycles, findings, scan)
    metrics["business_rules"] = len(business_rules)
    project_name = project_name or root.name.replace("_", " ").title()
    overview = build_overview(project_name, classes, endpoints, tables, layers, metrics)
    summary = {
        "project_name": project_name,
        "file_count": len(scan.files),
        "loc": scan.total_loc,
        "class_count": len(classes),
        "method_count": metrics["methods"],
        "endpoint_count": len(endpoints),
        "table_count": len(tables),
        "rule_count": len(business_rules),
        "layer_count": len(layers),
        "legacy_score": metrics["legacy_score"],
        "legacy_grade": metrics["legacy_grade"],
        "top_layers": [
            {"name": layer.name, "class_count": layer.class_count, "loc": layer.loc}
            for layer in layers
        ],
        "language_stats": scan.language_stats,
    }
    return AnalysisResult(
        analysis_id=analysis_id,
        project_name=project_name,
        root=str(root),
        generated_at=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        files=scan.files,
        classes=classes,
        endpoints=endpoints,
        tables=tables,
        dependencies=dependencies,
        findings=findings,
        business_rules=business_rules,
        layers=layers,
        metrics=metrics,
        cycles=cycles,
        summary=summary,
        overview=overview,
    )
