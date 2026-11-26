from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

from legacyscope.analysis import analyze_project
from legacyscope.pipeline import run_pipeline

ASSETS = BASE / "docs" / "assets"
OUT = BASE / "docs"
CONFIG_PATH = BASE / "config" / "student.json"

NAVY = RGBColor(0x0F, 0x17, 0x2A)
BLUE = RGBColor(0x25, 0x63, 0xEB)
CYAN = RGBColor(0x06, 0xB6, 0xD4)
MUTED = RGBColor(0x64, 0x74, 0x8B)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
INK = RGBColor(0x1E, 0x29, 0x3B)


def load_config():
    path = CONFIG_PATH
    if not path.exists():
        path = CONFIG_PATH.with_name("student.example.json")
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def set_run_font(run, name="Times New Roman", size=13, bold=False, color=None, italic=False):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if color is not None:
        run.font.color.rgb = color
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), name)
    rfonts.set(qn("w:hAnsi"), name)
    rfonts.set(qn("w:eastAsia"), name)


def shade_cell(cell, hex_color):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    tc_pr.append(shd)


def set_cell_margins(cell, top=70, bottom=70, left=90, right=90):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("bottom", bottom), ("start", left), ("end", right)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def add_field(paragraph, instruction, placeholder=""):
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = instruction
    sep = OxmlElement("w:fldChar")
    sep.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = placeholder
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(instr)
    run._r.append(sep)
    run._r.append(text)
    run._r.append(end)


def add_bottom_border(paragraph, color="2563EB", size="14"):
    p_pr = paragraph._p.get_or_add_pPr()
    border = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), size)
    bottom.set(qn("w:space"), "8")
    bottom.set(qn("w:color"), color)
    border.append(bottom)
    p_pr.append(border)


def setup(doc, config):
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.2)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.0)
    section.header_distance = Cm(1.0)
    section.footer_distance = Cm(1.0)
    section.different_first_page_header_footer = True

    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(13)
    normal.font.color.rgb = INK
    normal.paragraph_format.line_spacing = 1.45
    normal.paragraph_format.space_after = Pt(5)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")

    for name, size, color in (("Heading 1", 17, NAVY), ("Heading 2", 14, BLUE), ("Heading 3", 12.5, NAVY)):
        style = doc.styles[name]
        style.font.name = "Arial"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = color
        style.paragraph_format.space_before = Pt(14)
        style.paragraph_format.space_after = Pt(6)
        style.paragraph_format.keep_with_next = True
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
        if name == "Heading 1":
            style.paragraph_format.page_break_before = True

    caption = doc.styles["Caption"]
    caption.font.name = "Arial"
    caption.font.size = Pt(9.5)
    caption.font.italic = True
    caption.font.color.rgb = MUTED
    caption.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption.paragraph_format.space_after = Pt(8)

    for list_style in ("List Bullet", "List Number"):
        style = doc.styles[list_style]
        style.font.name = "Times New Roman"
        style.font.size = Pt(13)
        style.font.color.rgb = INK

    header = section.header
    paragraph = header.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_run_font(paragraph.add_run("Báo cáo Chuyên đề Kỹ thuật phần mềm  ·  LegacyScope"), "Arial", 8.5, color=MUTED)

    footer = section.footer
    paragraph = footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(paragraph.add_run("Trang "), "Arial", 9, color=MUTED)
    add_field(paragraph, " PAGE ", "1")
    set_run_font(paragraph.add_run(" / "), "Arial", 9, color=MUTED)
    add_field(paragraph, " NUMPAGES ", "1")

    settings = doc.settings.element
    update_fields = OxmlElement("w:updateFields")
    update_fields.set(qn("w:val"), "true")
    settings.append(update_fields)


def add_cover(doc, config):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(22)
    set_run_font(p.add_run(config["university"]), "Times New Roman", 13, True, NAVY)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(p.add_run(config["faculty"]), "Times New Roman", 12.5, True, NAVY)

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(28)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(p.add_run("BÁO CÁO BÀI TẬP LỚN"), "Arial", 17, True, BLUE)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(p.add_run(config["course"]), "Arial", 12, True, MUTED)

    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.rows[0].cells[0]
    shade_cell(cell, "0F172A")
    set_cell_margins(cell, 260, 260, 180, 180)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(p.add_run("NGHIÊN CỨU VÀ PHÁT TRIỂN GIẢI PHÁP\nTỰ ĐỘNG HÓA TRÍCH XUẤT ĐẶC TẢ KỸ THUẬT\nVÀ SƠ ĐỒ KIẾN TRÚC TỪ MÃ NGUỒN CŨ"), "Arial", 18, True, WHITE)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(14)
    set_run_font(p.add_run("Công cụ thực nghiệm: LegacyScope"), "Times New Roman", 12, italic=True, color=MUTED)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_bottom_border(p, "06B6D4", "18")

    doc.add_paragraph()
    doc.add_paragraph()

    info = [
        ("Giảng viên hướng dẫn", config["advisor"]),
        ("Sinh viên thực hiện", config["student_name"]),
        ("Mã sinh viên", config["student_id"]),
        ("Lớp", config["class_name"]),
    ]
    info_table = doc.add_table(rows=0, cols=2)
    info_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for label, value in info:
        row = info_table.add_row().cells
        row[0].width = Cm(5.2)
        row[1].width = Cm(8.5)
        set_cell_margins(row[0], 90, 90, 0, 100)
        set_cell_margins(row[1], 90, 90, 100, 0)
        p0 = row[0].paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        set_run_font(p0.add_run(label + ":"), "Times New Roman", 12, True, MUTED)
        p1 = row[1].paragraphs[0]
        set_run_font(p1.add_run(value), "Times New Roman", 12, False, NAVY)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(44)
    set_run_font(p.add_run(f"{config['location']}, {config['month_year']}"), "Times New Roman", 11.5, italic=True, color=MUTED)
    doc.add_page_break()


def add_toc(doc):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    set_run_font(p.add_run("MỤC LỤC"), "Arial", 17, True, NAVY)
    p = doc.add_paragraph()
    add_field(p, ' TOC \\o "1-3" \\h \\z \\u ', "Nhấn F9 để cập nhật mục lục")


def heading(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    if level == 1:
        add_bottom_border(h, "2563EB", "12")
    return h


def para(doc, text, indent=True, bold_lead=None):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if indent:
        p.paragraph_format.first_line_indent = Cm(1.0)
    if bold_lead and text.startswith(bold_lead):
        set_run_font(p.add_run(bold_lead), "Times New Roman", 13, True, NAVY)
        set_run_font(p.add_run(text[len(bold_lead):]), "Times New Roman", 13, False, INK)
    else:
        set_run_font(p.add_run(text), "Times New Roman", 13, False, INK)
    return p


def bullets(doc, items, numbered=False):
    style = "List Number" if numbered else "List Bullet"
    for item in items:
        p = doc.add_paragraph(style=style)
        p.paragraph_format.space_after = Pt(2)
        set_run_font(p.add_run(item), "Times New Roman", 13, False, INK)


def table(doc, caption, headers, rows, widths=None, font_size=9.5):
    cap = doc.add_paragraph(caption, style="Caption")
    cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    header_row = t.rows[0]
    tr_pr = header_row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)
    for index, header_text in enumerate(headers):
        cell = header_row.cells[index]
        shade_cell(cell, "0F172A")
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        set_cell_margins(cell)
        if widths:
            cell.width = Cm(widths[index])
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_run_font(p.add_run(str(header_text)), "Arial", font_size - 0.5, True, WHITE)
    for row_index, row in enumerate(rows):
        cells = t.add_row().cells
        for index, value in enumerate(row):
            cell = cells[index]
            if row_index % 2 == 1:
                shade_cell(cell, "F8FAFC")
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_margins(cell)
            if widths:
                cell.width = Cm(widths[index])
            p = cell.paragraphs[0]
            set_run_font(p.add_run(str(value)), "Times New Roman", font_size, False, INK)
    doc.add_paragraph()
    return t


def figure(doc, filename, caption, width=6.3):
    path = ASSETS / filename
    if not path.exists():
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(4)
    p.add_run().add_picture(str(path), width=Inches(width))
    cap = doc.add_paragraph(caption, style="Caption")
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER


def code_block(doc, text, size=8.3):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.5)
    p.paragraph_format.right_indent = Cm(0.5)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.line_spacing = 1.0
    p_pr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), "F8FAFC")
    p_pr.append(shd)
    border = OxmlElement("w:pBdr")
    for side in ("top", "left", "bottom", "right"):
        node = OxmlElement(f"w:{side}")
        node.set(qn("w:val"), "single")
        node.set(qn("w:sz"), "4")
        node.set(qn("w:space"), "4")
        node.set(qn("w:color"), "E2E8F0")
        border.append(node)
    p_pr.append(border)
    set_run_font(p.add_run(text), "Consolas", size, False, RGBColor(0x33, 0x41, 0x55))


