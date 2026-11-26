package vn.edu.library.controller;

import vn.edu.library.model.Book;
import vn.edu.library.service.BookService;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.List;

@WebServlet("/books")
public class BookServlet extends HttpServlet {
    private BookService bookService = new BookService();

    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
        request.setCharacterEncoding("UTF-8");
        response.setContentType("text/html;charset=UTF-8");
        String action = request.getParameter("action");
        if ("edit".equals(action)) {
            int id = Integer.parseInt(request.getParameter("id"));
            Book book = bookService.findById(id);
            request.setAttribute("book", book);
            request.getRequestDispatcher("/WEB-INF/views/book-form.jsp").forward(request, response);
            return;
        }
        String keyword = request.getParameter("keyword");
        List<Book> books = bookService.search(keyword);
        request.setAttribute("books", books);
        request.setAttribute("keyword", keyword);
        request.getRequestDispatcher("/WEB-INF/views/book-list.jsp").forward(request, response);
    }

    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
        request.setCharacterEncoding("UTF-8");
        String action = request.getParameter("action");
        if ("create".equals(action)) {
            Book book = readBook(request);
            String message = bookService.create(book);
            request.getSession().setAttribute("message", message);
        } else if ("update".equals(action)) {
            Book book = readBook(request);
            book.setId(Integer.parseInt(request.getParameter("id")));
            String message = bookService.update(book);
            request.getSession().setAttribute("message", message);
        } else if ("delete".equals(action)) {
            int id = Integer.parseInt(request.getParameter("id"));
            String message = bookService.delete(id);
            request.getSession().setAttribute("message", message);
        }
        response.sendRedirect(request.getContextPath() + "/books");
    }

    private Book readBook(HttpServletRequest request) {
        Book book = new Book();
        book.setIsbn(request.getParameter("isbn"));
        book.setTitle(request.getParameter("title"));
        book.setAuthor(request.getParameter("author"));
        String categoryId = request.getParameter("categoryId");
        if (categoryId != null && !categoryId.isEmpty()) {
            book.setCategoryId(Integer.parseInt(categoryId));
        }
        String quantity = request.getParameter("quantity");
        if (quantity != null && !quantity.isEmpty()) {
            book.setQuantity(Integer.parseInt(quantity));
            book.setAvailable(Integer.parseInt(quantity));
        }
        book.setStatus("ACTIVE");
        return book;
    }
}
