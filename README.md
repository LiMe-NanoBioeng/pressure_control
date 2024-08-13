# An automated microfluidic controller for a constant flow rate by a PID feedback control.
## Abstract
an open source that controls 10-channel fluidics and imaging via pycro-manager
We employ an off-the-shelf pressure regulator and selection valve to balance cost and reliability.
Our fluidic system controls a pneumatic pump, a pressure regulator, and 10 individually addressable on/off valves with an Arduino micro.
We also offer a Python program that integrates the fluidics control, off-the-shelf switching valve, and imaging via pyro-manager, which makes the system available to broad users.
We demonstrate…
We envision that this open source will be

### Hardware in context
In microfluidic systems, flow control is typically achieved by syringe pumps or pressure-based fluidic systems.
A syringe pump gives a constant flow rate by forwarding the plunger at a constant speed.
The pressure output of a syringe pump is dependent on the microfluidic system's flow resistance.
The syringe pump is advantageous when injecting a solution at a high pressure (>100 kPa) and regulating at a constant flow rate.
In contrast, a pressure-based fluidic system provides a constant flow by pneumatically pressuring the solution.
The flow rate becomes dependent on the microfluidic system's flow resistance.
Thus, a pressure-based fluidic system requires feedback control when regulating the flow at a constant flow rate or terminating the flow at a finite injection volume.
The pressure-based fluidic system typically uses a sample tube or a bottle to store the sample solution.
This configuration is beneficial for maintaining the temperature of the sample solution before the injection simply by using dry bathes to cool or heat sample tubes.
Unlike syringe pumps, the pressure-based fluidic system can easily be multiplexed by adding sample tubes.
The system can reduce the dead volume and avoid contamination by using a one-time-use sample tube.
Thus, it is advantageous to adapt the system to multiplexed assays, such as multiplexed fluorescent in situ hybridization, which involves multiple washing and reaction steps.
Although pressure-based liquid handling systems are commercially available for multiplexed assays, they are expensive and less flexible than open-source systems.
Previously reported systems based on pressure regulation use open-loop control for the flow rate. 
Thus, to provide a constant flow rate, the devices require a calibration curve that characterizes the relation between pressure and flow rate for each microfluidic system.


Here, we present an open-source microfluidic system that enables regulation of the flow rate using the proportional-integral-derivative (PID) feedback control.
Our system uses an Arduino micro that fully integrates the PID feedback control. This control involves measuring the flow rate with a flow sensor and controlling the pressure with an electromagnetic regulator to provide a constant flow rate.
We show the robust fluid exchange with our system demonstrating XX rounds of fluorescent oligo hybridization and stripping.

To demonstrate our system's flexibility, we show an extension of our system using open-loop control and demonstrate two different applications: microfluidic droplet generation and pulsed jet formation.
The extended system controls two electromagnetic regulators to provide different pressures for two phases, oil and aqueous solutions or gas and liquid.
In the microfluidic droplet generation, we injected oil and aqueous solutions into a hydrophobic microfluidic device, in which aqueous droplets are generated in an oil continuous phase.
We used agarose gel as the aqueous phase and demonstrated the single-cell encapsulation in agarose gel beads.
To keep the agarose gel matrix in liquid form before the injection, we maintain the temperature of the agarose gel matrix containing cells in a 1.5 mL tube at 37C.
In the pulsed jet formation, we integrated our system with a nozzle that generates small droplets using two-phase flows.
To minimize the amount of aqueous solution used, we here leveraged the solenoid valve to generate a liquid jet for a short period of time.
These demonstrations show the robustness and flexibility of our open-source microfluidic system for various applications.

## Hardware description
### Overview Fig.1
The controller works on GUI-based Python code that communicates with devices through an Arduino micro.
The controller provides a constant flow rate or a constant pressure to a microfluidic system by regulating the pressure with an electro-pneumatic regulator (SMC, ITV0010-2CS).
To switch among different solutions, it uses ten on/off solenoid valves connected to respective sample tubes and a selector valve (IDEX Health & Science, MXX778-605).
The selector valve connects a tube out of ten sample tubes to a single outlet tube.
The system monitors the flow rate with a flow sensor (Sensirion, LG16-1000D) serially connected between the outlet tube and the microfluidic system.
To prevent a gravitational flow when all the solenoid valves are closed, we installed a latching solenoid valve (Takasago Electric Inc, FLV-2-N1F) in the PEEK tube downstream of the microfluidic system.


