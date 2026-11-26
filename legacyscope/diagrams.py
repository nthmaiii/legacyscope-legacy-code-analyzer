from __future__ import annotations

import textwrap
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle, Wedge

from .models import AnalysisResult

plt.rcParams["font.family"] = "Arial"
plt.rcParams["axes.unicode_minus"] = False

BG = "#F8FAFC"
INK = "#0F172A"
MUTED = "#64748B"
GRID = "#E2E8F0"
ACCENT = "#2563EB"
SEVERITY_COLORS = {"Cao": "#DC2626", "Trung bình": "#F59E0B", "Thấp": "#0EA5E9"}


def _canvas(width=13, height=8):
    fig, ax = plt.subplots(figsize=(width, height), dpi=200)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    return fig, ax


def _save(fig, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=220, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def _box(ax, x, y, w, h, face, edge, radius=0.015, lw=1.2, z=2, alpha=1.0):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.008,rounding_size={radius}",
        linewidth=lw, edgecolor=edge, facecolor=face, zorder=z, alpha=alpha,
    )
    ax.add_patch(patch)
    return patch


def _arrow(ax, start, end, color=MUTED, lw=1.6, style="-|>", rad=0.0, z=1):
    arrow = FancyArrowPatch(
        start, end, arrowstyle=style, mutation_scale=14,
        linewidth=lw, color=color, zorder=z,
        connectionstyle=f"arc3,rad={rad}",
    )
    ax.add_patch(arrow)
    return arrow


def _truncate(value: str, limit=26):
    return value if len(value) <= limit else value[: limit - 1] + "…"


def _chip_text(classes, limit=4):
    if not classes:
        return "Chưa phát hiện lớp"
    shown = classes[:limit]
    suffix = f"  +{len(classes) - limit}" if len(classes) > limit else ""
    return " · ".join(shown) + suffix


def architecture_layers(result: AnalysisResult, output: Path) -> str:
    fig, ax = _canvas(13, 8.2)
    ax.text(0.04, 0.95, "Kiến trúc phân tầng phục hồi từ mã nguồn", fontsize=23, weight="bold", color=INK)
    ax.text(0.04, 0.91, f"{result.project_name} · {result.metrics['classes']} lớp · {result.metrics['loc']} dòng mã · {result.generated_at}",
            fontsize=10.5, color=MUTED)
    _box(ax, 0.28, 0.825, 0.44, 0.055, "#0F172A", "#0F172A", radius=0.02)
    ax.text(0.5, 0.852, "Người dùng / Trình duyệt / Ứng dụng khách", color="white", ha="center", va="center", fontsize=11, weight="bold")
    _arrow(ax, (0.5, 0.825), (0.5, 0.785), color="#94A3B8", lw=2)

    y_positions = [0.625, 0.49, 0.355, 0.22, 0.085]
    order = ["presentation", "business", "persistence", "domain", "infrastructure"]
    for index, key in enumerate(order):
        layer = next((layer for layer in result.layers if layer.key == key), None)
        if layer is None:
            continue
        y = y_positions[index]
        h = 0.105
        _box(ax, 0.055, y, 0.89, h, "white", "#CBD5E1", lw=1.2)
        _box(ax, 0.055, y, 0.018, h, layer.color, layer.color, radius=0.01, lw=0)
        ax.text(0.09, y + h - 0.026, layer.name, fontsize=12.5, weight="bold", color=layer.color)
        ax.text(0.09, y + h - 0.060, layer.description, fontsize=8.6, color=MUTED)
        ax.text(0.69, y + h - 0.026, f"{layer.class_count} lớp  ·  {layer.methods} phương thức  ·  {layer.loc} dòng",
                fontsize=9, color=INK, ha="left")
        ax.text(0.69, y + h - 0.060, _chip_text(layer.classes, 5), fontsize=8.2, color=MUTED)
        if index < len(order) - 1 and any(l.key == order[index + 1] for l in result.layers):
            _arrow(ax, (0.5, y - 0.002), (0.5, y - 0.022), color="#94A3B8", lw=1.5)

    _box(ax, 0.29, 0.012, 0.42, 0.05, "#ECFDF5", "#10B981", radius=0.018, lw=1.1)
    ax.text(0.5, 0.037, f"CSDL quan hệ · {result.metrics['tables']} bảng · {result.metrics['endpoints']} endpoint",
            ha="center", va="center", fontsize=10, color="#047857", weight="bold")
    path = output / "architecture_layers.png"
    _save(fig, path)
    return str(path)


