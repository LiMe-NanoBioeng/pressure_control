# -*- coding: utf-8 -*-
"""
Created on Sat Mar  2 22:20:46 2019

@author: shintaku

Update: 2020-11-05, kaneko
"""

import time, datetime, os, serial

ser = serial.Serial('COM8', 9600, timeout=1)

class AI():  
    def DefFile(FolderName1): # Making Folder for saving outputs
           
        FolderName1=FolderName1+"/"+str(datetime.datetime.today().strftime("%Y%m%d"))
        os.makedirs(FolderName1,exist_ok=True)
        
        FileName=str(datetime.datetime.
                     today().strftime("%Y%m%d_%H%M%S"))+'_exp'
        FileName1=FolderName1+"/"+FileName+str(1+len([x for x in os.listdir(FolderName1) if x.endswith(".csv")])).zfill(4)
        return(FileName1)
        

    def ArduinoAI(x,y,c):
        #ser.flushInput()
        #ser.open()
        
        # Initialize c[]
        c = []

        # Read analog input of AN4-5
        ser.write(b'AI6')
        
        # Arduino will return the read value of analog input
        # format: AN1, AN2, ...
        ser_bytes = ser.readline().decode("utf-8")
        decoded_bytes = ser_bytes.strip()
        
        # x and y are sequential data from the begining
        x.append(time.time())
        y.extend(decoded_bytes.split(","))

        # c is a temporal data
        c.append(time.time())
        c.extend(decoded_bytes.split(","))

        if c[1] == '':  # if faied in obtaining data
            c[1] = 0
#            c.extend([0,0])
            
        for i in range(len(c)): # range(X):Xはチャンネル数
            #print(c)
            c[i] = float(c[i]) # listをfloat形式に変換
 
        return(x,y,c)
    
    # Control Valve    
    def ArduinoDO(channel,flag):
        #ser.flushInput() 
        if flag:
            Dout = 'DO' + str(channel) + 'H\n'   
        else:
            Dout = 'DO' + str(channel) + 'L\n'
        ser.write(Dout.encode('utf-8'))
        #print(str(channel))
            
    def ArduinoDP(ch,pulsewidth,duty,number):
        command = str.encode("DP:"+str(ch)+":"+str(int(pulsewidth))+":"+str(duty)+":"+str(number)+"\n")
        ser.write(command)
        
    def ArduinoAO(channel,flag,values):
        #ser = serial.Serial('COM3',9600,timeout=1)
        #ser.flushInput()
#        AO9out = 'AO9v' + str(values[1]*50) + '\n'
#        AO10out = 'AO10v' + str(values[2]*50) + '\n'
#        AO11out = 'AO11v' + str(values[3]*50) + '\n'
        if flag == True:
            AO6out = 'AO'+str(channel)+'v'+ str(values*50) + '\n'
        #import serial
#            ser.write(AO9out.encode('utf-8'))
#            ser.write(AO10out.encode('utf-8'))
#            ser.write(AO11out.encode('utf-8'))
        else:
            AO6out = 'AO'+str(channel)+'v'+'0\n'
#            ser.write(b'AO6v0\n')
#            ser.write(b'AO9v0\n')
#            ser.write(b'AO10v0\n')
#            ser.write(b'AO11v0\n')
        #print('AO6v1000')
        #ser.close()
        ser.write(AO6out.encode('utf-8'))
        
    def NIDAQAI(x,y):
        import nidaqmx
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan("Dev2/ai0:3",
                                                    terminal_config=nidaqmx.constants.TerminalConfiguration.RSE)
            x.append(time.time())
            y.extend(task.read(number_of_samples_per_channel=1))
            return(x,y)

    def NIDAQ_Stream():
        import numpy
        import nidaqmx
        from nidaqmx.stream_readers import (AnalogSingleChannelReader, AnalogMultiChannelReader)
        from nidaqmx.constants import (Edge, Slope)
        from nidaqmx._task_modules.triggering.start_trigger import StartTrigger
        
        #from nidaqmx.tests.fixtures import x_series_device
        #        import nidaqmx.task as task
        data= numpy.zeros((3,100), dtype=numpy.float64)
        
        with nidaqmx.Task() as read_task:
            read_task.ai_channels.add_ai_voltage_chan("Dev2/ai0:2",
                                             terminal_config=nidaqmx.constants.TerminalConfiguration.RSE)

            read_task.timing.cfg_samp_clk_timing(1e4, active_edge=Edge.RISING,samps_per_chan=100)
            read_task.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source="/Dev2/PFI0")
            #read_task.timing.delay_from_samp_clk_delay=0
            #s=nidaqmx.stream_readers.AnalogMultiChannelReader()
            
            reader=AnalogMultiChannelReader(read_task.in_stream)
            reader.read_many_sample(data, number_of_samples_per_channel=100,timeout=10)
            # print(data)
            return(data)
            
    def NIDAQ_DO():
        import nidaqmx
        from nidaqmx.constants import LineGrouping
        import visa, time
        rm = visa.ResourceManager()
        wv = rm.get_instrument("USB0::0x0D4A::0x000D::9148960::INSTR")
        wv.write(':TRIGger1:SEQuence:IMMediate')
        
        with nidaqmx.Task () as task:
            task.do_channels.add_do_chan("Dev1/port1/line7",
                                         line_grouping=LineGrouping.CHAN_PER_LINE)
            task.write(True,auto_start=True)
#           time.sleep(1)
            task.write(False,auto_start=True)
