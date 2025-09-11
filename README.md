# MiSA as an automated microfluidic controller

## Abstract
MiSA is an open-source device for [microfluidic sequence automation](https://pubs.rsc.org/en/content/articlelanding/2025/lc/d5lc00551e/unauth). 
MiSA offers flexible and multiplexed fluid control for various applications, providing a constant flow rate via pressure-based feedback control with 10-plex capability and transient flow by rapidly opening and closing pressure valves. The detailed build instructions are [here](https://www.rsc.org/suppdata/d5/lc/d5lc00551e/d5lc00551e1.pdf).

## HybISS-MiSA
MiSA provides a constant flow rate or a constant pressure to a microfluidic system by regulating the pressure with an electro-pneumatic regulator.
MiSA multiplexes the pressure control with open/close solenoid valves and pushes out the solution from individual sample tubes to the peek tube inserted down to the tube bottom.
A selector valve (IDEX Health & Science, MXX778-605) connects the tubing from the sample tubes to the single outlet tube.
MiSA monitors the flow rate with a flow sensor (Sensirion, LG16-1000D) serially connected between the outlet tube of the selector valve and the microfluidic system.

### Software and device control via Arduino micro
MiSA works on GUI-based Python code that communicates with devices through an Arduino micro via a serial connection using pySerial.
We provide the program for the Arduino micro as [another repository](https://github.com/LiMe-NanoBioeng/Arduino-to-DAQ.git).
The Arduino micro communicates with the flow sensor through I2C, reading two's complement and outputting the scaled flow rate ul/min.
We note that the other example Arduino programs for communicating with the flow sensors through I2C are available from [Sensirion's GitHub](https://github.com/Sensirion/arduino-liquid-flow-snippets).