def dependency_graph(result: AnalysisResult, output: Path) -> str:
    fig, ax = _canvas(12.5, 8)
    ax.text(0.04, 0.95, "Bản đồ phụ thuộc giữa các tầng", fontsize=22, weight="bold", color=INK)
    ax.text(0.04, 0.91, "Mũi tên thể hiện chiều phụ thuộc; độ dày cạnh tỉ lệ với số quan hệ lớp", fontsize=10, color=MUTED)

    layer_by_key = {layer.key: layer for layer in result.layers}
    positions = {
        "presentation": (0.50, 0.79),
        "business": (0.50, 0.60),
        "persistence": (0.50, 0.41),
        "domain": (0.22, 0.20),
        "infrastructure": (0.78, 0.20),
    }
    class_to_layer = {cls.name: cls.layer for cls in result.classes}
    edge_counts: Counter[tuple[str, str]] = Counter()
    for dependency in result.dependencies:
        source_layer = class_to_layer.get(dependency.source)
        target_layer = class_to_layer.get(dependency.target)
        if source_layer and target_layer and source_layer != target_layer:
            edge_counts[(source_layer, target_layer)] += 1

    nodes = {}
    for key, (cx, cy) in positions.items():
        layer = layer_by_key.get(key)
        if layer is None:
            continue
        w, h = 0.27, 0.11
        _box(ax, cx - w / 2, cy - h / 2, w, h, "white", layer.color, lw=1.6)
        _box(ax, cx - w / 2, cy - h / 2, 0.014, h, layer.color, layer.color, radius=0.008, lw=0)
        ax.text(cx - w / 2 + 0.03, cy + 0.022, layer.name, fontsize=11.5, weight="bold", color=layer.color, va="center")
        ax.text(cx - w / 2 + 0.03, cy - 0.013, f"{layer.class_count} lớp · {layer.loc} dòng · {layer.methods} hàm",
                fontsize=8, color=MUTED, va="center")
        nodes[key] = (cx, cy, w, h)

    _box(ax, 0.38, 0.025, 0.24, 0.06, "#ECFDF5", "#10B981", radius=0.015, lw=1.0)
    ax.text(0.50, 0.055, f"CSDL · {result.metrics['tables']} bảng", ha="center", va="center", fontsize=10, color="#047857", weight="bold")

    def center(key, side="top"):
        cx, cy, w, h = nodes[key]
        if side == "top":
            return (cx, cy + h / 2)
        if side == "bottom":
            return (cx, cy - h / 2)
        return (cx, cy)

    for (source, target), count in sorted(edge_counts.items(), key=lambda item: -item[1]):
        if source not in nodes or target not in nodes:
            continue
        start = center(source, "bottom")
        end = center(target, "top")
        color = layer_by_key[target].color
        rad = 0.08 if source == "presentation" and target == "persistence" else 0.0
        _arrow(ax, start, end, color=color, lw=1.2 + min(2.2, count * 0.12), rad=rad, z=1)
        _ = count

    _arrow(ax, (0.50, 0.37), (0.50, 0.095), color="#10B981", lw=1.8, z=1)
    ax.text(0.515, 0.24, "SQL / JDBC", fontsize=8, color="#047857", rotation=90, va="center")

    ax.text(0.04, 0.12, "Độ dày cạnh tỉ lệ với số quan hệ lớp được phát hiện", fontsize=8, color=MUTED)
    if result.cycles:
        ax.text(0.04, 0.07, f"Phát hiện {len(result.cycles)} chu trình phụ thuộc", fontsize=9, color="#DC2626", weight="bold")
    else:
        ax.text(0.04, 0.07, "Không phát hiện chu trình phụ thuộc giữa các lớp", fontsize=9, color="#047857", weight="bold")
    path = output / "dependency_graph.png"
    _save(fig, path)
    return str(path)


