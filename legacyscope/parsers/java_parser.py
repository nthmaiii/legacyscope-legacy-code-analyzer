from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from ..models import ClassInfo, EndpointInfo, FieldInfo, MethodInfo


MASK_CHAR = " "


def mask_java(text: str) -> str:
    """Che giấu comment và nội dung chuỗi để matching cấu trúc chính xác hơn."""
    chars = list(text)
    i = 0
    state = "normal"
    while i < len(chars):
        ch = chars[i]
        nxt = chars[i + 1] if i + 1 < len(chars) else ""
        if state == "normal":
            if ch == "/" and nxt == "/":
                chars[i] = chars[i + 1] = MASK_CHAR
                state = "line_comment"
                i += 2
                continue
            if ch == "/" and nxt == "*":
                chars[i] = chars[i + 1] = MASK_CHAR
                state = "block_comment"
                i += 2
                continue
            if ch == '"':
                chars[i] = MASK_CHAR
                state = "string"
                i += 1
                continue
            if ch == "'":
                chars[i] = MASK_CHAR
                state = "char"
                i += 1
                continue
        elif state == "line_comment":
            if ch == "\n":
                state = "normal"
            else:
                chars[i] = MASK_CHAR
        elif state == "block_comment":
            if ch == "*" and nxt == "/":
                chars[i] = chars[i + 1] = MASK_CHAR
                state = "normal"
                i += 2
                continue
            if ch != "\n":
                chars[i] = MASK_CHAR
        elif state == "string":
            if ch == "\\":
                chars[i] = MASK_CHAR
                if i + 1 < len(chars):
                    chars[i + 1] = MASK_CHAR
                i += 2
                continue
            if ch == '"':
                chars[i] = MASK_CHAR
                state = "normal"
            elif ch != "\n":
                chars[i] = MASK_CHAR
        elif state == "char":
            if ch == "\\":
                chars[i] = MASK_CHAR
                if i + 1 < len(chars):
                    chars[i + 1] = MASK_CHAR
                i += 2
                continue
            if ch == "'":
                chars[i] = MASK_CHAR
                state = "normal"
            elif ch != "\n":
                chars[i] = MASK_CHAR
        i += 1
    return "".join(chars)


def matching_brace(masked: str, open_index: int) -> int:
    depth = 0
    for i in range(open_index, len(masked)):
        if masked[i] == "{":
            depth += 1
        elif masked[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    return len(masked) - 1


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, max(0, index)) + 1


def extract_annotations(text: str) -> list[str]:
    result = []
    for match in re.finditer(r"@([A-Za-z_$][\w.]*)(?:\s*\(([^)]*)\))?", text):
        name, args = match.group(1), match.group(2)
        if args:
            result.append(f"@{name}({re.sub(r'\s+', ' ', args.strip())})")
        else:
            result.append(f"@{name}")
    return result


def annotation_strings(text: str) -> list[str]:
    return re.findall(r'"([^"]*)"', text)


