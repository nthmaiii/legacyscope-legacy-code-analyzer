from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

plt.rcParams["font.family"] = "Arial"
BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "docs" / "assets"
OUT.mkdir(parents=True, exist_ok=True)
BG = "#F8FAFC"
INK = "#0F172A"
MUTED = "#64748B"
NAVY = "#0B1220"


def canvas(width, height):
    fig, ax = plt.subplots(figsize=(width, height), dpi=220)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, face, edge, radius=0.02, lw=1.2, z=2):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle=f"round,pad=0.008,rounding_size={radius}",
        facecolor=face, edgecolor=edge, linewidth=lw, zorder=z
    ))


def arrow(ax, start, end, color="#94A3B8", lw=1.6):
    ax.add_patch(FancyArrowPatch(
        start, end, arrowstyle="-|>", mutation_scale=15,
        linewidth=lw, color=color, zorder=1
    ))


def solution_architecture():
    fig, ax = canvas(13, 7.8)
    ax.text(0.04, 0.95, "Kiến trúc tổng thể của LegacyScope", fontsize=24, weight="bold", color=INK)
    ax.text(0.04, 0.905, "Mô hình bốn lớp: giao diện, API, lõi phân tích và sinh tài liệu", fontsize=10.5, color=MUTED)

    box(ax, 0.05, 0.79, 0.90, 0.085, "#0B1220", "#0B1220", radius=0.018)
    ax.text(0.09, 0.845, "Người dùng", fontsize=11, weight="bold", color="#7DD3FC")
    ax.text(0.09, 0.812, "Sinh viên / giảng viên / kỹ sư bảo trì", fontsize=9.5, color="#9FB2D0")
    ax.text(0.67, 0.845, "Đầu vào: ZIP mã nguồn hoặc bộ mẫu", fontsize=9.5, color="#C7D7EF")
    ax.text(0.67, 0.812, "Java · SQL · JSP · cấu trúc thư mục", fontsize=8.5, color="#7F96BD")

    layers = [
        (0.635, "Giao diện Web", "Dashboard kết quả · tab kiến trúc · tải tài liệu", "#DBEAFE", "#2563EB"),
        (0.495, "API ứng dụng", "FastAPI · phân tích đồng bộ · quản lý artifact", "#E0F2FE", "#0284C7"),
        (0.355, "Lõi phân tích", "Scanner · Java parser · SQL parser · Architecture analyzer", "#FEF3C7", "#D97706"),
        (0.215, "Sinh tài liệu", "Diagram generator · DOCX · Markdown · JSON · ZIP", "#D1FAE5", "#059669"),
    ]
    for y, title, desc, face, color in layers:
        box(ax, 0.08, y, 0.84, 0.10, "white", "#CBD5E1")
        box(ax, 0.08, y, 0.018, 0.10, color, color, radius=0.008, lw=0)
        ax.text(0.115, y + 0.064, title, fontsize=12, weight="bold", color=color)
        ax.text(0.115, y + 0.034, desc, fontsize=8.8, color=MUTED)
        if y > 0.25:
            arrow(ax, (0.5, y - 0.004), (0.5, y - 0.028), color="#94A3B8", lw=1.4)

    box(ax, 0.34, 0.045, 0.32, 0.075, "#0F172A", "#0F172A", radius=0.018)
    ax.text(0.5, 0.082, "Thư mục outputs/  ·  artifact + manifest JSON", fontsize=9.5, color="white", ha="center", weight="bold")
    arrow(ax, (0.5, 0.21), (0.5, 0.123), color="#059669", lw=1.8)
    fig.savefig(OUT / "solution_architecture.png", dpi=220, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def pipeline():
    fig, ax = canvas(15, 4.6)
    ax.text(0.03, 0.90, "Pipeline phân tích và sinh đặc tả", fontsize=22, weight="bold", color=INK)
    ax.text(0.03, 0.82, "Một luồng xử lý khép kín, không phụ thuộc dịch vụ bên ngoài", fontsize=10, color=MUTED)
    steps = [
        ("01", "Chọn nguồn", "ZIP hoặc mẫu", "#DBEAFE", "#2563EB"),
        ("02", "Quét dự án", "File · LOC\nngôn ngữ", "#E0F2FE", "#0284C7"),
        ("03", "Phân tích Java", "Lớp · hàm\nannotation", "#FEF3C7", "#D97706"),
        ("04", "Phân tích SQL", "Bảng · PK\nFK", "#FCE7F3", "#DB2777"),
        ("05", "Kiến trúc", "Tầng · phụ thuộc\nrủi ro", "#EDE9FE", "#7C3AED"),
        ("06", "Sinh sơ đồ", "6 hình PNG\n+ Mermaid", "#D1FAE5", "#059669"),
        ("07", "Sinh đặc tả", "DOCX · MD\nJSON · ZIP", "#E2E8F0", "#475569"),
    ]
    n = len(steps)
    width = 0.115
    gap = (0.94 - n * width) / (n - 1)
    y = 0.38
    for index, (num, title, desc, face, color) in enumerate(steps):
        x = 0.03 + index * (width + gap)
        box(ax, x, y, width, 0.31, face, color, lw=1.0)
        ax.text(x + 0.014, y + 0.262, num, fontsize=8.8, weight="bold", color=color)
        ax.text(x + 0.014, y + 0.205, title, fontsize=8.8, weight="bold", color=INK)
        ax.text(x + 0.014, y + 0.145, desc, fontsize=7.2, color=MUTED, linespacing=1.45, va="top")
        if index < n - 1:
            arrow(ax, (x + width + 0.006, y + 0.155), (x + width + gap - 0.006, y + 0.155), color="#94A3B8", lw=1.4)
    ax.text(0.03, 0.16, "Đầu vào", fontsize=8.5, color=MUTED)
    ax.text(0.78, 0.16, "Đầu ra", fontsize=8.5, color=MUTED)
    fig.savefig(OUT / "pipeline.png", dpi=220, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


if __name__ == "__main__":
    solution_architecture()
    pipeline()
    print("figures built")
