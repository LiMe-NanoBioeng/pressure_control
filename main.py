# -*- coding: utf-8 -*-

import sys
import numpy as np
from ArduinoDAQ import AI as NI
import tkinter.filedialog
import os
from os.path import expanduser
#import serial
import time
from PyQt5 import QtWidgets, QtCore#, QtGui
from PyQt5.QtWidgets import QActionGroup, QApplication
from droplet_gui import Ui_Droplet_formation
from matplotlibwidget import MatplotlibWidget
from MXsII import MXsIIt as MXsII
from ThermoPlate import ThermoPlate
from pycromanager_pipe import acq_pycromanager
import datetime
from config import config
conf=config()

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
        ui.MXsII=conf.SELECT_VALVE  # selector valve True/False  ##change for HybISS version
        ui.UseThermoPlate=conf.THERMO_PLATE
        ui.t = [] # time
        ui.dt = [] # time difference
        ui.c = [] # voltage of pressure
        ui.f = [] # flow rate
        ui.voltage = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0] # voltage to pressre regulator
        ui.setupUi(self)
        ui.comboBox.addItems(
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']) # valve/channel number
        ui.comboBox_2.addItems(
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']) # valve channel number
        ui.graphwidget = MatplotlibWidget(ui.centralwidget,
                                          xlim=None, ylim=None, xscale='linear', yscale='linear',
                                          width=12, height=5, dpi=95)

        if(conf.FLOW_SENSOR):
            unit=NI.ArduinoAFU()
            print(unit)
            if(unit!=""):
                ui.unit_display.setText(NI.ArduinoAFU())
        else:
            ui.unit_display.setText("(no flow sensor)")
            print("NO flow sensor")


        ui.timer= QtCore.QTimer(self)
        ui.timer.start(30) # update the display every this ms
        ui.timer.timeout.connect(self.update_figure)
        ui.save = False  # Record data or not
        # valve initialization
        ui.valve_state = [False, False, False, False,
                      False, False, False, False, False, False]
        self.open_single_valve(-1) # shut all the valves
        #ui.vNumA=11
        # valve channels
        #
        # arduino channel number should be defiend in ArduionDAQ.py
        ui.vNumA=9 # first AO channel feedback channel ##this number order is MISA for HyBISS version
        ui.vNumB=10 # second AO channel

        NI.ArduinoFB(False,ui.vNumA,0,0,0,0) # initialize feedback parameters
        NI.ArduinoAO(ui.vNumA, False, 0) # initialize the pressure regulator
        ui.Filename = ' ' # file name to save
        ui.Foldername = homedir # file saving directory
        #ui.value = 0
        #
        # parameters for sequence
        #
        ui.residualtime = 0
        ui.start = time.time()
        ui.termination_mode="" # volume or time
        ui.mode="" #feedback or not
        ui.qstart=0 # cummulative quantity
        ui.volume=0 #
        ui.duration = 0 # duration
        ui.RunSequenceFlag = False
        ui.number_of_commands = 0 # number of commands
        ui.command = 1 # current command
        ui.pid_parameters = {} # Ki Kp Kd
        ui.last_pid = (0.1,0.001,0.1) #initial values


        ui.tuning_is_running=False
        #JM added
        ui.valveButton_2.hide()
        ui.valveLcd_2.hide()
        ui.horizontalSlider_2.hide()
        ui.comboBox_2.hide()
        ui.label_8.hide()
        ui.label_10.hide()
        ui.lcdnumber_2.hide()
        ui.line.hide()
        ui.valveindex1=0
        ui.valveindex2=0
        ui.reg=0
        self.function_change(conf.REG_TYPE)
        ui.Numpre=0
        ui.actionITV0010_2.triggered.connect(lambda: self.function_change(0))
        ui.actionITV0030_2.triggered.connect(lambda: self.function_change(1))
        ui.actionITV0090.triggered.connect(lambda: self.function_change(2))
        ui.actionEVL1050.triggered.connect(lambda: self.function_change(3))
        ui.actionsingle_2.triggered.connect(lambda: self.pressure_number(0))
        ui.actiondouble_2.triggered.connect(lambda: self.pressure_number(1))
        ui.actionOn.triggered.connect(lambda: self.check_selectorvalve(0))
        ui.actionOff.triggered.connect(lambda:self.check_selectorvalve(1))
        action_group1 = QActionGroup(self)
        action_group1.addAction(ui.actionITV0010_2)
        action_group1.addAction(ui.actionITV0030_2)
        action_group1.addAction(ui.actionITV0090)
        action_group1.addAction(ui.actionEVL1050)
        action_group2 = QActionGroup(self)
        action_group2.addAction(ui.actionsingle_2)
        action_group2.addAction(ui.actiondouble_2)
        action_group3 = QActionGroup(self)
        action_group3.addAction(ui.actionOn)

        action_group3.addAction(ui.actionOff)
        self.MDA_file_path = None
        self.Pos_file_path = None
        ui.ThermoPlate = ThermoPlate()
        ui.magnitude=0.1
        ui.magnitude_initialize=False
        ui.initsum=0.0
        ui.initcount=0
        

    def open_single_valve(self, index):
        for i in range(len(ui.valve_state)):
            if i != index-1:
                ui.valve_state[i] = False
            else:
                ui.valve_state[i] = True
            NI.ArduinoDO(i, ui.valve_state[i])
        if any(ui.valve_state):  # open the check valve
            NI.ArduinoDO(10, True)
            print('LSV is open')
        else:
            #s=NI.ArduinoDO(10, False)
            NI.ArduinoDO(10, False)

    def check_selectorvalve(self,index): #JM added
        if index == 0:
            ui.MXsII = True
            print('use selector valve')
        else:
            ui.MXsII = False
            print('quit using selector valve')

    def SequenceControlTime(self):
        Kp,Ki,Kd = ui.last_pid
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
                mode, valve, valve_num, pressure, duration,volume = self.read_seq_commands(
                    ui.command)
                ui.current_valve=valve
                ui.current_valve_num=valve_num
                ui.current_pressure=pressure # pressure/flow rate
                ui.duration = duration
                ui.volume=volume
                # ui.current_duration=duration
                ui.voltage[valve_num-1] = pressure  # register pressure value


                #close valveFile ~/github/pressure_control/main.py:387, in MainWindow.update_figure(self)

                self.open_single_valve(-1)
                if ui.MXsII==True:
                    MXsII.FTWrite(str(valve) + '\r')  # switch the valve
                    # message = 'S' + '\r'[1] + h[ui.reg]
                    # rmessage = MXsII.FTWriteRead(message)
                    # print('Current valve is ' + rmessage)
                    # print('Setting valve is ' + str(valve_num))
                # send commands when switch the sequence
                #time.sleep(1)

                if ui.command in ui.pid_parameters:
                    ui.last_pid = ui.pid_parameters[ui.command]
                Kp,Ki,Kd = ui.last_pid

                NI.ArduinoFB(False,ui.vNumA,ui.current_pressure,Kp,Ki,Kd)
                NI.ArduinoAO(ui.vNumA, False, 0)

                time.sleep(1)
                # send pressure value
                # NI.ArduinoAO(ui.vNumA,True,pressure)
                # global operating
                if mode=="p":#open loop
                    # self.open_single_valve(valve_num)
                    # NI.ArduinoAO(ui.vNumA, True, int(pressure/100*255))
                    pressure=float(pressure)
                    NI.ArduinoAO(ui.vNumA, True, min(int(pressure*165.0/ui.magnitude),254))
                    self.open_single_valve(valve_num)
                elif mode=="u": # closed loop
                    if pressure >0:
                        self.open_single_valve(valve_num)
                        NI.ArduinoFB(True,ui.vNumA,ui.current_pressure,Kp,Ki,Kd)
                        # operating=1
                    else:
                        NI.ArduinoFB(False,ui.vNumA,ui.current_pressure,Kp,Ki,Kd)
                        NI.ArduinoAO(ui.vNumA, False, 0)
                        # operating =0
                elif mode=="a": #acquire image
                    from pycromanager import MagellanAcquisition,Core
                    try:
                        core = Core()
                    #     # no need to use the normal "with" syntax because these acquisition are cleaned up automatically
                        # acq = MagellanAcquisition(magellan_acq_index=0)
                        # acq.await_completion()
                        mda_file = self.MDA_file_path
                        pos_file = self.Pos_file_path
                        print(mda_file,pos_file)
                        acq = acq_pycromanager(mda_file,pos_file)
                        print('sucess_acquirment')
                    except:
                        print('false')
                        #Mail
                        # import yagmail
                        # #personal information
                        # user = "xxx@gmail.com"
                        # app_password = "xxx"
                        # to = "xxx@gmail.com"
                        # subject = "PLZ help MiSA!"
                        # body = "microscopy is shutdown"
                        # yag = yagmail.SMTP(user=user, password=app_password)
                        # yag.send(to=to, subject=subject, contents=body)
                        ui.timer.stop()
                        NI.Arduinobye()
                        self.close()
                elif mode=="c": #temperature set
                    if(ui.UseThermoPlate):
                        ui.ThermoPlate.settemp(int(pressure))

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
        c = float(width)
        NI.ArduinoDigitalPulse(a,b,1,c,10) # 100 is the threshold

    def pressure_number(self,index):#add JM
        ui.Numpre = index
        if ui.Numpre == 0:
            print('single pressure')
            ui.valveButton_2.hide()
            ui.valveLcd_2.hide()
            ui.horizontalSlider_2.hide()
            ui.comboBox_2.hide()
            ui.label_8.hide()
            ui.label_10.hide()
            ui.lcdnumber_2.hide()
            ui.line.hide()

        elif ui.Numpre == 1:
            print('double pressure')
            ui.valveButton_2.show()
            ui.valveLcd_2.show()
            ui.horizontalSlider_2.show()
            ui.comboBox_2.show()
            ui.label_8.show()
            ui.label_10.show()
            ui.lcdnumber_2.show()
            ui.line.show()

    def read_seq_commands(self, command):
        text = ui.tableWidget.item(command, 0).text()
        message = text.split(',')
        valve = message[0]  # valve number
        parameter = float(message[1][:-1])# pressure value
        mode=message[1][-1]
        terminal = message[2].rstrip()
        if terminal[-1] =="s":
            duration=int(terminal[:-1])
            volume=0
        elif terminal[-1]=="u":
            volume=float(terminal[:-1])
            duration=0
        valve_num = int(valve[-1], 16)
        ui.termination_mode=terminal[-1]
        ui.mode=mode

        #read PID parameters
        if len(message) > 3:
            Kp,Ki,Kd = map(float,message[3].split(';'))
            ui.pid_parameters[command] = (Kp,Ki,Kd)
            ui.last_pid = (Kp,Ki,Kd)
        return (mode,valve, valve_num, parameter, duration,volume)

    def initialize_magnitude(self):
        NI.ArduinoAO(ui.vNumA, True, 254)
        ui.magnitude_initialize=True
    

    def initialize_end(self):
        return 1;


    def draw_graph(self): #update JM
        ui.graphwidget.figure.clear()
        ui.graphwidget.axes1.clear()
        ui.graphwidget.axes2.clear()
        ui.graphwidget.axes3.clear()

        ui.graphwidget.axes1 = ui.graphwidget.figure.add_subplot(221, xlabel = 'Time [s]', ylabel = 'Pressure [kPa]')
        ui.graphwidget.x = ui.dt
        ui.graphwidget.y = np.transpose(ui.CA1[:ui.Numpre+1])
        # ui.graphwidget.y = np.transpose(ui.CA1)
        ui.graphwidget.axes1.plot(ui.graphwidget.x, ui.graphwidget.y)
        ui.graphwidget.draw()

        ui.graphwidget.axes2 = ui.graphwidget.figure.add_subplot(222, xlabel = 'Time [s]', ylabel = 'Flow rate [μL/min]')
        ui.graphwidget.x = ui.dt
        ui.graphwidget.y = ui.f
        ui.graphwidget.axes2.plot(ui.graphwidget.x, ui.graphwidget.y)
        ui.graphwidget.draw()

        ui.graphwidget.axes3 = ui.graphwidget.figure.add_subplot(223, xlabel = 'Time [s]', ylabel = 'Pumped volume [μL]')
        ui.graphwidget.x = ui.dt
        ui.graphwidget.y = ui.q
        ui.graphwidget.axes3.plot(ui.graphwidget.x, ui.graphwidget.y)
        ui.graphwidget.figure.tight_layout()
        ui.graphwidget.draw()

        ui.graphwidget.axes4 = ui.graphwidget.figure.add_subplot(224, xlabel = 'Time [s]', ylabel = 'Temperature [C]')
        ui.graphwidget.x = ui.dt
        ui.graphwidget.y = ui.temperature
        ui.graphwidget.axes4.plot(ui.graphwidget.x, ui.graphwidget.y)
        ui.graphwidget.figure.tight_layout()
        ui.graphwidget.draw()
    def function_change(self,index):
        ui.reg = index

    def update_figure(self):
        #print("magnitude: ",ui.magnitude)
        status = NI.ArduinoStatusCheck()
        if ui.tuning_is_running:
            self.tuningCore()
        if status =='R':
            time, c, r= NI.ArduinoAI()
            if(conf.FLOW_SENSOR):
                f = NI.ArduinoI2C()
            else:
                f=-1
            if(ui.UseThermoPlate==False):
                temp=-1
            else:
                
                temp = float(ui.ThermoPlate.readtemp())
                
            #print(temp)
            # print(c)#for test
            if r:
                g = [0.1208, 1.097, -0.1208, 0.0610]
                h = [-23.75, -223.75, 23.78, -12.5]
                c[0] = g[ui.reg] * c[0] + h[ui.reg]
                c[1] = g[ui.reg] * c[1] + h[ui.reg]
                ui.valveLcd_1.display(c[0])
                ui.valveLcd_2.display(c[1]) #add JM
                if(c[0]>0 and ui.magnitude_initialize and ui.initcount<10):
                    print("now tuning")
                    print("initsum: ", ui.initsum)
                    ui.initsum+=c[0]
                    ui.initcount+=1
                if(ui.initcount==10):
                    print("end tuning")
                    ui.initcount=0
                    ui.magnitude=ui.initsum/10.0
                    ui.initsum=0.0
                    ui.magnitude_initialize=False
                    NI.ArduinoAO(ui.vNumA,True,0)
                    print("reset magnitude: ", ui.magnitude)
                if ui.save == True:
                    # add Hiroyuki
                    if ui.count != 0:
                        ui.dt = np.append(ui.dt, time-ui.t)
                        ui.CA1 = np.c_[ui.CA1,c]
                        ui.f = np.append(ui.f, f)
                        ui.temperature=np.append(ui.temperature,temp)
                        if ui.count != 1:  # compute integrated flow quantity at t > 1
                            q = ui.q[-1]+np.median([ui.f[-3], ui.f[-2], ui.f[-1]])*(ui.dt[-1]-ui.dt[-2])/60
                        else:  # compute integrated flow quantity at t=1
                            q = f*(ui.dt[-1])/60
                        ui.q = np.append(ui.q, q)

                        c = np.append(np.append(
                            np.append(np.append(round(ui.dt[-1], 6), c), float(f)), float(q)),float(temp))
                        self.draw_graph()

                        file = open(ui.Filename, 'a')
                    else:
                        ui.t = time  # initial time
                        ui.dt = time-ui.t
                        ui.CA1 = c
                        ui.f = f
                        ui.q = 0
                        ui.temperature=temp
                        file = open(ui.Filename, 'w')
                        c = np.append(np.append(
                            np.append(np.append(round(ui.dt, 6), c), float(f)), float(ui.q)),float(temp))

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
        for x in f:
            ui.tableWidget.insertRow(rowPosition)
            ui.tableWidget.setItem(
                rowPosition, 0, QtWidgets.QTableWidgetItem(x))
            rowPosition += 1

    def openMDAFile(self):
        fTyp = [("MultiDimensionalAcquisitionFile", "*.txt")]
        iDir = os.path.abspath(os.path.dirname(__file__))
        self.MDA_file_path = tkinter.filedialog.askopenfilename(
            filetypes=fTyp, initialdir=iDir)
        print("Selected MDA file:", self.MDA_file_path)

    def openPosFile(self):
        fTyp = [("PositionFile","*.pos")]
        iDir = os.path.abspath(os.path.dirname(__file__))
        self.Pos_file_path = tkinter.filedialog.askopenfilename(
            filetypes=fTyp, initialdir=iDir)
        print("Selected Pos file:", self.Pos_file_path)

    def tuning_resistanse_rate(self): # click tuning event
        #ui.timer.timeout.connect(self.check_tuning)
        ui.magnitude_initialize=True
        NI.ArduinoAO(ui.vNumA, True, 254)
        print("tuning on")
        #if not ui.tuning_is_running:
        #    NI.ArduinoDO(0, True)
        #    print("number 1 opened")
        #    if ui.MXsII==True: MXsII.FTWrite(str(1) + '\r')
        #    NI.ArduinoAO(ui.vNumA, True, 100)
        #    ui.tuning_is_running=True
        #    NI.ArduinoDO(10, True)
        #else:
        #    ui.tuning_is_running = False
        #    NI.ArduinoAO(ui.vNumA, False, 100)
        #    NI.ArduinoDO(0, False)
        #    print("tuning ended")
        #    NI.ArduinoDO(10, False)

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
        ui.lcdnumber_1.display(ui.voltage[index])
        ui.horizontalSlider.setValue(ui.voltage[index])
        if hasattr(ui, 'valve_1'):
            if ui.valve_state[index]==True:
                ui.valveButton_1.setText('ON')
            else:
                ui.valveButton_1.setText('OFF')

        if ui.MXsII==True:
            MXsII.FTWrite(message)
            # message = 'S' + '\r'
            # rmessage = MXsII.FTWriteRead(message)
            # print(rmessage)


    #add JM
    def valve2_number_changed(self, index):
        #ui.selected_valve_index_index = index
        ui.valveindex2=index
        valvenum = str(hex(index+1).upper())
        message = 'P0' + valvenum[-1] + '\r'
        ui.lcdnumber_2.display(ui.voltage[index])
        ui.horizontalSlider_2.setValue(ui.voltage[index])
        if hasattr(ui, 'valve_1'):
            if ui.valve_state[index]==True:
                ui.valveButton_2.setText('ON')
            else:
                ui.valveButton_2.setText('OFF')

        if ui.MXsII==True:
            MXsII.FTWrite(message)
            # message = 'S' + '\r'
            # rmessage = MXsII.FTWriteRead(message)
            # print(rmessage)

    def recordIO(self):
        ui.save = not ui.save
        if ui.save == True:
            ui.Filename = NI.DefFile(ui.Foldername)
            ui.recordButton.testAttribute

    # ValveBotton_1
    def ValveOC(self):

        ui.valve_state[ui.valveindex1] = not ui.valve_state[ui.valveindex1]
        #s = NI.ArduinoDO(ui.valveindex1,
        #                  ui.valve_state[ui.valveindex1])
        NI.ArduinoDO(ui.valveindex1,
                          ui.valve_state[ui.valveindex1])
        if ui.valve_state[ui.valveindex1]==True:
            ui.valveButton_1.setText('ON')
        else:
            ui.valveButton_1.setText('OFF')
        if any(ui.valve_state):  # open the check valve
            #s = NI.ArduinoDO(10, True)
            NI.ArduinoDO(10, True)
            print('LSV is open')
        else:
            #s = NI.ArduinoDO(10, False)
            NI.ArduinoDO(10, False)

    # add JM ValveButton_2  # can be combined with ValveOC
    def ValveOC2(self):

        ui.valve_state[ui.valveindex2] = not ui.valve_state[ui.valveindex2]
        # s = NI.ArduinoDO(ui.valveindex2,
        #                      ui.valve_state[ui.valveindex2])
        NI.ArduinoDO(ui.valveindex2,
                             ui.valve_state[ui.valveindex2])
        if ui.valve_state[ui.valveindex2]==True:
            ui.valveButton_2.setText('ON')
        else:
            ui.valveButton_2.setText('OFF')
        if any(ui.valve_state):  # open the check valve
            #s = NI.ArduinoDO(10, True)
            NI.ArduinoDO(10, True)
        else:
            #s = NI.ArduinoDO(10, False)
            NI.ArduinoDO(10, False)

    def svalue_changed(self):

        ui.voltage[ui.valveindex1] = ui.horizontalSlider.value()
        ui.lcdnumber_1.display(ui.horizontalSlider.value())
        NI.ArduinoAO(ui.vNumA, True, ui.voltage[ui.valveindex1])

    def svalue2_changed(self):

        ui.voltage[ui.valveindex2] = ui.horizontalSlider_2.value()
        ui.lcdnumber_2.display(ui.horizontalSlider_2.value())
        NI.ArduinoAO(ui.vNumB, True, ui.voltage[ui.valveindex2])


    def abort_program(self):
        ui.timer.stop()
        self.open_single_valve(-1)
        NI.Arduinobye()
        self.close()
        QApplication.quit()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    #print("app insert")
    w = MainWindow()
    #print("w insert")
    w.show()
    #print("show")
    sys.exit(app.exec_())
