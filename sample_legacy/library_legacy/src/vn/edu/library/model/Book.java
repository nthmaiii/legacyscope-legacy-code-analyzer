package vn.edu.library.model;

import java.io.Serializable;
import java.util.Date;

public class Book implements Serializable {
    private int id;
    private String isbn;
    private String title;
    private String author;
    private int categoryId;
    private int quantity;
    private int available;
    private String status;
    private Date createdAt;

    public Book() {
    }

    public Book(int id, String isbn, String title, String author, int categoryId, int quantity, int available, String status) {
        this.id = id;
        this.isbn = isbn;
        this.title = title;
        this.author = author;
        this.categoryId = categoryId;
        this.quantity = quantity;
        this.available = available;
        this.status = status;
    }

    public int getId() {
        return id;
    }

    public void setId(int id) {
        this.id = id;
    }

    public String getIsbn() {
        return isbn;
    }

    public void setIsbn(String isbn) {
        this.isbn = isbn;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getAuthor() {
        return author;
    }

    public void setAuthor(String author) {
        this.author = author;
    }

    public int getCategoryId() {
        return categoryId;
    }

    public void setCategoryId(int categoryId) {
        this.categoryId = categoryId;
    }

    public int getQuantity() {
        return quantity;
    }

    public void setQuantity(int quantity) {
        this.quantity = quantity;
    }

    public int getAvailable() {
        return available;
    }

    public void setAvailable(int available) {
        this.available = available;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public Date getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(Date createdAt) {
        this.createdAt = createdAt;
    }

    public boolean isAvailable() {
        return available > 0 && "ACTIVE".equals(status);
    }

    @Override
    public String toString() {
        return title + " - " + author;
    }
}
