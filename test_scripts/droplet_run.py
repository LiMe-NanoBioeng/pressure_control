# -*- coding: utf-8 -*-
# C:\Users\hirof\Anaconda3\Library\bin\pyuic5 -o gui_ui.pygui_main1.ui
import sys

import numpy as np
from NIDAQ_plt3 import AI as NI
import time
from PyQt5 import QtWidgets, QtCore
from test import Ui_MainWindow
from matplotlibwidget import MatplotlibWidget

# class of GUI window        
class MainWindow(QtWidgets.QMainWindow):    
    def __init__(self, parent=None):
        global ui
        super(MainWindow, self).__init__(parent=parent)
        ui = Ui_MainWindow()
        ui.setupUi(self)
        ui.graphwidget = MatplotlibWidget(ui.centralwidget,title='', xlabel='Time', ylabel='Pressure',
                 xlim=None, ylim=None, xscale='linear', yscale='linear',
                 width=8, height=3, dpi=100)

        ui.graphwidget.axes = ui.graphwidget.figure.add_subplot(121)  
        ui.graphwidget.axes = ui.graphwidget.figure.add_subplot(122)   
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_figure)
        timer.start(50)
        ui.x=[]
        ui.y=[]
        ui.c=[]
        ui.save=False
        ui.valve=False
        ui.Filename="./"
        ui.value=0
        
    def update_figure(self):
        #ui.graphwidget.clf
            
        x,y,c=NI.ArduinoAI(ui.x,ui.y,ui.c)
        #Convert voltage into pressure 
        c[1]=c[1]*24.75-23.75   # Valve1
        c[2]=c[2]*24.75-23.75   # Valve2
 
        if ui.save == True:
            
            # add Hiroyuki
            if ui.count != 0:
                # ui.count = 0で新規file open 
                ui.Ti = np.append(ui.Ti,c[0]-x[1])
                #print(ui.Ti)
                ui.CA1 = np.append(ui.CA1,c[1])
                ui.CA2 = np.append(ui.CA2,c[2])

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
#            ui.x=[]
#            ui.y=[]
#            ui.c=[]
            ui.count = 0 # add Hiroyuki
#            x,y,c=NI.ArduinoAI(ui.x,ui.y,ui.c) # add Hiroyuki
            

        # counter Display
        #NI.ArduinoAO(ui.valve)
        ui.lcdNumber.display(c[1])
        ui.lcdNumber_2.display(c[2])

        
    def slot1(self):

        ui.save = not ui.save
        if ui.save == True:

            ui.Filename = NI.DefFile()
    
    def slot2(self):# valve1 on off
#        NI.NIDAQ_Stream()
        ui.valve = not ui.valve
        NI.ArduinoDO(ui.valve)
        #I.ArduinoAO(ui.valve, ui.value)
#    def slot3(self):
#        NI.NIDAQ_DO()
    
    def slot3(self):# valve2 on off
#        NI.NIDAQ_Stream()
        ui.valve = not ui.valve
        NI.ArduinoDO(ui.valve)
        #I.ArduinoAO(ui.valve, ui.value)
#    def slot3(self):
#        NI.NIDAQ_DO()    

    def svalue_changed(self):
        ui.lcdNumber.display(ui.horizontalSlider_1.value())
        ui.lcdNumber_2.display(ui.horizontalSlider_2.value())
        ui.lcdNumber_3.display(ui.horizontalSlider_3.value())
        ui.lcdNumber_4.display(ui.horizontalSlider_4.value())
        ui.value = int(ui.horizontalSlider_1.value()*5000/99)
        #time.sleep(1)
        #ui.statusBar.showMessage(ui.horizontalSlider_1.value())
       

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())