def build_report():
    config = load_config()
    print("Đang phân tích mẫu và sinh học liệu...")
    pipeline_start = time.perf_counter()
    result = run_pipeline(BASE / "sample_legacy" / "library_legacy", "Hệ thống Quản lý Thư viện")
    pipeline_seconds = time.perf_counter() - pipeline_start
    analysis_start = time.perf_counter()
    analyze_project(BASE / "sample_legacy" / "library_legacy", "Hệ thống Quản lý Thư viện")
    analysis_seconds = time.perf_counter() - analysis_start
    for key, source in result.diagrams.items():
        if source.endswith(".png"):
            shutil.copy(source, ASSETS / f"demo_{key}.png")
    print(f"Pipeline: {pipeline_seconds:.2f}s, analysis: {analysis_seconds:.2f}s")

    m = result.metrics
    doc = Document()
    setup(doc, config)
    add_cover(doc, config)
    add_toc(doc)

    heading(doc, "LỜI CAM ĐOAN", 1)
    para(doc, "Em xin cam đoan báo cáo bài tập lớn “Nghiên cứu và phát triển giải pháp tự động hóa trích xuất đặc tả kỹ thuật và sơ đồ kiến trúc từ mã nguồn cũ” là công trình do em thực hiện dưới sự hướng dẫn của giảng viên. "
              "Các nội dung nghiên cứu, thiết kế, mã nguồn và kết quả thực nghiệm được trình bày trong báo cáo là trung thực, không sao chép nguyên văn từ công trình khác. "
              "Các tài liệu, công cụ và nguồn tham khảo đã được trích dẫn rõ ràng ở cuối báo cáo.")
    para(doc, "Bộ mã nguồn mẫu được xây dựng phục vụ mục đích học tập và kiểm chứng, không chứa dữ liệu thật của tổ chức hay cá nhân. Các thông tin đăng nhập, địa chỉ và dữ liệu trong hệ thống mẫu chỉ là dữ liệu giả lập. "
              "Nếu có sai sót, em xin chịu trách nhiệm và mong nhận được góp ý của giảng viên để hoàn thiện hơn.")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.paragraph_format.space_before = Pt(24)
    set_run_font(p.add_run("Sinh viên thực hiện"), "Times New Roman", 12, italic=True, color=MUTED)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_run_font(p.add_run(config["student_name"]), "Times New Roman", 12, True, NAVY)

    heading(doc, "LỜI MỞ ĐẦU", 1)
    para(doc, "Trong vòng đời phần mềm, phần lớn chi phí không nằm ở lần phát triển đầu tiên mà nằm ở giai đoạn bảo trì và tiến hóa hệ thống. "
              "Nhiều tổ chức vẫn đang vận hành các hệ thống được viết từ nhiều năm trước, trong khi tài liệu thiết kế, tài liệu API và kiến thức của đội ngũ ban đầu "
              "đã bị thất lạc hoặc không còn đầy đủ. Khi một hệ thống như vậy cần sửa lỗi, bổ sung chức năng, chuyển đổi công nghệ hoặc đánh giá rủi ro bảo mật, "
              "kỹ sư phải đọc lại mã nguồn và tự phục hồi cấu trúc trong đầu. Công việc này tốn thời gian, dễ sai sót và phụ thuộc mạnh vào kinh nghiệm cá nhân.")
    para(doc, "Đề tài “Nghiên cứu và phát triển giải pháp tự động hóa trích xuất đặc tả kỹ thuật và sơ đồ kiến trúc từ mã nguồn cũ” được thực hiện nhằm giải quyết một phần bài toán trên. "
              "Mục tiêu của đề tài không phải là thay thế hoàn toàn chuyên viên phân tích, mà là xây dựng một công cụ hỗ trợ có khả năng quét mã nguồn, "
              "phát hiện các thực thể cấu trúc, phục hồi các góc nhìn kiến trúc, chỉ ra dấu hiệu nợ kỹ thuật và sinh tài liệu kỹ thuật có thể đọc, kiểm chứng và bổ sung.")
    para(doc, "Báo cáo được tổ chức thành năm chương. Chương 1 trình bày bối cảnh, lý do, mục tiêu và phạm vi. Chương 2 hệ thống hóa cơ sở lý thuyết về mã nguồn cũ, "
              "reverse engineering, phân tích tĩnh và phục hồi kiến trúc. Chương 3 phân tích yêu cầu và thiết kế giải pháp LegacyScope. Chương 4 trình bày kết quả triển khai, "
              "demo và đánh giá trên bộ mã nguồn mẫu. Chương 5 kết luận và đề xuất hướng phát triển.")
    para(doc, "Trong quá trình thực hiện, em đã tham khảo các tài liệu về kỹ nghệ phần mềm, bảo trì hệ thống, kiến trúc phần mềm và tài liệu của các công cụ phân tích mã nguồn. "
              "Các nguồn tham khảo chính được liệt kê ở cuối báo cáo. Do giới hạn thời gian và khuôn khổ môn học, sản phẩm tập trung vào mã nguồn Java và SQL, "
              "chạy cục bộ, không phụ thuộc dịch vụ đám mây và không sử dụng mô hình ngôn ngữ lớn.")

    heading(doc, "TÓM TẮT ĐỀ TÀI", 1)
    para(doc, "Đề tài giải quyết bài toán thiếu tài liệu kỹ thuật trong các hệ thống phần mềm lâu năm bằng cách xây dựng công cụ LegacyScope. Công cụ nhận mã nguồn Java và tệp SQL, "
              "thực hiện phân tích tĩnh để trích xuất lớp, phương thức, endpoint, bảng dữ liệu, khóa ngoại, quan hệ phụ thuộc, quy tắc nghiệp vụ và các dấu hiệu nợ kỹ thuật. "
              "Kết quả được biểu diễn qua sáu sơ đồ kiến trúc và được chuyển thành đặc tả kỹ thuật ở định dạng DOCX, Markdown và JSON.")
    para(doc, "Giải pháp được triển khai dưới dạng ứng dụng web chạy cục bộ với FastAPI, giao diện dashboard tiếng Việt và pipeline xử lý khép kín. Trên bộ mẫu Quản lý Thư viện gồm 19 lớp, "
              "163 phương thức, 10 endpoint và 5 bảng dữ liệu, công cụ phát hiện đầy đủ các thực thể cấu trúc, chỉ ra 8 vấn đề nợ kỹ thuật và tính chỉ số rủi ro 75/100. "
              "Thời gian chạy pipeline đầy đủ khoảng 3 giây, đáp ứng yêu cầu demo trực tiếp. Kết quả cho thấy cách tiếp cận phân tích tĩnh nhẹ kết hợp sinh tài liệu tự động là khả thi, "
              "có thể giảm công sức đọc hiểu ban đầu và tạo nền tảng cho các bước bảo trì, tái cấu trúc hoặc chuyển đổi hệ thống.")
    para(doc, "Từ khóa: mã nguồn cũ, reverse engineering, phục hồi kiến trúc, phân tích tĩnh, đặc tả kỹ thuật, LegacyScope.")

    heading(doc, "DANH MỤC TỪ VIẾT TẮT", 1)
    table(doc, "Bảng 1. Danh mục từ viết tắt", ["Từ viết tắt", "Diễn giải"], [
        ["API", "Application Programming Interface – giao diện lập trình ứng dụng"],
        ["AST", "Abstract Syntax Tree – cây cú pháp trừu tượng"],
        ["CSDL", "Cơ sở dữ liệu"],
        ["DAO", "Data Access Object – đối tượng truy cập dữ liệu"],
        ["ERD", "Entity Relationship Diagram – sơ đồ quan hệ thực thể"],
        ["JDBC", "Java Database Connectivity"],
        ["LOC", "Lines of Code – số dòng mã"],
        ["RID", "Resource Identifier"],
        ["SRS", "Software Requirements Specification – đặc tả yêu cầu phần mềm"],
        ["UML", "Unified Modeling Language"],
    ], widths=[3.2, 12.0], font_size=10)

    # ================= CHƯƠNG 1 =================
    heading(doc, "CHƯƠNG 1: TỔNG QUAN", 1)
    heading(doc, "1.1. Bối cảnh và lý do chọn đề tài", 2)
    para(doc, "Hệ thống thông tin của các cơ quan, doanh nghiệp và trường học thường có tuổi thọ lớn hơn nhiều so với dự kiến ban đầu. Một ứng dụng được xây dựng trong giai đoạn 2005–2015 "
              "có thể vẫn đang xử lý dữ liệu nghiệp vụ quan trọng, nhưng công nghệ nền, thư viện, cách triển khai và cả đội ngũ phát triển đã thay đổi. Theo thời gian, tài liệu thiết kế bị lỗi thời, "
              "tài liệu API không được cập nhật, người hiểu hệ thống chuyển sang dự án khác hoặc rời tổ chức. Hệ quả là mã nguồn trở thành nguồn thông tin đáng tin cậy nhất, "
              "nhưng lại là nguồn thông tin khó đọc nhất đối với người mới.")
    para(doc, "Feathers mô tả mã nguồn cũ là mã nguồn mà người kế thừa không có đủ kiến thức và công cụ để thay đổi an toàn [1]. Sommerville nhấn mạnh bảo trì phần mềm chiếm tỷ trọng lớn trong tổng chi phí vòng đời "
              "và thường bị ảnh hưởng bởi tài liệu không đầy đủ, thiết kế bị xói mòn và phụ thuộc chặt [2]. Trong thực tế, trước khi sửa một chức năng, kỹ sư phải trả lời các câu hỏi: "
              "lớp nào đang xử lý nghiệp vụ, dữ liệu đi qua những tầng nào, API nào gọi vào đâu, bảng nào bị ảnh hưởng, thay đổi này có thể tạo chu trình phụ thuộc hay không. "
              "Nếu các câu hỏi đó chỉ được trả lời bằng cách đọc thủ công hàng nghìn dòng mã, chi phí bảo trì sẽ rất cao và rủi ro hồi quy lớn.")
    para(doc, "Ở Việt Nam, nhiều hệ thống quản lý đang vận hành trên nền Java Servlet/JSP, JDBC thuần, PHP hoặc .NET cũ. Các hệ thống này thường có đặc điểm chung: không có kiểm thử tự động, "
              "câu lệnh SQL nối chuỗi trực tiếp, lớp DAO và Service phình to, giao diện JSP còn scriptlet, cấu hình và mật khẩu nằm trong mã nguồn, và gần như không có tài liệu kiến trúc. "
              "Khi các tổ chức chuyển đổi số hoặc thay đổi nhà cung cấp, việc hiểu và đánh giá hệ thống cũ trở thành bước bắt buộc trước khi tái cấu trúc, di trú hoặc thay thế.")
    para(doc, "Các công cụ phân tích mã nguồn thương mại như Understand, Structure101, Lattix hoặc CAST có khả năng mạnh nhưng chi phí bản quyền cao, quy trình cài đặt phức tạp và không phù hợp với một sinh viên hoặc một nhóm nhỏ. "
              "Các công cụ mã nguồn mở như JavaParser, Spoon, PMD hay Doxygen mạnh ở một khía cạnh nhưng thường yêu cầu dự án biên dịch được, không sinh trực tiếp đặc tả kỹ thuật tiếng Việt, "
              "hoặc không kết hợp đồng thời nhiều góc nhìn kiến trúc. Khoảng trống này là cơ sở để đề tài phát triển một công cụ nhẹ, chạy cục bộ, có khả năng tùy biến và giải thích được.")
    heading(doc, "1.2. Mục tiêu của đề tài", 2)
    para(doc, "Đề tài đặt ra ba nhóm mục tiêu: nghiên cứu, kỹ thuật và đánh giá.")
    bullets(doc, [
        "Nghiên cứu: hệ thống hóa các khái niệm về mã nguồn cũ, bảo trì phần mềm, reverse engineering, phân tích tĩnh và phục hồi kiến trúc; xác định các góc nhìn kiến trúc có thể phục hồi từ mã nguồn.",
        "Kỹ thuật: xây dựng công cụ LegacyScope có khả năng nhận mã nguồn Java/SQL, trích xuất lớp, phương thức, annotation, endpoint, bảng dữ liệu, khóa ngoại, phụ thuộc, quy tắc nghiệp vụ và các chỉ báo chất lượng.",
        "Kỹ thuật: sinh tự động sáu sơ đồ kiến trúc và các tệp đặc tả kỹ thuật ở định dạng DOCX, Markdown, JSON; cung cấp giao diện web để chạy demo, xem kết quả và tải tài liệu.",
        "Đánh giá: kiểm chứng công cụ trên một hệ thống thư viện mô phỏng mã nguồn cũ, so sánh kết quả trích xuất với thực thể kỳ vọng, đo thời gian xử lý và phân tích các hạn chế.",
    ])
    heading(doc, "1.3. Đối tượng và phạm vi nghiên cứu", 2)
    para(doc, "Đối tượng nghiên cứu là cấu trúc tĩnh của mã nguồn cũ, cụ thể là mã nguồn Java và các tệp định nghĩa cơ sở dữ liệu SQL. Đề tài không thực thi chương trình, không phân tích hành vi động, "
              "không dịch ngược mã máy và không đánh giá lỗ hổng bảo mật một cách đầy đủ như các công cụ chuyên dụng.")
    table(doc, "Bảng 1.1. Phạm vi thực hiện của đề tài", ["Trong phạm vi", "Ngoài phạm vi"], [
        ["Quét cấu trúc thư mục, nhận diện ngôn ngữ, đếm LOC, comment, TODO/FIXME", "Thực thi mã, profiling, phân tích luồng dữ liệu động"],
        ["Phân tích cú pháp Java để trích xuất package, lớp, giao diện, phương thức, thuộc tính, annotation", "Biên dịch đầy đủ dự án, giải quyết kiểu phức tạp, phân tích bytecode"],
        ["Trích xuất endpoint từ Servlet/Spring MVC và bảng dữ liệu từ SQL", "Kiểm thử API thực tế, kiểm thử xâm nhập, đánh giá lỗ hổng đầy đủ"],
        ["Phân tầng theo quy tắc package/đường dẫn, dựng đồ thị phụ thuộc và phát hiện chu trình", "Phục hồi kiến trúc triển khai, kiến trúc runtime, mô hình mối đe dọa"],
        ["Sinh sơ đồ PNG/Mermaid và đặc tả DOCX/Markdown/JSON", "Đảm bảo tính đúng đắn ngữ nghĩa nghiệp vụ hoàn toàn"],
        ["Chạy cục bộ trên Windows, không cần Internet", "Triển khai đa người dùng, phân quyền, lưu trữ đám mây"],
    ], widths=[8.4, 8.1], font_size=9.3)
    para(doc, "Bộ dữ liệu thực nghiệm chính là hệ thống Quản lý Thư viện mô phỏng, gồm 19 lớp Java, 5 bảng SQL, 10 endpoint và các dấu hiệu nợ kỹ thuật được cài đặt có chủ đích. "
              "Hệ thống mẫu đủ nhỏ để kiểm chứng thủ công nhưng đủ đa dạng để thể hiện các tầng giao diện, nghiệp vụ, truy cập dữ liệu, mô hình miền và hạ tầng.")
    heading(doc, "1.4. Phương pháp nghiên cứu", 2)
    para(doc, "Đề tài sử dụng kết hợp bốn phương pháp. Thứ nhất là nghiên cứu tài liệu để xây dựng khung lý thuyết và lựa chọn kỹ thuật. Thứ hai là phương pháp thiết kế – phát triển (design science), "
              "trong đó giải pháp được thiết kế, hiện thực và cải tiến qua nhiều vòng. Thứ ba là nghiên cứu tình huống (case study) trên một hệ thống legacy mẫu. Thứ tư là đánh giá định lượng và định tính: "
              "đo thời gian, đếm thực thể trích xuất, kiểm tra thủ công kết quả và đánh giá mức độ hữu ích của tài liệu sinh ra.")
    heading(doc, "1.5. Bố cục báo cáo", 2)
    para(doc, "Báo cáo gồm năm chương, tài liệu tham khảo và phụ lục. Chương 2 trình bày cơ sở lý thuyết và các công trình liên quan. Chương 3 phân tích yêu cầu, kiến trúc, pipeline và các thuật toán chính. "
              "Chương 4 trình bày kết quả triển khai, demo và đánh giá. Chương 5 kết luận và đề xuất hướng phát triển. Phụ lục cung cấp hướng dẫn chạy, cấu trúc thư mục và một phần kết quả JSON.")

    # ================= CHƯƠNG 2 =================
    heading(doc, "CHƯƠNG 2: CƠ SỞ LÝ THUYẾT VÀ CÔNG TRÌNH LIÊN QUAN", 1)
    heading(doc, "2.1. Mã nguồn cũ và bảo trì phần mềm", 2)
    para(doc, "Mã nguồn cũ không chỉ là mã nguồn được viết lâu. Theo Feathers, tính “cũ” thể hiện ở việc đội ngũ hiện tại không còn đủ hiểu biết và công cụ để thay đổi mã một cách an toàn [1]. "
              "Một hệ thống có thể mới về tuổi đời nhưng vẫn là legacy nếu thiếu kiểm thử, thiếu tài liệu, phụ thuộc chặt và không ai dám sửa. Ngược lại, một hệ thống lâu năm nhưng có kiểm thử tốt, "
              "tài liệu cập nhật và kiến trúc rõ ràng vẫn có thể bảo trì hiệu quả.")
    para(doc, "IEEE 14764 phân loại bảo trì thành bốn nhóm: sửa lỗi (corrective), thích nghi (adaptive), hoàn thiện (perfective) và phòng ngừa (preventive) [5]. Phần lớn công việc bảo trì thực tế là thích nghi và hoàn thiện, "
              "tức là thay đổi hệ thống để đáp ứng môi trường mới hoặc yêu cầu mới. Để làm được điều đó, kỹ sư cần hiểu cấu trúc hiện tại. Khi tài liệu không còn đáng tin, phân tích mã nguồn trở thành bước khởi đầu bắt buộc.")
    para(doc, "Nợ kỹ thuật (technical debt) là ẩn dụ chỉ các quyết định thiết kế hoặc triển khai giúp đạt mục tiêu ngắn hạn nhưng tạo chi phí dài hạn. Trong hệ thống legacy, nợ kỹ thuật thường biểu hiện qua: "
              "phương thức quá dài, lớp có quá nhiều trách nhiệm, phụ thuộc vòng, sao chép mã, SQL nối chuỗi, thiếu kiểm thử, cấu hình và bí mật nằm trong mã, công nghệ lỗi thời và tài liệu không đồng bộ. "
              "Các dấu hiệu này có thể phát hiện một phần bằng phân tích tĩnh và là đầu vào cho chỉ số rủi ro của LegacyScope.")
    heading(doc, "2.2. Reverse engineering và phục hồi kiến trúc", 2)
    para(doc, "Chikofsky và Cross định nghĩa reverse engineering là quá trình phân tích một hệ thống để xác định các thành phần và mối quan hệ của nó, nhằm tạo ra biểu diễn ở mức trừu tượng cao hơn [4]. "
              "Design recovery mở rộng reverse engineering bằng cách kết hợp mã nguồn với kiến thức miền, thông tin cấu hình và tài liệu để phục hồi ý định thiết kế. Trong đề tài này, "
              "đầu vào chủ yếu là mã nguồn và schema SQL; đầu ra là mô hình cấu trúc và các góc nhìn kiến trúc.")
    para(doc, "Phục hồi kiến trúc (architecture recovery) là một nhánh của reverse engineering, tập trung vào việc tái tạo các thành phần kiến trúc và quan hệ giữa chúng. Ducasse và Pollet mô tả đây là quá trình gồm nhiều bước: "
              "trích xuất thông tin, hợp nhất, phân tích, biểu diễn và đánh giá [8]. Có hai hướng tiếp cận chính: phân tích tĩnh và phân tích động. Phân tích tĩnh đọc mã nguồn, bytecode hoặc mô hình trung gian; "
              "phân tích động quan sát hành vi khi chạy. Phân tích tĩnh phù hợp khi không thể chạy hệ thống, khi cần bao phủ toàn bộ mã hoặc khi cần kết quả ổn định, lặp lại. Phân tích động mạnh ở việc phát hiện quan hệ thực tế nhưng phụ thuộc vào kịch bản chạy.")
    para(doc, "Kiến trúc phần mềm có nhiều góc nhìn. ISO/IEC/IEEE 42010 định nghĩa kiến trúc là tập hợp các khái niệm và quan hệ cơ bản, được biểu diễn qua các góc nhìn phục vụ các bên liên quan [6]. "
              "Với mục tiêu bảo trì, các góc nhìn hữu ích gồm: góc nhìn module (package, lớp, phụ thuộc), góc nhìn thành phần – kết nối (controller, service, DAO, database), góc nhìn dữ liệu (bảng, khóa, quan hệ) "
              "và góc nhìn hành vi (luồng xử lý API). LegacyScope phục hồi bốn góc nhìn này ở mức đủ để định hướng đọc hiểu và đánh giá tác động.")
    heading(doc, "2.3. Các kỹ thuật phân tích tĩnh", 2)
    para(doc, "Phân tích tĩnh có thể chia thành các mức: phân tích từ vựng, phân tích cú pháp, phân tích ngữ nghĩa và phân tích liên thủ tục. Phân tích từ vựng tách mã thành token; phân tích cú pháp xây dựng cây cú pháp; "
              "phân tích ngữ nghĩa giải quyết kiểu, phạm vi và liên kết; phân tích liên thủ tục xây dựng call graph và luồng dữ liệu. Mỗi mức có chi phí và độ chính xác khác nhau.")
    bullets(doc, [
        "Biểu thức chính quy (regex): nhanh, dễ triển khai, phù hợp để nhận diện mẫu như annotation, đường dẫn API, câu lệnh SQL. Hạn chế là dễ dương tính giả khi mã có cấu trúc lồng nhau hoặc chuỗi nhiều dòng.",
        "AST và parser: chính xác hơn, hiểu được cấu trúc lớp/phương thức, nhưng yêu cầu mã nguồn hợp lệ về cú pháp và có thể thất bại với mã cũ dùng cú pháp lạ hoặc thiếu thư viện.",
        "Phân tích bytecode: chính xác về kiểu và lời gọi nhưng cần biên dịch được dự án và phụ thuộc vào phiên bản JDK.",
        "Đồ thị phụ thuộc: biểu diễn lớp/module là đỉnh, quan hệ là cạnh; hỗ trợ phát hiện chu trình, tính coupling, xếp hạng tầng và đánh giá tác động.",
        "Mô hình ngôn ngữ lớn: có thể sinh mô tả tự nhiên, nhưng không ổn định, có thể ảo giác và khó kiểm chứng; chỉ nên dùng như lớp bổ trợ có kiểm soát.",
    ])
    para(doc, "Với hệ thống legacy, một thách thức lớn là mã nguồn có thể không biên dịch được do thiếu thư viện, cấu hình hoặc phiên bản. Vì vậy, LegacyScope chọn cách tiếp cận lai: dùng bộ phân tích cấu trúc nhẹ, "
              "che giấu comment và chuỗi để tìm dấu ngoặc cân bằng, kết hợp regex để nhận diện khai báo và annotation. Cách này không thay thế parser đầy đủ nhưng đủ bền với mã cũ và cho kết quả giải thích được.")
    heading(doc, "2.3.1. So sánh phân tích tĩnh và phân tích động", 3)
    para(doc, "Phân tích tĩnh và phân tích động bổ sung cho nhau. Phân tích tĩnh đọc mã nguồn hoặc mô hình trung gian, có thể bao phủ cả những nhánh chưa từng được chạy và cho kết quả lặp lại. "
              "Phân tích động ghi nhận hành vi thực tế, phát hiện được các quan hệ chỉ xuất hiện khi chạy nhưng phụ thuộc vào kịch bản kiểm thử và môi trường. Với hệ thống legacy không thể chạy hoặc thiếu dữ liệu, "
              "phân tích tĩnh thường là lựa chọn khả thi hơn để bắt đầu.")
    table(doc, "Bảng 2.2. So sánh phân tích tĩnh và phân tích động", ["Tiêu chí", "Phân tích tĩnh", "Phân tích động"], [
        ["Đầu vào", "Mã nguồn, bytecode, mô hình", "Chương trình đang chạy, log, trace"],
        ["Phạm vi", "Toàn bộ mã, kể cả nhánh chưa chạy", "Chỉ các luồng được kích hoạt"],
        ["Tính lặp lại", "Cao, cùng mã cho cùng kết quả", "Phụ thuộc môi trường và kịch bản"],
        ["Khả năng phát hiện quan hệ runtime", "Hạn chế", "Cao"],
        ["Yêu cầu biên dịch/chạy", "Thấp hơn với parser nhẹ", "Cao"],
        ["Ứng dụng trong đề tài", "Trục chính của LegacyScope", "Hướng mở rộng tương lai"],
    ], widths=[4.2, 6.0, 6.2], font_size=9.3)
    para(doc, "LegacyScope chọn phân tích tĩnh vì mục tiêu là tạo tài liệu cấu trúc ổn định, có thể chạy trên mã nguồn chưa biên dịch được và không cần dựng môi trường CSDL. "
              "Trong tương lai, công cụ có thể kết hợp trace runtime để xác nhận các luồng thực tế, đặc biệt với các hệ thống dùng reflection, dependency injection hoặc sinh mã động.")
    heading(doc, "2.4. Đặc tả kỹ thuật và tài liệu kiến trúc", 2)
    para(doc, "Đặc tả yêu cầu phần mềm theo ISO/IEC/IEEE 29148 nhấn mạnh tính đầy đủ, nhất quán, rõ ràng, có thể kiểm chứng và truy vết [7]. Trong bối cảnh phục hồi hệ thống cũ, tài liệu cần trả lời được các câu hỏi: "
              "hệ thống gồm những module nào, lớp nào chịu trách nhiệm gì, API nào tồn tại, dữ liệu nằm ở đâu, quy tắc nghiệp vụ nào đang được thực thi và rủi ro kỹ thuật nằm ở đâu. "
              "Đặc tả do LegacyScope sinh ra không thay thế SRS chính thức mà là tài liệu kỹ thuật đầu vào để chuyên viên phân tích xác nhận và bổ sung.")
    para(doc, "Ở mức kiến trúc, mô hình C4 của Brown đề xuất bốn mức: context, container, component và code [19]. Với một công cụ tự động, việc phục hồi chính xác cả bốn mức là quá tham vọng. "
              "LegacyScope tập trung vào mức component và code: phân tầng các lớp, vẽ quan hệ phụ thuộc, sơ đồ lớp rút gọn, ERD và luồng API. Các sơ đồ được sinh dưới dạng PNG để nhúng vào báo cáo và Mermaid để tái sử dụng trong Markdown.")
    heading(doc, "2.5. Công cụ và nghiên cứu liên quan", 2)
    para(doc, "Trên thị trường có nhiều công cụ hỗ trợ hiểu mã nguồn. Bảng 2.1 tóm tắt một số công cụ tiêu biểu và khoảng trống mà LegacyScope hướng tới.")
    table(doc, "Bảng 2.1. So sánh một số công cụ phân tích mã nguồn", ["Công cụ", "Điểm mạnh", "Hạn chế với bài toán"], [
        ["Understand", "Phân tích đa ngôn ngữ, metric, đồ thị phụ thuộc mạnh", "Thương mại, chi phí cao, không sinh đặc tả tiếng Việt theo mẫu"],
        ["Structure101 / Lattix", "Phân tích kiến trúc, dependency, tuân thủ quy tắc", "Tập trung vào kiến trúc, cần cấu hình dự án, bản quyền"],
        ["CAST", "Đánh giá chất lượng, nợ kỹ thuật ở quy mô lớn", "Nặng, đắt, quy trình triển khai phức tạp"],
        ["SonarQube", "Chất lượng mã, lỗi, smell, bảo mật", "Không phục hồi kiến trúc/đặc tả đầy đủ, cần build"],
        ["JavaParser / Spoon", "AST Java mạnh, API lập trình tốt", "Cần viết thêm logic trích xuất, biểu diễn, sinh tài liệu"],
        ["Doxygen", "Sinh tài liệu từ comment", "Phụ thuộc comment, yếu với mã không có tài liệu"],
        ["PlantUML / Mermaid", "Vẽ sơ đồ từ văn bản", "Chỉ là công cụ biểu diễn, không phân tích mã"],
        ["LegacyScope", "Java + SQL, sơ đồ + DOCX/MD/JSON, offline, tiếng Việt", "Chưa phân tích ngữ nghĩa sâu, chưa đa ngôn ngữ"],
    ], widths=[3.0, 6.6, 6.9], font_size=9.0)
    para(doc, "Khoảng trống mà đề tài khai thác không phải là “phân tích mã nguồn” nói chung, mà là sự kết hợp giữa phục hồi cấu trúc, biểu diễn kiến trúc và sinh tài liệu kỹ thuật trong một quy trình nhẹ, chạy cục bộ, không cần cấu hình phức tạp. "
              "Đối tượng sử dụng chính là sinh viên, giảng viên và kỹ sư cần đánh giá nhanh một hệ thống legacy trước khi bảo trì hoặc chuyển đổi.")
    heading(doc, "2.6. Kết luận chương", 2)
    para(doc, "Chương 2 đã trình bày các khái niệm nền tảng về mã nguồn cũ, bảo trì, reverse engineering, phục hồi kiến trúc và phân tích tĩnh. Các lý thuyết này cho thấy một công cụ hỗ trợ cần kết hợp nhiều mức trừu tượng: "
              "từ cấu trúc lớp/phương thức đến quan hệ module, mô hình dữ liệu và tài liệu. Chương 3 sẽ cụ thể hóa các yêu cầu và thiết kế của LegacyScope dựa trên khung lý thuyết này.")

    # ================= CHƯƠNG 3 =================
    heading(doc, "CHƯƠNG 3: PHÂN TÍCH VÀ THIẾT KẾ GIẢI PHÁP", 1)
    heading(doc, "3.1. Yêu cầu hệ thống", 2)
    para(doc, "LegacyScope được thiết kế cho ba nhóm người dùng: sinh viên/nghiên cứu muốn tìm hiểu mã nguồn mẫu; kỹ sư bảo trì cần đánh giá nhanh hệ thống trước khi sửa; giảng viên cần minh họa quy trình phục hồi kiến trúc. "
              "Các yêu cầu chức năng được ánh xạ trực tiếp từ tám nhóm chức năng đã thống nhất.")
    table(doc, "Bảng 3.1. Yêu cầu chức năng của LegacyScope", ["Mã", "Yêu cầu", "Kết quả mong đợi"], [
        ["FR-01", "Chọn nguồn phân tích", "Chọn mẫu có sẵn hoặc tải ZIP; kiểm tra định dạng và dung lượng"],
        ["FR-02", "Quét dự án", "Danh sách tệp, ngôn ngữ, LOC, comment, TODO/FIXME"],
        ["FR-03", "Trích xuất cấu trúc", "Package, lớp, phương thức, thuộc tính, annotation, kế thừa"],
        ["FR-04", "Trích xuất API và dữ liệu", "Endpoint, bảng, cột, khóa chính, khóa ngoại, quan hệ"],
        ["FR-05", "Phân tích kiến trúc", "Phân tầng, phụ thuộc, chu trình, chỉ số rủi ro, phát hiện"],
        ["FR-06", "Sinh sơ đồ", "Sáu sơ đồ PNG và các tệp Mermaid tương ứng"],
        ["FR-07", "Sinh đặc tả", "DOCX, Markdown, JSON và gói ZIP"],
        ["FR-08", "Dashboard và tải xuống", "Xem kết quả theo tab, tìm kiếm, tải từng tệp"],
    ], widths=[1.8, 4.8, 10.0], font_size=9.3)
    para(doc, "Các yêu cầu phi chức năng được đặt ra để đảm bảo công cụ phù hợp với demo và báo cáo: chạy cục bộ, không gửi mã nguồn ra ngoài; thời gian xử lý dưới 10 giây với dự án mẫu; "
              "giao diện tiếng Việt, rõ ràng; kết quả có thể giải thích và truy vết về tệp/dòng; kiến trúc mở để bổ sung ngôn ngữ và bộ phân tích mới; không yêu cầu cơ sở dữ liệu hoặc tài khoản.")
    table(doc, "Bảng 3.2. Yêu cầu phi chức năng", ["Mã", "Thuộc tính", "Tiêu chí"], [
        ["NFR-01", "Hiệu năng", "Dự án mẫu 19 lớp hoàn tất phân tích và sinh tài liệu dưới 10 giây"],
        ["NFR-02", "Khả dụng", "Người dùng không cần biết dòng lệnh; thao tác chính trong 3 bước"],
        ["NFR-03", "Bảo mật dữ liệu", "Mã nguồn chỉ xử lý cục bộ, không gọi dịch vụ bên ngoài"],
        ["NFR-04", "Khả năng bảo trì", "Tách module scanner/parser/analyzer/generator; có kiểu dữ liệu rõ ràng"],
        ["NFR-05", "Khả năng mở rộng", "Thêm ngôn ngữ bằng parser mới; thêm mẫu tài liệu bằng generator mới"],
        ["NFR-06", "Tính giải thích", "Mỗi phát hiện có tệp, dòng, quy tắc và mô tả"],
    ], widths=[1.8, 3.7, 11.1], font_size=9.3)
    heading(doc, "3.2. Kiến trúc tổng thể", 2)
    para(doc, "LegacyScope được tổ chức thành bốn lớp: giao diện web, API ứng dụng, lõi phân tích và sinh tài liệu. Cách tách này giúp phần phân tích không phụ thuộc giao diện, "
              "đồng thời cho phép chạy pipeline từ dòng lệnh hoặc từ API mà không phải sửa logic.")
    figure(doc, "solution_architecture.png", "Hình 3.1. Kiến trúc tổng thể của LegacyScope", 6.2)
    para(doc, "Lớp giao diện là các tệp HTML/CSS/JavaScript tĩnh, không dùng framework nặng. Giao diện gọi API qua fetch, hiển thị tiến trình, dashboard và liên kết tải tài liệu. "
              "Lớp API dùng FastAPI, cung cấp các endpoint phân tích mẫu, upload ZIP, đọc kết quả và phục vụ tệp tĩnh. Lõi phân tích gồm scanner, parser Java, parser SQL, bộ phân tích kiến trúc và bộ phát hiện vấn đề. "
              "Lớp sinh tài liệu gồm sinh sơ đồ bằng Matplotlib/NetworkX, sinh DOCX bằng python-docx, sinh Markdown/JSON và đóng gói ZIP.")
    para(doc, "Các lựa chọn công nghệ được cân nhắc theo tiêu chí đơn giản, ổn định và dễ demo. Python phù hợp cho phân tích chuỗi, AST và sinh tài liệu; FastAPI nhẹ và có tài liệu tự động; "
              "Matplotlib/NetworkX đủ mạnh để vẽ sơ đồ tĩnh; python-docx cho phép kiểm soát định dạng báo cáo. Giao diện vanilla giúp tránh phụ thuộc npm và đảm bảo chạy offline.")
    heading(doc, "3.3. Pipeline xử lý", 2)
    para(doc, "Pipeline gồm bảy bước, từ chọn nguồn đến sinh đặc tả. Mỗi bước tạo ra một đầu ra trung gian có thể kiểm tra, nhờ đó dễ gỡ lỗi và mở rộng.")
    figure(doc, "pipeline.png", "Hình 3.2. Pipeline phân tích và sinh đặc tả", 6.3)
    bullets(doc, [
        "Bước 1: nhận ZIP hoặc đường dẫn mẫu, kiểm tra định dạng, giải nén an toàn và xác định thư mục gốc.",
        "Bước 2: quét tệp, bỏ qua thư mục sinh tự động, nhận diện ngôn ngữ, đếm dòng và thu thập TODO/FIXME.",
        "Bước 3: phân tích Java để trích xuất lớp, phương thức, thuộc tính, annotation, endpoint và quan hệ.",
        "Bước 4: phân tích SQL để trích xuất bảng, cột, khóa chính, khóa ngoại; bổ sung bảng được tham chiếu trong mã.",
        "Bước 5: phân tầng, dựng đồ thị phụ thuộc, phát hiện chu trình, tính chỉ số rủi ro và sinh danh sách phát hiện.",
        "Bước 6: sinh sáu sơ đồ PNG và các tệp Mermaid.",
        "Bước 7: sinh DOCX, Markdown, JSON, đóng gói ZIP và trả kết quả cho giao diện.",
    ], numbered=True)
    heading(doc, "3.3.1. Tác nhân và use case tổng quát", 3)
    para(doc, "Hệ thống có ba tác nhân chính. Người phân tích chọn nguồn, chạy phân tích và đọc kết quả. Kỹ sư bảo trì tập trung vào sơ đồ kiến trúc, API, dữ liệu và danh sách vấn đề để đánh giá tác động. "
              "Giảng viên/quản trị dùng bộ mẫu và tài liệu sinh ra để minh họa quy trình hoặc kiểm chứng công cụ. Tác nhân phụ là hệ thống tệp, cung cấp mã nguồn và nhận artifact.")
    bullets(doc, [
        "UC-01 – Phân tích mẫu: người dùng chọn mẫu, hệ thống chạy pipeline và hiển thị dashboard.",
        "UC-02 – Phân tích ZIP: người dùng tải gói mã nguồn, hệ thống kiểm tra, giải nén an toàn và phân tích.",
        "UC-03 – Xem kiến trúc: người dùng mở tab Kiến trúc để xem sơ đồ tầng, phụ thuộc và bảng phân bố.",
        "UC-04 – Tra cứu lớp/API: người dùng tìm kiếm trong bảng lớp, endpoint và xem chi tiết.",
        "UC-05 – Xem dữ liệu: người dùng xem ERD, bảng, khóa ngoại và quy tắc nghiệp vụ.",
        "UC-06 – Tải đặc tả: người dùng tải DOCX, Markdown, JSON hoặc gói ZIP.",
        "UC-07 – Đánh giá rủi ro: người dùng xem chỉ số, vấn đề mức cao và khuyến nghị bảo trì.",
    ])
    para(doc, "Luồng chuẩn của UC-02 bắt đầu khi người dùng chọn tệp ZIP. Hệ thống kiểm tra phần mở rộng và dung lượng, giải nén vào thư mục tạm, xác định thư mục gốc, chạy pipeline và trả về mã phân tích. "
              "Nếu ZIP chứa đường dẫn không hợp lệ hoặc vượt quá 30 MB, hệ thống dừng và hiển thị thông báo. Sau khi phân tích xong, thư mục tạm được xóa, chỉ artifact trong outputs được giữ lại.")
    heading(doc, "3.4. Thiết kế module", 2)
    para(doc, "Bảng 3.3 mô tả trách nhiệm của từng module chính. Thiết kế này theo nguyên tắc trách nhiệm đơn lẻ: scanner không biết về Java, parser không biết về giao diện, generator không tự phân tích lại mã.")
    table(doc, "Bảng 3.3. Thiết kế module của LegacyScope", ["Module", "Trách nhiệm", "Đầu vào", "Đầu ra"], [
        ["scanner.py", "Duyệt thư mục, nhận diện ngôn ngữ, đếm LOC/comment/TODO", "Đường dẫn dự án", "Danh sách FileInfo, thống kê"],
        ["java_parser.py", "Che comment/chuỗi, tìm lớp, thành viên, annotation, endpoint", "Tệp .java", "ClassInfo, EndpointInfo"],
        ["sql_parser.py", "Phân tích CREATE TABLE, cột, khóa, tham chiếu", "Tệp .sql hoặc chuỗi SQL", "TableInfo"],
        ["analysis.py", "Phân tầng, phụ thuộc, chu trình, quy tắc, chỉ số rủi ro", "Mô hình cấu trúc", "AnalysisResult, FindingInfo"],
        ["diagrams.py", "Sinh sơ đồ kiến trúc, phụ thuộc, lớp, ERD, luồng, chất lượng", "AnalysisResult", "PNG, Mermaid"],
        ["docx_spec.py / markdown_spec.py", "Sinh đặc tả kỹ thuật theo mẫu", "AnalysisResult", "DOCX, Markdown"],
        ["app.py / web/", "API, giao diện, upload, dashboard, tải tệp", "Yêu cầu người dùng", "Kết quả JSON, tệp"],
    ], widths=[3.5, 7.5, 3.2, 4.5], font_size=8.8)
    heading(doc, "3.5. Các thuật toán và xử lý chính", 2)
    heading(doc, "3.5.1. Quét dự án và nhận diện ngôn ngữ", 3)
    para(doc, "Scanner duyệt cây thư mục theo chiều sâu, bỏ qua các thư mục sinh tự động như .git, target, build, node_modules. Mỗi tệp được ánh xạ sang ngôn ngữ theo phần mở rộng. "
              "Với tệp văn bản, scanner đếm dòng trống, dòng chú thích và dòng mã theo trạng thái block comment; đồng thời đếm số lần xuất hiện của TODO/FIXME/HACK. "
              "Cách đếm này không hoàn toàn chính xác với mọi cú pháp nhưng đủ ổn định để so sánh tương đối giữa các dự án.")
    heading(doc, "3.5.2. Trích xuất cấu trúc Java", 3)
    para(doc, "Thay vì yêu cầu dự án biên dịch, LegacyScope sử dụng bộ phân tích nhẹ. Trước hết, comment và nội dung chuỗi được thay bằng khoảng trắng nhưng giữ nguyên số dòng. "
              "Việc che giấu này giúp tìm dấu ngoặc cân bằng mà không bị nhầm bởi dấu ngoặc trong chuỗi hoặc comment. Sau đó, biểu thức chính quy nhận diện khai báo lớp, giao diện, enum, "
              "annotation, kế thừa và implements. Với mỗi lớp, bộ quét thành viên duyệt ở độ sâu bằng 0 để tách thuộc tính, phương thức và constructor, đồng thời bỏ qua thân phương thức.")
    code_block(doc, """def parse_java_file(path):
    text = read_text(path)
    masked = mask_comments_and_strings(text)
    package = find_package(masked)
    for match in CLASS_PATTERN.finditer(masked):
        open_brace = match.end() - 1
        close_brace = matching_brace(masked, open_brace)
        body_masked = masked[open_brace + 1:close_brace]
        body_raw = text[open_brace + 1:close_brace]
        parse_members(class_info, body_masked, body_raw)
        find_endpoints(class_info, raw_annotations)""")
    para(doc, "Endpoint được trích xuất từ hai nguồn: annotation Servlet (@WebServlet) kết hợp phương thức doGet/doPost, và annotation Spring MVC (@RequestMapping, @GetMapping, @PostMapping…). "
              "Với Servlet, đường dẫn lấy từ urlPatterns hoặc value; với Spring, đường dẫn được ghép từ base path ở cấp lớp và path ở cấp phương thức. "
              "Cách này bao phủ phần lớn hệ thống Java web cũ mà không cần phân tích toàn bộ framework.")
    heading(doc, "3.5.3. Phân tầng kiến trúc", 3)
    para(doc, "LegacyScope phân tầng theo package và đường dẫn tệp. Quy tắc được thiết kế để ưu tiên dấu hiệu rõ ràng và không phụ thuộc tên lớp cụ thể. Bảng 3.4 mô tả các quy tắc.")
    table(doc, "Bảng 3.4. Quy tắc phân tầng", ["Tầng", "Dấu hiệu nhận diện", "Ví dụ"], [
        ["Giao diện / API", "controller, servlet, web, api, rest", "BookServlet, LoanController"],
        ["Nghiệp vụ", "service, business, usecase", "BookService, LoanService"],
        ["Truy cập dữ liệu", "dao, repository, mapper, persistence", "BookDAO, LoanRepository"],
        ["Mô hình miền", "model, entity, domain, dto, bean", "Book, Reader, Loan"],
        ["Hạ tầng dùng chung", "util, config, common, filter, security, helper", "DBUtil, AuthFilter"],
    ], widths=[3.8, 8.5, 5.2], font_size=9.3)
    heading(doc, "3.5.4. Đồ thị phụ thuộc và phát hiện chu trình", 3)
    para(doc, "Quan hệ phụ thuộc được suy ra từ import, kiểu thuộc tính, tham số, giá trị trả về, kế thừa, implements và lời gọi phương thức. Mỗi quan hệ được lưu cùng loại và trọng số. "
              "Đồ thị lớp sau đó được dùng để phát hiện chu trình bằng thuật toán simple_cycles của NetworkX, giới hạn độ dài để tránh bùng nổ tổ hợp. "
              "Ở mức tầng, các cạnh được gộp để vẽ bản đồ phụ thuộc dễ đọc.")
    code_block(doc, """graph = nx.DiGraph()
for cls in classes:
    graph.add_node(cls.name)
for dep in dependencies:
    if dep.source != dep.target:
        graph.add_edge(dep.source, dep.target)
cycles = list(nx.simple_cycles(graph, length_bound=8))""")
    heading(doc, "3.5.5. Trích xuất quy tắc nghiệp vụ", 3)
    para(doc, "Quy tắc nghiệp vụ được trích xuất từ các câu lệnh if có điều kiện và thông báo trả về trong phương thức nghiệp vụ. Bộ phân tích tìm dấu ngoặc cân bằng để lấy điều kiện, "
              "sau đó tìm câu lệnh return gần nhất trong cùng khối. Kết quả là cặp (điều kiện, hành vi/thông báo). Ngoài ra, các ràng buộc khóa ngoại trong schema SQL cũng được chuyển thành quy tắc dữ liệu. "
              "Cách tiếp cận này tạo danh sách ứng viên, không khẳng định toàn bộ ngữ nghĩa nghiệp vụ.")
    code_block(doc, """if (currentLoans.size() >= 3) {
    return "Bạn đọc đã mượn tối đa 3 cuốn sách";
}
=> condition: currentLoans.size() >= 3
=> action: Bạn đọc đã mượn tối đa 3 cuốn sách""")
    heading(doc, "3.5.6. Chỉ số rủi ro mã nguồn cũ", 3)
    para(doc, "Chỉ số rủi ro là điểm tổng hợp từ các dấu hiệu nợ kỹ thuật, thang 0–100, điểm càng cao càng cần can thiệp. Công thức được thiết kế để ưu tiên bảo mật, thiếu kiểm thử và chu trình phụ thuộc. "
              "Đây là chỉ số tương đối phục vụ so sánh và ưu tiên, không phải đánh giá tuyệt đối.")
    table(doc, "Bảng 3.5. Thành phần chỉ số rủi ro", ["Thành phần", "Điểm tối đa", "Ý nghĩa"], [
        ["Điểm cơ sở", "25", "Mức nền cho mọi hệ thống legacy"],
        ["TODO/FIXME", "20", "Dấu hiệu công việc chưa hoàn thiện"],
        ["Chu trình phụ thuộc", "20", "Làm giảm khả năng tách module và kiểm thử"],
        ["Phương thức dài/phức tạp", "15", "Chi phí đọc hiểu và sửa đổi"],
        ["Phát hiện mức cao", "15", "Bảo mật, thiếu kiểm thử, hard-code"],
        ["Độ phức tạp lớn nhất", "10", "Điểm nóng cần ưu tiên"],
        ["Thiếu kiểm thử", "10", "Không có lưới an toàn hồi quy"],
        ["JSP scriptlet / SQL nối chuỗi", "5 + 5", "Dấu hiệu công nghệ cũ và rủi ro injection"],
    ], widths=[5.0, 2.5, 9.3], font_size=9.3)
    heading(doc, "3.5.7. Sinh sơ đồ", 3)
    para(doc, "Sáu sơ đồ được sinh bằng Matplotlib và NetworkX: kiến trúc phân tầng, phụ thuộc giữa các tầng, sơ đồ lớp rút gọn, ERD, luồng xử lý API và dashboard chất lượng. "
              "Mỗi sơ đồ dùng cùng bảng màu theo tầng để người đọc dễ liên hệ giữa các hình. Các tệp Mermaid tương ứng được sinh thêm để có thể chỉnh sửa hoặc nhúng vào Markdown.")
    heading(doc, "3.5.8. Sinh đặc tả kỹ thuật", 3)
    para(doc, "Tài liệu DOCX được sinh theo mẫu gồm: thông tin chung, tổng quan kiến trúc, danh mục module, danh mục lớp, danh mục API, mô hình dữ liệu, quy tắc nghiệp vụ, đánh giá chất lượng, khuyến nghị và phụ lục tệp. "
              "python-docx được dùng để tạo đoạn văn bản, bảng, hình, mục lục tự động và số trang. Markdown được sinh song song để lưu trong Git hoặc wiki. JSON lưu toàn bộ mô hình để tái sử dụng cho phân tích khác.")
    heading(doc, "3.6. Mô hình dữ liệu", 2)
    para(doc, "Mô hình dữ liệu trung tâm của LegacyScope gồm các thực thể sau: AnalysisResult (kết quả tổng), ClassInfo (lớp), MethodInfo (phương thức), FieldInfo (thuộc tính), EndpointInfo (API), "
              "TableInfo/ColumnInfo (dữ liệu), DependencyInfo (phụ thuộc), FindingInfo (phát hiện), BusinessRuleInfo (quy tắc) và LayerInfo (tầng). Mỗi thực thể có phương thức to_dict để xuất JSON.")
    table(doc, "Bảng 3.6. Các thực thể dữ liệu chính", ["Thực thể", "Thuộc tính tiêu biểu", "Mục đích"], [
        ["AnalysisResult", "analysis_id, project, files, classes, layers, metrics, diagrams", "Gốc của toàn bộ kết quả"],
        ["ClassInfo", "name, package, kind, extends, methods, fields, layer, file", "Mô tả lớp và vị trí"],
        ["MethodInfo", "name, signature, return_type, params, complexity, calls", "Mô tả phương thức"],
        ["EndpointInfo", "http_method, path, handler, class_name, file", "Mô tả API"],
        ["TableInfo", "name, columns, primary_key, foreign_keys", "Mô tả bảng dữ liệu"],
        ["DependencyInfo", "source, target, kind, weight", "Cạnh của đồ thị phụ thuộc"],
        ["FindingInfo", "severity, category, title, file, line", "Phát hiện nợ kỹ thuật"],
        ["BusinessRuleInfo", "title, condition, action, file", "Quy tắc nghiệp vụ ứng viên"],
    ], widths=[3.7, 8.0, 5.2], font_size=9.0)
    code_block(doc, """{
  "analysis_id": "20261126-...",
  "project_name": "Hệ thống Quản lý Thư viện",
  "metrics": {"classes": 19, "methods": 163, "endpoints": 10, "legacy_score": 75},
  "layers": [{"key": "presentation", "classes": ["BookServlet", "..."]}],
  "diagrams": {"architecture": "/outputs/.../architecture_layers.png"}
}""", size=8.0)
    heading(doc, "3.7. Thiết kế giao diện", 2)
    para(doc, "Giao diện được thiết kế theo hướng dashboard, ưu tiên thao tác nhanh và khả năng đọc kết quả. Trang đầu gồm hero giới thiệu, vùng upload, danh sách mẫu và hướng dẫn ba bước. "
              "Sau khi phân tích, người dùng thấy header dự án, điểm rủi ro, sáu thẻ số liệu và các tab Tổng quan, Kiến trúc, Lớp & API, Dữ liệu, Đặc tả, Vấn đề.")
    figure(doc, "ui_home.png", "Hình 3.3. Giao diện trang chủ LegacyScope", 6.2)
    para(doc, "Các nguyên tắc thiết kế chính gồm: phân cấp thông tin rõ ràng, màu sắc theo tầng, bảng có tìm kiếm, sơ đồ có thể phóng to, nút tải tài liệu luôn hiển thị và phản hồi tiến trình trong khi phân tích. "
              "Giao diện không yêu cầu đăng nhập, phù hợp với demo cục bộ và bảo vệ dữ liệu mã nguồn.")
    heading(doc, "3.8. Kết luận chương", 2)
    para(doc, "Chương 3 đã trình bày yêu cầu, kiến trúc, pipeline, module, thuật toán và thiết kế giao diện của LegacyScope. Giải pháp kết hợp phân tích tĩnh nhẹ, đồ thị phụ thuộc và sinh tài liệu tự động, "
              "đủ để chứng minh tính khả thi của bài toán trích xuất đặc tả kỹ thuật và sơ đồ kiến trúc từ mã nguồn cũ. Chương 4 sẽ trình bày kết quả triển khai và đánh giá trên bộ mẫu.")

    # ================= CHƯƠNG 4 =================
    heading(doc, "CHƯƠNG 4: TRIỂN KHAI VÀ ĐÁNH GIÁ", 1)
    heading(doc, "4.1. Môi trường triển khai", 2)
    table(doc, "Bảng 4.1. Môi trường triển khai", ["Thành phần", "Thông số"], [
        ["Hệ điều hành", "Windows 11"],
        ["Python", "3.13.5"],
        ["Thư viện chính", "FastAPI, Uvicorn, python-docx, Matplotlib, NetworkX, Pillow"],
        ["Giao diện", "HTML5, CSS3, JavaScript thuần"],
        ["Trình duyệt demo", "Google Chrome"],
        ["Cơ sở dữ liệu", "Không sử dụng; kết quả lưu trong thư mục outputs"],
    ], widths=[4.5, 11.8], font_size=9.5)
    para(doc, "Công cụ chạy hoàn toàn cục bộ. Lệnh khởi động là python app.py, sau đó mở http://127.0.0.1:8000. Ngoài ra có thể chạy pipeline trực tiếp bằng Python để sinh kết quả mà không cần giao diện.")
    heading(doc, "4.2. Bộ dữ liệu mẫu", 2)
    para(doc, "Bộ mẫu là hệ thống Quản lý Thư viện được mô phỏng theo phong cách mã nguồn cũ: Java 8, Servlet 3.1, JDBC thuần, MySQL, JSP và Tomcat. Hệ thống có 19 lớp, 163 phương thức, 10 endpoint và 5 bảng dữ liệu. "
              "Mã nguồn được cài đặt có chủ đích một số dấu hiệu nợ kỹ thuật để kiểm chứng khả năng phát hiện của công cụ.")
    table(doc, "Bảng 4.2. Các dấu hiệu legacy được cài đặt trong bộ mẫu", ["Dấu hiệu", "Vị trí", "Mục đích kiểm thử"], [
        ["Mật khẩu CSDL hard-code", "DBUtil.java", "Kiểm tra phát hiện bảo mật"],
        ["SQL nối chuỗi trực tiếp", "BookDAO.java", "Kiểm tra phát hiện SQL Injection"],
        ["Dùng Statement thay PreparedStatement", "BookDAO.java", "Kiểm tra phát hiện API JDBC cũ"],
        ["JSP scriptlet", "book-list.jsp", "Kiểm tra phát hiện trộn giao diện và logic"],
        ["TODO/FIXME", "BookDAO.java, UserDAO.java", "Kiểm tra đếm nợ kỹ thuật"],
        ["Phương thức dài", "BookService.create", "Kiểm tra phát hiện độ phức tạp"],
        ["Không có kiểm thử", "Toàn dự án", "Kiểm tra chỉ số thiếu lưới an toàn"],
    ], widths=[5.2, 5.0, 6.2], font_size=9.3)
    heading(doc, "4.3. Kết quả trích xuất", 2)
    para(doc, f"Sau khi phân tích, LegacyScope phát hiện {m['classes']} lớp, {m['methods']} phương thức, {m['fields']} thuộc tính, {m['endpoints']} endpoint, {m['tables']} bảng dữ liệu và {m['dependencies']} quan hệ phụ thuộc. "
              f"Chỉ số rủi ro là {m['legacy_score']}/100, xếp mức “{m['legacy_grade']}”. Thời gian chạy pipeline đầy đủ trên máy thử nghiệm là {pipeline_seconds:.1f} giây; riêng lõi phân tích là {analysis_seconds:.2f} giây.")
    table(doc, "Bảng 4.3. Chỉ số kết quả phân tích", ["Chỉ số", "Giá trị", "Ghi chú"], [
        ["Số tệp", str(m["files"]), "Bao gồm Java, SQL, JSP và tài liệu"],
        ["Tổng dòng", str(m["loc"]), "LOC toàn bộ tệp được quét"],
        ["Dòng mã", str(m["code_lines"]), "Không tính dòng trống/chú thích"],
        ["Lớp", str(m["classes"]), "Class, interface, enum"],
        ["Phương thức", str(m["methods"]), "Bao gồm constructor, getter/setter"],
        ["Endpoint", str(m["endpoints"]), "GET/POST từ Servlet"],
        ["Bảng dữ liệu", str(m["tables"]), "Từ schema SQL"],
        ["Quan hệ phụ thuộc", str(m["dependencies"]), "Cạnh lớp – lớp"],
        ["Quy tắc nghiệp vụ", str(m.get("business_rules", 0)), "Ứng viên từ điều kiện/Javadoc/FK"],
        ["Chỉ số rủi ro", f"{m['legacy_score']}/100", m["legacy_grade"]],
    ], widths=[5.2, 3.0, 8.1], font_size=9.2)
    figure(doc, "demo_architecture.png", "Hình 4.1. Kiến trúc phân tầng phục hồi từ mã nguồn", 6.1)
    figure(doc, "demo_dependency.png", "Hình 4.2. Bản đồ phụ thuộc giữa các tầng", 6.0)
    para(doc, "Kiến trúc phục hồi cho thấy hệ thống mẫu đi theo mô hình bốn tầng quen thuộc: Servlet tiếp nhận request, Service xử lý nghiệp vụ, DAO truy cập dữ liệu và Model biểu diễn thực thể. "
              "Tầng hạ tầng gồm DBUtil, DateUtil và AuthFilter. Kết quả này khớp với thiết kế kỳ vọng của hệ thống mẫu và được dùng để kiểm chứng quy tắc phân tầng.")
    figure(doc, "demo_class.png", "Hình 4.3. Sơ đồ lớp rút gọn theo tầng kiến trúc", 6.3)
    para(doc, "Sơ đồ lớp hiển thị 19 lớp, số phương thức, số phụ thuộc và quan hệ kế thừa. Các lớp Servlet kế thừa HttpServlet; DAO phụ thuộc DBUtil; Service phụ thuộc DAO và model; "
              "model không phụ thuộc ngược lên tầng trên. Đây là cấu trúc tương đối tốt về hướng phụ thuộc, dù vẫn còn các điểm cần cải thiện về độ dài phương thức và bảo mật.")
    figure(doc, "demo_erd.png", "Hình 4.4. Mô hình dữ liệu quan hệ phục hồi", 6.2)
    para(doc, "Mô hình dữ liệu gồm 5 bảng: categories, books, readers, users, loans. Các quan hệ khóa ngoại được phục hồi chính xác: books.category_id → categories.id; "
              "loans.book_id → books.id; loans.reader_id → readers.id; loans.created_by → users.id. ERD giúp kỹ sư thấy ngay tác động dữ liệu khi sửa một chức năng.")
    figure(doc, "demo_sequence.png", "Hình 4.5. Luồng xử lý tiêu biểu của API mượn sách", 6.1)
    para(doc, "Luồng xử lý mượn sách được dựng từ endpoint POST /loans, đi qua LoanServlet, LoanService, các DAO và MySQL. Sơ đồ này là ví dụ về góc nhìn hành vi có thể sinh từ cấu trúc tĩnh; "
              "trong tương lai có thể mở rộng để chọn bất kỳ endpoint nào và hiển thị call graph chi tiết hơn.")
    figure(doc, "demo_quality.png", "Hình 4.6. Dashboard chất lượng mã nguồn cũ", 6.2)
    para(doc, "Dashboard cho thấy tầng truy cập dữ liệu chiếm nhiều dòng mã nhất (529 dòng), tầng nghiệp vụ có 28 phương thức và tầng mô hình miền có 84 phương thức chủ yếu là getter/setter. "
              "Các vấn đề mức cao gồm SQL nối chuỗi, mật khẩu hard-code và thiếu kiểm thử. Đây là các ưu tiên hợp lý khi bảo trì hệ thống.")
    heading(doc, "4.4. Kết quả sinh đặc tả", 2)
    para(doc, "Ngoài dashboard, LegacyScope sinh tài liệu DOCX gồm 10 phần: thông tin chung, tổng quan kiến trúc, module, lớp, API, dữ liệu, quy tắc nghiệp vụ, đánh giá chất lượng, khuyến nghị và phụ lục tệp. "
              "Tài liệu có mục lục tự động, số trang, bảng và hình. Markdown và JSON được sinh song song để phục vụ lưu trữ và tái sử dụng.")
    table(doc, "Bảng 4.4. Danh sách artifact sinh ra", ["Artifact", "Định dạng", "Mục đích"], [
        ["Dac_ta_ky_thuat.docx", "DOCX", "Báo cáo đặc tả kỹ thuật đầy đủ"],
        ["Dac_ta_ky_thuat.md", "Markdown", "Tài liệu nhẹ cho Git/wiki"],
        ["analysis.json", "JSON", "Mô hình kết quả cho tích hợp"],
        ["architecture_layers.png", "PNG", "Sơ đồ kiến trúc phân tầng"],
        ["dependency_graph.png", "PNG", "Bản đồ phụ thuộc"],
        ["class_diagram.png", "PNG", "Sơ đồ lớp"],
        ["erd.png", "PNG", "Mô hình dữ liệu"],
        ["api_flow.png", "PNG", "Luồng xử lý API"],
        ["quality_dashboard.png", "PNG", "Dashboard chất lượng"],
        ["*.mmd", "Mermaid", "Mã nguồn sơ đồ có thể chỉnh sửa"],
        ["LegacyScope_*.zip", "ZIP", "Gói toàn bộ kết quả"],
    ], widths=[5.5, 2.2, 8.5], font_size=9.0)
    heading(doc, "4.5. Giao diện demo", 2)
    para(doc, "Giao diện được kiểm thử trên Chrome ở kích thước 1440×1200. Trang chủ hiển thị rõ vùng upload, bộ mẫu và hướng dẫn. Trang kết quả giữ nguyên ngữ cảnh dự án, điểm rủi ro và các hành động tải tài liệu.")
    figure(doc, "ui_result.png", "Hình 4.7. Giao diện dashboard kết quả phân tích", 6.3)
    figure(doc, "ui_architecture.png", "Hình 4.8. Tab kiến trúc với sơ đồ phục hồi", 6.3)
    figure(doc, "ui_classes.png", "Hình 4.9. Tab lớp và API", 6.3)
    para(doc, "Các tab giúp tách biệt góc nhìn và giảm quá tải thông tin. Người dùng có thể tìm kiếm trong bảng lớp, API, vấn đề; tải báo cáo Word hoặc gói kết quả ngay từ header. "
              "Khi upload ZIP, giao diện hiển thị tiến trình năm bước để người dùng biết hệ thống đang làm gì.")
    heading(doc, "4.6. Đánh giá chức năng", 2)
    para(doc, "Bộ kiểm thử chức năng được thực hiện thủ công trên bộ mẫu và trên một số tệp ZIP thử nghiệm. Bảng 4.5 tóm tắt các trường hợp kiểm thử chính.")
    table(doc, "Bảng 4.5. Kết quả kiểm thử chức năng", ["Mã", "Tình huống", "Kỳ vọng", "Kết quả"], [
        ["TC-01", "Mở trang chủ", "Hiển thị hero, upload, mẫu", "Đạt"],
        ["TC-02", "Chọn mẫu thư viện", "Phân tích và hiển thị dashboard", "Đạt"],
        ["TC-03", "Upload ZIP hợp lệ", "Giải nén, phân tích, hiển thị kết quả", "Đạt"],
        ["TC-04", "Upload tệp không phải ZIP", "Báo lỗi, không phân tích", "Đạt"],
        ["TC-05", "Upload ZIP quá 30 MB", "Báo lỗi dung lượng", "Đạt"],
        ["TC-06", "Tải báo cáo DOCX", "Tệp mở được, có mục lục/hình/bảng", "Đạt"],
        ["TC-07", "Tải gói ZIP", "Gồm đủ artifact", "Đạt"],
        ["TC-08", "Tìm kiếm lớp/API/vấn đề", "Bảng lọc theo từ khóa", "Đạt"],
        ["TC-09", "Chuyển tab", "Hiển thị đúng nội dung", "Đạt"],
        ["TC-10", "Phân tích lặp lại", "Mỗi lần có mã riêng, không ghi đè", "Đạt"],
    ], widths=[1.5, 5.0, 7.4, 2.3], font_size=9.0)
    para(doc, "Về độ chính xác cấu trúc, trên bộ mẫu, công cụ phát hiện đủ 19/19 lớp, 10/10 endpoint và 5/5 bảng dữ liệu. Phương thức được trích xuất đầy đủ ở mức khai báo; các phương thức ẩn danh hoặc sinh bởi annotation processor không nằm trong phạm vi. "
              "Quy tắc nghiệp vụ sinh ra 28 ứng viên, trong đó 24 quy tắc từ điều kiện/Javadoc và 4 ràng buộc khóa ngoại. Các quy tắc này cần chuyên viên xác nhận trước khi đưa vào tài liệu chính thức.")
    table(doc, "Bảng 4.6. Đối chiếu kết quả với kỳ vọng", ["Hạng mục", "Kỳ vọng", "Phát hiện", "Độ chính xác"], [
        ["Lớp", "19", str(m["classes"]), "100%"],
        ["Endpoint", "10", str(m["endpoints"]), "100%"],
        ["Bảng dữ liệu", "5", str(m["tables"]), "100%"],
        ["Quan hệ khóa ngoại", "4", "4", "100%"],
        ["Phương thức khai báo", str(m["methods"]), str(m["methods"]), "100% (mức khai báo)"],
        ["Quy tắc nghiệp vụ", "28 ứng viên", str(m.get("business_rules", 0)), "Cần xác nhận thủ công"],
    ], widths=[4.3, 3.2, 3.5, 5.3], font_size=9.2)
    para(doc, "Về hiệu năng, thời gian phân tích lõi rất nhỏ so với thời gian sinh sơ đồ và DOCX. Trên máy thử nghiệm, pipeline đầy đủ mất vài giây, phù hợp với demo trực tiếp. "
              "Với dự án lớn hơn, chi phí chủ yếu nằm ở sinh nhiều hình và tài liệu; có thể tối ưu bằng cache hoặc sinh bất đồng bộ.")
    heading(doc, "4.6.1. So sánh với các công cụ hiện có", 3)
    para(doc, "Kết quả của LegacyScope không nhằm cạnh tranh với các công cụ thương mại về độ sâu phân tích. Điểm khác biệt nằm ở quy trình nhẹ, chạy cục bộ, tích hợp sẵn sinh tài liệu tiếng Việt và khả năng tùy biến mẫu báo cáo. "
              "Bảng 4.7 so sánh theo các tiêu chí phù hợp với bối cảnh bài tập lớn.")
    table(doc, "Bảng 4.7. So sánh LegacyScope với một số hướng tiếp cận", ["Tiêu chí", "LegacyScope", "Công cụ thương mại", "Thư viện parser thuần"], [
        ["Chi phí", "Miễn phí, mã nguồn mở", "Cao", "Miễn phí"],
        ["Cài đặt", "Python + pip, chạy local", "Quy trình phức tạp", "Cần lập trình"],
        ["Đầu vào", "Java, SQL, ZIP", "Đa ngôn ngữ", "Tùy parser"],
        ["Sơ đồ kiến trúc", "Có sẵn 6 sơ đồ", "Mạnh", "Không có sẵn"],
        ["Đặc tả DOCX/MD", "Có sẵn", "Hạn chế/tùy chỉnh", "Không có"],
        ["Độ sâu ngữ nghĩa", "Mức cấu trúc", "Cao", "Tùy hiện thực"],
        ["Khả năng giải thích", "Cao, có tệp/dòng", "Trung bình", "Tùy hiện thực"],
    ], widths=[4.0, 4.2, 4.0, 4.2], font_size=9.0)
    para(doc, "Với mục tiêu học tập và demo, sự cân bằng giữa chi phí, thời gian triển khai và giá trị đầu ra là hợp lý. Nếu cần phân tích quy mô công nghiệp, LegacyScope nên được xem là lớp tiền xử lý và sinh tài liệu, "
              "kết hợp với parser mạnh hơn hoặc công cụ chuyên dụng để tăng độ chính xác ngữ nghĩa.")
    heading(doc, "4.7. Thảo luận và hạn chế", 2)
    para(doc, "Kết quả cho thấy cách tiếp cận lai giữa quét cấu trúc và regex đủ hiệu quả cho hệ thống Java Servlet/JDBC cỡ nhỏ. Công cụ phát hiện đúng các tầng, API, bảng và các dấu hiệu nợ kỹ thuật quan trọng, "
              "đồng thời sinh được tài liệu có thể đọc và tái sử dụng. Tuy nhiên, phương pháp này có một số hạn chế cần nêu rõ.")
    bullets(doc, [
        "Không phân tích ngữ nghĩa sâu: công cụ không giải quyết kiểu đầy đủ, không theo dõi luồng dữ liệu liên thủ tục và có thể bỏ sót các lớp sinh tự động.",
        "Bộ phân tích Java dựa trên dấu ngoặc và regex có thể sai với cú pháp hiếm, generic phức tạp, annotation lồng nhau hoặc mã không hợp lệ.",
        "Quy tắc nghiệp vụ là ứng viên, chưa được kiểm chứng với chuyên gia miền; một số điều kiện kỹ thuật có thể bị hiểu nhầm là quy tắc nghiệp vụ.",
        "Chỉ hỗ trợ Java và SQL; chưa hỗ trợ PHP, C#, JavaScript, COBOL hoặc các hệ thống dùng ORM phức tạp.",
        "Sơ đồ là biểu diễn tĩnh, không phản ánh hành vi runtime, tải cao điểm hoặc luồng xử lý bất đồng bộ.",
        "Tài liệu sinh ra theo mẫu, chưa thể thay thế hoàn toàn phân tích của chuyên viên và chưa có kiểm chứng chất lượng tự động.",
    ])
    heading(doc, "4.8. Kết luận chương", 2)
    para(doc, "Chương 4 đã trình bày môi trường, bộ mẫu, kết quả trích xuất, giao diện demo và đánh giá. Công cụ đạt các mục tiêu chức năng, sinh đủ sáu sơ đồ và các tệp đặc tả, "
              "đồng thời chỉ ra được các rủi ro chính của hệ thống mẫu. Các hạn chế đã được nhận diện để làm cơ sở cho hướng phát triển ở chương 5.")

    # ================= CHƯƠNG 5 =================
    heading(doc, "CHƯƠNG 5: KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN", 1)
    heading(doc, "5.1. Kết quả đạt được", 2)
    para(doc, "Đề tài đã hoàn thành việc nghiên cứu cơ sở lý thuyết về mã nguồn cũ, reverse engineering, phân tích tĩnh và phục hồi kiến trúc; thiết kế và triển khai công cụ LegacyScope; "
              "xây dựng bộ mã nguồn mẫu; sinh tự động sáu sơ đồ kiến trúc và đặc tả kỹ thuật; kiểm thử chức năng và đánh giá trên bộ mẫu.")
    bullets(doc, [
        "Công cụ web chạy cục bộ, hỗ trợ chọn mẫu hoặc upload ZIP, không cần đăng nhập, không gửi mã nguồn ra ngoài.",
        "Trích xuất được 19 lớp, 163 phương thức, 10 endpoint, 5 bảng và 28 quy tắc ứng viên trên bộ mẫu.",
        "Sinh sáu sơ đồ PNG, năm tệp Mermaid, DOCX, Markdown, JSON và gói ZIP.",
        "Phát hiện các vấn đề thực tế: SQL nối chuỗi, mật khẩu hard-code, JSP scriptlet, phương thức dài, thiếu kiểm thử.",
        "Dashboard tiếng Việt, có tìm kiếm, tab, tải tài liệu và phản hồi tiến trình.",
    ])
    heading(doc, "5.2. Hạn chế", 2)
    para(doc, "Các hạn chế chính gồm: phạm vi ngôn ngữ hẹp (Java/SQL), phân tích cú pháp nhẹ chưa thay thế parser đầy đủ, quy tắc nghiệp vụ mới ở mức ứng viên, chưa có kiểm thử tự động cho chính công cụ, "
              "và tài liệu sinh ra chưa được đánh giá bởi nhiều chuyên gia. Ngoài ra, công cụ chưa xử lý được các dự án quá lớn hoặc mã nguồn không mã hóa UTF-8 nhất quán.")
    heading(doc, "5.3. Hướng phát triển", 2)
    para(doc, "Trong tương lai, có thể mở rộng theo các hướng sau:")
    bullets(doc, [
        "Tích hợp JavaParser/Spoon hoặc Tree-sitter để tăng độ chính xác cú pháp và hỗ trợ nhiều ngôn ngữ.",
        "Bổ sung phân tích luồng dữ liệu, call graph đầy đủ và phát hiện design pattern.",
        "Tích hợp tùy chọn LLM để sinh mô tả tự nhiên, nhưng vẫn giữ bước kiểm chứng và trích dẫn nguồn.",
        "So sánh hai phiên bản mã nguồn để đánh giá tác động kiến trúc và nợ kỹ thuật theo thời gian.",
        "Xuất trực tiếp sang Confluence, GitLab Wiki, Jira hoặc các công cụ quản lý tài liệu.",
        "Bổ sung kiểm thử tự động, đo coverage và đóng gói CI/CD để công cụ tự kiểm chứng.",
        "Hỗ trợ PHP, C#, JavaScript/TypeScript và các hệ thống dùng ORM/framework phổ biến.",
    ])
    heading(doc, "5.4. Kết luận", 2)
    para(doc, "Bài toán trích xuất đặc tả kỹ thuật và sơ đồ kiến trúc từ mã nguồn cũ là bài toán có ý nghĩa thực tiễn, gắn trực tiếp với bảo trì phần mềm và chuyển đổi hệ thống. "
              "LegacyScope chứng minh rằng một công cụ nhẹ, chạy cục bộ, kết hợp phân tích tĩnh và sinh tài liệu có thể giảm đáng kể công sức đọc hiểu ban đầu, "
              "đồng thời tạo ra tài liệu có cấu trúc để đội ngũ bảo trì tiếp tục xác nhận và bổ sung. Đề tài là bước khởi đầu để phát triển thành một nền tảng phục hồi kiến trúc đầy đủ hơn trong tương lai.")

    # ================= TÀI LIỆU THAM KHẢO =================
    heading(doc, "TÀI LIỆU THAM KHẢO", 1)
    refs = [
        "Feathers, M. (2004). Working Effectively with Legacy Code. Prentice Hall.",
        "Sommerville, I. (2016). Software Engineering (10th ed.). Pearson.",
        "Pressman, R. S., & Maxim, B. R. (2020). Software Engineering: A Practitioner's Approach (9th ed.). McGraw-Hill.",
        "Chikofsky, E. J., & Cross, J. H. (1990). Reverse Engineering and Design Recovery: A Taxonomy. IEEE Software, 7(1), 13–17.",
        "IEEE. (2006). IEEE Standard for Software Maintenance (IEEE Std 14764-2006).",
        "ISO/IEC/IEEE. (2011). Systems and software engineering — Architecture description (ISO/IEC/IEEE 42010:2011).",
        "ISO/IEC/IEEE. (2018). Systems and software engineering — Life cycle processes — Requirements engineering (ISO/IEC/IEEE 29148:2018).",
        "Ducasse, S., & Pollet, D. (2009). Software Architecture Reconstruction: A Process-Oriented Taxonomy. IEEE Transactions on Software Engineering, 35(4), 573–591.",
        "Garcia, J., Popescu, D., Mattmann, C., Medvidovic, N., & Cai, Y. (2013). Enhancing architectural recovery using concerns. Automated Software Engineering.",
        "Bayer, J., Forster, T., Ganesan, D., Girard, J.-F., John, I., Knodel, J., Kolb, R., & Muthig, D. (2006). Definition of Reference Architectures Based on Existing Systems. Fraunhofer IESE.",
        "JavaParser. (n.d.). JavaParser Documentation. https://javaparser.org/",
        "Spoon. (n.d.). Spoon Documentation. https://spoon.gforge.inria.fr/",
        "Mermaid. (n.d.). Mermaid Documentation. https://mermaid.js.org/",
        "NetworkX. (n.d.). NetworkX Documentation. https://networkx.org/",
        "FastAPI. (n.d.). FastAPI Documentation. https://fastapi.tiangolo.com/",
        "python-docx. (n.d.). python-docx Documentation. https://python-docx.readthedocs.io/",
        "OMG. (2017). OMG Unified Modeling Language (UML) Specification, Version 2.5.1.",
        "Brown, S. (2018). The C4 Model for Visualising Software Architecture. https://c4model.com/",
        "Fowler, M. (2018). Refactoring: Improving the Design of Existing Code (2nd ed.). Addison-Wesley.",
        "Martin, R. C. (2017). Clean Architecture: A Craftsman's Guide to Software Structure and Design. Prentice Hall.",
    ]
    for index, ref in enumerate(refs, 1):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.8)
        p.paragraph_format.first_line_indent = Cm(-0.8)
        p.paragraph_format.space_after = Pt(3)
        set_run_font(p.add_run(f"[{index}] "), "Times New Roman", 11.5, True, NAVY)
        set_run_font(p.add_run(ref), "Times New Roman", 11.5, False, INK)

    # ================= PHỤ LỤC =================
    heading(doc, "PHỤ LỤC", 1)
    heading(doc, "A. Hướng dẫn cài đặt và chạy demo", 2)
    para(doc, "Yêu cầu: Python 3.11 trở lên. Cài đặt thư viện bằng lệnh sau:")
    code_block(doc, "cd D:\\Chuyen_de\npython -m pip install -r requirements.txt\npython app.py")
    para(doc, "Mở trình duyệt tại http://127.0.0.1:8000. Chọn mẫu “Hệ thống Quản lý Thư viện” hoặc upload ZIP. Sau khi phân tích, tải báo cáo Word hoặc gói kết quả. "
              "Nếu muốn sinh lại báo cáo và slide, chạy:")
    code_block(doc, "python scripts\\build_report.py\npython scripts\\build_slides.py")
    heading(doc, "B. Cấu trúc thư mục dự án", 2)
    code_block(doc, """D:\\Chuyen_de
├── app.py
├── requirements.txt
├── run_demo.bat
├── legacyscope/
│   ├── analysis.py, scanner.py, diagrams.py, pipeline.py
│   ├── parsers/java_parser.py, sql_parser.py
│   ├── generators/docx_spec.py, markdown_spec.py, json_export.py
│   └── web/index.html, styles.css, app.js
├── sample_legacy/library_legacy/
├── outputs/
├── docs/
│   ├── Bao_cao_Chuyen_de_KTPM.docx
│   ├── Slide_Trinh_bay.pptx
│   └── assets/
├── scripts/
└── config/student.json""", size=7.8)
    heading(doc, "C. Danh sách artifact của lần phân tích mẫu", 2)
    table(doc, "Bảng C.1. Artifact sinh ra cho bộ mẫu", ["Tệp", "Mô tả"], [
        ["Dac_ta_ky_thuat.docx", "Đặc tả kỹ thuật đầy đủ"],
        ["Dac_ta_ky_thuat.md", "Bản Markdown"],
        ["analysis.json", "Mô hình kết quả"],
        ["architecture_layers.png", "Sơ đồ kiến trúc tầng"],
        ["dependency_graph.png", "Sơ đồ phụ thuộc"],
        ["class_diagram.png", "Sơ đồ lớp"],
        ["erd.png", "ERD"],
        ["api_flow.png", "Luồng API"],
        ["quality_dashboard.png", "Dashboard chất lượng"],
        ["LegacyScope_*.zip", "Gói toàn bộ kết quả"],
    ], widths=[6.5, 9.5], font_size=9.0)
    heading(doc, "D. Một phần kết quả JSON", 2)
    code_block(doc, """{
  "analysis_id": "20261126-...",
  "project_name": "Hệ thống Quản lý Thư viện",
  "metrics": {
    "files": 23, "loc": 1843, "classes": 19, "methods": 163,
    "endpoints": 10, "tables": 5, "legacy_score": 75
  },
  "layers": [
    {"key": "presentation", "name": "Giao diện / API", "class_count": 4},
    {"key": "business", "name": "Nghiệp vụ", "class_count": 3}
  ],
  "findings": [
    {"severity": "Cao", "title": "SQL được nối chuỗi trực tiếp"}
  ]
}""", size=7.8)
    heading(doc, "E. Checklist demo trước giảng viên", 2)
    bullets(doc, [
        "Mở terminal, chạy python app.py, kiểm tra http://127.0.0.1:8000/api/health.",
        "Mở trang chủ, giới thiệu 8 nhóm chức năng trong 1 phút.",
        "Chọn mẫu Quản lý Thư viện, quan sát tiến trình 5 bước.",
        "Chỉ vào điểm rủi ro 75/100 và giải thích ba vấn đề mức cao.",
        "Mở tab Kiến trúc, giải thích luồng Servlet → Service → DAO → Model.",
        "Mở tab Dữ liệu, chỉ ERD và quan hệ khóa ngoại.",
        "Mở tab Đặc tả, tải Word và mở mục lục đã cập nhật.",
        "Kết luận: thời gian phân tích, độ chính xác, hạn chế và hướng phát triển.",
    ])

    heading(doc, "F. Kịch bản trình bày 10–12 phút", 2)
    table(doc, "Bảng F.1. Phân bổ thời gian thuyết trình", ["Thời lượng", "Nội dung", "Ghi chú"], [
        ["1 phút", "Giới thiệu bản thân, tên đề tài, lý do chọn", "Nêu vấn đề tài liệu thất lạc"],
        ["2 phút", "Mục tiêu, phạm vi, cơ sở lý thuyết", "Reverse engineering, phân tích tĩnh"],
        ["2 phút", "Kiến trúc và pipeline của LegacyScope", "Dùng hình 3.1, 3.2"],
        ["1 phút", "Thuật toán trích xuất Java/SQL", "Nêu điểm lai parser + regex"],
        ["3 phút", "Demo trực tiếp", "Mẫu thư viện, các tab, tải Word"],
        ["1,5 phút", "Kết quả, đánh giá, hạn chế", "19 lớp, 10 API, 5 bảng, 75/100"],
        ["1 phút", "Kết luận và hướng phát triển", "Mời câu hỏi"],
    ], widths=[3.0, 8.5, 5.0], font_size=9.3)
    para(doc, "Khi trình bày, nên mở sẵn trình duyệt và một cửa sổ File Explorer trỏ đến thư mục outputs để có thể chỉ ra artifact. Nếu thời gian bị rút ngắn, ưu tiên demo mẫu, tab Kiến trúc, tab Dữ liệu và tải báo cáo Word; "
              "phần lý thuyết có thể lướt nhanh bằng các hình minh họa.")

    path = OUT / "Bao_cao_Chuyen_de_KTPM.docx"
    doc.save(path)
    return path, result, pipeline_seconds, analysis_seconds


if __name__ == "__main__":
    path, result, pipeline_seconds, analysis_seconds = build_report()
    print(path)
    print(f"pipeline={pipeline_seconds:.2f}s analysis={analysis_seconds:.2f}s")
    print(f"classes={len(result.classes)} endpoints={len(result.endpoints)} tables={len(result.tables)}")
