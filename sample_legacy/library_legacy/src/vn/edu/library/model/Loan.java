package vn.edu.library.model;

import java.io.Serializable;
import java.util.Date;

public class Loan implements Serializable {
    private int id;
    private int bookId;
    private int readerId;
    private int createdBy;
    private Date borrowDate;
    private Date dueDate;
    private Date returnDate;
    private String status;
    private double fineAmount;

    public Loan() {
    }

    public Loan(int bookId, int readerId, int createdBy, Date borrowDate, Date dueDate) {
        this.bookId = bookId;
        this.readerId = readerId;
        this.createdBy = createdBy;
        this.borrowDate = borrowDate;
        this.dueDate = dueDate;
        this.status = "BORROWING";
    }

    public int getId() {
        return id;
    }

    public void setId(int id) {
        this.id = id;
    }

    public int getBookId() {
        return bookId;
    }

    public void setBookId(int bookId) {
        this.bookId = bookId;
    }

    public int getReaderId() {
        return readerId;
    }

    public void setReaderId(int readerId) {
        this.readerId = readerId;
    }

    public int getCreatedBy() {
        return createdBy;
    }

    public void setCreatedBy(int createdBy) {
        this.createdBy = createdBy;
    }

    public Date getBorrowDate() {
        return borrowDate;
    }

    public void setBorrowDate(Date borrowDate) {
        this.borrowDate = borrowDate;
    }

    public Date getDueDate() {
        return dueDate;
    }

    public void setDueDate(Date dueDate) {
        this.dueDate = dueDate;
    }

    public Date getReturnDate() {
        return returnDate;
    }

    public void setReturnDate(Date returnDate) {
        this.returnDate = returnDate;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public double getFineAmount() {
        return fineAmount;
    }

    public void setFineAmount(double fineAmount) {
        this.fineAmount = fineAmount;
    }

    public boolean isOverdue(Date today) {
        return returnDate == null && dueDate != null && today.after(dueDate);
    }
}
