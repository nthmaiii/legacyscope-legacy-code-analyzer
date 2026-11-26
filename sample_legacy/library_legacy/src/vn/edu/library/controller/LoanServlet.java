package vn.edu.library.controller;

import vn.edu.library.model.Loan;
import vn.edu.library.model.User;
import vn.edu.library.service.LoanService;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;
import java.io.IOException;
import java.util.List;

@WebServlet(name = "LoanServlet", urlPatterns = {"/loans", "/loans/return"})
public class LoanServlet extends HttpServlet {
    private LoanService loanService = new LoanService();

    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
        request.setCharacterEncoding("UTF-8");
        String path = request.getServletPath();
        if ("/loans/return".equals(path)) {
            int loanId = Integer.parseInt(request.getParameter("id"));
            request.setAttribute("loan", loanService.findById(loanId));
            request.setAttribute("fine", loanService.calculateFine(loanId));
            request.getRequestDispatcher("/WEB-INF/views/return-form.jsp").forward(request, response);
            return;
        }
        List<Loan> loans = loanService.findAll();
        request.setAttribute("loans", loans);
        request.getRequestDispatcher("/WEB-INF/views/loan-list.jsp").forward(request, response);
    }

    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
        request.setCharacterEncoding("UTF-8");
        HttpSession session = request.getSession();
        User user = (User) session.getAttribute("user");
        if (user == null) {
            response.sendRedirect(request.getContextPath() + "/login");
            return;
        }
        String path = request.getServletPath();
        if ("/loans/return".equals(path)) {
            int loanId = Integer.parseInt(request.getParameter("loanId"));
            int readerId = Integer.parseInt(request.getParameter("readerId"));
            session.setAttribute("message", loanService.returnBook(loanId, readerId));
        } else {
            int bookId = Integer.parseInt(request.getParameter("bookId"));
            int readerId = Integer.parseInt(request.getParameter("readerId"));
            session.setAttribute("message", loanService.borrowBook(bookId, readerId, user.getId()));
        }
        response.sendRedirect(request.getContextPath() + "/loans");
    }
}
