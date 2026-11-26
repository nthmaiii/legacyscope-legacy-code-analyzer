package vn.edu.library.service;

import vn.edu.library.dao.BookDAO;
import vn.edu.library.dao.LoanDAO;
import vn.edu.library.dao.ReaderDAO;
import vn.edu.library.model.Book;
import vn.edu.library.model.Loan;
import vn.edu.library.model.Reader;
import vn.edu.library.util.DateUtil;

import java.util.Calendar;
import java.util.Date;
import java.util.List;

public class LoanService {
    private LoanDAO loanDAO = new LoanDAO();
    private BookDAO bookDAO = new BookDAO();
    private ReaderDAO readerDAO = new ReaderDAO();

    public List<Loan> findAll() {
        return loanDAO.findAll();
    }

    public Loan findById(int id) {
        return loanDAO.findById(id);
    }

    public List<Loan> findBorrowingByReader(int readerId) {
        return loanDAO.findBorrowingByReader(readerId);
    }

    public List<Loan> findOverdue() {
        return loanDAO.findOverdue(new Date());
    }

    /**
     * Nghiệp vụ mượn sách:
     * - Bạn đọc phải đang hoạt động.
     * - Sách phải còn khả dụng.
     * - Mỗi bạn đọc tối đa 3 cuốn đang mượn.
     * - Thời hạn mượn mặc định 14 ngày.
     */
    public String borrowBook(int bookId, int readerId, int createdBy) {
        Book book = bookDAO.findById(bookId);
        if (book == null) {
            return "Sách không tồn tại";
        }
        Reader reader = readerDAO.findById(readerId);
        if (reader == null) {
            return "Bạn đọc không tồn tại";
        }
        if (!"ACTIVE".equals(reader.getStatus())) {
            return "Tài khoản bạn đọc đang bị khóa";
        }
        if (!book.isAvailable()) {
            return "Sách hiện không còn khả dụng";
        }
        List<Loan> currentLoans = loanDAO.findBorrowingByReader(readerId);
        if (currentLoans.size() >= 3) {
            return "Bạn đọc đã mượn tối đa 3 cuốn sách";
        }
        Date now = new Date();
        Date dueDate = DateUtil.addDays(now, 14);
        Loan loan = new Loan(bookId, readerId, createdBy, now, dueDate);
        int loanId = loanDAO.create(loan);
        if (loanId <= 0) {
            return "Không thể tạo phiếu mượn";
        }
        if (!bookDAO.update(bookAfterBorrow(book))) {
            return "Đã tạo phiếu nhưng không cập nhật được số lượng sách";
        }
        return "Mượn sách thành công. Hạn trả: " + DateUtil.format(dueDate);
    }

    public String returnBook(int loanId, int readerId) {
        Loan loan = loanDAO.findById(loanId);
        if (loan == null) {
            return "Phiếu mượn không tồn tại";
        }
        if (loan.getReaderId() != readerId) {
            return "Phiếu mượn không thuộc bạn đọc này";
        }
        if ("RETURNED".equals(loan.getStatus())) {
            return "Sách đã được trả trước đó";
        }
        Date now = new Date();
        double fine = loanDAO.calculateFine(loan.getDueDate(), now);
        boolean updated = loanDAO.markReturned(loanId, now, fine);
        if (!updated) {
            return "Không thể cập nhật phiếu trả";
        }
        Book book = bookDAO.findById(loan.getBookId());
        if (book != null) {
            book.setAvailable(Math.min(book.getAvailable() + 1, book.getQuantity()));
            bookDAO.update(book);
        }
        if (fine > 0) {
            return "Trả sách thành công. Tiền phạt: " + (long) fine + " đồng";
        }
        return "Trả sách thành công";
    }

    public double calculateFine(int loanId) {
        Loan loan = loanDAO.findById(loanId);
        if (loan == null) {
            return 0;
        }
        return loanDAO.calculateFine(loan.getDueDate(), new Date());
    }

    public long daysRemaining(Loan loan) {
        if (loan == null || loan.getDueDate() == null) {
            return 0;
        }
        long days = DateUtil.daysBetween(new Date(), loan.getDueDate());
        return Math.max(0, days);
    }

    private Book bookAfterBorrow(Book book) {
        int available = book.getAvailable() - 1;
        if (available < 0) {
            available = 0;
        }
        book.setAvailable(available);
        return book;
    }
}
