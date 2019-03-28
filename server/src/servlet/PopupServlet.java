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

	private static final String SQL_INCREACE_ACCESS = ""
			+ "UPDATE commodity "
			+ "SET access_num = access_num+1"
			+ "WHERE item_url_md5='%s'; ";
	
    public PopupServlet() {
    	super();
    }

	/**
	 * @see HttpServlet#doGet(HttpServletRequest request, HttpServletResponse response)
	 */
	protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
//		response.setContentType("application/text; charset=utf-8"); //download mode
		PrintWriter pw = response.getWriter();
		response.setHeader("Access-Control-Allow-Origin","*");//跨域访问
		String itemUrl = request.getParameter("item_url");//直接访问用
		String json = request.getParameter("json");//插件用
		System.out.println("+++++++++++++++++++Get request:"+json);
		try {
			ResultSet rs = null;
			if(itemUrl != null && itemUrl.length()!=0) {
				rs = helper.execute(String.format(SQL_QUERY, 
						getMD5(itemUrl), (double)(new Date().getTime()/1000 - LIMITSECOND)));
				increaseAccessNum(itemUrl);
				//调取半年内的数据
				pw.append(produceChart(rs));
				rs.close();
			}else if(json!=null && json.length()!=0){
				rs = helper.execute(String.format(SQL_QUERY, 
						getMD5(json), (double)(new Date().getTime()/1000 - LIMITSECOND)));
				increaseAccessNum(itemUrl);
				//调取半年内的数据
				rs.last();
				int num = rs.getRow();
				if(num != 0) {
					pw.append(produceArrayDataSequence(rs).replace('\n', ' '));
				}else {
					pw.append("Empty record.");
				}
				rs.close();
			}else {
				pw.append("Empty record.");
			}
				
		} catch (SQLException e) {
			e.printStackTrace();
			pw.append("Server failed");
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
	
	private void increaseAccessNum(String item_url) throws SQLException {
		String md5 = getMD5(item_url);
		helper.execute(String.format(SQL_INCREACE_ACCESS, md5));
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
							return "The commodity haven't record.";
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
			con +=String.format( "{\n disp:'%s',\n value: %f\n}, "
				,doubleToDate((long)(rs.getDouble(1)*1000)), rs.getDouble(2));
		}
		con +=String.format( "{\n disp:'%s',\n value: %f\n} "
			,SDF.format(new Date()), rs.getDouble(2));  //使用最近一次价格
		return con;
	}
	
	private String produceArrayDataSequence(ResultSet rs) throws SQLException {
		String con = "";
		rs.last();
		int num = rs.getRow();
		if(num == 0) {
			return con;
		}
		//TODO:locate oldest time(half year?)
		for(int i=1;i<=num;i++) {
			rs.absolute(i);
			con +=String.format( "{ \"disp\":\"%s\", \"value\": %f}| "
				,doubleToDate((long)(rs.getDouble(1)*1000)), rs.getDouble(2));
		}
		con +=String.format( "{ \"disp\":\"%s\",\"value\": %f } "
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
			if(info == null || info.length() == 0)
				return "empty";
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
