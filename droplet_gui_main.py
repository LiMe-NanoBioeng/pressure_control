# -*- coding: utf-8 -*-

import sys
import numpy as np
from ArduinoDAQ import AI as NI
import tkinter.filedialog
import os
from os.path import expanduser
import serial
import time
from PyQt5 import QtWidgets, QtCore, QtGui
from droplet_gui import Ui_Droplet_formation
from matplotlibwidget import MatplotlibWidget
from MXsII import MXsIIt as MXsII
import datetime
now=datetime.datetime.now()
timestamp=now.strftime("%Y%m%d%H%M%S")
resultfilename="result"+timestamp
homedir=expanduser("~")

# operating=0;
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        global ui
        super(MainWindow, self).__init__(parent=parent)
        ui = Ui_Droplet_formation()
        ui.MXsII=False  # selector valve True/False
        ui.t = []
        ui.dt = []
        ui.c = []
        ui.f = []
        ui.voltage1 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        ui.setupUi(self)
        ui.comboBox.addItems(
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])
        ui.comboBox_2.addItems(
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])
        ui.graphwidget = MatplotlibWidget(ui.centralwidget,
                                          xlim=None, ylim=None, xscale='linear', yscale='linear',
                                          width=12, height=3, dpi=95)


        ui.timer= QtCore.QTimer(self)
        ui.timer.start(50)
        ui.timer.timeout.connect(self.update_figure)
        #K2 Added
       # ui.timer.timeout.connect(self.check_tuning)
        ui.save = False
        # valve initialization
        ui.valve_1 = [False, False, False, False,
                      False, False, False, False, False, False]
        self.open_single_valve(-1)
        #ui.vNumA=11
        # valve channels
        ui.vNumA=10 # first AO channel feedback channel
        ui.vNumB=9 # second AO channel
        NI.ArduinoFB(False,ui.vNumA,0,0,0,0)
        NI.ArduinoAO(ui.vNumA, False, 0)
        
        ui.Filename = ' '
        ui.Foldername = homedir
        ui.value = 0
        ui.residualtime = 0
        ui.start = time.time()
        ui.termination_mode=""
        ui.mode=""
        ui.qstart=0
        ui.volume=0
        ui.duration = 0
        ui.RunSequenceFlag = False
        ui.number_of_commands = 0
        ui.command = 1
        ui.pid_parameters = {}
        
       
        ui.tuning_is_running=False
        #JM added
        ui.valveButton_2.hide()
        ui.valveLcd_2.hide()
        ui.horizontalSlider_2.hide()
        ui.comboBox_2.hide()
        ui.label_8.hide()
        ui.lcdnumber_2.hide()
        ui.valveindex1=0
        ui.valveindex2=0
        ui.reg=0
        ui.actionITV0010_2.triggered.connect(lambda: self.function_change(0))
        ui.actionITV0030_2.triggered.connect(lambda: self.function_change(1))
        ui.actionITV0090.triggered.connect(lambda: self.function_change(2)) 

    def open_single_valve(self, index):
        for i in range(len(ui.valve_1)):
            if i != index-1:
                ui.valve_1[i] = False
            else:
                ui.valve_1[i] = True
            NI.ArduinoDO(i, ui.valve_1[i])
        if any(ui.valve_1):  # open the check valve
            #s= NI.ArduinoDO(10, True)
            NI.ArduinoDO(10, True)
            print('LSV is open')
        else:
            #s=NI.ArduinoDO(10, False)
            NI.ArduinoDO(10, False)

    def SequenceControlTime(self):
        #Kp = ui.Kp #0.1
        #Ki = ui.Ki #0.001
        #Kd = ui.Kd #0.1
        Kp,Ki,Kd = ui.pid_parameters.get(ui.command,(0.1,0.001,0.1))
        
        elapsed_time = time.time()-ui.start
        residualvol=ui.volume-(ui.q[-1]-ui.qstart)
        ui.residualtime = ui.duration-elapsed_time
        
        # swtich modes between volume and time terminations
        if ui.termination_mode=="s": # time based
            residual=ui.residualtime
            ui.unit.setText("s")
        elif ui.termination_mode=="u": #volume based
            residual=residualvol
            ui.unit.setText("ul")
        else: #initial
            residual=-1
        ui.lcdTimer.display(residual)
        
        if ui.number_of_commands-ui.command > 0:
            # commands during the sequence
            # ui.lcdTimer.display(ui.residualtime)
            
            if residual > 0:
                value=NI.ArduinoFBStatus(ui.vNumA)
                ui.lcdnumber_1.display(value)
            else:
            #if residual <0:
                # proceeds when the ui.residual time is less than 0 (wh\en negative)
                valve, valve_num, pressure, duration,volume = self.read_seq_commands(
                    ui.command)
                ui.current_valve=valve
                ui.current_valve_num=valve_num
                ui.current_pressure=pressure # flow rate
                ui.duration = duration
                ui.volume=volume
                # ui.current_duration=duration
                ui.voltage1[valve_num-1] = pressure  # register pressure value
                
        
                #close valve
                self.open_single_valve(-1)
                MXsII.FTWrite(str(valve) + '\r')  # switch the valve
                # send commands when switch the sequence
                #time.sleep(1)
                
                NI.ArduinoFB(False,ui.vNumA,ui.current_pressure,Kp,Ki,Kd)
                NI.ArduinoAO(ui.vNumA, False, 0)
                
                #MXsII.FTWrite(str(valve) + '\r')  # switch the valve
                time.sleep(1)
                # send pressure value
                # NI.ArduinoAO(ui.vNumA,True,pressure)
                # global operating
                if ui.mode=="p":#open loop
                    # self.open_single_valve(valve_num)
                    # NI.ArduinoAO(ui.vNumA, True, int(pressure/100*255))
                    NI.ArduinoAO(ui.vNumA, True, int(pressure))
                    self.open_single_valve(valve_num)
                else: # closed loop
                    if pressure >0:
                        self.open_single_valve(valve_num)
                        NI.ArduinoFB(True,ui.vNumA,ui.current_pressure,Kp,Ki,Kd)
                        # operating=1
                    else:
                        NI.ArduinoFB(False,ui.vNumA,ui.current_pressure,Kp,Ki,Kd) 
                        NI.ArduinoAO(ui.vNumA, False, 0)
                        # operating =0
                    
                ui.start = time.time()
                ui.qstart=ui.q[-1]
                # proceedsd ui.command
                ui.command += 1
                ui.lcdSeqNumber.display(ui.command)
        else:
            # commands at the end of the sequence (when ui.number_of_commands-ui.command==0)
            if residual > 0:
                value=NI.ArduinoFBStatus(ui.vNumA)
                ui.lcdnumber_1.display(value)

            elif ui.number_of_commands != 0:
            #if ui.number_of_commands !=0 and residual <0 :
                NI.ArduinoFB(False,ui.vNumA,ui.current_pressure,Kp,Ki,Kd)
                NI.ArduinoAO(ui.vNumA, False, 0)
                value=NI.ArduinoFBStatus(ui.vNumA)
                ui.lcdnumber_1.display(value)
            # # commands at the end of the last sequence
                self.open_single_valve(-1)
                ui.number_of_commands = 0
                ui.save = not ui.save  # stop saving and displaying
                ui.lcdSeqNumber.display(ui.number_of_commands)
                time.sleep(1)
   
    def DigitalPulse(self):
        ui.mode='Pulse'
        a = ui.valveindex1
        b = ui.valveindex2
        width = ui.plainTextEdit.toPlainText()
        #print(width)
        c = float(width)
        NI.ArduinoDigitalPulse(a,b,1,c,10) # 100 is the threshold
        #NI.ArduinoDigitalPulse(0,1,1,0.1)
        # valve numberが　ひとつめとふたつ目に入るようにする
    
    def SinglePressure(self):# add JM
        #print('work well')
        ui.valveButton_2.hide()
        ui.valveLcd_2.hide()
        ui.horizontalSlider_2.hide()
        ui.comboBox_2.hide()
        ui.label_8.hide()
        ui.lcdnumber_2.hide()
        
    def DoublePressure(self):# add JM
        #print('work very well')
        ui.valveButton_2.show()
        ui.valveLcd_2.show()
        ui.horizontalSlider_2.show()
        ui.comboBox_2.show()
        ui.label_8.show()
        ui.lcdnumber_2.show()
        
    def read_seq_commands(self, command):
        text = ui.tableWidget.item(command, 0).text()
        message = text.split(',')
        valve = message[0]  # valve number
        
        pressure = float(message[1][:-1])# pressure value
        text = message[2].rstrip()
        if text[-1] =="s":
            duration=int(text[:-1])
            volume=0
        elif text[-1]=="u":
            #volume=int(text[:-1])
            volume=float(text[:-1])
            duration=0
                
        valve_num = int(valve[-1], 16)
        ui.termination_mode=text[-1]
        ui.mode=str(message[1][-1])
        
        #read PID parameters
        if len(message) > 3:
            Kp,Ki,Kd = map(float,message[3].split(';'))
            ui.pid_parameters[command] = (Kp,Ki,Kd)
        
        return (valve, valve_num, pressure, duration,volume)

    def draw_graph(self):
        ui.graphwidget.figure.clear()
        ui.graphwidget.axes.clear()
        ui.graphwidget.axes = ui.graphwidget.figure.add_subplot(131, xlabel = 'Time [s]', ylabel = 'Pressure [kPa]')
        #ui.graphwidget.axes.clear()
        ui.graphwidget.x = ui.dt
        ui.graphwidget.y = np.transpose(ui.CA1)
        ui.graphwidget.axes.plot(ui.graphwidget.x, ui.graphwidget.y)
        ui.graphwidget.draw()

                
        ui.graphwidget.axes = ui.graphwidget.figure.add_subplot(132, xlabel = 'Time [s]', ylabel = 'Flow rate [μL/min]')
        #ui.graphwidget.axes.clear()
        ui.graphwidget.x = ui.dt
        ui.graphwidget.y = ui.f
        ui.graphwidget.axes.plot(ui.graphwidget.x, ui.graphwidget.y)
        ui.graphwidget.draw()

        ui.graphwidget.axes = ui.graphwidget.figure.add_subplot(133, xlabel = 'Time [s]', ylabel = 'Pumped volume [μL]')
        #ui.graphwidget.axes.clear()
        ui.graphwidget.x = ui.dt
        ui.graphwidget.y = ui.q
        ui.graphwidget.axes.plot(ui.graphwidget.x, ui.graphwidget.y)    
        ui.graphwidget.figure.tight_layout()
        ui.graphwidget.draw()
    
    def function_change(self,index):
        ui.reg = index
            
    def update_figure(self):
        status = NI.ArduinoStatusCheck()
        if status =='R':
            time, c, r= NI.ArduinoAI()
            f = NI.ArduinoI2C()
            if r:
                g = [0.1208, 1.097, -0.1208]
                h = [-23.75, -223.75, 23.78]
                c[0] = g[ui.reg] * c[0] + h[ui.reg]
                c[1] = g[ui.reg] * c[1] + h[ui.reg]
                ui.valveLcd_1.display(c[0])
                ui.valveLcd_2.display(c[1]) #add JM
                if ui.save == True:
                    # add Hiroyuki
                    if ui.count != 0:
                        ui.dt = np.append(ui.dt, time-ui.t)
                        # ui.CA1 = np.append(ui.CA1, c)
                        ui.CA1 = np.c_[ui.CA1,c]
                        ui.f = np.append(ui.f, f)
                        if ui.count != 1:  # compute integrated flow quantity at t > 1
                            q = ui.q[-1]+np.median([ui.f[-3], ui.f[-2], ui.f[-1]])*(ui.dt[-1]-ui.dt[-2])/60
                        else:  # compute integrated flow quantity at t=1
                            q = f*(ui.dt[-1])/60
                        ui.q = np.append(ui.q, q)
    
                        c = np.append(
                            np.append(np.append(round(ui.dt[-1], 6), c), float(f)), float(q))
                        self.draw_graph()
    
                        file = open(ui.Filename, 'a')
                    else:
                        ui.t = time  # initial time
                        ui.dt = time-ui.t
                        ui.CA1 = c
                        ui.f = f
                        ui.q = 0
                        file = open(ui.Filename, 'w')
                        c = np.append(
                            np.append(np.append(round(ui.dt, 6), c), float(f)), float(ui.q))
    
                    ui.count = ui.count + 1
    
                    for i in c:
                        jp = (str(i))
                        file.write(jp)
                        file.write(',')  # コンマ
                    file.write('\n')  # 改行コード
                    file.close()
    
                else:
                    ui.count = 0  # add Hiroyuki
                ui.flowrate.display(f)
                # counter Display
                #
                if ui.number_of_commands != 0 and len(ui.f) > 4:
                    self.SequenceControlTime()
    

    def RunSequence(self):
        ui.command = 0
        ui.number_of_commands = ui.tableWidget.rowCount()

    def openSeqFile(self):
        fTyp = [("SequenceFile", "*.txt")]
        iDir = os.path.abspath(os.path.dirname(__file__))
        file_name = tkinter.filedialog.askopenfilename(
            filetypes=fTyp, initialdir=iDir)
        f = open(file_name, 'r')

        # ui.tableWidget.setRowCount(0)
        
        ui.tableWidget.setColumnCount(1)
        rowPosition = 0
        ui.tableWidget.setRowCount(0)
        #parameters=(f.readlines(1))
        #parameters=parameters[0].split(',')
        #ui.Kp=float(parameters[0])
        #ui.Ki=float(parameters[1])
        #ui.Kd=float(parameters[2].rstrip())
        for x in f:
            ui.tableWidget.insertRow(rowPosition)
            ui.tableWidget.setItem(
                rowPosition, 0, QtWidgets.QTableWidgetItem(x))
            rowPosition += 1

    def check_tuning(self):
        if ui.tuning_is_running:
            self.tuningCore()

    def tuning_resistanse_rate(self): # click tuning event
        if not ui.tuning_is_running:
            NI.ArduinoDO(0, True)
            print("number 1 opened")
            if ui.MXsII==True: MXsII.FTWrite(str(1) + '\r')
            NI.ArduinoAO(ui.vNumA, True, 100)
            #NI.ArduinoFB(True,10,50,1,1,1) 
            #ui.timer.timeout.connect(self.tuningCore)
            #ui.timer.start(100)
            ui.tuning_is_running=True
            NI.ArduinoDO(10, True)
        else:
            #ui.timer.stop()  # タイマーを停止
            ui.tuning_is_running = False
            NI.ArduinoAO(ui.vNumA, False, 100)
            #NI.ArduinoFB(False,10,0,0,0,0)
            NI.ArduinoDO(0, False)
            print("tuning ended")
            NI.ArduinoDO(10, False)
            
    def tuningCore(self):
        potentio = NI.ArduinoTuning() #time c,r　are not used in this stack
        displaypotentio="{:.3}".format(potentio)
        ui.resistance_rate.display(displaypotentio)
        maxflowrate = min(1000, 1000*potentio/0.6)
        print(maxflowrate)
        minflowrate = max(20,63.4*potentio-13.6)
        print(minflowrate)
        ui.maxflowrate.display(str(round(maxflowrate,1)))
        ui.minflowrate.display(str(round(minflowrate,1)))
        
        
    
    def valve_number_changed(self, index):
        #ui.selected_valve_index_index = index 
        ui.valveindex1=index
        valvenum = str(hex(index+1).upper())
        message = 'P0' + valvenum[-1] + '\r'
        ui.lcdnumber_1.display(ui.voltage1[index])
        ui.horizontalSlider.setValue(ui.voltage1[index])
        if hasattr(ui, 'valve_1'):
            if ui.valve_1[index]==True: 
                ui.valveButton_1.setText('ON')
            else: 
                ui.valveButton_1.setText('OFF')
            
        if ui.MXsII==True: MXsII.FTWrite(message)


    #add JM
    def valve2_number_changed(self, index):
        #ui.selected_valve_index_index = index
        ui.valveindex2=index
        valvenum = str(hex(index+1).upper())
        message = 'P0' + valvenum[-1] + '\r'
        ui.lcdnumber_2.display(ui.voltage1[index])
        ui.horizontalSlider.setValue(ui.voltage1[index])
        if hasattr(ui, 'valve_1'):
            if ui.valve_1[index]==True: 
                ui.valveButton_2.setText('ON')
            else: 
                ui.valveButton_2.setText('OFF')
            
        if ui.MXsII==True: MXsII.FTWrite(message)

    def recordIO(self):
        ui.save = not ui.save
        if ui.save == True:
            ui.Filename = NI.DefFile(ui.Foldername)
            ui.recordButton.testAttribute

    # ValveBotton_1
    def ValveOC(self):

        ui.valve_1[ui.valveindex1] = not ui.valve_1[ui.valveindex1]
        #s = NI.ArduinoDO(ui.valveindex1,
        #                  ui.valve_1[ui.valveindex1])
        NI.ArduinoDO(ui.valveindex1,
                          ui.valve_1[ui.valveindex1])
        if ui.valve_1[ui.valveindex1]==True: 
            ui.valveButton_1.setText('ON')
        else: 
            ui.valveButton_1.setText('OFF')
        if any(ui.valve_1):  # open the check valve
            #s = NI.ArduinoDO(10, True)
            NI.ArduinoDO(10, True)
            print('LSV is open')
        else:
            #s = NI.ArduinoDO(10, False)
            NI.ArduinoDO(10, False)

    # add JM ValveButton_2  # can be combined with ValveOC
    def ValveOC2(self):

        ui.valve_1[ui.valveindex2] = not ui.valve_1[ui.valveindex2]
        # s = NI.ArduinoDO(ui.valveindex2,
        #                      ui.valve_1[ui.valveindex2])
        NI.ArduinoDO(ui.valveindex2,
                             ui.valve_1[ui.valveindex2])
        if ui.valve_1[ui.valveindex2]==True: 
            ui.valveButton_2.setText('ON')
        else: 
            ui.valveButton_2.setText('OFF')
        if any(ui.valve_1):  # open the check valve
            #s = NI.ArduinoDO(10, True)
            NI.ArduinoDO(10, True)
        else:
            #s = NI.ArduinoDO(10, False)
            NI.ArduinoDO(10, False)
                
    def svalue_changed(self):

        ui.voltage1[ui.valveindex1] = ui.horizontalSlider.value()
        ui.lcdnumber_1.display(ui.horizontalSlider.value())
        NI.ArduinoAO(ui.vNumA, True, ui.voltage1[ui.valveindex1])
        
    def svalue2_changed(self):

        ui.voltage1[ui.valveindex2] = ui.horizontalSlider_2.value()
        ui.lcdnumber_2.display(ui.horizontalSlider_2.value())
        NI.ArduinoAO(ui.vNumB, True, ui.voltage1[ui.valveindex2])
        


    def abort_program(self):

        ui.timer.stop()
        NI.Arduinobye()
        self.close()
        
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
