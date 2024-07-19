
# An automated microfluidic controller for a constant flow rate by a PID feedback control.


## System Overview
The controller works on a GUI-based Python code communicated with a PC through an Arduino micro.
It provides a constant flow rate or a constant pressure to a microfluidic system by regulating the pressure given to a sample tube containing a solution with an electro-pneumatic regulator (SMC, ITV0010-2CS).
To switch different solutions, it uses tens of on/off solenoid valves connected to respective sample tubes and a selector valve (IDEX Health & Science, MXX778-605), which assembles the PEEK tubes from different sample tubes into a single PEEK tube.
The system monitors the flow rate with a flow sensor (Sensirion, LG16-1000D) serially connected between the output from the selector valve and the microfluidic system.
To stabilize the PID feedback control for a low constant flow rate, we installed a potentiometer at the analog output given to the electro-pneumatic regulator. 
The potentiometer effectively modulates the maximum voltage of the analog output (originally, 0-5 V) from the Arduino micro and enables using the full 8-bit resolution when regulating at low pressure (e.g., 1 kPa).
To prevent a gravitational flow when all the solenoid valves are closed, we installed a latching solenoid valve (Takasago Electric Inc, FLV-2-N1F) in the PEEK tube downstream of the microfluidic system.

### Communication with PC
The Arduino micro on the controller can communicate via a serial connection with a PC.
To read data and send commands upon request from the PC, the Arduino routinely checks the availability of a serial command.
The Arduino micro opens or closes the solenoid valves using digital I/O.
It communicates with the flow sensor through I2C, reading two's complement and outputing the scaled flow rate ul/min.
https://github.com/Sensirion/arduino-liquid-flow-snippets

It communicates with the electro-pneumatic regulator through analog out (PWM).
Our circuit converts the PWM (8 bit) to analog voltages ranging 0-5V through DAC.
Then, 




and then feedback-controls the pressure from the electro-pneumatic regulator to give a constant 


### Pressure connection
A miniature diaphragm pump creates the pressure source at about 100 kPa.
The electro-pneumatic regulator controls 

### Electric circuit

The devices drives
at 24V
electro-pneumatic regulator
ON/OFF solenoid valves
at 9V
Arduino micro
at 5V
FS Flow sensor
SV the latching solenoid valve
DAC digital analog converter

The controller contains a miniature DC diaphragm pump (Denso-sangyo, DSA-2FT-24) as a pressure source.
The electro-pneumatic regulator controlled via 0-5 V DC voltage from Arduino micro.
The regulated pressure is 


