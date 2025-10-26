# MiSA as an automated microfluidic controller

## MiSA
MiSA is an open-source device for [microfluidic sequence automation](https://pubs.rsc.org/en/content/articlelanding/2025/lc/d5lc00551e/unauth). 
MiSA offers flexible and multiplexed fluid control for various applications, providing a constant flow rate via pressure-based feedback control with 10-plex capability and transient flow by rapidly opening and closing pressure valves. The detailed build instructions are [here](https://www.rsc.org/suppdata/d5/lc/d5lc00551e/d5lc00551e1.pdf).
(Note: The parts list is missing connectors (S070-14A, SMC) for the Solenoid valves (S070B-5BC, SMC).)
MiSA works on GUI-based Python code that communicates with devices through an Arduino micro via a serial connection using pySerial.
We provide the program for the Arduino micro as [another repository](https://github.com/LiMe-NanoBioeng/Arduino-to-DAQ.git).

## HybISS-MiSA
To automate HybISS protocol with MiSA, we integrate the MiSA with a selector valve (IDEX Health & Science, MXX778-605), a ThermoPlate, and a microscope via pycromanager.






