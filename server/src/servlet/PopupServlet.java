package servlet;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.io.PrintWriter;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.text.SimpleDateFormat;
import java.util.Date;

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
	private static final SimpleDateFormat SDF = new SimpleDateFormat("yyyy-MM-dd");
	private static final long serialVersionUID = 1L;
	private static final int LIMITSECOND = 365/2*24*60*60;  //默认显示历史价格区间
	private static final String SQL_QUERY = 
			"SELECT data_begin_time,item_price "
			+ "FROM item "
			+ "WHERE item_url_md5='%s' AND data_begin_time>%f "
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
		try {
			ResultSet rs = helper.execute(String.format(SQL_QUERY, 
					getMD5(itemUrl), new Date().getTime() - LIMITSECOND));
			//调取半年内的数据
			pw.append(produceChart(rs));
			rs.close();
		} catch (SQLException e) {
			e.printStackTrace();
			pw.append("");  //TODO:显示错误
			return;
		}
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
		BufferedReader br;
		File templet = new File("chartTemplet.html");
		try {
			br = new BufferedReader( new FileReader(templet) );
			int count = 0;  //record %s appear number.
			do {
				String line = br.readLine();
				if(line == null) {
					break;
				}
				if( line.indexOf("%s") != -1 ) {
					switch(count) {
					case 0: //first parameter
						String data = produceChartDataSequence(rs);
						if(data.length() == 0) {
							//record is null
							return "Empty.";
						}
						line = line.replace("%s", data);
						break;
					default:
						break;
					}
					count++;
				}
				script += line + '\n';
			}while(true);
			br.close();
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		} catch (IOException e) {
			e.printStackTrace();
		} catch (SQLException e) {
			e.printStackTrace();
		}
		return script;
	}
	
	private String produceChartDataSequence(ResultSet rs) throws SQLException {
		String con = "";
		rs.last();
		int num = rs.getRow();
		if(num == 0) {
			return con;
		}
		//TODO:locate oldest time(half year?)
		for(int i=1;i<=num;i++) {
			rs.absolute(i);
			con +=String.format( "{\r\n disp:'%s',\r\nvalue: %f\r\n}, "
				,doubleToDate((long)(rs.getDouble(1)*1000)), rs.getDouble(2));
		}
		con +=String.format( "{\r\n disp:'%s',\r\nvalue: %f\r\n} "
			,SDF.format(new Date()), rs.getDouble(2));  //使用最近一次价格
		return con;
	}
	
	private String doubleToDate(long time) {
		Date dt = new Date(time);
		return SDF.format(dt);
	}
	
	public static String getMD5(String info) {
		try {
			StringBuilder sb = new StringBuilder();
			MessageDigest md5 = MessageDigest.getInstance("MD5");
			md5.update(info.getBytes());
			byte[] cons = md5.digest();
			for (int i,offset = 0; offset < cons.length; offset++) {
				i = cons[offset];
				if (i < 0)
					i += 256;
				if (i < 16)
					sb.append("0");
				sb.append(Integer.toHexString(i));
			}
			return sb.toString();
		} catch (NoSuchAlgorithmException e1) {
			e1.printStackTrace();
		}
		return "Error";
	}
	
}
