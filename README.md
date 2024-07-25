
# An automated microfluidic controller for a constant flow rate by a PID feedback control.


## System Overview
The controller works on a GUI-based Python code communicated with a PC through an Arduino micro.
It provides a constant flow rate or pressure to a microfluidic system by regulating the pressure given to a sample tube containing a solution with an electro-pneumatic regulator (SMC, ITV0010-2CS).
To switch different solutions, it uses ten on/off solenoid valves connected to respective sample tubes and a selector valve (IDEX Health & Science, MXX778-605), which assembles up to ten PEEK tubes from different sample tubes into a single PEEK tube.
The system monitors the flow rate with a flow sensor (Sensirion, LG16-1000D) serially connected between the output from the selector valve and the microfluidic system.
We installed a potentiometer at the analog output given to the electro-pneumatic regulator to stabilize the proportional-integral-derivative (PID) feedback control for a low constant flow rate. 
The potentiometer effectively modulates the maximum voltage of the analog output (originally, 0-5 V) from the Arduino micro. The modulation enables using the full 8-bit resolution when regulating at low pressure (e.g., 1 kPa).
To prevent a gravitational flow when all the solenoid valves are closed, we installed a latching solenoid valve (Takasago Electric Inc, FLV-2-N1F) in the PEEK tube downstream of the microfluidic system.

### Communication with PC via Arduino micro
The Arduino micro on the controller can communicate via a serial connection with a PC using pySerial.
To read data from and control devices upon request, the Arduino micro routinely checks a serial command sent from the PC.
The Arduino micro communicates with the flow sensor through I2C, reading two's complement and outputting the scaled flow rate ul/min to the serial connection upon request.
The example programs that communicate with the flow sensors are available from the github by Sensirion (https://github.com/Sensirion/arduino-liquid-flow-snippets).
It monitors the pressure via the regulator's analog input, which is 0-5 V voltage and controls the electro-pneumatic regulator via 8-bit PWM, which is converted to a 0-5 V analog output with a digital-analog converter (DAC).
The Arduino micro controls the solenoid valves via digital I/O, which is boosted to 24 V-on/off with N-type MOS-FET-based switching circuits.

The controller creates the flows at a constant pressure or flow rate, respectively, with open-loop or feedback controls.
Under open-loop control, the controller regulates the pressure at a constant value defined by the analog output from the Arduino micro.
Under feedback control, the Arduino micro reads the flow rate and regulates the pressure using PID control to achieve the specified flow rate.
The Arduino micro switches the control modes among open-loop and feedback upon request via a serial command.

### Pressure source and tubings
A miniature diaphragm pump creates the pressure source at about 100 kPa, which is then passed through a filter to the electro-pneumatic regulator.
The electro-pneumatic regulator controls the output pressure refering to the analog output from DAC.
The pressurized gas is distributed to a designated sample tube via open/close solenoid valves.
The pressurized gas increases the pressure in the sample tube and pushes out the solution to the peek tube inserted down to the tube bottom.
The pump, regulator, and manifold of solenoid valves are connected with tubes made of urethane.
We changed the outer diameter (OD) of tubes from phi 6 to phi 5 using a fitting between the pump and the regulator.
The regulator and the manifold of the solenoid valves are connected through a tube of phi 5.
The individual outlet from the manifold is connected with a phi 3 tube.
The phi three tubes are converted to PTFE tubes with fittings.
We installed rubber lids with two through holes that can fit a PTFE tube for pressurization and a peek tube for a sample outlet to a 1.5 mm sample tube.
To minimize the pressure drop in the tubing, we connect the sample tube and the selector valve using a peek tube with an inner diameter (ID) of phi 0.5.
We then used a peek tube with phi X OD and phi 0.5 for the outlet from the selector valve.
We installed the flow sensor between the microfluidic device and the selector valve.
To fit the peek tube with phi X OD to 1/16" connectors, we used XXX.
We used 1/16" peek tube at the end of the phi X OD peek tube to fit the tubing to the 1-mm hole punched in the PDMS.

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


