from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

from ..models import AnalysisResult

NAVY = RGBColor(0x0F, 0x17, 0x2A)
BLUE = RGBColor(0x25, 0x63, 0xEB)
MUTED = RGBColor(0x64, 0x74, 0x8B)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)


def set_run_font(run, name="Times New Roman", size=12, bold=False, color=None, italic=False):
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


def shade_cell(cell, hex_color: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    tc_pr.append(shd)


def set_cell_margins(cell, top=80, bottom=80, left=100, right=100):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
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


def add_field(paragraph, instruction: str, placeholder: str = ""):
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = instruction
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    fld_text = OxmlElement("w:t")
    fld_text.text = placeholder
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_sep)
    run._r.append(fld_text)
    run._r.append(fld_end)


def add_bottom_border(paragraph, color="2563EB", size="16"):
    p_pr = paragraph._p.get_or_add_pPr()
    border = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), size)
    bottom.set(qn("w:space"), "8")
    bottom.set(qn("w:color"), color)
    border.append(bottom)
    p_pr.append(border)


def configure_styles(doc: Document):
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
    normal.paragraph_format.line_spacing = 1.35
    normal.paragraph_format.space_after = Pt(5)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")

    for name, size, color in (("Heading 1", 18, NAVY), ("Heading 2", 14, BLUE), ("Heading 3", 12, NAVY)):
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
    caption.font.size = Pt(9)
    caption.font.italic = True
    caption.font.color.rgb = MUTED
    caption.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER


def setup_page(doc: Document):
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.2)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.0)
    section.header_distance = Cm(1.0)
    section.footer_distance = Cm(1.0)

    header = section.header
    paragraph = header.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_run_font(paragraph.add_run("LegacyScope  ·  Đặc tả kỹ thuật"), "Arial", 8, color=MUTED)

    footer = section.footer
    paragraph = footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(paragraph.add_run("Trang "), "Arial", 8.5, color=MUTED)
    add_field(paragraph, " PAGE ", "1")
    set_run_font(paragraph.add_run(" / "), "Arial", 8.5, color=MUTED)
    add_field(paragraph, " NUMPAGES ", "1")


