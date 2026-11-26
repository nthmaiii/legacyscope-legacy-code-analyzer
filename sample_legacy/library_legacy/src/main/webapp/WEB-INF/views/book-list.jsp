<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<%@ page import="java.util.List" %>
<%@ page import="vn.edu.library.model.Book" %>
<html>
<head>
    <title>Danh sách sách</title>
</head>
<body>
<h2>Danh sách sách</h2>
<%
    String message = (String) session.getAttribute("message");
    if (message != null) {
        out.print("<p>" + message + "</p>");
        session.removeAttribute("message");
    }
    List<Book> books = (List<Book>) request.getAttribute("books");
    if (books != null && !books.isEmpty()) {
%>
<table border="1" cellpadding="5">
    <tr>
        <th>ID</th>
        <th>ISBN</th>
        <th>Tên sách</th>
        <th>Tác giả</th>
        <th>Khả dụng</th>
    </tr>
    <%
        for (Book book : books) {
    %>
    <tr>
        <td><%= book.getId() %></td>
        <td><%= book.getIsbn() %></td>
        <td><%= book.getTitle() %></td>
        <td><%= book.getAuthor() %></td>
        <td><%= book.getAvailable() %></td>
    </tr>
    <%
        }
    %>
</table>
<%
    } else {
        out.print("<p>Không có sách nào.</p>");
    }
%>
</body>
</html>
