
# An automated microfluidic controller for a constant flow rate with a PID feedback control.


## System Overview
The controller works on a GUI-based python code communicated with a PC through an Arduino micro.
It provides a flow at a constant rate or a constant pressure to a microfluidic system by regulating the pressure given to a sample tube containing a solution with an electro-pneumatic regulator (SMC, ITV0010-2CS).
To switch different solutions, it uses tens of on/off solenoid valves connected to respective sample tubes and a selector valve (IDEX Health & Science, MXX778-605), which combines the PEEK tubes from different sample tubes into a single PEEK tube.
The system monitors the flow rate with a flow sensor (Sensirion, LG16-1000D) serially connected between the selector valve and the microfluidic system.
To stabilize the PID feedback control especially at a low constant flow rate, we installed a potentiometer to the analog output from the Arduino micro given to the electro-pneumatic regulator. 
The potentiometer effectively limits the dynamic range of the analog output (originally 0-5 V) and improves the resolution of the controlling pressure when regulating at low pressure (e.g., 1 kPa).
To prevent a gravitational flow when all the solenoid valves are closed, a latching solenoid valve (Takasago Electric Inc, FLV-2-N1F) is installed downstream of the microfluidic system.

### Pressure source
The pressure source is a miniature DC diaphragm pump (Denso-sangyo, DSA-2FT-24).
An electro-pneumatic regulator (SMC, ITV0010-2CS) controls the operating pressure, which is controlled via 0-5 V DC voltage from Arduino micro.
The regulated pressure is 


### Electric circuit


