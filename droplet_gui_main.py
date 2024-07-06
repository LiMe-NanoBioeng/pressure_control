# -*- coding: utf-8 -*-

import sys

import numpy as np
from NIDAQ_plt3 import AI as NI
import tkinter.filedialog, os

import time
from PyQt5 import QtWidgets, QtCore, QtGui
from droplet_gui import Ui_Droplet_formation
from matplotlibwidget import MatplotlibWidget
from MXsII import MXsIIt as MXsII
# from simple_pid import PID


class wavefunc():
    def wf1974(exposure, laser, dt):
        import visa
#        float exposure
#        float width1; float width2
        rm = visa.ResourceManager()
        # wv = rm.get_instrument("USB0::0x0D4A::0x000E::9137840::INSTR")
        wv = rm.get_instrument("USB0::0x0D4A::0x000D::9148960::INSTR")
        #print(wv.query('*IDN?'))
        wv.write(':SOURce1:VOLTage:LEVel:IMMediate:AMPLitude 5.0; OFFSet 2.5')
        # wv.write(':SOURce2:VOLTage:LEVel:IMMediate:AMPLitude 5.0; OFFSet 2.5')
        numofpulse=100
        numofpulse=str(numofpulse)
        wv.write(':SOURce1:BURSt:TRIGger:NCYCles '+ numofpulse)#number of cycles output onw
        # wv.write(':SOURce2:BURSt:TRIGger:NCYCles '+ numofpulse)#number of cycles output two
        wv.write(':SOURce1:FUNCtion:SHAPe PULSe')
        # wv.write(':SOURce2:FUNCtion:SHAPe PULSe')
        wv.write(':TRIGger1:BURSt:SOURce EXT')
        # wv.write(':TRIGger2:BURSt:SOURce EXT')
        width1=exposure-0.002
        width2=dt-laser
        delay=exposure-dt+laser/2
        wv.write(':SOURce1:PULSe:PERiod '+str(exposure)+'ms')#control the pulse period of output1
        # wv.write(':SOURce2:PULSe:PERiod '+str(dt)+'ms')#control the pulse period of output2
        wv.write(':SOURce1:PULSe:WIDTh '+str(width1)+'ms')#control the pulse width of output one
        # wv.write(':SOURce2:PULSe:WIDTh '+str(width2)+'ms')#control the pulse width of output two
        wv.write(':SOURce1:BURSt:TGATe:OSTop CYCLe')
        # wv.write(':SOURce2:BURSt:TGATe:OSTop CYCLe')
        # wv.write(':SOURce2:BURSt:SLEVel 100PCT')
        # wv.write(':SOURce2:PHAse:ADJust -180DEG')
        wv.write(':SOURce1:BURSt:TDELay 400ms')
        # wv.write(':SOURce2:BURSt:TDELay '+str(delay)+'ms')
        wv.write('OUTPut1:STATe ON')
        # wv.write('OUTPut2:STATe ON')
        
