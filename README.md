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

## HybISS-MiSA
To automate HybISS protocol with MiSA, we integrate the MiSA with a selector valve (IDEX Health & Science, MXX778-605), a ThermoPlate, and a microscope via pycromanager.






