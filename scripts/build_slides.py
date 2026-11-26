from __future__ import annotations

import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

ASSETS = BASE / "docs" / "assets"
OUT = BASE / "docs" / "Slide_Trinh_bay.pptx"
CONFIG_PATH = BASE / "config" / "student.json"
if not CONFIG_PATH.exists():
    CONFIG_PATH = CONFIG_PATH.with_name("student.example.json")
CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

NAVY = RGBColor(0x0B, 0x12, 0x20)
NAVY2 = RGBColor(0x11, 0x1C, 0x33)
BLUE = RGBColor(0x25, 0x63, 0xEB)
CYAN = RGBColor(0x06, 0xB6, 0xD4)
BG = RGBColor(0xF3, 0xF6, 0xFB)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
INK = RGBColor(0x0F, 0x17, 0x2A)
MUTED = RGBColor(0x64, 0x74, 0x8B)
GREEN = RGBColor(0x10, 0xB9, 0x81)
AMBER = RGBColor(0xF5, 0x9E, 0x0B)
RED = RGBColor(0xDC, 0x26, 0x26)
LINE = RGBColor(0xE2, 0xE8, 0xF0)
SOFT = RGBColor(0xF8, 0xFA, 0xFC)
SOFT_BLUE = RGBColor(0xDB, 0xEA, 0xFE)

FONT = "Segoe UI"
MONO = "Consolas"


def rgb(hex_value):
    value = hex_value.lstrip("#")
    return RGBColor(int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def add_rect(slide, x, y, w, h, fill=None, line=None, radius=0.08, shape=MSO_SHAPE.ROUNDED_RECTANGLE, line_width=1):
    box = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            box.adjustments[0] = radius
        except Exception:
            pass
    if fill is None:
        box.fill.background()
    else:
        box.fill.solid()
        box.fill.fore_color.rgb = fill
    if line is None:
        box.line.fill.background()
    else:
        box.line.color.rgb = line
        box.line.width = Pt(line_width)
    box.shadow.inherit = False
    return box


def add_text(slide, text, x, y, w, h, size=18, color=INK, bold=False, align=PP_ALIGN.LEFT,
             font=FONT, anchor=MSO_ANCHOR.TOP, line_spacing=1.05, italic=False, margins=(0, 0, 0, 0)):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left, tf.margin_right, tf.margin_top, tf.margin_bottom = [Inches(v) for v in margins]
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = line_spacing
    run = p.add_run()
    run.text = text
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return box


def add_runs(slide, runs, x, y, w, h, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, line_spacing=1.05, margins=(0, 0, 0, 0)):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left, tf.margin_right, tf.margin_top, tf.margin_bottom = [Inches(v) for v in margins]
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = line_spacing
    for text, size, color, bold, font in runs:
        run = p.add_run()
        run.text = text
        run.font.name = font
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = color
    return box


def add_bg(slide, color=BG):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_footer(slide, number, dark=False):
    color = RGBColor(0x7F, 0x96, 0xBD) if dark else MUTED
    add_text(slide, "LegacyScope  ·  Chuyên đề Kỹ thuật phần mềm", 0.55, 7.12, 6.0, 0.24, 8.5, color, font="Arial")
    add_text(slide, f"{number:02d}", 12.2, 7.1, 0.55, 0.25, 9, color, bold=True, align=PP_ALIGN.RIGHT, font="Arial")


def add_slide_header(slide, kicker, title, subtitle=None, dark=False, number=None):
    title_color = WHITE if dark else NAVY
    kicker_color = CYAN if dark else BLUE
    sub_color = RGBColor(0xA9, 0xBA, 0xD7) if dark else MUTED
    add_text(slide, kicker.upper(), 0.62, 0.42, 9.0, 0.25, 9.5, kicker_color, bold=True, font="Arial")
    add_text(slide, title, 0.6, 0.72, 11.8, 0.8, 28, title_color, bold=True, font="Arial")
    if subtitle:
        add_text(slide, subtitle, 0.62, 1.45, 11.4, 0.45, 12, sub_color, font=FONT)
    if number is not None:
        add_footer(slide, number, dark)


def add_bullet(slide, text, x, y, w, h=0.45, size=13, color=INK, dot_color=BLUE):
    dot = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y + 0.12), Inches(0.07), Inches(0.07))
    dot.fill.solid()
    dot.fill.fore_color.rgb = dot_color
    dot.line.fill.background()
    add_text(slide, text, x + 0.18, y, w - 0.18, h, size, color, font=FONT)


def stat_card(slide, x, y, w, h, value, label, color=BLUE, dark=False):
    fill = WHITE if not dark else NAVY2
    line = LINE if not dark else RGBColor(0x25, 0x3B, 0x5C)
    add_rect(slide, x, y, w, h, fill, line, radius=0.1)
    add_text(slide, value, x + 0.18, y + 0.14, w - 0.3, 0.5, 25, color, bold=True, font="Arial")
    add_text(slide, label, x + 0.18, y + 0.68, w - 0.3, 0.3, 8.5, MUTED, font=FONT)


def add_image(slide, filename, x, y, w, h=None):
    path = ASSETS / filename
    if not path.exists():
        return
    if h is None:
        slide.shapes.add_picture(str(path), Inches(x), Inches(y), width=Inches(w))
    else:
        slide.shapes.add_picture(str(path), Inches(x), Inches(y), width=Inches(w), height=Inches(h))


