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
			LinkAdministrator la = new LinkAdministrator();
			la.sendMessage("Mysql Info not found", "At server mysql.txt not found");
			e1.printStackTrace();
		} catch (IOException e) {
			e.printStackTrace();
		}
		try {
//			ʹ��JDBCʱͨ����ʹ��Class.forName()�������������ݿ�����������
//			������Ϊ��JDBC�淶����ȷҪ��Driver(���ݿ�����)�������DriverManagerע���Լ���
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
		ResultSet rs = null;
		try {
			pst = conn.prepareStatement(sql);
			rs = pst.executeQuery();
		}catch(java.sql.SQLNonTransientConnectionException ntc) {
			initial(); //Long time not use connection maybe close.
			pst = conn.prepareStatement(sql);
			rs = pst.executeQuery();
		}catch(com.mysql.cj.jdbc.exceptions.CommunicationsException ce) {
			initial();
			pst = conn.prepareStatement(sql);
			rs = pst.executeQuery();
		}
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
