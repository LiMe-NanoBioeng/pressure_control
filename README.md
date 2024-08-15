# An automated microfluidic controller for a constant flow rate by a PID feedback control.
## Abstract
an open source that controls 10-channel fluidics and imaging via pycro-manager
We employ an off-the-shelf pressure regulator and selection valve to balance cost and reliability.
Our fluidic system controls a pneumatic pump, a pressure regulator, and 10 individually addressable on/off valves with an Arduino micro.
We also offer a Python program that integrates the fluidics control, off-the-shelf switching valve, and imaging via pyro-manager, which makes the system available to broad users.
We demonstrate…
We envision that this open source will be

### Hardware in context
In microfluidic systems, pressure-driven flow is typicslly given by syringe pumps or pressure-based fluidic systems.
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
We show the robust fluid exchange with our controller demonstrating XX rounds of fluorescent oligo hybridization and stripping.

To further demonstrate our system's flexibility, we show an extension of our controller using open-loop control demonstrating two different applications: microfluidic droplet generation and pulsed jet formation.
The extended controller integrated two electro-pneumatic regulators to provide different pressures for two phases, oil and aqueous solutions or gas and liquid.
In the microfluidic droplet generation, we injected oil and aqueous solutions into a hydrophobic microfluidic device, in which aqueous droplets are generated in an oil continuous phase.
We used agarose gel as the aqueous phase and demonstrated the single-cell encapsulation in agarose gel beads.
To keep the agarose gel matrix in liquid form before the injection, we maintained the temperature of the agarose gel matrix containing cells in a 1.5 mL tube at 37C.
In the pulsed jet formation, we adapted our controller to a nozzle that generated small droplets using two-phase flows.
To minimize the amount of aqueous solution used, we here leveraged the solenoid valve to generate a liquid jet for a short period of time.
Our controller has a capacity to integrate up to four electro-pneumatic regulators (four analog inputs/outputs), ten solenoid valves (driven at 24V via ten digital pins), one flow meter (I2C), and one latching valve  (driven at 5 V via one digital pin).
These demonstrations show the robustness and flexibility of our open-source microfluidic system for various applications.

## Hardware description
### Overview (Fig.1: Keisuke Kondo)
Our microfluidic controller provides a constant flow rate or a constant pressure to a microfluidic system by regulating the pressure with an electro-pneumatic regulator (SMC, ITV0010-2CS).
The pressurized gas is distributed to a designated sample tube via open/close solenoid valves and pushes out the solution to the peek tube inserted down to the tube bottom.
A selector valve (IDEX Health & Science, MXX778-605) connects the tubing out of ten sample tubes to the single outlet tube.
The controller monitors the flow rate with a flow sensor (Sensirion, LG16-1000D) serially connected between the outlet tube of the selector valve and the microfluidic system.
To prevent a gravitational flow when all the solenoid valves are closed, we installed a latching solenoid valve (Takasago Electric Inc, FLV-2-N1F) in the PEEK tube downstream of the microfluidic system.

