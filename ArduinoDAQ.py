# -*- coding: utf-8 -*-
"""
Created on Sat Mar  2 22:20:46 2019

@author: shintaku

Update: 2020-11-05, kaneko
"""

import time, datetime, os, serial, threading, contextlib, atexit
from config import config
conf=config()

"""
provide definition of Arduino pins
Analog IN 6,7,8,11
Analog OUT
Digital Out

"""
ser = serial.Serial()
ser.port    = conf.ARDUINO_PORT
ser.baudrate = 9600
ser.timeout  = 1  # NEVER CHANGE FROM 9600. Be patient...

_lock = threading.Lock()

@contextlib.contextmanager
def _serial_lock():
    with _lock:
        if not ser.is_open:
            ser.open()
        yield

atexit.register(lambda: ser.close() if ser.is_open else None)

class AI():
    def DefFile(FolderName1): # Making Folder for saving outputs

        FolderName1=FolderName1+"/"+str(datetime.datetime.today().strftime("%Y%m%d"))
        os.makedirs(FolderName1,exist_ok=True)

        FileName=str(datetime.datetime.
                     today().strftime("%Y%m%d_%H%M%S"))+'_exp'
        FileName1=FolderName1+"/"+FileName+str(1+len([x for x in os.listdir(FolderName1) if x.endswith(".txt")])).zfill(4)+".txt"
        return(FileName1)
    def ArduinoStatusCheck():
        with _serial_lock():
            ser.reset_input_buffer()  # flush stale bytes so we read only the fresh reply
            ser.write(b'S')
            time.sleep(0.01)
            waiting = max(ser.in_waiting, 1)
            ser_bytes = ser.read(waiting).decode("utf-8", errors='ignore')
        return 'R' if 'R' in ser_bytes else ''
    def ArduinoFBStatus(vNumA):
        with _serial_lock():
            ser.write(b'R')
            time.sleep(0.1)
            ser_bytes = ser.readline().decode("utf-8")
        return ser_bytes.strip()
    def ArduinoFB(value,vNumA,setpoint,Kp,Ki,Kd):
        if value==True:
            text='FB' + str(vNumA) + ',' + str(setpoint) + ',' + str(Kp) + ',' + str(Ki) + ',' + str(Kd) +'\n'
            with _serial_lock():
                ser.write(text.encode('utf-8'))
                time.sleep(0.1)
        else:
            with _serial_lock():
                ser.write(b'B')
                time.sleep(0.1)
    def ArduinoI2C():
        with _serial_lock():
            ser.write(b'II\n')
            time.sleep(0.01)
            ser_bytes = ser.readline()
        ser_bytes=ser_bytes.decode('utf-8').rstrip()
        return(float(ser_bytes))


    # Arduino Aquire Flowrate Unit
    def ArduinoAFU():
        with _serial_lock():
            ser.write(b'IU\n')
            time.sleep(0.01)
            ser_bytes=ser.readline()
        ser_bytes=ser_bytes.decode('utf-8').rstrip()
        return(str(ser_bytes))

    def ArduinoAI():
        with _serial_lock():
            ser.reset_input_buffer()
            ser.write(b'AI6,7\n')
            time.sleep(0.01)
            ser_bytes = ser.readline()
        t = time.time()
        try:
            text = ser_bytes.decode('utf-8', errors='ignore').strip()
            text = text.replace('R', '')  # strip stray status bytes
            fields = [f for f in text.split(',') if f]  # drop empty fields
            if not fields:
                return (t, [0, 0], False)
            c = [float(f) for f in fields]
            return (t, c, True)
        except Exception:
            return (t, [0, 0], False)

    def ArduinoAI8():
        with _serial_lock():
            ser.reset_input_buffer()
            ser.write(b'AI8\n')
            time.sleep(0.01)
            ser_bytes = ser.readline()
        try:
            text = ser_bytes.decode('utf-8', errors='ignore').strip().replace('R', '')
            return float(text)
        except Exception:
            return -1.0

    def ArduinoTuning():
        #potentiometer calcuration
        with _serial_lock():
            ser.write(b'AI8\n')
            time.sleep(0.1)
            r1 = ser.readline().decode('utf-8')
        with _serial_lock():
            ser.write(b'AI11\n')
            time.sleep(0.1)
            r2 = ser.readline().decode('utf-8')
        print("r1",r1)
        print("r2",r2)
        potentio=float(r1)/(float(r2)+0.0001)
        print(r1,r2)
        print(potentio)
        return potentio;


    # Control Valve
    def ArduinoDO(channel,flag):
        if flag:
            Dout = 'DO' + str(channel) + 'H\n'
        else:
            Dout = 'DO' + str(channel) + 'L\n'
        with _serial_lock():
            ser.write(Dout.encode('utf-8'))
            ser_bytes = ser.readline().decode('utf-8')
        return(ser_bytes.strip())

    def ArduinoDP(ch,pulsewidth,duty,number,threshold):
        text = 'DP'+str(ch)+':'+str(int(pulsewidth))+':'+str(duty)+':'+str(number)+'\n'
        with _serial_lock():
            ser.write(text.encode('utf-8'))
    def ArduinoDigitalPulse(ch1,ch2,delay,width,threshold):
        # text = 'PP'+str(ch1)+':'+str(ch2)+','+str(int(delay))+','+str(width)+'\n'
        text = 'PP'+str(ch1)+','+str(ch2)+','+str(int(delay))+','+str(width)+','+'8'+','+str(int(threshold))+'\n' #use for two valves in pulse
        with _serial_lock():
            ser.write(text.encode('utf-8'))
    def ArduinoAO(channel,flag,values):
        if flag == True:
            AO6out = 'AO'+str(channel)+'v'+ str(values) + '\n'
        else:
            AO6out = 'AO'+str(channel)+'v'+'0\n'
        with _serial_lock():
            ser.write(AO6out.encode('utf-8'))

    def ArduinoReset():
        with _serial_lock():
            ser.write(b'B')
            time.sleep(0.5)
            ser.reset_input_buffer()

    #K2 added
    def Arduinobye():
        if ser.is_open:
            ser.close()