def slide_title(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, NAVY)
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.gradient()
    bg.fill.gradient_angle = 135
    stops = bg.fill.gradient_stops
    stops[0].color.rgb = rgb("0B1220")
    stops[0].position = 0.0
    stops[1].color.rgb = rgb("142A50")
    stops[1].position = 1.0
    bg.line.fill.background()
    bg.shadow.inherit = False

    for x, y, diameter, color in [(10.4, -1.8, 5.6, "1E3A8A"), (11.8, 3.2, 3.4, "0E7490")]:
        ring = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(diameter), Inches(diameter))
        ring.fill.background()
        ring.line.color.rgb = rgb(color)
        ring.line.width = Pt(1)
        ring.shadow.inherit = False

    add_rect(slide, 0.75, 0.7, 0.62, 0.62, rgb("2563EB"), rgb("3B82F6"), radius=0.18)
    add_text(slide, "LS", 0.75, 0.82, 0.62, 0.28, 15, WHITE, bold=True, align=PP_ALIGN.CENTER, font="Arial")
    add_text(slide, "LEGACYSCOPE", 1.55, 0.82, 3.0, 0.28, 15, WHITE, bold=True, font="Arial")
    add_text(slide, "CODE ARCHAEOLOGY", 1.56, 1.11, 3.0, 0.2, 7.5, RGBColor(0x7D, 0xD3, 0xFC), bold=True, font="Arial")

    add_text(slide, "CHUYÊN ĐỀ KỸ THUẬT PHẦN MỀM  ·  2026", 0.78, 2.12, 8.0, 0.25, 9.5, CYAN, bold=True, font="Arial")
    add_text(slide, "Tự động hóa trích xuất", 0.75, 2.55, 10.5, 0.8, 40, WHITE, bold=True, font="Arial")
    add_text(slide, "đặc tả kỹ thuật & sơ đồ kiến trúc", 0.75, 3.27, 11.0, 0.8, 36, rgb("67E8F9"), bold=True, font="Arial")
    add_text(slide, "từ mã nguồn cũ", 0.75, 4.02, 8.0, 0.6, 36, WHITE, bold=True, font="Arial")
    add_text(slide, "Nghiên cứu và phát triển giải pháp tự động phục hồi cấu trúc, kiến trúc và tài liệu kỹ thuật cho hệ thống Java/SQL legacy.",
             0.78, 4.85, 8.4, 0.75, 11.5, RGBColor(0xA9, 0xBA, 0xD7), font=FONT)

    add_text(slide, "Sinh viên thực hiện", 0.78, 6.05, 2.2, 0.25, 8.5, RGBColor(0x7F, 0x96, 0xBD), bold=True, font="Arial")
    add_text(slide, CONFIG["student_name"], 0.78, 6.32, 4.8, 0.3, 11.5, WHITE, bold=True, font=FONT)
    add_text(slide, f"{CONFIG['class_name']}  ·  {CONFIG['student_id']}", 0.78, 6.64, 5.2, 0.25, 9.5, RGBColor(0xA9, 0xBA, 0xD7), font=FONT)
    add_text(slide, f"GVHD: {CONFIG['advisor']}", 0.78, 6.94, 5.0, 0.25, 9.5, RGBColor(0xA9, 0xBA, 0xD7), font=FONT)

    for index, label in enumerate(["Java", "SQL", "DOCX", "Mermaid"]):
        add_rect(slide, 9.25 + index * 0.77, 5.7, 0.68, 0.3, None, RGBColor(0x3B, 0x5C, 0x8A), radius=0.25)
        add_text(slide, label, 9.25 + index * 0.77, 5.76, 0.68, 0.18, 7.8, RGBColor(0xA9, 0xBA, 0xD7), align=PP_ALIGN.CENTER, font="Arial")

    slide.notes_slide.notes_text_frame.text = (
        "Kính chào cô và các bạn. Em là " + CONFIG["student_name"] + ", lớp " + CONFIG["class_name"] + ". "
        "Đề tài của em là nghiên cứu và phát triển giải pháp tự động hóa trích xuất đặc tả kỹ thuật và sơ đồ kiến trúc từ mã nguồn cũ. "
        "Sản phẩm thực nghiệm là LegacyScope, một công cụ web chạy cục bộ, phân tích Java và SQL, sinh sơ đồ và tài liệu kỹ thuật."
    )


