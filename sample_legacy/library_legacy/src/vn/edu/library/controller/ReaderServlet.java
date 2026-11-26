package vn.edu.library.controller;

import vn.edu.library.model.Reader;
import vn.edu.library.service.ReaderService;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.List;

@WebServlet("/readers")
public class ReaderServlet extends HttpServlet {
    private ReaderService readerService = new ReaderService();

    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
        request.setCharacterEncoding("UTF-8");
        String action = request.getParameter("action");
        if ("edit".equals(action)) {
            int id = Integer.parseInt(request.getParameter("id"));
            request.setAttribute("reader", readerService.findById(id));
            request.getRequestDispatcher("/WEB-INF/views/reader-form.jsp").forward(request, response);
            return;
        }
        List<Reader> readers = readerService.findAll();
        request.setAttribute("readers", readers);
        request.getRequestDispatcher("/WEB-INF/views/reader-list.jsp").forward(request, response);
    }

    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
        request.setCharacterEncoding("UTF-8");
        String action = request.getParameter("action");
        if ("create".equals(action)) {
            Reader reader = new Reader();
            reader.setCode(request.getParameter("code"));
            reader.setFullName(request.getParameter("fullName"));
            reader.setPhone(request.getParameter("phone"));
            reader.setEmail(request.getParameter("email"));
            reader.setAddress(request.getParameter("address"));
            request.getSession().setAttribute("message", readerService.create(reader));
        } else if ("update".equals(action)) {
            Reader reader = new Reader();
            reader.setId(Integer.parseInt(request.getParameter("id")));
            reader.setFullName(request.getParameter("fullName"));
            reader.setPhone(request.getParameter("phone"));
            reader.setEmail(request.getParameter("email"));
            reader.setAddress(request.getParameter("address"));
            reader.setStatus(request.getParameter("status"));
            request.getSession().setAttribute("message", readerService.update(reader));
        } else if ("delete".equals(action)) {
            int id = Integer.parseInt(request.getParameter("id"));
            request.getSession().setAttribute("message", readerService.delete(id));
        }
        response.sendRedirect(request.getContextPath() + "/readers");
    }
}
