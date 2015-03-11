LAB3 CMPUT 412:
Simon Fessehaye
Jonathon Machinski

All java files are found under the src folder. Report and README are with the same default directory.
To test (part 3):
1.set motors to A and B port
2.connect to EV3
3.open visualServoing.java
4.run visualServoing.java on the EV3

To test (part 4):
1.set motors to A and B port
2.connect to EV3
3.open visualServoing.java
4.CHANGE public static double threshold = 10; to public static double threshold = 35;
5.CHANGE Process p=Runtime.getRuntime().exec("python tracker.py");  to Process p=Runtime.getRuntime().exec("python part4.py"); 
6.run visualServoing.java on the EV3
