from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class FieldInfo:
    name: str
    type: str
    modifiers: str = ""
    annotations: list[str] = field(default_factory=list)
    line: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MethodInfo:
    name: str
    signature: str
    return_type: str = "void"
    parameters: str = ""
    annotations: list[str] = field(default_factory=list)
    visibility: str = "package"
    start_line: int = 0
    end_line: int = 0
    loc: int = 0
    complexity: int = 1
    calls: list[str] = field(default_factory=list)
    doc: str = ""
    owner: str = ""
    file: str = ""
    is_constructor: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ClassInfo:
    name: str
    package: str
    kind: str = "class"
    extends: str = ""
    implements: list[str] = field(default_factory=list)
    annotations: list[str] = field(default_factory=list)
    fields: list[FieldInfo] = field(default_factory=list)
    methods: list[MethodInfo] = field(default_factory=list)
    start_line: int = 0
    end_line: int = 0
    loc: int = 0
    file: str = ""
    layer: str = "Khác"
    referenced_types: list[str] = field(default_factory=list)
    source_excerpt: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return data

    @property
    def method_count(self) -> int:
        return len(self.methods)

    @property
    def field_count(self) -> int:
        return len(self.fields)


@dataclass
class EndpointInfo:
    http_method: str
    path: str
    handler: str
    class_name: str
    file: str
    line: int = 0
    description: str = ""
    source: str = "annotation"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ColumnInfo:
    name: str
    type: str
    is_primary: bool = False
    is_foreign: bool = False
    nullable: bool = True
    references: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TableInfo:
    name: str
    columns: list[ColumnInfo] = field(default_factory=list)
    source: str = ""
    primary_key: str = ""
    foreign_keys: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DependencyInfo:
    source: str
    target: str
    kind: str = "import"
    weight: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FindingInfo:
    severity: str
    category: str
    title: str
    description: str
    file: str = ""
    line: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BusinessRuleInfo:
    title: str
    condition: str
    action: str
    file: str = ""
    line: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LayerInfo:
    key: str
    name: str
    description: str
    color: str
    classes: list[str] = field(default_factory=list)
    loc: int = 0
    methods: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def class_count(self) -> int:
        return len(self.classes)


@dataclass
class FileInfo:
    path: str
    language: str
    loc: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    size_bytes: int = 0
    todos: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AnalysisResult:
    analysis_id: str
    project_name: str
    root: str
    generated_at: str
    files: list[FileInfo] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)
    endpoints: list[EndpointInfo] = field(default_factory=list)
    tables: list[TableInfo] = field(default_factory=list)
    dependencies: list[DependencyInfo] = field(default_factory=list)
    findings: list[FindingInfo] = field(default_factory=list)
    business_rules: list[BusinessRuleInfo] = field(default_factory=list)
    layers: list[LayerInfo] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    cycles: list[list[str]] = field(default_factory=list)
    diagrams: dict[str, str] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)
    overview: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "project_name": self.project_name,
            "root": self.root,
            "generated_at": self.generated_at,
            "files": [f.to_dict() for f in self.files],
            "classes": [c.to_dict() for c in self.classes],
            "endpoints": [e.to_dict() for e in self.endpoints],
            "tables": [t.to_dict() for t in self.tables],
            "dependencies": [d.to_dict() for d in self.dependencies],
            "findings": [f.to_dict() for f in self.findings],
            "business_rules": [r.to_dict() for r in self.business_rules],
            "layers": [l.to_dict() for l in self.layers],
            "metrics": self.metrics,
            "cycles": self.cycles,
            "diagrams": self.diagrams,
            "artifacts": self.artifacts,
            "summary": self.summary,
            "overview": self.overview,
        }
