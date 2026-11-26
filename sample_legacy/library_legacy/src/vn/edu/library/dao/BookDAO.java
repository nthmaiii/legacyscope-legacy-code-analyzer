package vn.edu.library.dao;

import vn.edu.library.model.Book;
import vn.edu.library.util.DBUtil;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;

public class BookDAO {

    public List<Book> findAll() {
        List<Book> books = new ArrayList<Book>();
        String sql = "SELECT id, isbn, title, author, category_id, quantity, available, status, created_at FROM books ORDER BY title";
        Connection connection = null;
        PreparedStatement statement = null;
        ResultSet resultSet = null;
        try {
            connection = DBUtil.getConnection();
            statement = connection.prepareStatement(sql);
            resultSet = statement.executeQuery();
            while (resultSet.next()) {
                books.add(map(resultSet));
            }
        } catch (SQLException e) {
            e.printStackTrace();
        } finally {
            DBUtil.close(connection, statement, resultSet);
        }
        return books;
    }

    public Book findById(int id) {
        String sql = "SELECT * FROM books WHERE id = ?";
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

    public List<Book> searchByTitle(String keyword) {
        List<Book> books = new ArrayList<Book>();
        // FIXME: nối chuỗi trực tiếp, cần chuyển sang PreparedStatement
        String sql = "SELECT * FROM books WHERE title LIKE '%" + keyword + "%' OR author LIKE '%" + keyword + "%'";
        Connection connection = null;
        Statement statement = null;
        ResultSet resultSet = null;
        try {
            connection = DBUtil.getConnection();
            statement = connection.createStatement();
            resultSet = statement.executeQuery(sql);
            while (resultSet.next()) {
                books.add(map(resultSet));
            }
        } catch (SQLException e) {
            e.printStackTrace();
        } finally {
            DBUtil.close(connection, statement, resultSet);
        }
        return books;
    }

    public int insert(Book book) {
        String sql = "INSERT INTO books (isbn, title, author, category_id, quantity, available, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, NOW())";
        Connection connection = null;
        PreparedStatement statement = null;
        try {
            connection = DBUtil.getConnection();
            statement = connection.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS);
            statement.setString(1, book.getIsbn());
            statement.setString(2, book.getTitle());
            statement.setString(3, book.getAuthor());
            statement.setInt(4, book.getCategoryId());
            statement.setInt(5, book.getQuantity());
            statement.setInt(6, book.getAvailable());
            statement.setString(7, book.getStatus());
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

    public boolean update(Book book) {
        String sql = "UPDATE books SET isbn = ?, title = ?, author = ?, category_id = ?, quantity = ?, available = ?, status = ? WHERE id = ?";
        Connection connection = null;
        PreparedStatement statement = null;
        try {
            connection = DBUtil.getConnection();
            statement = connection.prepareStatement(sql);
            statement.setString(1, book.getIsbn());
            statement.setString(2, book.getTitle());
            statement.setString(3, book.getAuthor());
            statement.setInt(4, book.getCategoryId());
            statement.setInt(5, book.getQuantity());
            statement.setInt(6, book.getAvailable());
            statement.setString(7, book.getStatus());
            statement.setInt(8, book.getId());
            return statement.executeUpdate() > 0;
        } catch (SQLException e) {
            e.printStackTrace();
        } finally {
            DBUtil.close(connection, statement);
        }
        return false;
    }

    public boolean delete(int id) {
        String sql = "DELETE FROM books WHERE id = ?";
        Connection connection = null;
        PreparedStatement statement = null;
        try {
            connection = DBUtil.getConnection();
            statement = connection.prepareStatement(sql);
            statement.setInt(1, id);
            return statement.executeUpdate() > 0;
        } catch (SQLException e) {
            e.printStackTrace();
        } finally {
            DBUtil.close(connection, statement);
        }
        return false;
    }

    public int countBorrowingByBook(int bookId) {
        String sql = "SELECT COUNT(*) FROM loans WHERE book_id = ? AND status = 'BORROWING'";
        Connection connection = null;
        PreparedStatement statement = null;
        ResultSet resultSet = null;
        try {
            connection = DBUtil.getConnection();
            statement = connection.prepareStatement(sql);
            statement.setInt(1, bookId);
            resultSet = statement.executeQuery();
            if (resultSet.next()) {
                return resultSet.getInt(1);
            }
        } catch (SQLException e) {
            e.printStackTrace();
        } finally {
            DBUtil.close(connection, statement, resultSet);
        }
        return 0;
    }

    private Book map(ResultSet resultSet) throws SQLException {
        Book book = new Book();
        book.setId(resultSet.getInt("id"));
        book.setIsbn(resultSet.getString("isbn"));
        book.setTitle(resultSet.getString("title"));
        book.setAuthor(resultSet.getString("author"));
        book.setCategoryId(resultSet.getInt("category_id"));
        book.setQuantity(resultSet.getInt("quantity"));
        book.setAvailable(resultSet.getInt("available"));
        book.setStatus(resultSet.getString("status"));
        book.setCreatedAt(resultSet.getTimestamp("created_at"));
        return book;
    }
}
