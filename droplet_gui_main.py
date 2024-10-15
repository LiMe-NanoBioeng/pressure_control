# -*- coding: utf-8 -*-

import sys

import numpy as np
from ArduinoDAQ import AI as NI
import tkinter.filedialog
import os
import keyboard
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

# operating=0;
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        global ui
        super(MainWindow, self).__init__(parent=parent)
        ui = Ui_Droplet_formation()
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

        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_figure)
        ui.timer=timer
        timer.start()
        ui.timer=timer
        ui.save = False
        ui.valve_1 = [False, False, False, False,
                      False, False, False, False, False, False]
        ui.valve_2 = [False, False, False, False,
                      False, False, False, False, False, False]
        # for icnt in range(len(ui.valve_1)):
        #     NI.ArduinoDO(icnt,ui.valve_1[icnt])
        self.open_single_valve(-1)
        #ui.vNumA=11
        ui.vNumA=9
        ui.vNumA2=10
        NI.ArduinoFB(False,ui.vNumA,0,0,0,0)
        NI.ArduinoAO(ui.vNumA, False, 0)
        ui.Filename = ' '
        ui.Foldername = 'C:/Users/Microfluidics-team'
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
        ui.abort.clicked.connect(self.abort_program)
        ui.pid_parameters = {}
        ui.tuningbutton.clicked.connect(self.tuning_resistanse_rate)
        #K2 Added
        ui.tuning_is_runnning=False
        #JM added
        ui.valveButton_2.hide()
        ui.valveLcd_2.hide()
        ui.horizontalSlider_2.hide()
        ui.comboBox_2.hide()
        ui.label_8.hide()
        ui.lcdnumber_2.hide()
        ui.valveindex1=0
        ui.valveindex2=0
        

    def open_single_valve(self, index):
        for i in range(len(ui.valve_1)):
            if i != index-1:
                ui.valve_1[i] = False
            else:
                ui.valve_1[i] = True
            s = NI.ArduinoDO(i, ui.valve_1[i])
        if any(ui.valve_1):  # open the check valve
            s= NI.ArduinoDO(10, True)
        else:
            s=NI.ArduinoDO(10, False)

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
                    NI.ArduinoAO(ui.vNumA, True, int(pressure/70*255))
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
        a = ui.valveindex1
        b = ui.valveindex2
        width = ui.plainTextEdit.toPlainText()
        #print(width)
        c = float(width)
        NI.ArduinoDigitalPulse(a,b,1,c)
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
            volume=int(text[:-1])
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
       
    def update_figure(self):

        time, c, r= NI.ArduinoAI()# potentio　does not used in this stack

        f = NI.ArduinoI2C()
        # print(c)
        # print(f)
        
        if r:
            c[0] = 0.1208*c[0]-23.75
            c[1] = 0.1208*c[1]-23.75
            ui.valveLcd_1.display(c[0])
            ui.valveLcd_2.display(c[1]) #add JM
            if ui.save == True:
                # add Hiroyuki
                if ui.count != 0:
                    # ui.count = 0で新規file open
                    # ui.t = np.append(ui.t,time)
                    ui.dt = np.append(ui.dt, time-ui.t)
                    # ui.CA1 = np.append(ui.CA1, c)
                    ui.CA1 = np.c_[ui.CA1,c]
                    ui.f = np.append(ui.f, f)
                    if ui.count != 1:  # compute integrated flow quantity at t > 1
                        q = ui.q[-1]+np.median([ui.f[-3], ui.f[-2], ui.f[-1]])*(ui.dt[-1]-ui.dt[-2])/60
                    else:  # compute integrated flow quantity at t=1
                        q = f*(ui.dt[-1])/60
                    ui.q = np.append(ui.q, q)
                    # global operating
                    # #save result phase
                    # print(time-ui.t,",",f,",",operating)
                    # result_file_path=os.path.join("./result/",resultfilename)
                    # resultitself=str(time-ui.t)+","+str(f)+","+str(operating)+"\n"
                    # with open(result_file_path,'a') as file:
                    #     file.write(resultitself)
                    #phase end
                    
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

            #ui.resistance_rate.display(str(potentio))

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
    
    def tuning_resistanse_rate(self):
        if not ui.tuning_is_runnning:
            NI.ArduinoDO(0, True)
            print("number 1 opened")
            MXsII.FTWrite(str(1) + '\r')
            NI.ArduinoFB(True,10,50,1,1,1) 
            ui.timer.timeout.connect(self.tuningCore)
            ui.timer.start(100)
            ui.tuning_is_runnning=True
            NI.ArduinoDO(10, True)
        else:
            ui.timer.stop()  # タイマーを停止
            ui.tuning_is_running = False
            NI.ArduinoFB(False,10,0,0,0,0)
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
        ui.selected_valve_index_index = index #selected_valve_index_index をそれぞれのバルブのインデクッスにそろえるとうまく行く？
        ui.valveindex1=index
        print(ui.valveindex1)
        valvenum = str(hex(ui.selected_valve_index_index+1).upper())
        message = 'P0' + valvenum[-1] + '\r'
        ui.lcdnumber_1.display(ui.voltage1[ui.selected_valve_index_index])
        ui.horizontalSlider.setValue(ui.voltage1[ui.selected_valve_index_index])
        if hasattr(ui, 'valve_1'):
            if ui.valve_1[ui.selected_valve_index_index]==True: 
                ui.valveButton_1.setText('ON')
            else: 
                ui.valveButton_1.setText('OFF')
            
        MXsII.FTWrite(message)
        # Recordbutton

    #add JM
    def valve2_number_changed(self, index):
        ui.selected_valve_index_index = index
        ui.valveindex2=index
        valvenum = str(hex(ui.selected_valve_index_index+1).upper())
        message = 'P0' + valvenum[-1] + '\r'
        ui.lcdnumber_2.display(ui.voltage1[ui.selected_valve_index_index])
        ui.horizontalSlider.setValue(ui.voltage1[ui.selected_valve_index_index])
        if hasattr(ui, 'valve_2'):
            if ui.valve_2[ui.selected_valve_index_index]==True: 
                ui.valveButton_2.setText('ON')
            else: 
                ui.valveButton_2.setText('OFF')
            
        MXsII.FTWrite(message)

    def recordIO(self):
        ui.save = not ui.save
        if ui.save == True:
            ui.Filename = NI.DefFile(ui.Foldername)
            ui.recordButton.testAttribute

    # ValveBotton_1
    def ValveOC(self):
        # ui.valve_1[ui.selected_valve_index_index] = not ui.valve_1[ui.selected_valve_index_index]
        # s = NI.ArduinoDO(ui.selected_valve_index_index,
        #                  ui.valve_1[ui.selected_valve_index_index])
        # if ui.valve_1[ui.selected_valve_index_index]==True: 
        ui.valve_1[ui.valveindex1] = not ui.valve_1[ui.valveindex1]
        s = NI.ArduinoDO(ui.valveindex1,
                          ui.valve_1[ui.valveindex1])
        if ui.valve_1[ui.valveindex1]==True: 
            ui.valveButton_1.setText('ON')
        else: 
            ui.valveButton_1.setText('OFF')
        if any(ui.valve_1):  # open the check valve
            s = NI.ArduinoDO(10, True)
        else:
            s = NI.ArduinoDO(10, False)

    # add JM ValveButton_2
    def ValveOC2(self):
            # ui.valve_2[ui.selected_valve_index_index] = not ui.valve_2[ui.selected_valve_index_index]
            # s = NI.ArduinoDO(ui.selected_valve_index_index,
            #                  ui.valve_2[ui.selected_valve_index_index])
            # if ui.valve_2[ui.selected_valve_index_index]==True: 
        ui.valve_2[ui.valveindex2] = not ui.valve_2[ui.valveindex2]
        s = NI.ArduinoDO(ui.valveindex2,
                             ui.valve_2[ui.valveindex2])
        if ui.valve_2[ui.valveindex2]==True: 
            ui.valveButton_2.setText('ON')
        else: 
            ui.valveButton_2.setText('OFF')
        if any(ui.valve_2):  # open the check valve
            s = NI.ArduinoDO(10, True)
        else:
            s = NI.ArduinoDO(10, False)
                
    def svalue_changed(self):
        # ui.voltage1[ui.selected_valve_index_index] = ui.horizontalSlider.value()
        # ui.lcdnumber_1.display(ui.horizontalSlider.value())
        # NI.ArduinoAO(ui.vNumA, True, ui.voltage1[ui.selected_valve_index_index])
        ui.voltage1[ui.valveindex1] = ui.horizontalSlider.value()
        ui.lcdnumber_1.display(ui.horizontalSlider.value())
        NI.ArduinoAO(ui.vNumA, True, ui.voltage1[ui.valveindex1])
        
    def svalue2_changed(self):
        # ui.voltage1[ui.selected_valve_index_index] = ui.horizontalSlider.value()
        # ui.lcdnumber_2.display(ui.horizontalSlider.value())
        # NI.ArduinoAO(ui.vNumA, True, ui.voltage1[ui.selected_valve_index_index])
        ui.voltage1[ui.valveindex2] = ui.horizontalSlider_2.value()
        ui.lcdnumber_2.display(ui.horizontalSlider_2.value())
        NI.ArduinoAO(ui.vNumA2, True, ui.voltage1[ui.valveindex2])
        
        
        #K2 ADDED
    #def calculate_resistance_value(self):
        #time, c, r, potentio = NI.ArduinoAI() #time c,r　are not used in this stack
        #ui.resistance_value.display(str(potentio))

    def abort_program(self):
        #ser = serial.Serial('COM11', 9600, timeout=1)
        #ser.dtr = False
        #time.sleep(0.1)
        #ser.dtr = True
        self.close()
        
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