def class_diagram(result: AnalysisResult, output: Path) -> str:
    fig, ax = _canvas(17, 8.6)
    ax.text(0.035, 0.965, "Sơ đồ lớp rút gọn theo tầng kiến trúc", fontsize=23, weight="bold", color=INK)

    columns = ["presentation", "business", "persistence", "domain", "infrastructure"]
    col_x = {key: 0.025 + index * 0.194 for index, key in enumerate(columns)}
    labels = {layer.key: layer.name for layer in result.layers}
    colors = {layer.key: layer.color for layer in result.layers}
    class_positions: dict[str, tuple[float, float, float, float]] = {}

    for key in columns:
        group = [cls for cls in result.classes if cls.layer == key]
        if not group:
            continue
        ax.text(col_x[key] + 0.09, 0.915, labels.get(key, key), fontsize=11.5, weight="bold", color=colors.get(key, MUTED), ha="center")
        ax.plot([col_x[key] + 0.005, col_x[key] + 0.178], [0.905, 0.905], color=colors.get(key, MUTED), lw=1.2)
        box_h = 0.115
        gap = 0.022
        max_rows = 5
        shown = group[:max_rows]
        for index, cls in enumerate(shown):
            y = 0.755 - index * (box_h + gap)
            _box(ax, col_x[key] + 0.005, y, 0.178, box_h, "white", colors.get(key, MUTED), lw=1.1)
            ax.text(col_x[key] + 0.015, y + 0.078, _truncate(cls.name, 24), fontsize=9.3, weight="bold", color=INK)
            dep_count = sum(1 for d in result.dependencies if d.source == cls.name)
            ax.text(col_x[key] + 0.015, y + 0.045, f"{len(cls.methods)} phương thức · {dep_count} phụ thuộc",
                    fontsize=7.2, color=MUTED)
            ax.text(col_x[key] + 0.015, y + 0.016, cls.kind + (f" · extends {cls.extends}" if cls.extends else ""),
                    fontsize=6.8, color=colors.get(key, MUTED))
            class_positions[cls.name] = (col_x[key] + 0.005, y, 0.178, box_h)
        if len(group) > max_rows:
            ax.text(col_x[key] + 0.09, 0.755 - max_rows * (box_h + gap) + 0.02,
                    f"+{len(group) - max_rows} lớp khác", fontsize=8, color=MUTED, ha="center")

    for dependency in result.dependencies:
        if dependency.source not in class_positions or dependency.target not in class_positions:
            continue
        sx, sy, sw, sh = class_positions[dependency.source]
        tx, ty, tw, th = class_positions[dependency.target]
        start = (sx + sw, sy + sh / 2) if sx < tx else (sx, sy + sh / 2)
        end = (tx, ty + th / 2) if sx < tx else (tx + tw, ty + th / 2)
        color = colors.get(class_to_layer(result, dependency.target), "#CBD5E1")
        _arrow(ax, start, end, color=color, lw=0.7, rad=0.12, z=1)
    ax.text(0.035, 0.025, "Quan hệ được suy ra từ import, kiểu thuộc tính, tham số, giá trị trả về và lời gọi hàm.",
            fontsize=8, color=MUTED)
    path = output / "class_diagram.png"
    _save(fig, path)
    return str(path)


def class_to_layer(result: AnalysisResult, name: str) -> str:
    for cls in result.classes:
        if cls.name == name:
            return cls.layer
    return "other"


