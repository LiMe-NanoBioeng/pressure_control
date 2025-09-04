# An automated microfluidic controller for a constant flow rate by a PID feedback control.

## Abstract
MiSA is an open-source device for [microfluidic sequence automation](https://pubs.rsc.org/en/content/articlelanding/2025/lc/d5lc00551e/unauth)
Multiplexed fluid control is a demanding task in various life sciences and bioengineering research. We here present an open-source microfluidic sequence automation (MiSA) that offers flexible and multiplexed fluid control for various applications, providing a constant flow rate via pressure-based feedback control with 10-plex capability and transient flow by rapidly opening and closing pressure valves. MiSA is self-contained, including a pressure source, and employs an Arduino Micro to integrate ten solenoid valves, an off-the-shelf pressure regulator, and a flow sensor to balance cost and reliability. To offer stable microflow control, especially at a low flow rate under a low flow resistance, MiSA uses a potentiometer that tunes the range of the pressure control by effectively leveraging the full 8-bit output from the Arduino Micro applied to the pressure regulator. We demonstrate the practical use of MiSA for multiplexed chemical reactions by performing the hybridization-based in situ sequencing. To demonstrate the flexibility of MiSA, we show the extensions of our system for two pressure regulations under open-loop control in the flow rate by demonstrating three independent applications for droplet generation, microfluidic spinning of spider silk fiber, and atomization of protein solution. We envision that this open source will offer resources for researchers to quickly explore microfluidic applications with an affordable investment.


### Hardware in context
In microfluidic systems, pressure-driven flow is typically given by syringe pumps or pressure-based fluidic systems.
A syringe pump gives a constant flow rate by forwarding the plunger at a constant speed.
The pressure output of a syringe pump is dependent on the microfluidic system's flow resistance.
The syringe pump is advantageous when injecting a solution at a high pressure (>100 kPa) and regulating at a defined flow rate.
In contrast, a pressure-based fluidic system provides a constant flow by pneumatically pressuring the solution.
The flow rate becomes dependent on the microfluidic system's flow resistance.
Thus, a pressure-based fluidic system requires feedback control when regulating the flow at a defined flow rate or terminating the flow at a finite injection volume.
The pressure-based fluidic system typically uses a sample tube or a bottle to store the sample solution.
This configuration is beneficial for maintaining the temperature of the sample solution before the injection simply by using dry bathes to cool or heat sample tubes.
Unlike syringe pumps, the pressure-based fluidic controller can easily multiplex sample tubes, avoiding contamination by using a one-time-use sample tube.
Thus, it is advantageous to adapt the system to multiplexed assays, such as multiplexed fluorescent in situ hybridization, which involves washing and reaction steps with multiple solutions.
Although pressure-based flow controllers are commercially available for multiplexed assays, they are relatively expensive and less flexible than open-source systems.
Previously reported systems based on pressure regulation use open-loop control for the flow rate. 
Thus, to provide a constant flow rate, the systems required a calibration curve that characterizes the relation between pressure and flow rate for each microfluidic system.


Here, we present an open-source microfluidic controller that enables regulation of the flow rate using the proportional-integral-derivative (PID) feedback control.
Our controller uses an Arduino micro that fully integrates the PID feedback control. This control involves measuring the flow rate with a flow sensor and controlling the pressure with an electro-pneumatic regulator to provide a constant flow rate.

## Hardware description
### Overview 
Our microfluidic controller provides a constant flow rate or a constant pressure to a microfluidic system by regulating the pressure with an electro-pneumatic regulator (SMC, ITV0010-2CS).
The pressurized gas is distributed to a designated sample tube via open/close solenoid valves and pushes out the solution to the peek tube inserted down to the tube bottom.
A selector valve (IDEX Health & Science, MXX778-605) connects the tubing out of ten sample tubes to the single outlet tube.
The controller monitors the flow rate with a flow sensor (Sensirion, LG16-1000D) serially connected between the outlet tube of the selector valve and the microfluidic system.
To prevent a gravitational flow when all the solenoid valves are closed, we installed a latching solenoid valve (Takasago Electric Inc, FLV-2-N1F) in the PEEK tube downstream of the microfluidic system.
The detailed build instructions are [here](https://www.rsc.org/suppdata/d5/lc/d5lc00551e/d5lc00551e1.pdf).

### Software and device control via Arduino micro
The controller works on GUI-based Python code that communicates with devices through an Arduino micro via a serial connection using pySerial.
We provide the program for the Arduino micro as [another repository](https://github.com/LiMe-NanoBioeng/Arduino-to-DAQ.git).
To read data from and control devices upon request, the Arduino micro routinely checks a serial command sent from the PC.
The Arduino micro monitors the pressure via the regulator's analog input, which is 0-5 V, and controls the electro-pneumatic regulator via 8-bit PWM, which is converted to a 0-5 V analog output with a digital-analog converter (DAC).
We installed a potentiometer at the analog output given to the electro-pneumatic regulator to stabilize PID feedback control, especially for a low constant flow rate. 
The potentiometer effectively modulates the maximum voltage of the analog output (originally, 0-5 V) from the Arduino micro down to a low voltage. Manual modulation enables the use of the full 8-bit resolution when regulating at low pressure (e.g., 1 kPa).
The Arduino micro controls the solenoid valves via digital I/O, which is boosted to 24 V-on/off with N-type MOS-FET-based switching circuits.
The Arduino micro communicates with the flow sensor through I2C, reading two's complement and outputting the scaled flow rate ul/min.
We note that the other example Arduino programs for communicating with the flow sensors through I2C are available from [Sensirion's GitHub](https://github.com/Sensirion/arduino-liquid-flow-snippets).
The Arduino micro operates the devices either under open-loop or feedback controls, respectively, for a constant pressure or constant flow rate.
Under open-loop control, the controller regulates the pressure at a constant value defined by the analog output from the Arduino micro.
Under feedback control, the Arduino micro reads the flow rate and regulates the pressure using PID control to achieve the specified flow rate.
The Arduino micro continues the feedback control until it is interrupted by a serial command from the PC.
The selector valve communicates with the PC through another USB.




