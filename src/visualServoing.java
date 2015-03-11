import java.awt.event.KeyEvent;
import java.awt.event.KeyListener;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.MalformedURLException;
import java.rmi.NotBoundException;
import java.rmi.RemoteException;

import javax.swing.JFrame;
import javax.swing.JPanel;

import lejos.utility.Matrix;
import lejos.remote.ev3.RMIRegulatedMotor;
import lejos.remote.ev3.RemoteEV3;

public class visualServoing extends JPanel{
	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	public static TrackerReader tracker  = new TrackerReader();
	public static RemoteEV3 ev3;
	public static double threshold = 10;
	public static double lamda = .001;
	public static double alpha = 1;
	public static boolean keyPress = false;
	public static boolean keyESC = false;
	public static Matrix e,q,Jacobian,dQ,lastJacUpdate;

	public visualServoing() {
		KeyListener listener = new MyKeyListener();
		addKeyListener(listener);
		setFocusable(true);
	}

	public static void main (String[] args) throws RemoteException, IOException {

		JFrame frame = new JFrame("Press buttons here");
		visualServoing vs = new visualServoing();
		frame.add(vs);
		frame.setSize(200, 200);
		frame.setVisible(true);
		frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);

		try {
			ev3 = new RemoteEV3("10.0.1.1");
		} catch (RemoteException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (MalformedURLException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (NotBoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}


		RMIRegulatedMotor MotorF = ev3.createRegulatedMotor("A", 'L');
		RMIRegulatedMotor MotorC = ev3.createRegulatedMotor("B", 'L');

		MotorF.setSpeed(90);
		MotorC.setSpeed(90);

		tracker.start();

		System.out.println("Press a button once camera is started");

		try 
		{ 
			Process p=Runtime.getRuntime().exec("python tracker.py"); 
		}
		catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} 
		
		System.in.read();

		System.out.println("Thumbs up");

		int xi, yi, xcf, ycf, xff, yff;

		while(!keyESC){
			keyPress = false;

			//wiggle
			MotorC.rotateTo(0);
			MotorF.rotateTo(90);
			xi = (int)tracker.x;
			yi = (int)tracker.y;
			MotorC.rotate(20*7);
			xcf = (int)tracker.x;
			ycf = (int)tracker.y;
			MotorC.rotateTo(0);
			MotorF.rotate(20);
			xff = (int)tracker.x;
			yff = (int)tracker.y;
			MotorF.rotateTo(90);

			reset(xi, yi, xcf, ycf, xff, yff);

			while(Math.abs(e.get(0, 0))>threshold || Math.abs(e.get(1, 0))>threshold){

				double[][] sPoints = {{tracker.x-tracker.targetx},{tracker.y-tracker.targety}};
				e = new Matrix(sPoints);

				//checkborydian update
				double qx = Math.abs(dQ.get(0,0));
				double qy = Math.abs(dQ.get(1,0));
				if( qx<1 && qy<1 && qx>0 && qy>0 ){
					borydianUpdate();
				}
				
				//check for borydian update
				double[][] mPoints = {{tracker.x-lastJacUpdate.get(0,0)},{tracker.y-lastJacUpdate.get(1,0)}};
				Matrix m = new Matrix(mPoints);
				double mx = Math.abs(m.get(0,0));
				double my = Math.abs(m.get(1,0));
				if( mx>=threshold || my>=threshold ){
					borydianUpdate();
				}

				dQ = Jacobian.times(e.times((-1)*lamda));
				q.plusEquals(dQ);


				MotorC.rotateTo((int) q.get(0,0)*7);
				MotorF.rotateTo((int) q.get(1,0));

				if(keyPress){
					break;
				}

			}
			System.in.read();
		}

		MotorC.rotateTo(0);
		MotorF.rotateTo(0);

		MotorC.close();
		MotorF.close();


	}

	public static void borydianUpdate(){

		Matrix qt = dQ.transpose();
		Matrix jq = Jacobian.times(dQ);
		Matrix sjq = jq.minus(jq);
		Matrix top = sjq.times(qt);
		Matrix bottom = qt.times(dQ);
		double bi = bottom.get(0,0);
		Matrix wa = top.times(alpha/bi);
		Matrix Jac2 = Jacobian.plus(wa);
		
		Jac2.print(System.out);
		Jacobian = Jac2;

		double[][] ljuPoints = {{tracker.x},{tracker.y}};
		lastJacUpdate = new Matrix(ljuPoints);
	}



	public class MyKeyListener implements KeyListener {


		@Override
		public void keyPressed(KeyEvent e) {
			keyPress = true;
			if (e.getKeyCode() == KeyEvent.VK_ESCAPE){
				keyESC = true;
			}
		}

		@Override
		public void keyTyped(KeyEvent e) {
			// TODO Auto-generated method stub

		}

		@Override
		public void keyReleased(KeyEvent e) {
			// TODO Auto-generated method stub

		}

	}

	public static void reset(int xi, int yi, int xcf, int ycf, int xff, int yff){
		double[][] qPoints = {{0},{90}};
		q = new Matrix(qPoints);
		
		double[][] dQPoints = {{0},{0}};
		dQ = new Matrix(dQPoints);

		double[][] jacPoints = {{xcf-xi,xff-xi},{ycf-yi,yff-yi}};
		Jacobian = new Matrix(jacPoints);

		Jacobian.print(System.out);

		double[][] ePoints = {{tracker.x-tracker.targetx},{tracker.y-tracker.targety}};
		e = new Matrix(ePoints);

		double[][] ljuPoints = {{tracker.x},{tracker.y}};
		lastJacUpdate = new Matrix(ljuPoints);
	}
}
