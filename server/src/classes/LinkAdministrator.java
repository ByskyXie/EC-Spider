package classes;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.io.UnsupportedEncodingException;

import javax.mail.MessagingException;
import javax.mail.NoSuchProviderException;
import javax.mail.Session;
import javax.mail.Transport;
import javax.mail.internet.InternetAddress;
import javax.mail.internet.MimeMessage;
import java.util.Date;
import java.util.Properties;

public class LinkAdministrator {
	private static final String host = "smtp.qq.com";
	private static final String port = "587";
	private static final String reciver = "byskyxie@qq.com";
	private static final String to = "byskyXie";

	private MimeMessage createMessage(Session session, String from, String to, String title, String msg) throws MessagingException, UnsupportedEncodingException {
		MimeMessage mm = new MimeMessage(session);
		mm.setFrom(new InternetAddress(from, "EC-Spider Server", "UTF-8"));
		mm.setRecipient(MimeMessage.RecipientType.TO,
				new InternetAddress(to, "ByskyXie", "UTF-8"));
		mm.setSubject(title, "UTF-8");
		mm.setText(msg, "UTF-8");
		mm.setSentDate(new Date());
		mm.saveChanges();
		return mm;
	}
	
	public void sendMessage(String title, String msg, String usr, String pwd) {
		Properties props = new Properties();
		props.setProperty("mail.transport.protocol", "smtp");
		props.setProperty("mail.smtp.host", host);  //smtp服务器
		props.setProperty("mail.smtp.port", port);
		props.setProperty("mail.smtp.auth", "true");  //身份验证
		props.setProperty("mail.user", usr);
		props.setProperty("mail.password", pwd);
		Session session = Session.getDefaultInstance(props);
		MimeMessage mime = null;
		try {
			mime = createMessage(session, usr, reciver, title, msg);
			Transport tran = session.getTransport();
			tran.connect(usr, pwd);
			tran.sendMessage(mime, mime.getAllRecipients());
			tran.close();
		} catch (UnsupportedEncodingException e) {
			e.printStackTrace();
		} catch (MessagingException e) {
			e.printStackTrace();
		}
	}
	
	public void sendMessage(String title, String msg) {
		String usr = null;
		String pwd = null;
		try {
			BufferedReader br = new BufferedReader(new FileReader(new File("smtp.txt")));
			usr = br.readLine();
			pwd = br.readLine();
			br.close();
			sendMessage(title, msg, usr, pwd); 
		} catch (FileNotFoundException e1) {
			e1.printStackTrace();
		} catch (IOException e) {
			e.printStackTrace();
		}
	}
	
}
