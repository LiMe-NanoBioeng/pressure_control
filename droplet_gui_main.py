# -*- coding: utf-8 -*-

import sys

import numpy as np
from NIDAQ_plt3 import AI as NI
import tkinter.filedialog
import os

import time
from PyQt5 import QtWidgets, QtCore, QtGui
from droplet_gui import Ui_Droplet_formation
from matplotlibwidget import MatplotlibWidget
from MXsII import MXsIIt as MXsII


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
        ui.graphwidget = MatplotlibWidget(ui.centralwidget,
                                          xlim=None, ylim=None, xscale='linear', yscale='linear',
                                          width=12, height=3, dpi=100)

        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_figure)
        timer.start()
        ui.save = False
        ui.valve_1 = [False, False, False, False,
                      False, False, False, False, False, False]
        # for icnt in range(len(ui.valve_1)):
        #     NI.ArduinoDO(icnt,ui.valve_1[icnt])
        self.open_single_valve(-1)
        NI.ArduinoAO(11, False, 0)

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

    def open_single_valve(self, index):
        for i in range(len(ui.valve_1)):
            if i != index-1:
                ui.valve_1[i] = False
            else:
                ui.valve_1[i] = True
            s = NI.ArduinoDO(i, ui.valve_1[i])
        if any(ui.valve_1):  # open the check valve
            s= NI.ArduinoDO(8, True)
        else:
            s=NI.ArduinoDO(8, False)

    def SequenceControlTime(self):
        Kp = 0.3
        Ki = 0.001
        Kd = 0.001
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
                value=NI.ArduinoFBStatus(11)
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
                NI.ArduinoAO(11, False, 0)
                self.open_single_valve(-1)
                #
                # send commands when switch the sequence
                MXsII.FTWrite(str(valve) + '\r')  # switch the valve
                time.sleep(1)
                # send pressure value
                # NI.ArduinoAO(11,True,pressure)
                if pressure >0:
                    self.open_single_valve(valve_num)
                ui.start = time.time()
                ui.qstart=ui.q[-1]
                # proceedsd ui.command
                ui.command += 1
                ui.lcdSeqNumber.display(ui.command)
                NI.ArduinoFB(True,11,ui.current_pressure,Kp,Ki,Kd)
        else:
            # commands at the end of the sequence (when ui.number_of_commands-ui.command==0)
            if residual > 0:
                value=NI.ArduinoFBStatus(11)
                ui.lcdnumber_1.display(value)

            elif ui.number_of_commands != 0:
            #if ui.number_of_commands !=0 and residual <0 :
                NI.ArduinoFB(False,11,ui.current_pressure,Kp,Ki,Kd)
            # # commands at the end of the last sequence
                self.open_single_valve(-1)
                ui.number_of_commands = 0
                ui.save = not ui.save  # stop saving and displaying
                ui.lcdSeqNumber.display(ui.number_of_commands)
                time.sleep(1)

    def read_seq_commands(self, command):
        text = ui.tableWidget.item(command, 0).text()
        message = text.split(',')
        valve = message[0]  # valve number
        
        pressure = float(message[1][:-1])  # pressure value
        
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
        return (valve, valve_num, pressure, duration,volume)

    def draw_graph(self):
        ui.graphwidget.figure.clear()
        ui.graphwidget.axes = ui.graphwidget.figure.add_subplot(131)
        ui.graphwidget.axes.clear()
        ui.graphwidget.x = ui.dt
        ui.graphwidget.y = ui.CA1
        ui.graphwidget.axes.plot(ui.graphwidget.x, ui.graphwidget.y)
        ui.graphwidget.draw()

        ui.graphwidget.axes = ui.graphwidget.figure.add_subplot(132)
        ui.graphwidget.axes.clear()
        ui.graphwidget.x = ui.dt
        ui.graphwidget.y = ui.f
        ui.graphwidget.axes.plot(ui.graphwidget.x, ui.graphwidget.y)
        ui.graphwidget.draw()

        ui.graphwidget.axes = ui.graphwidget.figure.add_subplot(133)
        ui.graphwidget.axes.clear()
        ui.graphwidget.x = ui.dt
        ui.graphwidget.y = ui.q
        ui.graphwidget.axes.plot(ui.graphwidget.x, ui.graphwidget.y)
        ui.graphwidget.draw()

    def update_figure(self):

        time, c, r = NI.ArduinoAI()

        f = NI.ArduinoI2C()
        # print(c)
        # print(f)
        
        if r:
            c[0] = 0.1208*c[0]-23.75
            ui.valveLcd_1.display(c[0])
            if ui.save == True:
                # add Hiroyuki
                if ui.count != 0:
                    # ui.count = 0で新規file open
                    # ui.t = np.append(ui.t,time)
                    ui.dt = np.append(ui.dt, time-ui.t)
                    ui.CA1 = np.append(ui.CA1, c[0])
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
                    ui.CA1 = c[0]
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

            #

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
        for x in f:
            ui.tableWidget.insertRow(rowPosition)
            ui.tableWidget.setItem(
                rowPosition, 0, QtWidgets.QTableWidgetItem(x))
            rowPosition += 1

    def valve_number_changed(self, index):
        ui.selected_valve_index_index = index
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

    def recordIO(self):
        ui.save = not ui.save
        if ui.save == True:
            ui.Filename = NI.DefFile(ui.Foldername)
            ui.recordButton.testAttribute

    # ValveBotton_1
    def ValveOC(self):
        ui.valve_1[ui.selected_valve_index_index] = not ui.valve_1[ui.selected_valve_index_index]
        s = NI.ArduinoDO(ui.selected_valve_index_index,
                         ui.valve_1[ui.selected_valve_index_index])
        if ui.valve_1[ui.selected_valve_index_index]==True: 
            ui.valveButton_1.setText('ON')
        else: 
            ui.valveButton_1.setText('OFF')
        if any(ui.valve_1):  # open the check valve
            s = NI.ArduinoDO(8, True)
        else:
            s = NI.ArduinoDO(8, False)

    def svalue_changed(self):
        ui.voltage1[ui.selected_valve_index_index] = ui.horizontalSlider.value()
        ui.lcdnumber_1.display(ui.horizontalSlider.value())
        NI.ArduinoAO(11, True, ui.voltage1[ui.selected_valve_index_index])


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