### Communication with PC via Arduino micro
We control the Arduino micro via a serial connection using pySerial.
We provide the program for the Arduino micro as another repository (https://github.com/LiMe-NanoBioeng/Arduino-to-DAQ.git).
To read data from and control devices upon request, the Arduino micro routinely checks a serial command sent from the PC.
The Arduino micro monitors the pressure via the regulator's analog input, which is 0-5 V, and controls the electro-pneumatic regulator via 8-bit PWM, which is converted to a 0-5 V analog output with a digital-analog converter (DAC).
We installed a potentiometer at the analog output given to the electro-pneumatic regulator to stabilize PID feedback control, especially for a low constant flow rate. 
The potentiometer effectively modulates the maximum voltage of the analog output (originally, 0-5 V) from the Arduino micro down to a low voltage. Manual modulation enables the use of the full 8-bit resolution when regulating at low pressure (e.g., 1 kPa).
The Arduino micro controls the solenoid valves via digital I/O, which is boosted to 24 V-on/off with N-type MOS-FET-based switching circuits.
The selector valve communicates with PC through another USB.
The Arduino micro communicates with the flow sensor through I2C, reading two's complement and outputting the scaled flow rate ul/min.
We note that the other example Arduino programs for communicating with the flow sensors through I2C are available from Sensirion's GitHub (https://github.com/Sensirion/arduino-liquid-flow-snippets).
The Arduino micro operates the devices either under open-loop or feedback controls, respectively, for a constant pressure or constant flow rate.
Under open-loop control, the controller regulates the pressure at a constant value defined by the analog output from the Arduino micro.
Under feedback control, the Arduino micro reads the flow rate and regulates the pressure using PID control to achieve the specified flow rate.
The Arduino micro continues the feedback control until it is interrupted by a serial command from the PC.

### Software


### Electric circuit
The circuit in the controller drives devices at three different voltages 24 V, 9 V and 5 V as summarized in Table 1.
Thus, our circuit uses a 24 V AC power supply and regulate the power to 9 V. 
The devices work at 5 V use output from the Arduino micro.

at 24V
a miniature DC diaphragm pump (Denso-sangyo, DSA-2FT-24)
electro-pneumatic regulator (SMC, ITV0010-2CS)
ON/OFF solenoid valves 

at 9V
Arduino micro

at 5V
FS Flow sensor (Sensirion, LG16-1000D)
SV the latching solenoid valve (Takasago Electric Inc, FLV-2-N1F)
DAC

### Pressure source and tubings
A miniature diaphragm pump creates the pressure source at about 100 kPa given to the electro-pneumatic regulator.
The electro-pneumatic regulator controls the output pressure by referring to the analog output from the DAC.
The pressurized gas is distributed to a designated sample tube via open/close solenoid valves.
The pressurized gas increases the pressure in the sample tube and pushes out the solution to the peek tube inserted down to the tube bottom.
The pump, regulator, and manifold (SMC, SS073B01-10C) of solenoid valves are connected with tubes made of urethane.
We changed the outer diameter (OD) of tubes from 6 mm to 4 mm using a fitting (MPG6-4) between the pump and the regulator.
The regulator and the solenoid valve manifold are connected through a syringe filter (sartorius, Minisart RC4) and a tube of 4 mm OD.
The individual outlet from the manifold is connected with a 3 mm OD tube via a fitting (Koganei, BF3BU-M3).
The phi 3 mm OD tubes are converted to 26G PTFE tubes (Chukyo Co Ltd	TUF-100) with fittings.
We cap sample tubes (1.5 mL tubes) with rubber lids (AsOne, 1-9662-06) having two through holes that can fit a PTFE tube for pressurization and a peek tube for a sample outlet.
To minimize the pressure drop in the tubing, we connect the sample tube and the selector valve using a peek tube with 0.5 mm ID.
We then used a peek tube (Institute of Microchemical Technology Co Ltd, ICP-30P) with 0.5 mm OD and 0.3 mm ID for the outlet from the selector valve.
To fit the peek tube with phi 0.5 mm OD to 1/16" connectors, we used 1/16-to-0.5 mm adapter sleeves (Institute of Microchemical Technology Co Ltd, ICT-16S).
We installed the flow sensor between the microfluidic device and the selector valve.
We used 1/16" peek tube at the end of the 0.5 mm OD peek tube to fit the tubing to the 1-mm hole punched in the PDMS.
We installed the latching solenoid valve in a tube extending from the outlet of the microfluidic system.

## Design files summary
Keisuke Kondo

## Bill of materials summary
Junichi Murai

## Build instructions
Keisuke (lead) and Junichi

## Operation instructions
Misa Mineghisi

## Validation and characterization
Junichi(lead) and Keisuke
### closed-loop

### open-loop

### extension to four pressure regulators (other applications)
#### droplet generator
Keiji Nozaki
#### jet
Mahmoud and Kohei Takamuro





