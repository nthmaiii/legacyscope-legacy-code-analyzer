package vn.edu.library.service;

import vn.edu.library.dao.BookDAO;
import vn.edu.library.model.Book;

import java.util.ArrayList;
import java.util.List;

public class BookService {
    private BookDAO bookDAO = new BookDAO();

    public List<Book> findAll() {
        return bookDAO.findAll();
    }

    public List<Book> search(String keyword) {
        if (keyword == null || keyword.trim().isEmpty()) {
            return bookDAO.findAll();
        }
        return bookDAO.searchByTitle(keyword.trim());
    }

    public Book findById(int id) {
        if (id <= 0) {
            return null;
        }
        return bookDAO.findById(id);
    }

    public String create(Book book) {
        List<String> errors = new ArrayList<String>();
        if (book == null) {
            return "Dữ liệu sách không hợp lệ";
        }
        if (book.getIsbn() == null || book.getIsbn().trim().isEmpty()) {
            errors.add("ISBN không được để trống");
        }
        if (book.getTitle() == null || book.getTitle().trim().isEmpty()) {
            errors.add("Tên sách không được để trống");
        }
        if (book.getQuantity() <= 0) {
            errors.add("Số lượng phải lớn hơn 0");
        }
        if (book.getAvailable() < 0 || book.getAvailable() > book.getQuantity()) {
            errors.add("Số lượng khả dụng không hợp lệ");
        }
        if (book.getStatus() == null) {
            book.setStatus("ACTIVE");
        }
        if (!errors.isEmpty()) {
            return join(errors);
        }
        int id = bookDAO.insert(book);
        if (id > 0) {
            return "Thêm sách thành công";
        }
        return "Không thể thêm sách";
    }

    public String update(Book book) {
        if (book == null || book.getId() <= 0) {
            return "Sách không tồn tại";
        }
        if (book.getTitle() == null || book.getTitle().trim().isEmpty()) {
            return "Tên sách không được để trống";
        }
        if (book.getQuantity() < 0 || book.getAvailable() < 0 || book.getAvailable() > book.getQuantity()) {
            return "Số lượng không hợp lệ";
        }
        if (bookDAO.update(book)) {
            return "Cập nhật sách thành công";
        }
        return "Cập nhật sách thất bại";
    }

    public String delete(int id) {
        Book book = bookDAO.findById(id);
        if (book == null) {
            return "Sách không tồn tại";
        }
        int borrowing = bookDAO.countBorrowingByBook(id);
        if (borrowing > 0) {
            return "Không thể xóa sách đang được mượn";
        }
        if (bookDAO.delete(id)) {
            return "Xóa sách thành công";
        }
        return "Xóa sách thất bại";
    }

    public boolean decreaseAvailable(int bookId) {
        Book book = bookDAO.findById(bookId);
        if (book == null) {
            return false;
        }
        if (book.getAvailable() <= 0) {
            return false;
        }
        book.setAvailable(book.getAvailable() - 1);
        return bookDAO.update(book);
    }

    public boolean increaseAvailable(int bookId) {
        Book book = bookDAO.findById(bookId);
        if (book == null) {
            return false;
        }
        if (book.getAvailable() < book.getQuantity()) {
            book.setAvailable(book.getAvailable() + 1);
            return bookDAO.update(book);
        }
        return false;
    }

    private String join(List<String> errors) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < errors.size(); i++) {
            if (i > 0) {
                builder.append("; ");
            }
            builder.append(errors.get(i));
        }
        return builder.toString();
    }
}