def slide_problem(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide)
    add_slide_header(slide, "01 · Vấn đề", "Mã nguồn còn đó, nhưng hiểu biết đã mất.", "Tài liệu thất lạc – con người thay đổi – hệ thống vẫn phải vận hành.", number=2)
    cards = [
        ("01", "Tài liệu thất lạc", "Thiết kế, API, quy tắc nghiệp vụ không còn đồng bộ với mã đang chạy.", BLUE),
        ("02", "Chi phí đọc hiểu", "Kỹ sư phải dựng lại kiến trúc trong đầu trước khi sửa một chức năng nhỏ.", AMBER),
        ("03", "Rủi ro thay đổi", "Thiếu kiểm thử, phụ thuộc chặt, SQL nối chuỗi và cấu hình hard-code.", RED),
    ]
    for index, (num, title, desc, color) in enumerate(cards):
        x = 0.62 + index * 4.23
        add_rect(slide, x, 2.05, 3.9, 2.55, WHITE, LINE, radius=0.08)
        add_rect(slide, x + 0.25, 2.28, 0.5, 0.5, color, color, radius=0.16)
        add_text(slide, num, x + 0.25, 2.4, 0.5, 0.2, 10.5, WHITE, bold=True, align=PP_ALIGN.CENTER, font="Arial")
        add_text(slide, title, x + 0.25, 3.0, 3.3, 0.35, 16, NAVY, bold=True, font="Arial")
        add_text(slide, desc, x + 0.25, 3.45, 3.35, 0.9, 10.5, MUTED, font=FONT)
    add_rect(slide, 0.62, 5.0, 12.1, 0.95, NAVY, NAVY, radius=0.12)
    add_text(slide, "Cần một lớp công cụ phục hồi cấu trúc trước khi bảo trì, tái cấu trúc hoặc chuyển đổi hệ thống.",
             0.95, 5.28, 11.4, 0.35, 13, WHITE, bold=True, font=FONT)
    add_text(slide, "Không thay thế chuyên gia – rút ngắn thời gian đọc hiểu và tạo tài liệu có thể kiểm chứng.",
             0.95, 5.64, 11.4, 0.25, 9.5, RGBColor(0x9F, 0xB2, 0xD0), font=FONT)
    slide.notes_slide.notes_text_frame.text = (
        "Vấn đề không phải là hệ thống cũ về tuổi đời, mà là mất khả năng thay đổi an toàn. "
        "Khi tài liệu không còn, kỹ sư phải đọc hàng nghìn dòng mã để trả lời bốn câu hỏi: lớp nào xử lý, dữ liệu đi đâu, API nào gọi vào, thay đổi này ảnh hưởng gì. "
        "Đó là chi phí rất lớn và là nguồn gốc của rủi ro hồi quy."
    )


def slide_objectives(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide)
    add_slide_header(slide, "02 · Mục tiêu", "Nghiên cứu để hiểu, phát triển để dùng được.", number=3)
    items = [
        ("Nghiên cứu", "Hệ thống hóa mã nguồn cũ, reverse engineering, phân tích tĩnh và phục hồi kiến trúc.", BLUE),
        ("Kỹ thuật", "Xây dựng LegacyScope: quét Java/SQL, trích xuất cấu trúc, sinh 6 sơ đồ và đặc tả.", AMBER),
        ("Đánh giá", "Kiểm chứng trên hệ thống thư viện legacy, đo độ chính xác, thời gian và hạn chế.", GREEN),
    ]
    for index, (title, desc, color) in enumerate(items):
        y = 1.9 + index * 1.4
        add_rect(slide, 0.62, y, 7.0, 1.12, WHITE, LINE, radius=0.1)
        add_rect(slide, 0.62, y, 0.08, 1.12, color, color, radius=0.0)
        add_text(slide, title, 0.92, y + 0.18, 1.6, 0.3, 13, color, bold=True, font="Arial")
        add_text(slide, desc, 2.35, y + 0.16, 4.95, 0.72, 10.3, MUTED, font=FONT)
    add_rect(slide, 8.0, 1.9, 4.7, 4.55, NAVY, NAVY, radius=0.08)
    add_text(slide, "PHẠM VI", 8.32, 2.18, 2.0, 0.25, 9, CYAN, bold=True, font="Arial")
    add_text(slide, "Trong phạm vi", 8.32, 2.55, 3.9, 0.3, 12, WHITE, bold=True, font="Arial")
    for i, text in enumerate(["Java Servlet/JDBC + SQL", "Cấu trúc lớp, API, bảng, phụ thuộc", "6 sơ đồ + DOCX/MD/JSON"]):
        add_bullet(slide, text, 8.32, 2.95 + i * 0.33, 3.95, 0.3, 9.8, RGBColor(0xC7, 0xD7, 0xEF), CYAN)
    add_text(slide, "Ngoài phạm vi", 8.32, 4.3, 3.9, 0.3, 12, WHITE, bold=True, font="Arial")
    for i, text in enumerate(["Chạy thử runtime, kiểm thử xâm nhập", "Đa ngôn ngữ, ORM phức tạp", "Đảm bảo ngữ nghĩa nghiệp vụ 100%"]):
        add_bullet(slide, text, 8.32, 4.7 + i * 0.33, 3.95, 0.3, 9.8, RGBColor(0xA9, 0xBA, 0xD7), RGBColor(0x64, 0x74, 0x8B))
    slide.notes_slide.notes_text_frame.text = (
        "Mục tiêu của em chia làm ba tầng: nghiên cứu để có khung lý thuyết, phát triển để có sản phẩm chạy được, và đánh giá để biết sản phẩm đúng đến đâu. "
        "Phạm vi tập trung Java và SQL vì đây là công nghệ phổ biến trong hệ thống legacy, đồng thời đủ sâu để chứng minh pipeline."
    )


