package vn.edu.library.service;

import vn.edu.library.dao.ReaderDAO;
import vn.edu.library.model.Reader;

import java.util.List;

public class ReaderService {
    private ReaderDAO readerDAO = new ReaderDAO();

    public List<Reader> findAll() {
        return readerDAO.findAll();
    }

    public Reader findById(int id) {
        return readerDAO.findById(id);
    }

    public String create(Reader reader) {
        if (reader == null) {
            return "Dữ liệu bạn đọc không hợp lệ";
        }
        if (reader.getCode() == null || reader.getCode().trim().isEmpty()) {
            return "Mã bạn đọc không được để trống";
        }
        if (reader.getFullName() == null || reader.getFullName().trim().isEmpty()) {
            return "Họ tên không được để trống";
        }
        if (reader.getPhone() == null || reader.getPhone().length() < 10) {
            return "Số điện thoại không hợp lệ";
        }
        if (readerDAO.findByCode(reader.getCode()) != null) {
            return "Mã bạn đọc đã tồn tại";
        }
        reader.setStatus("ACTIVE");
        int id = readerDAO.insert(reader);
        return id > 0 ? "Thêm bạn đọc thành công" : "Thêm bạn đọc thất bại";
    }

    public String update(Reader reader) {
        if (reader == null || reader.getId() <= 0) {
            return "Bạn đọc không tồn tại";
        }
        if (reader.getFullName() == null || reader.getFullName().trim().isEmpty()) {
            return "Họ tên không được để trống";
        }
        if (readerDAO.update(reader)) {
            return "Cập nhật bạn đọc thành công";
        }
        return "Cập nhật bạn đọc thất bại";
    }

    public String delete(int id) {
        if (id <= 0) {
            return "Bạn đọc không hợp lệ";
        }
        if (readerDAO.delete(id)) {
            return "Xóa bạn đọc thành công";
        }
        return "Xóa bạn đọc thất bại";
    }
}