def erd_diagram(result: AnalysisResult, output: Path) -> str:
    fig, ax = _canvas(15, 9)
    ax.text(0.035, 0.96, "Mô hình dữ liệu quan hệ phục hồi", fontsize=23, weight="bold", color=INK)
    ax.text(0.035, 0.925, "Bảng, khóa chính, khóa ngoại và quan hệ được trích xuất từ schema SQL", fontsize=10, color=MUTED)

    tables = {table.name.lower(): table for table in result.tables}
    order = ["categories", "books", "users", "readers", "loans"]
    order = [name for name in order if name in tables] + [name for name in tables if name not in order]
    positions = {
        "categories": (0.03, 0.60),
        "books": (0.36, 0.58),
        "users": (0.69, 0.60),
        "readers": (0.20, 0.10),
        "loans": (0.53, 0.08),
    }
    box_positions = {}
    for name in order[:5]:
        table = tables[name]
        x, y = positions.get(name, (0.36, 0.30))
        width = 0.28
        row_h = 0.034
        max_rows = min(max(len(table.columns), 3), 6)
        height = 0.075 + max_rows * row_h
        y = max(0.03, y)
        _box(ax, x, y, width, height, "white", "#94A3B8", lw=1.1)
        _box(ax, x, y + height - 0.055, width, 0.055, "#0F172A", "#0F172A", radius=0.012, lw=0)
        ax.text(x + 0.014, y + height - 0.028, name, fontsize=10.5, weight="bold", color="white", va="center")
        shown_columns = table.columns[:max_rows]
        for index, column in enumerate(shown_columns):
            cy = y + height - 0.082 - index * row_h
            badge = "PK" if column.is_primary else ("FK" if column.is_foreign else "")
            badge_color = "#D97706" if badge == "PK" else ("#2563EB" if badge == "FK" else "#CBD5E1")
            if badge:
                _box(ax, x + 0.012, cy - 0.011, 0.032, 0.022, badge_color, badge_color, radius=0.004, lw=0)
                ax.text(x + 0.028, cy, badge, fontsize=5.8, color="white", ha="center", va="center", weight="bold")
            ax.text(x + 0.052, cy, _truncate(column.name, 22), fontsize=7.4, color=INK, va="center")
            ax.text(x + width - 0.012, cy, _truncate(column.type, 16), fontsize=6.8, color=MUTED, ha="right", va="center")
        if len(table.columns) > max_rows:
            ax.text(x + 0.014, y + 0.01, f"+{len(table.columns) - max_rows} cột khác", fontsize=6.8, color=MUTED)
        box_positions[name] = (x, y, width, height)

    for name, table in tables.items():
        if name not in box_positions:
            continue
        for foreign_key in table.foreign_keys:
            if "->" not in foreign_key:
                continue
            left, right = foreign_key.split("->", 1)
            parent_table = right.split(".")[0].lower()
            if parent_table not in box_positions:
                continue
            sx, sy, sw, sh = box_positions[name]
            tx, ty, tw, th = box_positions[parent_table]
            start = (sx + sw / 2, sy + sh) if sy < ty else (sx + sw / 2, sy)
            end = (tx + tw / 2, ty) if sy < ty else (tx + tw / 2, ty + th)
            _arrow(ax, start, end, color="#2563EB", lw=1.2, rad=-0.12, z=1)
            mx, my = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
            ax.text(mx, my + 0.012, "N:1", fontsize=6.5, color="#2563EB", ha="center",
                    bbox=dict(boxstyle="round,pad=0.12", facecolor=BG, edgecolor="none"))
    ax.text(0.035, 0.02, "PK: khóa chính · FK: khóa ngoại · N:1: nhiều bản ghi tham chiếu một bản ghi",
            fontsize=7.5, color=MUTED)
    path = output / "erd.png"
    _save(fig, path)
    return str(path)


