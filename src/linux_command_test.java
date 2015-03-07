import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;


public class linux_command_test {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		try 
		{ 
		Process p=Runtime.getRuntime().exec("python tracker.py"); 
		p.waitFor();
		BufferedReader reader=new BufferedReader(new InputStreamReader(p.getInputStream())); 
		String line=reader.readLine(); 
		while(line!=null) 
		{ 
		System.out.println(line); 
		line=reader.readLine(); 
		} 
		}
		catch(InterruptedException e2) {} 
		catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} 
	}

}
