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
        ui.x=[]
        ui.y=[]
        ui.c=[]
        ui.voltage1=[0,0,0,0,0,0,0,0,0,0]    
        ui.setupUi(self)
        ui.comboBox.addItems(['1','2','3','4','5','6','7','8','9','10'])
        ui.graphwidget = MatplotlibWidget(ui.centralwidget,
                 xlim=None, ylim=None, xscale='linear', yscale='linear',
                 width=12, height=3, dpi=100)
        
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_figure)
        timer.start(50)  
        ui.save=False
        ui.valve_1=[False,False,False,False,False,False,False,False,False,False]
        for icnt in range(len(ui.valve_1)):
            NI.ArduinoDO(icnt,ui.valve_1[icnt])
        ui.Filename=' '
        ui.Foldername='C:/Users/Microfluidics-team'
        ui.value=0
        ui.residualtime=0
        ui.start=time.time()
        ui.duration=0
        ui.RunSequenceFlag=False
        ui.number_of_commands=0
        ui.command=1
        
    def update_figure(self):
        def open_single_valve(index,duration):
            for i in range(len(ui.valve_1)):
                if i != index-1:
                    ui.valve_1[i]=False
                else:
                    ui.valve_1[i]=True
                NI.ArduinoDO(i,ui.valve_1[i])    
            ui.start=time.time()
            ui.duration=duration
        f=NI.ArduinoI2C()
        x,y,c,r=NI.ArduinoAI(ui.x,ui.y,ui.c)
        if r :
            c[1]=0.1208*c[1]-23.75
            if ui.save == True:
                # add Hiroyuki
                if ui.count != 0:
                    # ui.count = 0で新規file open 
                    ui.Ti = np.append(ui.Ti,c[0]-x[1])
                    ui.CA1 = np.append(ui.CA1,c[1])
                    ui.graphwidget.figure.clear()
                    ui.graphwidget.axes = ui.graphwidget.figure.add_subplot(131)
                    ui.graphwidget.axes.clear()
                    ui.graphwidget.x  = ui.Ti
                    ui.graphwidget.y  = ui.CA1          
                    ui.graphwidget.axes.plot(ui.graphwidget.x,ui.graphwidget.y)
                    ui.graphwidget.draw()
                    file = open(ui.Filename, 'a')
                else:
                    ui.Ti = c[0]-x[1]
                    ui.CA1  = c[1]
                    file = open(ui.Filename, 'w')
                    
                ui.count = ui.count + 1
                c[0] = c[0]-x[1]  #時間変換
                #
                #  record Display Time by Hiroyuki
    
                c[0]=round(c[0],6)
                for i in c:
                    jp = (str(i))
                    file.write(jp)
                    file.write(',') # コンマ
                file.write(f)
                file.write('\n')  # 改行コード
                file.close()
    
                ui.c=[]
                
            else:
                ui.count = 0 # add Hiroyuki
            
            # counter Display
            ui.valveLcd_1.display(c[1])
            if ui.number_of_commands-ui.command>0:
                ui.residualtime=ui.duration-(time.time()-ui.start)
                if ui.residualtime >0 :
                    ui.lcdTimer.display(ui.residualtime)
                else:
                    text=ui.tableWidget.item(ui.command,0).text()
                    message=text.split(',')
                    MXsII.FTWrite(message[0]+ '\r')
                    valve=message[0]
                    pressure=message[1]
                    ui.voltage1[int(valve[-1],16)-1]=pressure
                    NI.ArduinoAO(11,True, ui.voltage1[int(valve[-1],16)-1])
                    duration = int(message[2].rstrip())
                    open_single_valve(int(valve[-1],16),duration)
                    ui.command+=1
            else:
                ui.residualtime=ui.duration-(time.time()-ui.start)
                if ui.residualtime >0 :
                    ui.lcdTimer.display(ui.residualtime)
                elif ui.number_of_commands !=0 :
                    for i in range(len(ui.valve_1)):
                        ui.valve_1[i]=False
                        NI.ArduinoDO(i,ui.valve_1[i])
                    ui.number_of_commands=0
                    
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