class MainWindow(QtWidgets.QMainWindow):    
    def __init__(self, parent=None):
        global ui  
        super(MainWindow, self).__init__(parent=parent)
        ui = Ui_Droplet_formation()
        ui.t=[]
        ui.dt=[]
        ui.c=[]
        ui.f=[]
        ui.voltage1=[0,0,0,0,0,0,0,0,0,0]    
        ui.setupUi(self)
        ui.comboBox.addItems(['1','2','3','4','5','6','7','8','9','10'])
        ui.graphwidget = MatplotlibWidget(ui.centralwidget,
                 xlim=None, ylim=None, xscale='linear', yscale='linear',
                 width=12, height=3, dpi=100)
        
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_figure)
        timer.start()  
        ui.save=False
        ui.valve_1=[False,False,False,False,False,False,False,False,False,False]
        # for icnt in range(len(ui.valve_1)):
        #     NI.ArduinoDO(icnt,ui.valve_1[icnt])
        self.open_single_valve(-1, 0)
        NI.ArduinoAO(11,False, 0)
        
        ui.Filename=' '
        ui.Foldername='C:/Users/Microfluidics-team'
        ui.value=0
        ui.residualtime=0
        ui.start=time.time()
        ui.duration=0
        ui.RunSequenceFlag=False
        ui.number_of_commands=0
        ui.command=1
    def open_single_valve(self,index,duration):
        for i in range(len(ui.valve_1)):
            if i != index-1:
                ui.valve_1[i]=False
            else:
                ui.valve_1[i]=True
            NI.ArduinoDO(i,ui.valve_1[i])    
        ui.start=time.time()
        ui.duration=duration
    def PID(self,Kp, Ki, Kd, setpoint, integral,dt):
        # global time, integral, time_prev, e_prev
        max_val=500
        # Value of offset - when the error is equal zero
        offset = 0
        measurement = np.median([ui.f[-3],ui.f[-2],ui.f[-1]])
        pre_measurement = np.median([ui.f[-4],ui.f[-3],ui.f[-2]])
                                
        # PID calculations
        e = float(setpoint - measurement)
        e_prev=float(setpoint-pre_measurement)
        
        P = max(min(Kp*e,max_val),-max_val)
        integral = integral + max(min(Ki*e*dt,max_val),-max_val)
        D = max(min(Kd*(e - e_prev)/dt,max_val),-max_val)

        # calculate manipulated variable - MV 
        MV = offset + P + integral + D
        #print(str(setpoint) + "," + str(int(MV)) + "," + str(integral))
        MV=max(min(MV,64*50),0)
        # update stored data for next iteration
    #    e_prev = e
    #    time_prev = time
        return(MV,e)
    def SequenceControlTime(self):
        Kp=1.2
        Ki=0.03
        Kd=0.3
        elapsed_time = time.time()-ui.start
        ui.residualtime=ui.duration-elapsed_time
        ui.lcdTimer.display(ui.residualtime)
        #ui.residualtime=ui.duration-(time.time()-ui.start)
        MV=0
        e=0
        if ui.number_of_commands-ui.command>0:
            #commands during the sequence
            ui.lcdTimer.display(ui.residualtime)
            if ui.residualtime >0 :
                # ui.command proceeds when the seq proceeds.
                # thus, we refer the valve number and values at ui.command -1 
                valve, valve_num,pressure,duration = self.read_seq_commands(ui.command-1)                
                
                MV,e = self.PID(Kp,Ki,Kd,pressure,
                                ui.voltage1[valve_num-1],
                                ui.dt[-1]-ui.dt[-2])
                MV=int(MV)
                ui.voltage1[valve_num-1]=MV
                NI.ArduinoAO(11,True,MV)
            else:
                # proceeds when the ui.residual time is less than 0 (wh\en negative)
                valve, valve_num,pressure,duration = self.read_seq_commands(ui.command)
                ui.voltage1[valve_num-1]=pressure # register pressure value
                NI.ArduinoAO(11,False, 0)
                self.open_single_valve(-1, 0)
                #
                # send commands when switch the sequence
                MXsII.FTWrite(str(valve)+ '\r') # switch the valve
                time.sleep(1)
                # send pressure value
                #NI.ArduinoAO(11,True,pressure)
                self.open_single_valve(valve_num,duration)
                # proceedsd ui.command
                ui.command+=1
        else:
            #commands at the end of the sequence (when ui.number_of_commands-ui.command==0)
            if ui.residualtime >0 :
                valve, valve_num,pressure,duration = self.read_seq_commands(ui.command-1)
                MV,e = self.PID(Kp,Ki,Kd,pressure,
                                ui.voltage1[valve_num-1],
                                ui.dt[-1]-ui.dt[-2]) 
                MV=int(MV)     
                ui.voltage1[valve_num-1]=MV
                NI.ArduinoAO(11,True,MV)
            elif ui.number_of_commands !=0 :
                #commands at the end of the last sequence
                for i in range(len(ui.valve_1)):
                    ui.valve_1[i]=False
                    NI.ArduinoDO(i,ui.valve_1[i])
                ui.number_of_commands=0
                time.sleep(1)
                   
        # print(str(MV)+"," + str(ui.f[-1])+ "," + str(e))

    def read_seq_commands(self, command):
        text=ui.tableWidget.item(command,0).text()
        message=text.split(',')
        valve=message[0] # valve number
        pressure=float(message[1]) # pressure value
        duration = int(message[2].rstrip())
        valve_num=int(valve[-1],16)
        return(valve, valve_num,pressure,duration)
    def draw_graph(self):
        ui.graphwidget.figure.clear()
        ui.graphwidget.axes = ui.graphwidget.figure.add_subplot(131)
        ui.graphwidget.axes.clear()
        ui.graphwidget.x  = ui.dt
        ui.graphwidget.y  = ui.CA1          
        ui.graphwidget.axes.plot(ui.graphwidget.x,ui.graphwidget.y)
        ui.graphwidget.draw()

        ui.graphwidget.axes = ui.graphwidget.figure.add_subplot(132)
        ui.graphwidget.axes.clear()
        ui.graphwidget.x  = ui.dt
        ui.graphwidget.y  = ui.f        
        ui.graphwidget.axes.plot(ui.graphwidget.x,ui.graphwidget.y)
        ui.graphwidget.draw()
        
        ui.graphwidget.axes = ui.graphwidget.figure.add_subplot(133)
        ui.graphwidget.axes.clear()
        ui.graphwidget.x  = ui.dt
        ui.graphwidget.y  = ui.q
        ui.graphwidget.axes.plot(ui.graphwidget.x,ui.graphwidget.y)
        ui.graphwidget.draw()        
    def update_figure(self):

        f=NI.ArduinoI2C()
        f=float(f)/32767*1000
        time,c,r=NI.ArduinoAI()
        if r :
            c[0]=0.1208*c[0]-23.75
            if ui.save == True:
                # add Hiroyuki
                if ui.count != 0:
                    # ui.count = 0で新規file open 
                    #ui.t = np.append(ui.t,time)
                    ui.dt= np.append(ui.dt,time-ui.t)
                    ui.CA1 = np.append(ui.CA1,c[0])
                    ui.f=np.append(ui.f,f)
                    if ui.count !=1: # compute integrated flow quantity at t > 1 
                        q=ui.q[-1]+f*(ui.dt[-1]-ui.dt[-2])/60
                    else: # compute integrated flow quantity at t=1
                        q=f*(ui.dt[-1])/60
                    ui.q=np.append(ui.q,q)                    
                    c=np.append(np.append(np.append(round(ui.dt[-1],6),c),float(f)),float(q))
                    self.draw_graph()

                    file = open(ui.Filename, 'a')
                else:
                    ui.t=time # initial time
                    ui.dt = time-ui.t
                    ui.CA1  = c[0]
                    ui.f=f
                    ui.q=0
                    file = open(ui.Filename, 'w')
                    c=np.append(np.append(np.append(round(ui.dt,6),c),float(f)),float(ui.q))
                
                ui.count = ui.count + 1
                

                for i in c:
                    jp = (str(i))
                    file.write(jp)
                    file.write(',') # コンマ
                file.write('\n')  # 改行コード
                file.close()
    
                
            else:
                ui.count = 0 # add Hiroyuki
                ui.valveLcd_1.display(c[0])
                ui.flowrate.display(f)
            # counter Display
            # 
            if ui.number_of_commands != 0:
                self.SequenceControlTime()
                    
            #     

            
                 


    def RunSequence(self):
        ui.command=0
        ui.number_of_commands= ui.tableWidget.rowCount()

           

    def openSeqFile(self):
        fTyp = [("SequenceFile", "*.txt")]
        iDir = os.path.abspath(os.path.dirname(__file__))
        file_name = tkinter.filedialog.askopenfilename(filetypes=fTyp, initialdir=iDir)
        f=open(file_name,'r')
        
        #ui.tableWidget.setRowCount(0)
        ui.tableWidget.setColumnCount(1)
        rowPosition=0
        for x in f:
            ui.tableWidget.insertRow(rowPosition)
            ui.tableWidget.setItem(rowPosition, 0, QtWidgets.QTableWidgetItem(x))
            rowPosition+=1


    def valve_number_changed(self,index):
        ui.selected_valve_index_index=index
        valvenum=str(hex(ui.selected_valve_index_index+1).upper())
        message = 'P0' + valvenum[-1] + '\r'
        ui.lcdnumber_1.display(ui.voltage1[ui.selected_valve_index_index])
        MXsII.FTWrite(message) 
        # Recordbutton    
    def recordIO(self):
        ui.save = not ui.save
        if ui.save == True:
            ui.Filename = NI.DefFile(ui.Foldername)
    
    # ValveBotton_1
    def ValveOC(self):
        ui.valve_1[ui.selected_valve_index_index] = not ui.valve_1[ui.selected_valve_index_index]
        s=NI.ArduinoDO(ui.selected_valve_index_index,ui.valve_1[ui.selected_valve_index_index])
        
        
    def svalue_changed(self):
        ui.voltage1[ui.selected_valve_index_index]=ui.horizontalSlider.value()
        ui.lcdnumber_1.display(ui.horizontalSlider.value())
        NI.ArduinoAO(11,True, ui.voltage1[ui.selected_valve_index_index])

        
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())