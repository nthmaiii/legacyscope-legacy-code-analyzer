package vn.edu.library.dao;

import vn.edu.library.model.Reader;
import vn.edu.library.util.DBUtil;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;

public class ReaderDAO {

    public List<Reader> findAll() {
        List<Reader> readers = new ArrayList<Reader>();
        String sql = "SELECT * FROM readers ORDER BY full_name";
        Connection connection = null;
        PreparedStatement statement = null;
        ResultSet resultSet = null;
        try {
            connection = DBUtil.getConnection();
            statement = connection.prepareStatement(sql);
            resultSet = statement.executeQuery();
            while (resultSet.next()) {
                readers.add(map(resultSet));
            }
        } catch (SQLException e) {
            e.printStackTrace();
        } finally {
            DBUtil.close(connection, statement, resultSet);
        }
        return readers;
    }

    public Reader findById(int id) {
        String sql = "SELECT * FROM readers WHERE id = ?";
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

    public Reader findByCode(String code) {
        String sql = "SELECT * FROM readers WHERE code = ?";
        Connection connection = null;
        PreparedStatement statement = null;
        ResultSet resultSet = null;
        try {
            connection = DBUtil.getConnection();
            statement = connection.prepareStatement(sql);
            statement.setString(1, code);
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

    public int insert(Reader reader) {
        String sql = "INSERT INTO readers (code, full_name, phone, email, address, status, joined_at) VALUES (?, ?, ?, ?, ?, ?, NOW())";
        Connection connection = null;
        PreparedStatement statement = null;
        try {
            connection = DBUtil.getConnection();
            statement = connection.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS);
            statement.setString(1, reader.getCode());
            statement.setString(2, reader.getFullName());
            statement.setString(3, reader.getPhone());
            statement.setString(4, reader.getEmail());
            statement.setString(5, reader.getAddress());
            statement.setString(6, reader.getStatus());
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

    public boolean update(Reader reader) {
        String sql = "UPDATE readers SET full_name = ?, phone = ?, email = ?, address = ?, status = ? WHERE id = ?";
        Connection connection = null;
        PreparedStatement statement = null;
        try {
            connection = DBUtil.getConnection();
            statement = connection.prepareStatement(sql);
            statement.setString(1, reader.getFullName());
            statement.setString(2, reader.getPhone());
            statement.setString(3, reader.getEmail());
            statement.setString(4, reader.getAddress());
            statement.setString(5, reader.getStatus());
            statement.setInt(6, reader.getId());
            return statement.executeUpdate() > 0;
        } catch (SQLException e) {
            e.printStackTrace();
        } finally {
            DBUtil.close(connection, statement);
        }
        return false;
    }

    public boolean delete(int id) {
        String sql = "DELETE FROM readers WHERE id = ?";
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

    private Reader map(ResultSet resultSet) throws SQLException {
        Reader reader = new Reader();
        reader.setId(resultSet.getInt("id"));
        reader.setCode(resultSet.getString("code"));
        reader.setFullName(resultSet.getString("full_name"));
        reader.setPhone(resultSet.getString("phone"));
        reader.setEmail(resultSet.getString("email"));
        reader.setAddress(resultSet.getString("address"));
        reader.setStatus(resultSet.getString("status"));
        reader.setJoinedAt(resultSet.getTimestamp("joined_at"));
        return reader;
    }
}
