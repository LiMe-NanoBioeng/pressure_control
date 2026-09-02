# MiSA as an automated microfluidic controller
![MiSA system](https://static.wixstatic.com/media/ac6344_fcc36213162a4f77aa4f625d5739c330~mv2.png)
## MiSA
MiSA is an open-source device for [microfluidic sequence automation](https://pubs.rsc.org/en/content/articlelanding/2025/lc/d5lc00551e/unauth). 
MiSA offers flexible and multiplexed fluid control for various applications, providing a constant flow rate via pressure-based feedback control with 10-plex capability and transient flow by rapidly opening and closing pressure valves. The detailed build instructions are [here](https://www.rsc.org/suppdata/d5/lc/d5lc00551e/d5lc00551e1.pdf).

MiSA works on GUI-based Python code that communicates with devices through an Arduino micro via a serial connection using pySerial.
We provide the program for the Arduino micro as [another repository](https://github.com/LiMe-NanoBioeng/Arduino-to-DAQ.git).

### Update:

-　The parts list is missing connectors (S070-14A, SMC) for the solenoid valves (S070B-5BC, SMC).  
-　The latching valve (FLV2-N1F, Takasago Electric) becomes unstable when continuously operated. We recommend NLV-2-N1G (Takasago Electric) instead of FLV2-N1F.  
-　We use PEEK Luer-lock-adapters [PS6601](https://www.isis-ltd.co.jp/product/tube-connector-valve/adapter-connector/A107) to connect phi3 tubes to 1/16" tubes.  

### Circuit Design
-[ver 1.0.0](https://ac63445c-dd2d-48c4-b03c-9c81ed2f14bc.usrfiles.com/ugd/ac6344_7c2367e04c394b84b0bb4f0bfbd53f81.pdf).  
-　Added GND terminal for 5V switching.  
-　Updated the silk screen.  

-[ver 0.2.2](https://ac63445c-dd2d-48c4-b03c-9c81ed2f14bc.usrfiles.com/ugd/ac6344_b9b48091d1b346df86037f14fb917185.pdf).  
-　Added TTL and 5V switching for latching solenoid valve.  
-　Added ports for D0, reset, D11, and 3V.  

-[ver 0.2.1](https://ac63445c-dd2d-48c4-b03c-9c81ed2f14bc.usrfiles.com/ugd/ac6344_4acba23fb57944239136985bc084c761.pdf).  
-　Added I2C communication.  

-[ver 0.1.0](https://ac63445c-dd2d-48c4-b03c-9c81ed2f14bc.usrfiles.com/ugd/ac6344_303ffac2c8ba416eb04ca054ac08d01f.pdf).

## HybISS-MiSA
To automate HybISS protocol with MiSA, we integrate the MiSA with a selector valve (IDEX Health & Science, MXX778-605), a ThermoPlate, and a microscope via pycromanager.
install [pycromanager](https://pycro-manager.readthedocs.io/en/latest/index.html) for micro-manager, [pymobus](https://pypi.org/project/pymodbus/) for Thermoplate, and [pytest](https://pypi.org/project/pytest/).


### Sequece file format
"P01,200u,400u,0.16;0.022;0.1" are respectively [Valve position],[parameter1&mode],[parameter2&unit],[P,I,D parameters].

-　[parameter1&mode] The parameter1 is an integer number for the condition. The mode can be p, u, a, or c, which respectively stand for Pa, uL/min, acquisition, or Celsius, respectively.  
50p means 50Pa. 50u meands 50uL/min. 0a means acquire images (specify MDA and position files in advance),500c means 50.0 celsius.   
-　[parameter2&unit]: The parameter2 is an integer number for a stop condition. The unit can be u or s, which mean uL or seconds.  
-　[P,I,D parameters]: The P,I,D parameters are paramters for PID control.  
-　[stability watchdog] (optional, requires the P,I,D field to be present): "\<a|l\>\<tolerance\>per[,\<duration\>s]". Only applies to 'u' mode steps. 'a' aborts the sequence (closes valves, stops PID, pops up a message) if the flow rate stays outside +/-tolerance% of the setpoint for longer than duration seconds; 'l' just logs a warning instead of aborting. The watchdog arms once flow first enters the tolerance band, so filling an empty line doesn't trigger it (default 120s allowed to first reach the band). Omit entirely to leave the watchdog off (default, and the only behavior for all pre-existing sequence files).

### Sequence-wide pressure limit (optional)
Put a line like "a30kPa,60s" as the very **first line** of the file, before any step, to abort (or "l30kPa,60s" to just log) if pressure stays above 30 kPa for a continuous 60s at any point in the run — regardless of which step or mode is active. Protects the sample from prolonged high-pressure exposure. Omit this line entirely to leave it disabled.

example: 
-　P01,30u,50u,0.16;0.022;0.1,a50per,10s: flow rate of 30 uL/min until 50 uL has been pumped; abort if flow strays outside +/-50% of 30 uL/min for more than 10s (after first reaching that band).  
-　P01,0u,20s: This means at valve position 01 with a flow rate of 0 uL/min for 20s.  
-　P03,400c,0s: This means setting temerature of the thermoplate at 40.0c.  





