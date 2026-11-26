# Hệ thống Quản lý Thư viện (phiên bản cũ)

Đây là bộ mã nguồn mẫu mô phỏng một hệ thống quản lý thư viện được xây dựng từ năm 2014,
vẫn đang vận hành nhưng gần như không còn tài liệu thiết kế.

## Công nghệ

- Java 8, Servlet 3.1, JSP
- JDBC thuần, không ORM
- MySQL 5.6
- Triển khai trên Apache Tomcat 7

## Tình trạng

- Không có tài liệu kiến trúc và tài liệu API.
- Nhiều đoạn SQL nối chuỗi trực tiếp, tiềm ẩn lỗi bảo mật.
- Một số lớp DAO và Service có phương thức quá dài.
- Có các ghi chú TODO/FIXME từ nhiều năm trước.
- Không có kiểm thử tự động.

## Mục đích

Bộ mã nguồn này được dùng làm đầu vào cho công cụ **LegacyScope** nhằm:
1. Trích xuất các lớp, phương thức, phụ thuộc và API.
2. Phục hồi sơ đồ kiến trúc phân tầng và mô hình dữ liệu.
3. Sinh đặc tả kỹ thuật phục vụ bảo trì và chuyển đổi hệ thống.
