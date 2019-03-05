package classes;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

public class DBHelper {

	private String url ="jdbc:mysql://localhost/%s?serverTimezone=UTC"
			+ "&useUnicode=true&characterEncoding=utf-8";
	private String usr;
	private String pwd;
	private String dbName;
	private static String classname = "com.mysql.cj.jdbc.Driver";;
	
	private Connection conn = null;
	private PreparedStatement pst = null;
	
	public DBHelper(){
		initial();
	}
	
	private void initial() {
		File info = new File("mysql.txt");
		try {
			BufferedReader br = new BufferedReader(new FileReader(info));
			usr = br.readLine();
			pwd = br.readLine();
			dbName = br.readLine();
			br.close();
		} catch (FileNotFoundException e1) {
			//TODO: report to admin
			e1.printStackTrace();
		} catch (IOException e) {
			e.printStackTrace();
		}
		try {
//			使用JDBC时通常是使用Class.forName()方法来加载数据库连接驱动。
//			这是因为在JDBC规范中明确要求Driver(数据库驱动)类必须向DriverManager注册自己。
			Class.forName(classname);
			conn = DriverManager.getConnection(String.format(url, dbName), usr, pwd);
		} catch (ClassNotFoundException e) {
			System.err.println(e);
			e.printStackTrace();
		} catch (SQLException e) {
			e.printStackTrace();
		}
		
	}
	
	public ResultSet execute(String sql) throws SQLException {
		pst = conn.prepareStatement(sql);
		ResultSet rs = pst.executeQuery();
		return rs;
	}
	
	public void close() {
		try {
			if(conn != null)
				conn.close();
		} catch (SQLException e) {
			e.printStackTrace();
		}
	}
	
	
}