def sequence_diagram(result: AnalysisResult, output: Path) -> str:
    fig, ax = _canvas(13, 7.8)
    ax.text(0.04, 0.95, "Luồng xử lý tiêu biểu: mượn sách", fontsize=22, weight="bold", color=INK)
    ax.text(0.04, 0.91, "Chuỗi lời gọi được suy ra từ endpoint, service và DAO trong mã nguồn", fontsize=9.5, color=MUTED)
    actors = [
        ("Client", 0.07, "#0F172A"),
        ("LoanServlet", 0.28, "#2563EB"),
        ("LoanService", 0.49, "#D97706"),
        ("BookDAO / LoanDAO", 0.70, "#059669"),
        ("MySQL", 0.91, "#7C3AED"),
    ]
    for name, x, color in actors:
        _box(ax, x - 0.065, 0.82, 0.13, 0.052, "white", color, lw=1.2)
        ax.text(x, 0.846, name, ha="center", va="center", fontsize=8.4, weight="bold", color=color)
        ax.plot([x, x], [0.82, 0.12], color="#CBD5E1", lw=1.0, linestyle=(0, (3, 4)), zorder=0)

    steps = [
        (0, 1, 0.75, "POST /loans", "#0F172A"),
        (1, 2, 0.68, "borrowBook(bookId, readerId, userId)", "#2563EB"),
        (2, 3, 0.59, "findById(bookId)", "#D97706"),
        (3, 4, 0.51, "SELECT ... FROM books", "#059669"),
        (4, 3, 0.45, "book", "#7C3AED"),
        (2, 3, 0.38, "findBorrowingByReader(readerId)", "#D97706"),
        (3, 4, 0.31, "SELECT ... FROM loans", "#059669"),
        (2, 3, 0.24, "create(loan) + update(book)", "#D97706"),
        (3, 4, 0.18, "INSERT / UPDATE", "#059669"),
        (1, 0, 0.12, "Thông báo kết quả", "#2563EB"),
    ]
    for source, target, y, label, color in steps:
        x1 = actors[source][1]
        x2 = actors[target][1]
        _arrow(ax, (x1, y), (x2, y), color=color, lw=1.2, z=2)
        ax.text((x1 + x2) / 2, y + 0.012, label, fontsize=6.9, color=color, ha="center",
                bbox=dict(boxstyle="round,pad=0.12", facecolor=BG, edgecolor="none"))
    ax.text(0.04, 0.055, "Ghi chú: sơ đồ minh họa luồng phổ biến; công cụ có thể chọn endpoint khác để sinh luồng tương tự.",
            fontsize=7.2, color=MUTED)
    path = output / "api_flow.png"
    _save(fig, path)
    return str(path)


