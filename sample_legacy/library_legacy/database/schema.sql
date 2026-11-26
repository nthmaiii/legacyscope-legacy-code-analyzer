-- Cơ sở dữ liệu hệ thống quản lý thư viện
-- Phiên bản: 1.4 (2016)
-- Lưu ý: chưa có migration, mọi thay đổi thực hiện trực tiếp trên production.

CREATE TABLE categories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255)
);

CREATE TABLE books (
    id INT PRIMARY KEY AUTO_INCREMENT,
    isbn VARCHAR(20) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(150),
    category_id INT,
    quantity INT NOT NULL DEFAULT 0,
    available INT NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at DATETIME,
    CONSTRAINT fk_books_category FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE readers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    code VARCHAR(20) NOT NULL UNIQUE,
    full_name VARCHAR(150) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(150),
    address VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    joined_at DATETIME,
    created_at DATETIME
);

CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    full_name VARCHAR(150),
    role VARCHAR(20) NOT NULL DEFAULT 'LIBRARIAN',
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'
);

CREATE TABLE loans (
    id INT PRIMARY KEY AUTO_INCREMENT,
    book_id INT NOT NULL,
    reader_id INT NOT NULL,
    created_by INT NOT NULL,
    borrow_date DATETIME NOT NULL,
    due_date DATETIME NOT NULL,
    return_date DATETIME,
    status VARCHAR(20) NOT NULL DEFAULT 'BORROWING',
    fine_amount DOUBLE NOT NULL DEFAULT 0,
    CONSTRAINT fk_loans_book FOREIGN KEY (book_id) REFERENCES books(id),
    CONSTRAINT fk_loans_reader FOREIGN KEY (reader_id) REFERENCES readers(id),
    CONSTRAINT fk_loans_user FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_books_title ON books(title);
CREATE INDEX idx_loans_status ON loans(status);
CREATE INDEX idx_loans_reader ON loans(reader_id);

INSERT INTO users (username, password, full_name, role, status)
VALUES ('admin', 'admin123', 'Quản trị viên', 'ADMIN', 'ACTIVE');
