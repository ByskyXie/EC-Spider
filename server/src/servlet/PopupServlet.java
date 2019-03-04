package servlet;

import java.io.IOException;
import java.io.PrintWriter;
import java.sql.ResultSet;
import java.sql.SQLException;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import classes.DBHelper;

/**
 * Servlet implementation class PopupServlet
 */

@WebServlet(urlPatterns="/popup")
public class PopupServlet extends HttpServlet {
	private final DBHelper helper = new DBHelper();
	private static final long serialVersionUID = 1L;
	private static final int point = 365/2;  //Ĭ����ʾ��ʷ�۸�����
	private static final String SQL_QUERY = 
			"SELECT data_begin_time,item_price "
			+ "FROM item "
			+ "WHERE item_url_md5='%s' "
			+ "ORDER BY data_begin_time ASC;";

    public PopupServlet() {
    	super();
    }

	/**
	 * @see HttpServlet#doGet(HttpServletRequest request, HttpServletResponse response)
	 */
	protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
		PrintWriter pw = response.getWriter();
		String itemUrl = request.getParameter("item_url");
		System.out.println("GET url="+itemUrl);
		try {
			ResultSet rs = helper.execute(String.format(SQL_QUERY, itemUrl));
			pw.append(produceChart(rs));
		} catch (SQLException e) {
			e.printStackTrace();
			pw.append("");  //TODO:��ʾ����
			return;
		}
		pw.append("Served at EC spider");
		pw.close();
	}

	/**
	 * @see HttpServlet#doPost(HttpServletRequest request, HttpServletResponse response)
	 */
	protected void doPost(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
		
		doGet(request, response);
	}

	public void destroy() {
		super.destroy();
		helper.close();
	}
	
	private String produceChart(ResultSet rs) {
		String script = "";
		//TODO:produce chart
		
		return script;
	}

}