def quality_dashboard(result: AnalysisResult, output: Path) -> str:
    fig, axes = plt.subplots(2, 2, figsize=(13, 8), dpi=200)
    fig.patch.set_facecolor(BG)
    for ax in axes.flat:
        ax.set_facecolor("white")
        for spine in ax.spines.values():
            spine.set_color(GRID)
    fig.suptitle("Bảng điều khiển chất lượng mã nguồn cũ", fontsize=20, weight="bold", color=INK, x=0.04, ha="left")
    fig.text(0.04, 0.925, f"{result.project_name} · Chỉ số rủi ro {result.metrics['legacy_score']}/100",
             fontsize=9.5, color=MUTED)

    ax = axes[0, 0]
    layers = result.layers
    names = [layer.name for layer in layers][::-1]
    locs = [layer.loc for layer in layers][::-1]
    colors = [layer.color for layer in layers][::-1]
    ax.barh(names, locs, color=colors, height=0.6)
    ax.set_title("Dòng mã theo tầng", loc="left", fontsize=11, weight="bold", color=INK)
    ax.tick_params(axis="y", labelsize=8)
    ax.tick_params(axis="x", labelsize=8)
    for index, value in enumerate(locs):
        ax.text(value + max(locs) * 0.02, index, str(value), va="center", fontsize=7.5, color=MUTED)
    ax.set_xlim(0, max(locs) * 1.18 if locs else 1)

    ax = axes[0, 1]
    severity = Counter(finding.severity for finding in result.findings)
    labels = [label for label in ["Cao", "Trung bình", "Thấp"] if severity[label]]
    values = [severity[label] for label in labels]
    if values:
        wedges, _ = ax.pie(values, colors=[SEVERITY_COLORS[label] for label in labels], startangle=90,
                           wedgeprops=dict(width=0.35, edgecolor="white"))
        ax.text(0, 0, f"{sum(values)}\nvấn đề", ha="center", va="center", fontsize=12, weight="bold", color=INK)
        ax.legend(wedges, [f"{label}: {value}" for label, value in zip(labels, values)],
                  loc="lower center", bbox_to_anchor=(0.5, -0.18), ncol=3, frameon=False, fontsize=8)
    else:
        ax.text(0.5, 0.5, "Không phát hiện vấn đề", ha="center", va="center", fontsize=11, color=MUTED)
    ax.set_title("Phân bố mức độ vấn đề", loc="left", fontsize=11, weight="bold", color=INK)
    ax.axis("off")

    ax = axes[1, 0]
    methods = []
    for cls in result.classes:
        for method in cls.methods:
            methods.append((f"{cls.name}.{method.name}", method.complexity, method.loc))
    methods.sort(key=lambda item: (item[1], item[2]), reverse=True)
    top = methods[:8][::-1]
    ax.barh([ _truncate(item[0], 28) for item in top], [item[1] for item in top], color="#F59E0B", height=0.6)
    ax.set_title("Phương thức phức tạp nhất", loc="left", fontsize=11, weight="bold", color=INK)
    ax.tick_params(axis="y", labelsize=7.2)
    ax.tick_params(axis="x", labelsize=8)
    ax.set_xlabel("Độ phức tạp ước lượng", fontsize=8, color=MUTED)

    ax = axes[1, 1]
    ax.axis("off")
    score = result.metrics["legacy_score"]
    color = "#DC2626" if score >= 80 else ("#F59E0B" if score >= 60 else "#10B981")
    wedge_bg = Wedge((0.5, 0.45), 0.38, 180, 360, width=0.12, facecolor="#E2E8F0")
    wedge_fg = Wedge((0.5, 0.45), 0.38, 180, 180 + 180 * score / 100, width=0.12, facecolor=color)
    ax.add_patch(wedge_bg)
    ax.add_patch(wedge_fg)
    ax.text(0.5, 0.50, f"{score}", ha="center", va="center", fontsize=28, weight="bold", color=color)
    ax.text(0.5, 0.405, "trên 100", ha="center", va="center", fontsize=8.5, color=MUTED)
    ax.text(0.5, 0.30, result.metrics["legacy_grade"], ha="center", va="center", fontsize=12, weight="bold", color=color)
    ax.text(0.5, 0.78, f"{result.metrics['long_methods']} phương thức dài · {result.metrics['todos']} TODO · {result.metrics['cycles']} chu trình",
            ha="center", va="center", fontsize=7.5, color=MUTED)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 0.85)
    ax.set_title("Chỉ số rủi ro mã nguồn cũ", loc="left", fontsize=11, weight="bold", color=INK)

    fig.tight_layout(rect=(0, 0, 1, 0.9))
    path = output / "quality_dashboard.png"
    _save(fig, path)
    return str(path)


