# -*- coding: utf-8 -*-
"""
Created on Sat Mar  2 22:20:46 2019

@author: shintaku

Update: 2020-11-05, kaneko
"""

import time, datetime, os, serial

ser = serial.Serial('COM11', 9600, timeout=1)

class AI():  
    def DefFile(FolderName1): # Making Folder for saving outputs
           
        FolderName1=FolderName1+"/"+str(datetime.datetime.today().strftime("%Y%m%d"))
        os.makedirs(FolderName1,exist_ok=True)
        
        FileName=str(datetime.datetime.
                     today().strftime("%Y%m%d_%H%M%S"))+'_exp'
        FileName1=FolderName1+"/"+FileName+str(1+len([x for x in os.listdir(FolderName1) if x.endswith(".csv")])).zfill(4)
        return(FileName1)
    def ArduinoFBStatus(vNumA):
        ser.write(b'R')
        time.sleep(0.1)
        ser_bytes = ser.readline().decode("utf-8")
        return(ser_bytes.strip())
    def ArduinoFB(value,vNumA,setpoint,Kp,Ki,Kd):
        if value==True:
            text='FB' + str(vNumA) + ',' + str(setpoint) + ',' + str(Kp) + ',' + str(Ki) + ',' + str(Kd) +'\n'
            ser.write(text.encode('utf-8'))
            time.sleep(0.2)
        else:
            ser.write(b'B')
    def ArduinoI2C():
        ser.write(b'II')
        time.sleep(0.1)
        ser_bytes = ser.readline().decode('utf-8')
        ser_bytes=ser_bytes.rstrip()
        return(float(ser_bytes))

    def ArduinoAI():        
        c = []
        # Read analog input of AN4-5
        ser.write(b'AI6,7')
        time.sleep(0.2)
        # Arduino will return the read value of analog input
        # format: AN1, AN2, ...
        ser_bytes = ser.readline().decode('utf-8')
        decoded_bytes = ser_bytes.strip()
        
        # x and y are sequential data from the begining
#        x.append(time.time())
#        y.extend(decoded_bytes.split(","))

        # c is a temporal data
        t = time.time()
        c=decoded_bytes.split(",")

        if c[0] == '':  # if faied in obtaining data
            c[0] = 0
            result= False
        else:
            result=True    
        for i in range(len(c)): # range(X):Xはチャンネル数
            c[i] = float(c[i]) # listをfloat形式に変換
        return(t,c,result)
    
    # Control Valve    
    def ArduinoDO(channel,flag):
        if flag:
            Dout = 'DO' + str(channel) + 'H\n'   
        else:
            Dout = 'DO' + str(channel) + 'L\n'
        ser.write(Dout.encode('utf-8'))
        ser_bytes = ser.readline().decode('utf-8')
        return(ser_bytes.strip())

    def ArduinoDP(ch,pulsewidth,duty,number):
        text = 'DP'+str(ch)+':'+str(int(pulsewidth))+':'+str(duty)+':'+str(number)+'\n'
        ser.write(text.encode('utf-8'))
    def ArduinoDigitalPulse(ch1,ch2,delay,width):
        text = 'PP'+str(ch1)+':'+str(ch2)+','+str(int(delay))+','+str(width)+'\n'
        ser.write(text.encode('utf-8'))
        # time.sleep(delay+width)
    def ArduinoAO(channel,flag,values):
        if flag == True:
            AO6out = 'AO'+str(channel)+'v'+ str(values) + '\n'
        else:
            AO6out = 'AO'+str(channel)+'v'+'0\n'
        ser.write(AO6out.encode('utf-8'))
        