def slide_gap(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide)
    add_slide_header(slide, "03 · Cơ sở lý thuyết", "Từ reverse engineering đến một khoảng trống thực tế.", number=4)
    theories = [
        ("Reverse engineering", "Tái tạo biểu diễn trừu tượng từ mã nguồn.", BLUE),
        ("Static analysis", "Đọc cấu trúc mà không cần chạy chương trình.", CYAN),
        ("Architecture recovery", "Phục hồi thành phần, tầng và quan hệ.", AMBER),
        ("Spec generation", "Chuyển mô hình thành tài liệu có thể đọc.", GREEN),
    ]
    for index, (title, desc, color) in enumerate(theories):
        x = 0.62 + (index % 2) * 3.0
        y = 1.85 + (index // 2) * 1.5
        add_rect(slide, x, y, 2.8, 1.25, WHITE, LINE, radius=0.1)
        add_text(slide, title, x + 0.18, y + 0.18, 2.4, 0.28, 10.5, color, bold=True, font="Arial")
        add_text(slide, desc, x + 0.18, y + 0.55, 2.45, 0.55, 8.5, MUTED, font=FONT)
    add_rect(slide, 6.95, 1.85, 5.75, 4.55, NAVY, NAVY, radius=0.08)
    add_text(slide, "KHOẢNG TRỐNG", 7.25, 2.15, 3.0, 0.25, 9, CYAN, bold=True, font="Arial")
    gaps = [
        ("Công cụ thương mại", "Mạnh nhưng đắt, quy trình nặng, khó tùy biến mẫu báo cáo."),
        ("Thư viện parser", "JavaParser/Spoon mạnh nhưng chỉ là hạ tầng, phải tự viết toàn bộ logic."),
        ("Tài liệu tự động", "Doxygen phụ thuộc comment; thiếu sơ đồ kiến trúc và đặc tả tiếng Việt."),
    ]
    for index, (title, desc) in enumerate(gaps):
        y = 2.62 + index * 1.0
        add_text(slide, f"0{index + 1}", 7.25, y, 0.3, 0.25, 10, CYAN, bold=True, font="Arial")
        add_text(slide, title, 7.62, y - 0.02, 2.1, 0.28, 10.8, WHITE, bold=True, font="Arial")
        add_text(slide, desc, 9.2, y - 0.02, 3.15, 0.7, 8.8, RGBColor(0xA9, 0xBA, 0xD7), font=FONT)
    add_text(slide, "LegacyScope chọn điểm cân bằng: nhẹ – offline – giải thích được – sinh tài liệu ngay.",
             7.25, 5.72, 5.0, 0.3, 9.2, RGBColor(0x67, 0xE8, 0xF9), bold=True, font=FONT)
    slide.notes_slide.notes_text_frame.text = (
        "Về lý thuyết, bài toán đã có nền tảng: reverse engineering, phân tích tĩnh, phục hồi kiến trúc và sinh đặc tả. "
        "Nhưng công cụ thương mại thì đắt, thư viện parser thì chỉ là hạ tầng, còn công cụ tài liệu thì thường phụ thuộc comment. "
        "LegacyScope chọn điểm cân bằng cho bối cảnh sinh viên và đội bảo trì nhỏ."
    )


def slide_solution(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide)
    add_slide_header(slide, "04 · Giải pháp", "LegacyScope – một pipeline, bốn năng lực.", number=5)
    items = [
        ("SCAN", "Quét dự án", "File, ngôn ngữ, LOC, comment, TODO/FIXME.", BLUE),
        ("EXTRACT", "Trích xuất cấu trúc", "Lớp, hàm, annotation, endpoint, bảng, khóa ngoại.", CYAN),
        ("ANALYZE", "Phân tích kiến trúc", "Tầng, phụ thuộc, chu trình, quy tắc, rủi ro.", AMBER),
        ("GENERATE", "Sinh tài liệu", "6 sơ đồ, DOCX, Markdown, JSON, ZIP.", GREEN),
    ]
    for index, (tag, title, desc, color) in enumerate(items):
        x = 0.62 + index * 3.13
        add_rect(slide, x, 1.85, 2.88, 2.6, WHITE, LINE, radius=0.1)
        add_text(slide, tag, x + 0.2, 2.05, 2.4, 0.2, 8, color, bold=True, font="Arial")
        add_text(slide, title, x + 0.2, 2.42, 2.45, 0.32, 13.5, NAVY, bold=True, font="Arial")
        add_text(slide, desc, x + 0.2, 2.86, 2.45, 0.75, 9.4, MUTED, font=FONT)
        add_rect(slide, x + 0.2, 3.75, 2.25, 0.06, color, color, radius=0.5)
    add_rect(slide, 0.62, 4.9, 12.1, 1.05, NAVY, NAVY, radius=0.12)
    add_text(slide, "Offline  ·  Java + SQL  ·  6 sơ đồ  ·  DOCX / Markdown / JSON", 0.95, 5.2, 11.2, 0.28, 13, WHITE, bold=True, font=FONT)
    add_text(slide, "Không API key, không gửi mã nguồn ra ngoài, kết quả có thể truy vết về tệp và dòng.",
             0.95, 5.56, 11.2, 0.22, 9.2, RGBColor(0x9F, 0xB2, 0xD0), font=FONT)
    slide.notes_slide.notes_text_frame.text = (
        "LegacyScope có bốn năng lực chính: quét, trích xuất, phân tích và sinh tài liệu. "
        "Điểm quan trọng là toàn bộ pipeline chạy cục bộ, không cần API key, không gửi mã nguồn ra ngoài. "
        "Kết quả không phải hộp đen: mỗi phát hiện đều có tệp, dòng và quy tắc."
    )


def slide_architecture(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide)
    add_slide_header(slide, "05 · Kiến trúc", "Bốn lớp tách biệt, một luồng dữ liệu.", number=6)
    add_image(slide, "solution_architecture.png", 0.68, 1.55, 8.15)
    add_rect(slide, 9.05, 1.6, 3.65, 4.9, WHITE, LINE, radius=0.08)
    add_text(slide, "VÌ SAO TÁCH LỚP?", 9.32, 1.9, 3.0, 0.25, 8.5, BLUE, bold=True, font="Arial")
    reasons = [
        ("Độc lập", "Lõi phân tích không phụ thuộc giao diện; có thể chạy CLI."),
        ("Mở rộng", "Thêm parser hoặc generator mới mà không sửa pipeline."),
        ("Kiểm thử", "Từng module có đầu vào/đầu ra rõ ràng."),
        ("Giải thích", "Mỗi tầng tạo artifact trung gian có thể kiểm tra."),
    ]
    for index, (title, desc) in enumerate(reasons):
        y = 2.35 + index * 0.95
        add_text(slide, title, 9.32, y, 1.2, 0.25, 10, NAVY, bold=True, font="Arial")
        add_text(slide, desc, 10.5, y - 0.02, 1.95, 0.62, 8.4, MUTED, font=FONT)
    slide.notes_slide.notes_text_frame.text = (
        "Kiến trúc gồm bốn lớp: giao diện web, API FastAPI, lõi phân tích và sinh tài liệu. "
        "Việc tách lớp giúp lõi có thể chạy độc lập, dễ kiểm thử và dễ mở rộng. "
        "Đây cũng là cách em áp dụng nguyên tắc trách nhiệm đơn lẻ vào chính công cụ."
    )


def slide_pipeline(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide)
    add_slide_header(slide, "06 · Pipeline", "Bảy bước từ mã nguồn đến tài liệu.", number=7)
    add_image(slide, "pipeline.png", 0.62, 1.65, 12.1)
    outcomes = [
        ("~3 giây", "pipeline mẫu"),
        ("6 sơ đồ", "PNG + Mermaid"),
        ("4 định dạng", "DOCX · MD · JSON · ZIP"),
    ]
    for index, (value, label) in enumerate(outcomes):
        x = 0.62 + index * 4.12
        add_rect(slide, x, 5.65, 3.8, 0.92, WHITE, LINE, radius=0.1)
        add_text(slide, value, x + 0.18, 5.78, 1.65, 0.38, 18, BLUE, bold=True, font="Arial")
        add_text(slide, label, x + 1.78, 5.86, 1.85, 0.25, 9, MUTED, font=FONT)
    slide.notes_slide.notes_text_frame.text = (
        "Pipeline gồm bảy bước: chọn nguồn, quét, phân tích Java, phân tích SQL, phân tích kiến trúc, sinh sơ đồ và sinh đặc tả. "
        "Mỗi bước tạo đầu ra trung gian nên dễ kiểm tra. Trên máy thử nghiệm, pipeline mẫu chạy khoảng 3 giây."
    )


def slide_extraction(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide)
    add_slide_header(slide, "07 · Kỹ thuật", "Lai parser nhẹ và regex để chịu được mã cũ.", number=8)
    add_rect(slide, 0.62, 1.7, 7.0, 4.9, NAVY, NAVY, radius=0.08)
    add_text(slide, "JAVA STRUCTURE EXTRACTION", 0.92, 1.98, 4.0, 0.25, 8.5, CYAN, bold=True, font="Arial")
    code = (
        "mask_comments_and_strings(text)\n"
        "package = find_package(masked)\n"
        "for class in CLASS_PATTERN.finditer(masked):\n"
        "    open  = class.end() - 1\n"
        "    close = matching_brace(masked, open)\n"
        "    parse_members(body_masked, body_raw)\n"
        "    find_endpoints(annotations, methods)\n"
        "\n"
        "# Ví dụ endpoint\n"
        "@WebServlet(\"/loans\")\n"
        "doGet()  -> GET  /loans\n"
        "doPost() -> POST /loans"
    )
    add_text(slide, code, 0.92, 2.42, 6.35, 3.85, 11, RGBColor(0xD7, 0xE3, 0xF4), font=MONO, line_spacing=1.15)
    add_rect(slide, 7.92, 1.7, 4.8, 4.9, WHITE, LINE, radius=0.08)
    features = [
        ("Lớp & annotation", "Package, extends, implements, field, method, Javadoc."),
        ("API", "Servlet @WebServlet và Spring MVC mapping."),
        ("Dữ liệu", "CREATE TABLE, cột, PK, FK, tham chiếu trong SQL."),
        ("Quy tắc", "Điều kiện if + thông báo trả về, ràng buộc FK."),
        ("Rủi ro", "SQL nối chuỗi, hard-code, JSP scriptlet, TODO."),
    ]
    for index, (title, desc) in enumerate(features):
        y = 2.08 + index * 0.78
        add_text(slide, title, 8.2, y, 1.45, 0.25, 9.6, BLUE, bold=True, font="Arial")
        add_text(slide, desc, 9.62, y - 0.02, 2.78, 0.55, 8.5, MUTED, font=FONT)
    slide.notes_slide.notes_text_frame.text = (
        "Điểm kỹ thuật chính là không yêu cầu dự án biên dịch được. Em che comment và chuỗi, dùng dấu ngoặc cân bằng để tách lớp và thành viên, "
        "sau đó dùng regex để nhận diện annotation, endpoint và SQL. Cách này chịu được mã cũ nhưng vẫn cho kết quả giải thích được."
    )


def slide_demo_home(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide)
    add_slide_header(slide, "08 · Demo", "Từ ZIP đến dashboard trong một màn hình.", number=9)
    add_rect(slide, 0.62, 1.65, 8.25, 5.15, WHITE, LINE, radius=0.06)
    add_image(slide, "ui_home.png", 1.35, 1.8, 6.6, 5.0)
    steps = [
        ("01", "Chọn nguồn", "Mẫu thư viện hoặc ZIP Java/SQL."),
        ("02", "Chạy phân tích", "Tiến trình 5 bước, phản hồi trực quan."),
        ("03", "Nhận kết quả", "Dashboard, sơ đồ, tài liệu tải về."),
    ]
    for index, (num, title, desc) in enumerate(steps):
        y = 1.85 + index * 1.45
        add_text(slide, num, 9.2, y, 0.4, 0.25, 10, BLUE, bold=True, font="Arial")
        add_text(slide, title, 9.65, y - 0.02, 2.9, 0.28, 12, NAVY, bold=True, font="Arial")
        add_text(slide, desc, 9.65, y + 0.3, 3.0, 0.55, 8.8, MUTED, font=FONT)
    add_text(slide, "Thao tác chính trong 3 bước, không cần đăng nhập.", 9.2, 6.0, 3.4, 0.3, 9, GREEN, bold=True, font=FONT)
    slide.notes_slide.notes_text_frame.text = (
        "Đây là giao diện trang chủ. Người dùng có thể chọn mẫu hoặc kéo thả ZIP. "
        "Mọi thao tác chính nằm trong ba bước: chọn nguồn, chạy phân tích và nhận kết quả. "
        "Giao diện chạy offline, không cần đăng nhập."
    )


def slide_results(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide)
    add_slide_header(slide, "09 · Kết quả", "Hệ thống thư viện: 19 lớp, 10 API, 5 bảng.", number=10)
    add_rect(slide, 0.62, 1.62, 8.05, 5.18, WHITE, LINE, radius=0.06)
    add_image(slide, "ui_result.png", 1.62, 1.78, 6.0, 5.0)
    stats = [
        ("75/100", "Chỉ số rủi ro", AMBER),
        ("8", "Vấn đề phát hiện", RED),
        ("28", "Quy tắc ứng viên", GREEN),
        ("5", "Tầng kiến trúc", BLUE),
    ]
    for index, (value, label, color) in enumerate(stats):
        y = 1.8 + index * 1.22
        add_rect(slide, 9.0, y, 3.7, 1.0, WHITE, LINE, radius=0.12)
        add_text(slide, value, 9.2, y + 0.14, 1.5, 0.38, 18, color, bold=True, font="Arial")
        add_text(slide, label, 9.2, y + 0.55, 3.25, 0.25, 8.5, MUTED, font=FONT)
    add_text(slide, "Điểm rủi ro ưu tiên bảo mật, thiếu kiểm thử và phương thức dài.", 9.0, 6.8, 3.8, 0.3, 7.8, MUTED, font=FONT)
    slide.notes_slide.notes_text_frame.text = (
        "Kết quả trên bộ mẫu: 19 lớp, 163 phương thức, 10 endpoint, 5 bảng. "
        "Chỉ số rủi ro 75/100, xếp mức rủi ro cao. Ba vấn đề mức cao là SQL nối chuỗi, mật khẩu hard-code và thiếu kiểm thử. "
        "Các thẻ số liệu giúp người đọc nắm nhanh quy mô hệ thống."
    )


def slide_recovered_arch(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide)
    add_slide_header(slide, "10 · Kiến trúc phục hồi", "Nhìn thấy luồng Servlet → Service → DAO → Model.", number=11)
    add_rect(slide, 0.62, 1.6, 8.6, 5.2, WHITE, LINE, radius=0.06)
    add_image(slide, "demo_architecture.png", 1.02, 1.8, 7.8, 4.9)
    facts = [
        ("5", "tầng chính"),
        ("19", "lớp"),
        ("4", "lớp DAO"),
        ("0", "chu trình"),
    ]
    for index, (value, label) in enumerate(facts):
        x = 9.55 + (index % 2) * 1.85
        y = 1.8 + (index // 2) * 1.4
        add_rect(slide, x, y, 1.65, 1.15, NAVY, NAVY, radius=0.12)
        add_text(slide, value, x + 0.12, y + 0.18, 1.4, 0.4, 22, CYAN if index == 0 else WHITE, bold=True, font="Arial")
        add_text(slide, label, x + 0.12, y + 0.68, 1.4, 0.25, 8.2, RGBColor(0xA9, 0xBA, 0xD7), font=FONT)
    add_text(slide, "Hướng phụ thuộc chủ yếu từ trên xuống, phù hợp mô hình phân tầng.", 9.55, 4.85, 3.3, 0.45, 8.8, MUTED, font=FONT)
    add_text(slide, "Không phát hiện chu trình giữa các lớp.", 9.55, 5.45, 3.3, 0.3, 9, GREEN, bold=True, font=FONT)
    slide.notes_slide.notes_text_frame.text = (
        "Sơ đồ kiến trúc phục hồi cho thấy hệ thống mẫu đi theo mô hình bốn tầng: Servlet, Service, DAO và Model. "
        "Hướng phụ thuộc chủ yếu từ trên xuống, không có chu trình. "
        "Đây là kết quả khớp với thiết kế kỳ vọng và là ví dụ về góc nhìn component."
    )


def slide_class_data(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide)
    add_slide_header(slide, "11 · Lớp & dữ liệu", "Cấu trúc lớp và mô hình dữ liệu được phục hồi.", number=12)
    add_rect(slide, 0.6, 1.62, 6.1, 4.85, WHITE, LINE, radius=0.06)
    add_image(slide, "demo_class.png", 0.74, 1.78, 5.82, 2.94)
    add_text(slide, "Hình 1. Sơ đồ lớp rút gọn", 0.8, 4.82, 3.0, 0.25, 8.5, MUTED, italic=True, font="Arial")
    add_bullet(slide, "19 lớp · 29 phụ thuộc", 0.82, 5.18, 5.1, 0.3, 9.5, INK, BLUE)
    add_bullet(slide, "Hướng phụ thuộc chủ yếu từ trên xuống", 0.82, 5.55, 5.1, 0.3, 9.5, INK, BLUE)
    add_bullet(slide, "Không phát hiện chu trình", 0.82, 5.92, 5.1, 0.3, 9.5, INK, GREEN)
    add_rect(slide, 6.9, 1.62, 5.85, 4.85, WHITE, LINE, radius=0.06)
    add_image(slide, "demo_erd.png", 7.05, 1.82, 5.55, 3.33)
    add_text(slide, "Hình 2. ERD từ schema SQL", 7.1, 5.2, 3.0, 0.25, 8.5, MUTED, italic=True, font="Arial")
    add_bullet(slide, "5 bảng · 4 khóa ngoại", 7.1, 5.55, 5.1, 0.3, 9.5, INK, GREEN)
    add_bullet(slide, "books ↔ loans ↔ readers / users", 7.1, 5.92, 5.1, 0.3, 9.5, INK, GREEN)
    add_text(slide, "19 lớp · 29 phụ thuộc · 5 bảng · 4 khóa ngoại", 0.8, 6.55, 10.0, 0.3, 10, NAVY, bold=True, font="Arial")
    slide.notes_slide.notes_text_frame.text = (
        "Bên trái là sơ đồ lớp rút gọn, bên phải là ERD. "
        "Các lớp Servlet kế thừa HttpServlet, DAO phụ thuộc DBUtil, Service phụ thuộc DAO và model. "
        "ERD phục hồi đúng bốn quan hệ khóa ngoại giữa books, loans, readers, users và categories."
    )


def slide_flow_quality(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide)
    add_slide_header(slide, "12 · Hành vi & chất lượng", "Một luồng API và các chỉ báo nợ kỹ thuật.", number=13)
    add_rect(slide, 0.6, 1.62, 6.1, 4.75, WHITE, LINE, radius=0.06)
    add_image(slide, "demo_sequence.png", 0.74, 1.8, 5.82, 3.48)
    add_text(slide, "Luồng mượn sách", 0.8, 5.34, 3.0, 0.25, 8.5, MUTED, italic=True, font="Arial")
    add_bullet(slide, "POST /loans → Servlet → Service → DAO", 0.82, 5.66, 5.4, 0.3, 8.8, INK, BLUE)
    add_bullet(slide, "Kiểm tra sách, bạn đọc, hạn mức, hạn trả", 0.82, 6.0, 5.4, 0.3, 8.8, INK, BLUE)
    add_rect(slide, 6.9, 1.62, 5.85, 4.75, WHITE, LINE, radius=0.06)
    add_image(slide, "demo_quality.png", 7.05, 1.8, 5.55, 3.42)
    add_text(slide, "Dashboard chất lượng", 7.1, 5.3, 3.0, 0.25, 8.5, MUTED, italic=True, font="Arial")
    add_bullet(slide, "3 vấn đề mức cao · 3 mức trung bình", 7.1, 5.62, 5.2, 0.3, 8.8, INK, AMBER)
    add_bullet(slide, "Điểm rủi ro 75/100", 7.1, 5.96, 5.2, 0.3, 8.8, RED, RED)
    add_text(slide, "SQL nối chuỗi  ·  hard-code  ·  JSP scriptlet  ·  thiếu kiểm thử", 0.8, 6.5, 11.8, 0.3, 9.5, RED, bold=True, font=FONT)
    slide.notes_slide.notes_text_frame.text = (
        "Sơ đồ tuần tự minh họa luồng POST /loans đi qua Servlet, Service, DAO và MySQL. "
        "Dashboard chất lượng cho thấy tầng DAO nhiều dòng nhất, vấn đề mức cao là SQL nối chuỗi, hard-code và thiếu kiểm thử. "
        "Đây là các ưu tiên bảo trì rõ ràng."
    )


def slide_evaluation(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide)
    add_slide_header(slide, "13 · Đánh giá", "Đúng cấu trúc, nhanh, nhưng còn giới hạn.", number=14)
    stats = [
        ("19/19", "lớp", GREEN),
        ("10/10", "endpoint", GREEN),
        ("5/5", "bảng dữ liệu", GREEN),
        ("~3s", "pipeline mẫu", BLUE),
    ]
    for index, (value, label, color) in enumerate(stats):
        x = 0.62 + index * 3.12
        stat_card(slide, x, 1.75, 2.85, 1.2, value, label, color)
    add_rect(slide, 0.62, 3.3, 5.95, 2.9, WHITE, LINE, radius=0.08)
    add_text(slide, "ĐIỂM MẠNH", 0.9, 3.55, 2.0, 0.25, 8.5, GREEN, bold=True, font="Arial")
    for index, text in enumerate(["Độ chính xác cấu trúc cao trên mẫu", "Giải thích được, có tệp/dòng", "Sinh tài liệu ngay, chạy offline"]):
        add_bullet(slide, text, 0.9, 3.95 + index * 0.55, 5.25, 0.4, 9.6, INK, GREEN)
    add_rect(slide, 6.78, 3.3, 5.95, 2.9, WHITE, LINE, radius=0.08)
    add_text(slide, "HẠN CHẾ", 7.06, 3.55, 2.0, 0.25, 8.5, AMBER, bold=True, font="Arial")
    for index, text in enumerate(["Chưa phân tích ngữ nghĩa sâu", "Quy tắc nghiệp vụ cần xác nhận", "Chỉ hỗ trợ Java + SQL"]):
        add_bullet(slide, text, 7.06, 3.95 + index * 0.55, 5.25, 0.4, 9.6, INK, AMBER)
    add_text(slide, "Kết quả là điểm khởi đầu cho chuyên viên, không thay thế đánh giá của con người.", 0.8, 6.55, 11.8, 0.3, 9.5, MUTED, italic=True, font=FONT)
    slide.notes_slide.notes_text_frame.text = (
        "Về đánh giá, công cụ phát hiện đủ 19/19 lớp, 10/10 endpoint và 5/5 bảng trên mẫu. "
        "Pipeline chạy khoảng 3 giây. Điểm mạnh là giải thích được và sinh tài liệu ngay; hạn chế là chưa phân tích ngữ nghĩa sâu, "
        "quy tắc nghiệp vụ mới là ứng viên và phạm vi ngôn ngữ còn hẹp."
    )


def slide_conclusion(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, NAVY)
    add_text(slide, "14 · KẾT LUẬN", 0.62, 0.42, 5.0, 0.25, 9.5, CYAN, bold=True, font="Arial")
    add_text(slide, "Từ mã nguồn cũ đến tài liệu có thể hành động.", 0.6, 0.76, 11.5, 0.75, 28, WHITE, bold=True, font="Arial")
    add_rect(slide, 0.62, 1.85, 6.1, 3.95, NAVY2, RGBColor(0x25, 0x3B, 0x5C), radius=0.08)
    add_text(slide, "ĐÃ ĐẠT ĐƯỢC", 0.92, 2.1, 2.5, 0.25, 8.5, CYAN, bold=True, font="Arial")
    for index, text in enumerate(["Công cụ web chạy cục bộ, 8 nhóm chức năng", "Phát hiện cấu trúc, API, dữ liệu, rủi ro", "Sinh 6 sơ đồ + DOCX/MD/JSON", "Demo trên hệ thống thư viện legacy"]):
        add_bullet(slide, text, 0.92, 2.55 + index * 0.65, 5.4, 0.5, 11, RGBColor(0xD7, 0xE3, 0xF4), CYAN)
    add_rect(slide, 6.95, 1.85, 5.8, 3.95, NAVY2, RGBColor(0x25, 0x3B, 0x5C), radius=0.08)
    add_text(slide, "HƯỚNG PHÁT TRIỂN", 7.25, 2.1, 2.8, 0.25, 8.5, CYAN, bold=True, font="Arial")
    for index, text in enumerate(["JavaParser/Spoon, Tree-sitter, đa ngôn ngữ", "Call graph, data flow, design pattern", "LLM tùy chọn có kiểm chứng", "So sánh 2 phiên bản, CI/CD"]):
        add_bullet(slide, text, 7.25, 2.55 + index * 0.65, 5.1, 0.5, 10.5, RGBColor(0xD7, 0xE3, 0xF4), CYAN)
    add_text(slide, "Cảm ơn cô và các bạn đã lắng nghe.", 0.62, 6.15, 7.0, 0.45, 17, WHITE, bold=True, font="Arial")
    add_text(slide, "Q&A  ·  " + CONFIG["student_name"] + "  ·  " + CONFIG["class_name"], 0.62, 6.67, 8.0, 0.3, 9.5, RGBColor(0x9F, 0xB2, 0xD0), font=FONT)
    add_footer(slide, 15, dark=True)
    slide.notes_slide.notes_text_frame.text = (
        "Kết luận: LegacyScope chứng minh tính khả thi của việc tự động phục hồi cấu trúc, kiến trúc và sinh tài liệu cho hệ thống legacy. "
        "Điểm mạnh là nhẹ, offline, giải thích được; hướng phát triển là parser mạnh hơn, đa ngôn ngữ, call graph và tích hợp CI/CD. "
        "Em xin cảm ơn cô và các bạn, sẵn sàng nhận câu hỏi."
    )


def build():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    slide_title(prs)
    slide_problem(prs)
    slide_objectives(prs)
    slide_gap(prs)
    slide_solution(prs)
    slide_architecture(prs)
    slide_pipeline(prs)
    slide_extraction(prs)
    slide_demo_home(prs)
    slide_results(prs)
    slide_recovered_arch(prs)
    slide_class_data(prs)
    slide_flow_quality(prs)
    slide_evaluation(prs)
    slide_conclusion(prs)
    prs.save(OUT)
    return OUT


if __name__ == "__main__":
    path = build()
    print(path)