def write_mermaid(result: AnalysisResult, output: Path) -> dict[str, str]:
    mermaid = {}
    layer_order = ["presentation", "business", "persistence", "domain", "infrastructure"]
    arch_lines = ["flowchart TB"]
    for index, key in enumerate(layer_order):
        layer = next((layer for layer in result.layers if layer.key == key), None)
        if not layer:
            continue
        arch_lines.append(f'    subgraph L{index}["{layer.name} ({layer.class_count} lớp)"]')
        for cls in layer.classes[:8]:
            arch_lines.append(f'        {cls}["{cls}"]')
        if len(layer.classes) > 8:
            arch_lines.append(f'        L{index}more["+{len(layer.classes) - 8} lớp"]')
        arch_lines.append("    end")
    for index in range(len(result.layers) - 1):
        arch_lines.append(f"    L{index} --> L{index + 1}")
    arch_path = output / "architecture.mmd"
    arch_path.write_text("\n".join(arch_lines), encoding="utf-8")
    mermaid["architecture"] = str(arch_path)

    class_lines = ["classDiagram"]
    for cls in result.classes:
        class_lines.append(f"    class {cls.name} {{")
        for field in cls.fields[:5]:
            class_lines.append(f"        {field.type} {field.name}")
        for method in cls.methods[:8]:
            params = method.parameters.replace(",", ", ")
            class_lines.append(f"        {method.return_type} {method.name}({params})")
        class_lines.append("    }")
    for cls in result.classes:
        if cls.extends:
            class_lines.append(f"    {cls.extends} <|-- {cls.name}")
        for interface in cls.implements:
            class_lines.append(f"    {interface} <|.. {cls.name}")
    for dependency in result.dependencies:
        if dependency.kind in {"field", "import"}:
            class_lines.append(f"    {dependency.source} --> {dependency.target}")
    class_path = output / "class_diagram.mmd"
    class_path.write_text("\n".join(class_lines), encoding="utf-8")
    mermaid["class"] = str(class_path)

    erd_lines = ["erDiagram"]
    for table in result.tables:
        for foreign_key in table.foreign_keys:
            if "->" not in foreign_key:
                continue
            _, target = foreign_key.split("->", 1)
            parent = target.split(".")[0]
            erd_lines.append(f"    {parent.upper()} ||--o{{ {table.name.upper()} : \"1:N\"")
        erd_lines.append(f"    {table.name.upper()} {{")
        for column in table.columns[:10]:
            key = "PK" if column.is_primary else ("FK" if column.is_foreign else "")
            erd_lines.append(f"        {column.type.replace(' ', '_')} {column.name} {key}".rstrip())
        erd_lines.append("    }")
    erd_path = output / "erd.mmd"
    erd_path.write_text("\n".join(erd_lines), encoding="utf-8")
    mermaid["erd"] = str(erd_path)

    dep_lines = ["flowchart LR"]
    for layer in result.layers:
        dep_lines.append(f'    {layer.key}["{layer.name}"]')
    for source in result.layers:
        for target in result.layers:
            count = sum(1 for d in result.dependencies if class_to_layer(result, d.source) == source.key and class_to_layer(result, d.target) == target.key)
            if count:
                dep_lines.append(f"    {source.key} -->|{count}| {target.key}")
    dep_path = output / "dependency.mmd"
    dep_path.write_text("\n".join(dep_lines), encoding="utf-8")
    mermaid["dependency"] = str(dep_path)

    seq_lines = [
        "sequenceDiagram",
        "    actor Client",
        "    participant Servlet",
        "    participant Service",
        "    participant DAO",
        "    participant DB as MySQL",
        "    Client->>Servlet: POST /loans",
        "    Servlet->>Service: borrowBook(bookId, readerId, userId)",
        "    Service->>DAO: findById(bookId)",
        "    DAO->>DB: SELECT ... FROM books",
        "    DB-->>DAO: book",
        "    Service->>DAO: findBorrowingByReader(readerId)",
        "    DAO->>DB: SELECT ... FROM loans",
        "    Service->>DAO: create(loan) + update(book)",
        "    DAO->>DB: INSERT / UPDATE",
        "    Service-->>Servlet: kết quả",
        "    Servlet-->>Client: thông báo",
    ]
    seq_path = output / "sequence.mmd"
    seq_path.write_text("\n".join(seq_lines), encoding="utf-8")
    mermaid["sequence"] = str(seq_path)
    return mermaid


def generate_all_diagrams(result: AnalysisResult, output: Path) -> dict[str, str]:
    output.mkdir(parents=True, exist_ok=True)
    paths = {
        "architecture": architecture_layers(result, output),
        "dependency": dependency_graph(result, output),
        "class": class_diagram(result, output),
        "erd": erd_diagram(result, output),
        "sequence": sequence_diagram(result, output),
        "quality": quality_dashboard(result, output),
    }
    mermaid = write_mermaid(result, output)
    for key, value in mermaid.items():
        paths[f"mermaid_{key}"] = value
    return paths
