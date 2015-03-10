##############
INCLUDED FILES
##############

json-simple-1.1.1.jar
    - For communication between tracker and NXT program

Demo.java
	- Read tracking position (u,v) pixel coordinate

tracker.py
    - Implements the cam_shift tracker through OpenCV

makefile
	- Commands for building and running the Tracker Demo

#######
RUNNING
#######
inside AS3/
1. javac -cp .:json-simple-1.1.1.jar TrackerReader.java
2. make demor
3. python tracker.py (in another terminal)