def clean_member(text: str) -> tuple[str, list[str], str]:
    annotations = extract_annotations(text)
    without_annotations = re.sub(r"@[A-Za-z_$][\w.]*(?:\s*\([^)]*\))?", " ", text)
    modifiers = ""
    for mod in ("public", "protected", "private", "static", "final", "abstract", "synchronized", "native", "transient", "volatile", "strictfp", "default"):
        if re.search(rf"\b{mod}\b", without_annotations):
            modifiers += mod + " "
    cleaned = re.sub(
        r"\b(public|protected|private|static|final|abstract|synchronized|native|transient|volatile|strictfp|default)\b",
        " ",
        without_annotations,
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned, annotations, modifiers.strip()


def extract_javadoc(body_raw: str, member_start: int) -> str:
    text = body_raw[max(0, member_start - 1200):member_start]
    return clean_javadoc(text)


def clean_javadoc(text: str) -> str:
    blocks = list(re.finditer(r"/\*\*(.*?)\*/", text, flags=re.DOTALL))
    if not blocks:
        return ""
    doc = blocks[-1].group(1)
    lines = []
    for line in doc.splitlines():
        line = re.sub(r"^\s*\*\s?", "", line).strip()
        if line:
            lines.append(line)
    return " ".join(lines).strip()


def parse_method(chunk_raw: str, body_raw: str, class_name: str, file: str, body_offset_line: int) -> MethodInfo | None:
    cleaned, annotations, modifiers = clean_member(chunk_raw)
    if "(" not in cleaned:
        return None
    if re.search(r"\b(class|interface|enum)\b", cleaned):
        return None
    match = re.search(r"([A-Za-z_$][\w$]*)\s*\(([^)]*)\)", cleaned)
    if not match:
        return None
    name = match.group(1)
    if name in {"if", "for", "while", "switch", "catch", "return", "new", "assert", "throw"}:
        return None
    params = re.sub(r"\s+", " ", match.group(2)).strip()
    before = cleaned[: match.start()].strip()
    return_type = before.split()[-1] if before else class_name
    is_constructor = not before or before == class_name
    if is_constructor:
        return_type = class_name
    visibility = "package"
    for candidate in ("public", "protected", "private"):
        if candidate in modifiers.split():
            visibility = candidate
            break
    if "public" in chunk_raw:
        visibility = "public"
    elif "protected" in chunk_raw:
        visibility = "protected"
    elif "private" in chunk_raw:
        visibility = "private"
    complexity = 1
    for keyword in ("if", "for", "while", "case", "catch", "&&", "||"):
        complexity += len(re.findall(rf"\b{keyword}\b" if keyword.isalpha() else re.escape(keyword), body_raw))
    complexity += len(re.findall(r"\?", body_raw))
    calls = []
    for call in re.findall(r"([A-Za-z_$][\w$]*)\s*\(", body_raw):
        if call in {"if", "for", "while", "switch", "catch", "return", "new", "throw", "assert", "super", "this"}:
            continue
        if call not in calls:
            calls.append(call)
    signature = f"{return_type} {name}({params})"
    if is_constructor:
        signature = f"{name}({params})"
    return MethodInfo(
        name=name,
        signature=signature,
        return_type=return_type,
        parameters=params,
        annotations=annotations,
        visibility=visibility,
        loc=body_raw.count("\n") + 1,
        complexity=complexity,
        calls=calls,
        doc="",
        owner=class_name,
        file=file,
        is_constructor=is_constructor,
    )


def parse_field(chunk_raw: str, file: str) -> list[FieldInfo]:
    cleaned, annotations, modifiers = clean_member(chunk_raw)
    if not cleaned or "(" in cleaned:
        return []
    if "=" in cleaned:
        cleaned = cleaned.split("=", 1)[0].strip()
    parts = cleaned.replace(",", " ").split()
    if len(parts) < 2:
        return []
    field_type = parts[0]
    names = parts[1:]
    return [
        FieldInfo(
            name=name.strip("[]"),
            type=field_type,
            modifiers=modifiers,
            annotations=annotations,
        )
        for name in names
        if re.match(r"^[A-Za-z_$][\w$]*", name)
    ]


def extract_referenced_types(class_info: ClassInfo, body_raw: str) -> list[str]:
    names: set[str] = set()
    if class_info.extends:
        names.add(class_info.extends.split(".")[-1])
    for interface in class_info.implements:
        names.add(interface.split(".")[-1])
    for field_info in class_info.fields:
        token = re.sub(r"<.*>", "", field_info.type)
        for candidate in re.findall(r"[A-Z][A-Za-z0-9_$]*", token):
            names.add(candidate)
    for method in class_info.methods:
        for token in [method.return_type, method.parameters]:
            for candidate in re.findall(r"[A-Z][A-Za-z0-9_$]*", token):
                names.add(candidate)
    for candidate in re.findall(r"\bnew\s+([A-Z][A-Za-z0-9_$]*)", body_raw):
        names.add(candidate)
    names.discard(class_info.name)
    return sorted(names)


def parse_members(
    class_info: ClassInfo,
    body_masked: str,
    body_raw: str,
    class_start_line: int,
    file: str,
) -> None:
    depth = 0
    paren_depth = 0
    member_start = 0
    i = 0
    while i < len(body_masked):
        ch = body_masked[i]
        if ch == "(":
            paren_depth += 1
        elif ch == ")":
            paren_depth = max(0, paren_depth - 1)
        elif ch == "{" and paren_depth == 0:
            chunk_masked = body_masked[member_start:i]
            chunk_raw = body_raw[member_start:i]
            if depth == 0 and chunk_masked.strip() and not re.search(r"\b(class|interface|enum)\b", chunk_masked):
                close = matching_brace(body_masked, i)
                method = parse_method(chunk_raw, body_raw[i + 1:close], class_info.name, file, class_start_line)
                if method is not None:
                    method.start_line = class_start_line + body_raw[:member_start].count("\n")
                    method.end_line = class_start_line + body_raw[:close].count("\n")
                    method.doc = clean_javadoc(chunk_raw)
                    class_info.methods.append(method)
                i = close
                member_start = i + 1
                depth = 0
            else:
                depth += 1
        elif ch == "}" and paren_depth == 0:
            depth = max(0, depth - 1)
        elif ch == ";" and depth == 0 and paren_depth == 0:
            chunk_raw = body_raw[member_start:i]
            chunk_masked = body_masked[member_start:i]
            if chunk_masked.strip() and not re.search(r"\b(class|interface|enum)\b", chunk_masked):
                if "(" in chunk_masked:
                    method = parse_method(chunk_raw, "", class_info.name, file, class_start_line)
                    if method is not None:
                        method.start_line = class_start_line + body_raw[:member_start].count("\n")
                        method.end_line = method.start_line
                        method.doc = clean_javadoc(chunk_raw)
                        class_info.methods.append(method)
                else:
                    fields = parse_field(chunk_raw, file)
                    for field_info in fields:
                        field_info.line = class_start_line + body_raw[:member_start].count("\n")
                        class_info.fields.append(field_info)
            member_start = i + 1
        i += 1


CLASS_RE = re.compile(
    r"(?P<ann>(?:@[A-Za-z_$][\w.]*(?:\s*\([^)]*\))?\s*)*)"
    r"(?P<mods>(?:(?:public|protected|private|abstract|final|static|strictfp|sealed|non-sealed)\s+)*)"
    r"(?P<kind>class|interface|enum)\s+"
    r"(?P<name>[A-Za-z_$][\w$]*)"
    r"(?:\s*<[^{};]*>)?"
    r"(?:\s+extends\s+(?P<extends>[\w.$]+))?"
    r"(?:\s+implements\s+(?P<implements>[\w.$,\s]+?))?"
    r"\s*\{",
    flags=re.MULTILINE,
)


def parse_java_file(path: Path, rel_path: str) -> tuple[list[ClassInfo], list[EndpointInfo]]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [], []
    masked = mask_java(text)
    package_match = re.search(r"\bpackage\s+([\w.]+)\s*;", masked)
    package = package_match.group(1) if package_match else ""
    imports = re.findall(r"\bimport\s+(?:static\s+)?([\w.*]+)\s*;", masked)
    classes: list[ClassInfo] = []
    endpoints: list[EndpointInfo] = []

    for match in CLASS_RE.finditer(masked):
        open_index = match.end() - 1
        close_index = matching_brace(masked, open_index)
        raw_decl = text[match.start():match.start("kind")]
        annotations = extract_annotations(raw_decl)
        extends = (match.group("extends") or "").strip()
        implements_raw = (match.group("implements") or "").strip()
        implements = [item.strip().split(".")[-1] for item in implements_raw.split(",") if item.strip()]
        class_start_line = line_of(text, match.start())
        class_end_line = line_of(text, close_index)
        body_raw = text[open_index + 1:close_index]
        body_masked = masked[open_index + 1:close_index]
        class_info = ClassInfo(
            name=match.group("name"),
            package=package,
            kind=match.group("kind"),
            extends=extends.split(".")[-1] if extends else "",
            implements=implements,
            annotations=annotations,
            start_line=class_start_line,
            end_line=class_end_line,
            loc=class_end_line - class_start_line + 1,
            file=rel_path,
            source_excerpt=body_raw[:300].strip(),
        )
        parse_members(class_info, body_masked, body_raw, class_start_line + 1, rel_path)
        class_info.referenced_types = extract_referenced_types(class_info, body_raw)
        # Imports được giữ ở cấp file để analyzer nối dependency.
        class_info.referenced_types = sorted(set(class_info.referenced_types + [i.split(".")[-1] for i in imports if not i.endswith("*")]))
        classes.append(class_info)
        endpoints.extend(extract_endpoints(class_info, text, match.start(), imports))

    return classes, endpoints


def combine_path(base: str, path: str) -> str:
    base = (base or "").strip()
    path = (path or "").strip()
    if not base:
        return path or "/"
    if not path:
        return base
    return "/" + "/".join(part.strip("/") for part in (base, path) if part.strip("/"))


def extract_endpoints(class_info: ClassInfo, text: str, class_start: int, imports: list[str]) -> list[EndpointInfo]:
    endpoints: list[EndpointInfo] = []
    class_annotation_raw = " ".join(class_info.annotations)
    web_paths: list[str] = []
    if "WebServlet" in class_annotation_raw:
        args = class_annotation_raw
        if "urlPatterns" in args:
            args = args.split("urlPatterns", 1)[1]
        elif "value" in args:
            args = args.split("value", 1)[1]
        strings = annotation_strings(args)
        web_paths = [value for value in strings if value.startswith("/")]
        if not web_paths:
            web_paths = ["/"]
        for method in class_info.methods:
            if method.name in {"doGet", "doPost", "doPut", "doDelete"}:
                http_method = {"doGet": "GET", "doPost": "POST", "doPut": "PUT", "doDelete": "DELETE"}[method.name]
                for web_path in web_paths:
                    endpoints.append(EndpointInfo(
                        http_method=http_method,
                        path=web_path if web_path.startswith("/") else "/" + web_path,
                        handler=method.name,
                        class_name=class_info.name,
                        file=class_info.file,
                        line=method.start_line,
                        description=describe_handler(method.name),
                        source="Servlet",
                    ))

    spring_base = ""
    for annotation in class_info.annotations:
        if annotation.startswith("@RequestMapping"):
            strings = annotation_strings(annotation)
            if strings:
                spring_base = strings[0]
    mapping_re = re.compile(r"@(Get|Post|Put|Delete|Patch|Request)Mapping\s*(?:\(([^)]*)\))?")
    for method in class_info.methods:
        for annotation in method.annotations:
            match = mapping_re.search(annotation)
            if not match:
                continue
            verb = match.group(1)
            args = match.group(2) or ""
            strings = annotation_strings(args)
            path = combine_path(spring_base, strings[0] if strings else "")
            if verb == "Request":
                method_match = re.search(r"RequestMethod\.(GET|POST|PUT|DELETE|PATCH)", args)
                http_method = method_match.group(1) if method_match else "ANY"
            else:
                http_method = {"Get": "GET", "Post": "POST", "Put": "PUT", "Delete": "DELETE", "Patch": "PATCH"}[verb]
            endpoints.append(EndpointInfo(
                http_method=http_method,
                path=path or "/",
                handler=method.name,
                class_name=class_info.name,
                file=class_info.file,
                line=method.start_line,
                description=describe_handler(method.name),
                source="Spring MVC",
            ))
    return dedupe_endpoints(endpoints)


def describe_handler(name: str) -> str:
    mapping = {
        "doGet": "Truy vấn / hiển thị dữ liệu",
        "doPost": "Tạo mới / cập nhật / xử lý nghiệp vụ",
        "doPut": "Cập nhật tài nguyên",
        "doDelete": "Xóa tài nguyên",
        "login": "Xác thực người dùng",
        "create": "Tạo mới tài nguyên",
        "update": "Cập nhật tài nguyên",
        "delete": "Xóa tài nguyên",
        "list": "Liệt kê tài nguyên",
        "search": "Tìm kiếm tài nguyên",
    }
    return mapping.get(name, f"Xử lý nghiệp vụ {name}")


def dedupe_endpoints(endpoints: list[EndpointInfo]) -> list[EndpointInfo]:
    seen = set()
    result = []
    for endpoint in endpoints:
        key = (endpoint.http_method, endpoint.path, endpoint.class_name, endpoint.handler)
        if key not in seen:
            seen.add(key)
            result.append(endpoint)
    return result
