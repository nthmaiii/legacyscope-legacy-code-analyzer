package vn.edu.library.dao;

import vn.edu.library.model.Loan;
import vn.edu.library.util.DBUtil;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

public class LoanDAO {

    public int create(Loan loan) {
        String sql = "INSERT INTO loans (book_id, reader_id, created_by, borrow_date, due_date, status, fine_amount) VALUES (?, ?, ?, ?, ?, ?, ?)";
        Connection connection = null;
        PreparedStatement statement = null;
        try {
            connection = DBUtil.getConnection();
            statement = connection.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS);
            statement.setInt(1, loan.getBookId());
            statement.setInt(2, loan.getReaderId());
            statement.setInt(3, loan.getCreatedBy());
            statement.setTimestamp(4, new java.sql.Timestamp(loan.getBorrowDate().getTime()));
            statement.setTimestamp(5, new java.sql.Timestamp(loan.getDueDate().getTime()));
            statement.setString(6, loan.getStatus());
            statement.setDouble(7, loan.getFineAmount());
            statement.executeUpdate();
            ResultSet keys = statement.getGeneratedKeys();
            if (keys.next()) {
                return keys.getInt(1);
            }
        } catch (SQLException e) {
            e.printStackTrace();
        } finally {
            DBUtil.close(connection, statement);
        }
        return 0;
    }

    public Loan findById(int id) {
        String sql = "SELECT * FROM loans WHERE id = ?";
        Connection connection = null;
        PreparedStatement statement = null;
        ResultSet resultSet = null;
        try {
            connection = DBUtil.getConnection();
            statement = connection.prepareStatement(sql);
            statement.setInt(1, id);
            resultSet = statement.executeQuery();
            if (resultSet.next()) {
                return map(resultSet);
            }
        } catch (SQLException e) {
            e.printStackTrace();
        } finally {
            DBUtil.close(connection, statement, resultSet);
        }
        return null;
    }

    public List<Loan> findBorrowingByReader(int readerId) {
        List<Loan> loans = new ArrayList<Loan>();
        String sql = "SELECT * FROM loans WHERE reader_id = ? AND status = 'BORROWING' ORDER BY due_date";
        Connection connection = null;
        PreparedStatement statement = null;
        ResultSet resultSet = null;
        try {
            connection = DBUtil.getConnection();
            statement = connection.prepareStatement(sql);
            statement.setInt(1, readerId);
            resultSet = statement.executeQuery();
            while (resultSet.next()) {
                loans.add(map(resultSet));
            }
        } catch (SQLException e) {
            e.printStackTrace();
        } finally {
            DBUtil.close(connection, statement, resultSet);
        }
        return loans;
    }

    public List<Loan> findOverdue(Date today) {
        List<Loan> loans = new ArrayList<Loan>();
        String sql = "SELECT * FROM loans WHERE status = 'BORROWING' AND due_date < ?";
        Connection connection = null;
        PreparedStatement statement = null;
        ResultSet resultSet = null;
        try {
            connection = DBUtil.getConnection();
            statement = connection.prepareStatement(sql);
            statement.setTimestamp(1, new java.sql.Timestamp(today.getTime()));
            resultSet = statement.executeQuery();
            while (resultSet.next()) {
                loans.add(map(resultSet));
            }
        } catch (SQLException e) {
            e.printStackTrace();
        } finally {
            DBUtil.close(connection, statement, resultSet);
        }
        return loans;
    }

    public boolean markReturned(int loanId, Date returnDate, double fineAmount) {
        String sql = "UPDATE loans SET return_date = ?, status = 'RETURNED', fine_amount = ? WHERE id = ? AND status = 'BORROWING'";
        Connection connection = null;
        PreparedStatement statement = null;
        try {
            connection = DBUtil.getConnection();
            statement = connection.prepareStatement(sql);
            statement.setTimestamp(1, new java.sql.Timestamp(returnDate.getTime()));
            statement.setDouble(2, fineAmount);
            statement.setInt(3, loanId);
            return statement.executeUpdate() > 0;
        } catch (SQLException e) {
            e.printStackTrace();
        } finally {
            DBUtil.close(connection, statement);
        }
        return false;
    }

    public double calculateFine(Date dueDate, Date returnDate) {
        if (returnDate == null || !returnDate.after(dueDate)) {
            return 0;
        }
        long diff = returnDate.getTime() - dueDate.getTime();
        long days = diff / (24 * 60 * 60 * 1000);
        if (days <= 0) {
            days = 1;
        }
        return days * 5000;
    }

    public List<Loan> findAll() {
        List<Loan> loans = new ArrayList<Loan>();
        String sql = "SELECT l.*, b.title AS book_title, r.full_name AS reader_name FROM loans l JOIN books b ON l.book_id = b.id JOIN readers r ON l.reader_id = r.id ORDER BY l.borrow_date DESC";
        Connection connection = null;
        PreparedStatement statement = null;
        ResultSet resultSet = null;
        try {
            connection = DBUtil.getConnection();
            statement = connection.prepareStatement(sql);
            resultSet = statement.executeQuery();
            while (resultSet.next()) {
                loans.add(map(resultSet));
            }
        } catch (SQLException e) {
            e.printStackTrace();
        } finally {
            DBUtil.close(connection, statement, resultSet);
        }
        return loans;
    }

    private Loan map(ResultSet resultSet) throws SQLException {
        Loan loan = new Loan();
        loan.setId(resultSet.getInt("id"));
        loan.setBookId(resultSet.getInt("book_id"));
        loan.setReaderId(resultSet.getInt("reader_id"));
        loan.setCreatedBy(resultSet.getInt("created_by"));
        loan.setBorrowDate(resultSet.getTimestamp("borrow_date"));
        loan.setDueDate(resultSet.getTimestamp("due_date"));
        loan.setReturnDate(resultSet.getTimestamp("return_date"));
        loan.setStatus(resultSet.getString("status"));
        loan.setFineAmount(resultSet.getDouble("fine_amount"));
        return loan;
    }
}
