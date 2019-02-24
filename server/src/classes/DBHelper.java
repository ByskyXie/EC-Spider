package classes;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;

public class DBHelper {

	private static String url;
	private static String usr;
	private static String pwd;
	private static String name = "com.mysql.cj.jdbc.Driver";;
	
	private Connection conn = null;
	private PreparedStatement pst = null;
	
	DBHelper(){
		initial();
	}
	
	private void initial() {
		try {
//			使用JDBC时通常是使用Class.forName()方法来加载数据库连接驱动。
//			这是因为在JDBC规范中明确要求Driver(数据库驱动)类必须向DriverManager注册自己。
			Class.forName(name);
		} catch (ClassNotFoundException e) {
			// TODO Auto-generated catch block
			System.err.println(e);
			e.printStackTrace();
		}
		
	}
	
}