### Software and device control via Arduino micro (Fig: Junichi Murai)
The controller works on GUI-based Python code that communicates with devices through an Arduino micro via a serial connection using pySerial.
We provide the program for the Arduino micro as another repository (https://github.com/LiMe-NanoBioeng/Arduino-to-DAQ.git).
To read data from and control devices upon request, the Arduino micro routinely checks a serial command sent from the PC.
The Arduino micro monitors the pressure via the regulator's analog input, which is 0-5 V, and controls the electro-pneumatic regulator via 8-bit PWM, which is converted to a 0-5 V analog output with a digital-analog converter (DAC).
We installed a potentiometer at the analog output given to the electro-pneumatic regulator to stabilize PID feedback control, especially for a low constant flow rate. 
The potentiometer effectively modulates the maximum voltage of the analog output (originally, 0-5 V) from the Arduino micro down to a low voltage. Manual modulation enables the use of the full 8-bit resolution when regulating at low pressure (e.g., 1 kPa).
The Arduino micro controls the solenoid valves via digital I/O, which is boosted to 24 V-on/off with N-type MOS-FET-based switching circuits.
The Arduino micro communicates with the flow sensor through I2C, reading two's complement and outputting the scaled flow rate ul/min.
We note that the other example Arduino programs for communicating with the flow sensors through I2C are available from Sensirion's GitHub (https://github.com/Sensirion/arduino-liquid-flow-snippets).
The Arduino micro operates the devices either under open-loop or feedback controls, respectively, for a constant pressure or constant flow rate.
Under open-loop control, the controller regulates the pressure at a constant value defined by the analog output from the Arduino micro.
Under feedback control, the Arduino micro reads the flow rate and regulates the pressure using PID control to achieve the specified flow rate.
The Arduino micro continues the feedback control until it is interrupted by a serial command from the PC.
The selector valve communicates with the PC through another USB.

### Electric circuit (Fig?: Keisuke Kondo)
The circuit in the controller drives devices at three different voltages 24 V, 9 V and 5 V as summarized in Table 1.
The circuit thus uses a 24 V for the power supply and regulates 5V from the Arduino micro and 9V with a three-terminal regulator. 
| Abbreviation | Part name | Voltage|
|:---:|:---|:---:|
| PMP | Miniature DC diaphragm pump (Denso-sangyo, DSA-2FT-24) | 24V |
| PREG | Electro-pneumatic regulator (SMC, ITV0010-2CS) | 24V |
| SV | Solenoid valves (SMC, S070B-5BC) | 24V |
| REG | Three-terminal regulator (JRC, NJM7809FA) | 24V | 
| AM | Arduino micro | 9V | 
| DAC | Digital analogue converter (Analogue Devices, LTC2645CMS-L8) | 5V | 
| FS | Flow sensor (Sensirion, LG16-1000D) | 5V | 
| LSV | Latching solenoid valve (Takasago Electric Inc, FLV-2-N1F) | 5V | 


### Pressure source and tubings (Fig?: Junichi Murai)
A miniature diaphragm pump creates the pressure source at about 100 kPa given to the electro-pneumatic regulator.
To adapt the pump outlet to the inlet of the electro-pneumatic regulator, we connected urethane tube of 6 mm of outer diameter (OD) to the pump outlet and converted to 4 mm OD using a fitting (MPG6-4).
The regulator and the solenoid valve manifold are connected through a syringe filter (sartorius, Minisart RC4) and a urethane tube of 4 mm OD.
The outlet of the regulator is connected to 4 mm OD urethane tube and connected to the manifold with a fitting(?).
The individual outlet from the manifold is connected with a 3 mm OD tube via a fitting (Koganei, BF3BU-M3).
The phi 3 mm OD tubes are converted to 26G PTFE tubes (Chukyo Co Ltd	TUF-100) with fittings.
We cap sample tubes (1.5 mL tubes) with rubber lids (AsOne, 1-9662-06) having two through holes that can fit a PTFE tube for pressurization and a peek tube for a sample outlet.
To minimize the pressure drop in the tubing, we connect the sample tube and the selector valve using a peek tube (XX part number?) with 0.5 mm ID.
We then used a peek tube (Institute of Microchemical Technology Co Ltd, ICP-30P) with 0.5 mm OD and 0.3 mm ID for the outlet from the selector valve.
To fit the peek tube with phi 0.5 mm OD to 1/16" connectors, we used 1/16-to-0.5 mm adapter sleeves (Institute of Microchemical Technology Co Ltd, ICT-16S).
We installed the flow sensor between the microfluidic device and the selector valve.
We used 1/16" peek tube at the end of the 0.5 mm OD peek tube to fit the tubing to the 1-mm hole punched in the PDMS.
We installed the latching solenoid valve in a tube extending from the outlet of the microfluidic system.

## Design files summary
Keisuke Kondo

## Bill of materials summary
Junichi Murai

https://docs.google.com/spreadsheets/d/1DA3WnisZPPh0mLJruJ4DynrS7ac4WS7NuqQuolvCBMg/edit?usp=drive_link

## Build instructions
Keisuke (lead) and Junichi

## Operation instructions
Misa Mineghisi

## Validation and characterization
### closed-loop
Junichi(lead) and Keisuke

### open-loop extension to four pressure regulators (other applications)
#### droplet generator
Keiji Nozaki
#### jet
Mahmoud and Kohei Takamuro





