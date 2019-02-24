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
//			ʹ��JDBCʱͨ����ʹ��Class.forName()�������������ݿ�����������
//			������Ϊ��JDBC�淶����ȷҪ��Driver(���ݿ�����)�������DriverManagerע���Լ���
			Class.forName(name);
		} catch (ClassNotFoundException e) {
			// TODO Auto-generated catch block
			System.err.println(e);
			e.printStackTrace();
		}
		
	}
	
}
