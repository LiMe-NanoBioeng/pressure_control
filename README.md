
# An automated microfluidic controller for a constant flow rate by a PID feedback control.


## System Overview
The controller works on a GUI-based Python code communicated with a PC through an Arduino micro.
It provides a constant flow rate or pressure to a microfluidic system by regulating the pressure with an electro-pneumatic regulator (SMC, ITV0010-2CS) and pressurizing a sample tube containing a solution.
To switch among different solutions, it uses ten on/off solenoid valves connected to respective sample tubes and a selector valve (IDEX Health & Science, MXX778-605), which selects a solution coming from one of ten sample tubes and lets the solution flow into the outlet tube.
The system monitors the flow rate with a flow sensor (Sensirion, LG16-1000D) serially connected between the outlet tube and the microfluidic system.
We installed a potentiometer at the analog output given to the electro-pneumatic regulator to stabilize the proportional-integral-derivative (PID) feedback control for a low constant flow rate. 
The potentiometer effectively modulates the maximum voltage of the analog output (originally, 0-5 V) from the Arduino micro. The manual modulation enables using the full 8-bit resolution when regulating at low pressure (e.g., 1 kPa).
To prevent a gravitational flow when all the solenoid valves are closed, we installed a latching solenoid valve (Takasago Electric Inc, FLV-2-N1F) in the PEEK tube downstream of the microfluidic system.

### Communication with PC via Arduino micro
The Arduino micro on the controller can communicate via a serial connection with a PC using pySerial.
We provide the program for the Arduino micro as another repository (https://github.com/LiMe-NanoBioeng/Arduino-to-DAQ.git).
To read data from and control devices upon request, the Arduino micro routinely checks a serial command sent from the PC.
The Arduino micro operates the devices either under open-loop or feedback controls, respectively, for a constant pressure or flow rate.
Under open-loop control, the controller regulates the pressure at a constant value defined by the analog output from the Arduino micro.
Under feedback control, the Arduino micro reads the flow rate and regulates the pressure using PID control to achieve the specified flow rate.
The Arduino micro continues the feedback control until being interupted by a serial command from the PC.
The Arduino micro communicates with the flow sensor through I2C, reading two's complement and outputting the scaled flow rate ul/min.
We note that the other example programs of Arduino for communicating with the flow sensors through I2C are available from the GitHub by Sensirion (https://github.com/Sensirion/arduino-liquid-flow-snippets).
The Arduino micro monitors the pressure via the regulator's analog input, which is 0-5 V, and controls the electro-pneumatic regulator via 8-bit PWM, which is converted to a 0-5 V analog output with a digital-analog converter (DAC).
The Arduino micro controls the solenoid valves via digital I/O, which is boosted to 24 V-on/off with N-type MOS-FET-based switching circuits.

### Electric circuit
The circuit in the controler drives devices at three different voltages 24 V, 9 V and 5 V as summarized in Table 1

The devices drive
at 24V
a miniature DC diaphragm pump (Denso-sangyo, DSA-2FT-24)
electro-pneumatic regulator
ON/OFF solenoid valves

at 9V
Arduino micro

at 5V
FS Flow sensor
SV the latching solenoid valve
DAC

Thus, our circuit uses a 24 V AC power supply and regulate the power to 9 V. 

The controller contains  as a pressure source.
The electro-pneumatic regulator controlled via 0-5 V DC voltage from Arduino micro.


### Pressure source and tubings
A miniature diaphragm pump creates the pressure source at about 100 kPa, which is then passed through a filter () to the electro-pneumatic regulator.
The electro-pneumatic regulator controls the output pressure by referring to the analog output from the DAC.
The pressurized gas is distributed to a designated sample tube via open/close solenoid valves.
The pressurized gas increases the pressure in the sample tube and pushes out the solution to the peek tube inserted down to the tube bottom.
The pump, regulator, and manifold of solenoid valves are connected with tubes made of urethane.
We changed the outer diameter (OD) of tubes from phi 6 mm to phi 5 mm using a fitting between the pump and the regulator.
The regulator and the manifold of the solenoid valves are connected through a tube of phi 5 mm.
The individual outlet from the manifold is connected with a phi 3 mm tube.
The phi 3 mm tubes are converted to PTFE tubes with fittings.
We cap sample tubes (1.5 mL tubes) with rubber lids having two through holes that can fit a PTFE tube for pressurization and a peek tube for a sample outlet.
To minimize the pressure drop in the tubing, we connect the sample tube and the selector valve using a peek tube with an inner diameter (ID) of phi 0.5 mm.
We then used a peek tube with phi X OD and phi 0.5 for the outlet from the selector valve.
We installed the flow sensor between the microfluidic device and the selector valve.
To fit the peek tube with phi X OD to 1/16" connectors, we used XXX.
We used 1/16" peek tube at the end of the phi X OD peek tube to fit the tubing to the 1-mm hole punched in the PDMS.



