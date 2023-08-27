# -*- coding: utf-8 -*-

import sys

import numpy as np
from NIDAQ_plt3 import AI as NI
import time
from PyQt5 import QtWidgets, QtCore, QtGui
from droplet_gui import Ui_Droplet_formation
from matplotlibwidget import MatplotlibWidget


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
        ui.setupUi(self)
        ui.graphwidget = MatplotlibWidget(ui.centralwidget,
                 xlim=None, ylim=None, xscale='linear', yscale='linear',
                 width=8, height=3, dpi=100)

        ui.graphwidget.axes = ui.graphwidget.figure.add_subplot(121, title = 'Valve1', xlabel='Time', ylabel='Pressure, kPa')  
        ui.graphwidget.axes = ui.graphwidget.figure.add_subplot(122, title = 'Valve2', xlabel='Time', ylabel='Pressure, kPa')   
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_figure)
        timer.start(50)
        ui.x=[]
        ui.y=[]
        ui.c=[]
        ui.voltage1=0
        ui.voltage2=0
        
        ui.save=False
        ui.valve_1=False
        ui.valve_2=False
        ui.Filename="./"
        ui.value=0
        
        
#        # for function generator
#        exposure=10
#        laser=0.025
#        dt=0.05
#        ui.plainTextEdit_1.setPlainText(str(dt))
#        ui.plainTextEdit_2.setPlainText(str(exposure))
#        ui.plainTextEdit_3.setPlainText(str(laser))
#        ui.plainTextEdit.setPlainText('1000')#interval
#        ui.plainTextEdit_4.setPlainText('1')#number of pulsese
#        wavefunc.wf1974(exposure, laser, dt)

    def update_figure(self):
            
        x,y,c=NI.ArduinoAI(ui.x,ui.y,ui.c)
        
        c_1v = c[1]*0.004882
        c_2v = c[2]*0.0048822
        #print(c_1v,c_2v)
        c[1]=0.1208*c[1]-23.75
        c[2]=0.1208*c[2]-23.75
        voltage = [0,0]
        if ui.valve_1:
            voltage[0]=ui.voltage1
        else:
            voltage[0]=0
                
        if ui.valve_2:
            voltage[1]=ui.voltage2
        else:
            voltage[1]=0
            
        NI.ArduinoAO(True, voltage)
 
        if ui.save == True:
            
            # add Hiroyuki
            if ui.count != 0:
                # ui.count = 0で新規file open 
                ui.Ti = np.append(ui.Ti,c[0]-x[1])
                ui.CA1 = np.append(ui.CA1,c[1])
                ui.CA2 = np.append(ui.CA2,c[2])
          
                ui.graphwidget.figure.clear()
                ui.graphwidget.axes = ui.graphwidget.figure.add_subplot(121)
                ui.graphwidget.axes.clear()
                ui.graphwidget.x  = ui.Ti
                ui.graphwidget.y  = ui.CA1          
                ui.graphwidget.axes.plot(ui.graphwidget.x,ui.graphwidget.y)
                ui.graphwidget.draw()
 
                ui.graphwidget.axes = ui.graphwidget.figure.add_subplot(122)       
                ui.graphwidget.axes.clear()
                ui.graphwidget.x  = ui.Ti
                ui.graphwidget.y  = ui.CA2
                ui.graphwidget.axes.plot(ui.graphwidget.x,ui.graphwidget.y)
                ui.graphwidget.draw()
                
                

                file = open(ui.Filename, 'a')

            else:
                ui.Ti = c[0]-x[1]
                ui.CA1  = c[1]
                ui.CA2  = c[2]
                
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
            file.write('\n')  # 改行コード
            file.close()

            ui.c=[]
            
        else:
            ui.count = 0 # add Hiroyuki
        

        # counter Display
        #NI.ArduinoAO(ui.valve)
        ui.valveLcd_1.display(c[1])
        ui.valveLcd_2.display(c[2])

    
    # Recordbutton    
    def slot1(self):
        ui.save = not ui.save
        if ui.save == True:
            ui.Filename = NI.DefFile()
    
    # ValveBotton_1
    def slot2(self):
        ui.valve_1 = not ui.valve_1
        NI.ArduinoDO_1(ui.valve_1)
        print('Valve1_pusshed.')

    # ValveBotton_2
    def slot3(self):
        ui.valve_2 = not ui.valve_2
        NI.ArduinoDO_2(ui.valve_2)
        print('Valve2_pusshed.')
    
    def s2value_changed(self):
        #print('slider2_changed.')
        ui.voltage1=ui.horizontalSlider.value()
        ui.voltage2=ui.horizontalSlider_2.value()
        
    def svalue_changed(self):
        #print('slider1_changed.')
        ui.voltage1=ui.horizontalSlider.value()
        ui.voltage2=ui.horizontalSlider_2.value()
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())