def add_cover(doc: Document, result: AnalysisResult):
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(28)
    set_run_font(paragraph.add_run("TRƯỜNG ĐẠI HỌC THỦY LỢI"), "Times New Roman", 13, True, NAVY)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(p.add_run("KHOA CÔNG NGHỆ THÔNG TIN"), "Times New Roman", 12, True, NAVY)

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(28)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(p.add_run("BÁO CÁO ĐẶC TẢ KỸ THUẬT"), "Arial", 16, True, BLUE)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(p.add_run("HỆ THỐNG ĐƯỢC PHỤC HỒI TỰ ĐỘNG"), "Arial", 11, True, MUTED)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(18)
    set_run_font(p.add_run(result.project_name.upper()), "Arial", 22, True, NAVY)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_bottom_border(p, "2563EB", "18")

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(12)
    set_run_font(p.add_run("Tài liệu được trích xuất tự động từ mã nguồn cũ bằng LegacyScope"), "Times New Roman", 12, italic=True, color=MUTED)

    doc.add_paragraph()
    info = [
        ("Mã phân tích", result.analysis_id),
        ("Thời điểm sinh", result.generated_at),
        ("Nguồn mã nguồn", result.root),
        ("Số lớp phát hiện", str(result.metrics["classes"])),
        ("Số API phát hiện", str(result.metrics["endpoints"])),
        ("Số bảng dữ liệu", str(result.metrics["tables"])),
    ]
    table = doc.add_table(rows=0, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for label, value in info:
        row = table.add_row().cells
        row[0].width = Cm(4.2)
        row[1].width = Cm(9.5)
        p0 = row[0].paragraphs[0]
        set_run_font(p0.add_run(label), "Arial", 9, True, MUTED)
        p1 = row[1].paragraphs[0]
        set_run_font(p1.add_run(value), "Arial", 9, color=NAVY)
        set_cell_margins(row[0])
        set_cell_margins(row[1])

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(30)
    set_run_font(p.add_run("Hà Nội, tháng 11 năm 2026"), "Times New Roman", 11, italic=True, color=MUTED)
    doc.add_page_break()


def add_toc(doc: Document):
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_before = Pt(6)
    set_run_font(title.add_run("MỤC LỤC"), "Arial", 17, True, NAVY)
    p = doc.add_paragraph()
    add_field(p, ' TOC \\o "1-3" \\h \\z \\u ', "Nhấn F9 để cập nhật mục lục")
    doc.add_page_break()


def add_table(doc: Document, headers, rows, widths=None, font_size=8.5, header_color="0F172A"):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    header_cells = table.rows[0].cells
    for index, header in enumerate(headers):
        cell = header_cells[index]
        shade_cell(cell, header_color)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        set_cell_margins(cell)
        paragraph = cell.paragraphs[0]
        run = paragraph.add_run(str(header))
        set_run_font(run, "Arial", font_size, True, WHITE)
        if widths:
            cell.width = Cm(widths[index])
    for row_index, row in enumerate(rows):
        cells = table.add_row().cells
        for index, value in enumerate(row):
            cell = cells[index]
            if row_index % 2 == 1:
                shade_cell(cell, "F1F5F9")
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_margins(cell)
            paragraph = cell.paragraphs[0]
            run = paragraph.add_run(str(value))
            set_run_font(run, "Times New Roman", font_size, color=RGBColor(0x1E, 0x29, 0x3B))
            if widths:
                cell.width = Cm(widths[index])
    doc.add_paragraph()
    return table


def add_figure(doc: Document, image_path: str, caption: str, width=6.4):
    path = Path(image_path)
    if not path.exists():
        return
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    run.add_picture(str(path), width=Inches(width))
    cap = doc.add_paragraph(caption, style="Caption")
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER


def add_body(doc: Document, text: str):
    paragraph = doc.add_paragraph(text)
    paragraph.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    paragraph.paragraph_format.first_line_indent = Cm(0.8)


def add_bullets(doc: Document, items: list[str]):
    for item in items:
        paragraph = doc.add_paragraph(item, style="List Bullet")
        paragraph.paragraph_format.space_after = Pt(2)


def generate_docx(result: AnalysisResult, output: Path) -> str:
    output.mkdir(parents=True, exist_ok=True)
    doc = Document()
    setup_page(doc)
    configure_styles(doc)
    add_cover(doc, result)
    add_toc(doc)

    m = result.metrics
    add_body(doc, f"Tài liệu này mô tả hệ thống {result.project_name} được phục hồi từ mã nguồn cũ bằng phương pháp phân tích tĩnh. "
                  f"Kết quả bao gồm kiến trúc phân tầng, danh mục lớp, API, mô hình dữ liệu, quy tắc nghiệp vụ và các chỉ báo chất lượng. "
                  f"Đây là đầu vào cho hoạt động bảo trì, đánh giá tác động và chuyển đổi hệ thống.")

    doc.add_heading("1. Thông tin chung", level=1)
    add_table(doc, ["Thuộc tính", "Giá trị"], [
        ["Tên dự án", result.project_name],
        ["Mã phân tích", result.analysis_id],
        ["Thời điểm sinh", result.generated_at],
        ["Đường dẫn nguồn", result.root],
        ["Số tệp được quét", str(m["files"])],
        ["Tổng dòng mã", str(m["loc"])],
        ["Dòng mã thực tế", str(m["code_lines"])],
        ["Dòng chú thích", str(m["comment_lines"])],
        ["Số lớp", str(m["classes"])],
        ["Số phương thức", str(m["methods"])],
        ["Số endpoint", str(m["endpoints"])],
        ["Số bảng dữ liệu", str(m["tables"])],
        ["Số quy tắc nghiệp vụ", str(m.get("business_rules", 0))],
        ["Chỉ số rủi ro mã nguồn cũ", f"{m['legacy_score']}/100 ({m['legacy_grade']})"],
    ], widths=[5.0, 11.0])

    doc.add_heading("2. Tổng quan kiến trúc", level=1)
    add_body(doc, result.overview.get("summary", ""))
    add_body(doc, "Các lớp được phân loại tự động theo package và đường dẫn tệp. Quy tắc phân tầng ưu tiên các dấu hiệu "
                  "controller/servlet/web cho tầng giao diện, service/business cho tầng nghiệp vụ, dao/repository cho tầng truy cập dữ liệu, "
                  "model/entity/domain cho mô hình miền và util/config/common/filter cho hạ tầng dùng chung.")
    add_table(doc, ["Tầng", "Số lớp", "Phương thức", "Dòng mã", "Mô tả"], [
        [layer.name, str(layer.class_count), str(layer.methods), str(layer.loc), layer.description]
        for layer in result.layers
    ], widths=[3.6, 1.6, 1.9, 1.7, 7.2])
    add_figure(doc, result.diagrams.get("architecture", ""), "Hình 1. Kiến trúc phân tầng được phục hồi từ mã nguồn")
    add_figure(doc, result.diagrams.get("dependency", ""), "Hình 2. Bản đồ phụ thuộc giữa các tầng", width=6.1)

    doc.add_heading("3. Danh mục module", level=1)
    add_body(doc, "Bảng dưới đây tóm tắt các module theo tầng, các lớp tiêu biểu và trách nhiệm chính được suy ra từ vị trí, "
                  "tên lớp và quan hệ phụ thuộc.")
    add_table(doc, ["Tầng", "Lớp tiêu biểu", "Trách nhiệm"], [
        [layer.name, ", ".join(layer.classes[:7]), layer.description]
        for layer in result.layers
    ], widths=[4.0, 7.0, 5.0])

    doc.add_heading("4. Danh mục lớp", level=1)
    add_body(doc, "Danh mục lớp là kết quả phân tích cấu trúc tệp Java: package, loại lớp, số phương thức, số thuộc tính, "
                  "số phụ thuộc trực tiếp và vị trí tệp. Số phụ thuộc được đếm từ import, kiểu thuộc tính, tham số, giá trị trả về và lời gọi hàm.")
    class_rows = []
    for cls in result.classes:
        deps = sum(1 for d in result.dependencies if d.source == cls.name)
        class_rows.append([cls.name, cls.layer, cls.kind, str(len(cls.methods)), str(len(cls.fields)), str(deps), str(cls.loc), cls.file])
    add_table(doc, ["Lớp", "Tầng", "Loại", "Phương thức", "Thuộc tính", "Phụ thuộc", "Dòng", "Tệp"], class_rows,
              widths=[3.0, 2.5, 1.4, 1.5, 1.6, 1.6, 1.3, 4.1], font_size=7.6)
    add_figure(doc, result.diagrams.get("class", ""), "Hình 3. Sơ đồ lớp rút gọn theo tầng kiến trúc", width=6.5)

    doc.add_heading("5. Danh mục API", level=1)
    if result.endpoints:
        add_body(doc, "Các endpoint được trích xuất từ annotation Servlet hoặc Spring MVC. Với Servlet, phương thức doGet/doPost "
                      "được ánh xạ tương ứng thành GET/POST; đường dẫn lấy từ @WebServlet.")
        add_table(doc, ["HTTP", "Đường dẫn", "Handler", "Lớp", "Tệp", "Dòng"], [
            [e.http_method, e.path, e.handler, e.class_name, e.file, str(e.line)]
            for e in result.endpoints
        ], widths=[1.5, 3.2, 2.5, 2.8, 4.3, 1.2], font_size=7.8)
        add_figure(doc, result.diagrams.get("sequence", ""), "Hình 4. Luồng xử lý tiêu biểu của API mượn sách", width=6.2)
    else:
        add_body(doc, "Không phát hiện endpoint trong mã nguồn.")

    doc.add_heading("6. Mô hình dữ liệu", level=1)
    if result.tables:
        add_body(doc, "Mô hình dữ liệu được phục hồi từ các câu lệnh CREATE TABLE và các tham chiếu SQL trong mã Java. "
                      "Các quan hệ khóa ngoại được dùng để dựng sơ đồ ERD.")
        add_figure(doc, result.diagrams.get("erd", ""), "Hình 5. Mô hình dữ liệu quan hệ", width=6.5)
        add_table(doc, ["Bảng", "Số cột", "Khóa chính", "Khóa ngoại", "Nguồn"], [
            [t.name, str(len(t.columns)), t.primary_key or "-", "; ".join(t.foreign_keys) or "-", t.source]
            for t in result.tables
        ], widths=[2.7, 1.5, 2.0, 5.4, 4.0], font_size=7.8)
    else:
        add_body(doc, "Không phát hiện bảng dữ liệu.")

    doc.add_heading("7. Quy tắc nghiệp vụ", level=1)
    if result.business_rules:
        add_body(doc, "Các quy tắc dưới đây được trích xuất từ điều kiện kiểm tra và thông báo trong phương thức nghiệp vụ, "
                      "Javadoc và ràng buộc khóa ngoại. Công cụ không diễn giải toàn bộ ngữ nghĩa nghiệp vụ mà chỉ cung cấp "
                      "danh sách ứng viên để chuyên viên phân tích xác nhận.")
        add_table(doc, ["STT", "Vị trí", "Điều kiện", "Hành vi / thông báo"], [
            [str(i + 1), rule.title, rule.condition, rule.action]
            for i, rule in enumerate(result.business_rules)
        ], widths=[1.0, 3.4, 6.3, 5.4], font_size=7.6)
    else:
        add_body(doc, "Không phát hiện quy tắc nghiệp vụ từ mã nguồn.")

    doc.add_heading("8. Đánh giá chất lượng", level=1)
    add_body(doc, f"Chỉ số rủi ro mã nguồn cũ được tính theo trọng số của TODO/FIXME, chu trình phụ thuộc, phương thức dài, "
                  f"phát hiện bảo mật và việc thiếu kiểm thử. Giá trị hiện tại là {m['legacy_score']}/100, xếp mức "
                  f"“{m['legacy_grade']}”. Điểm càng cao thể hiện mức độ cần can thiệp càng lớn.")
    add_figure(doc, result.diagrams.get("quality", ""), "Hình 6. Bảng điều khiển chất lượng mã nguồn cũ", width=6.3)
    add_table(doc, ["Chỉ số", "Giá trị"], [
        ["Độ phức tạp trung bình", str(m["avg_complexity"])],
        ["Độ phức tạp lớn nhất", str(m["max_complexity"])],
        ["Phương thức dài/phức tạp", str(m["long_methods"])],
        ["TODO/FIXME", str(m["todos"])],
        ["Chu trình phụ thuộc", str(m["cycles"])],
        ["Vấn đề mức cao", str(m["findings_high"])],
        ["Vấn đề mức trung bình", str(m["findings_medium"])],
        ["Kiểm thử tự động", "Có" if m["has_tests"] else "Không"],
    ], widths=[6.0, 4.0])
    add_table(doc, ["Mức độ", "Nhóm", "Vấn đề", "Tệp"], [
        [f.severity, f.category, f.title, f.file or "-"]
        for f in result.findings
    ], widths=[1.8, 2.5, 8.2, 3.5], font_size=7.8)

    doc.add_heading("9. Khuyến nghị bảo trì", level=1)
    add_bullets(doc, result.overview.get("recommendations", []))

    doc.add_heading("10. Phụ lục tệp", level=1)
    add_table(doc, ["Tệp", "Ngôn ngữ", "Dòng", "Code", "Comment", "TODO"], [
        [f.path, f.language, str(f.loc), str(f.code_lines), str(f.comment_lines), str(f.todos)]
        for f in result.files
    ], widths=[6.8, 2.2, 1.3, 1.3, 1.6, 1.3], font_size=7.4)

    path = output / "Dac_ta_ky_thuat.docx"
    doc.save(path)
    return str(path)
