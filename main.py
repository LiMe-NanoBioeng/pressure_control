# -*- coding: utf-8 -*-

import sys
import numpy as np
from ArduinoDAQ import AI as NI
import os
from os.path import expanduser
#import serial
import time
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QActionGroup, QApplication
from droplet_gui import Ui_Droplet_formation
import matplotlib
from matplotlibwidget import MatplotlibWidget
from MXsII import MXsIIt as MXsII
from ThermoPlate import ThermoPlate
from pycromanager_pipe import acq_pycromanager
import datetime
import json
import urllib.request
import urllib.parse
import threading
import ctypes
from collections import deque
from config import config
conf=config()

# Prevent Windows from sleeping or auto-restarting for updates while running
_ES_CONTINUOUS       = 0x80000000
_ES_SYSTEM_REQUIRED  = 0x00000001
_ES_DISPLAY_REQUIRED = 0x00000002

# Flow-stability watchdog (opt-in per sequence step via an optional 5th field,
# see read_seq_commands / README "Sequence file format")
STABILITY_SUSTAIN_S = 10.0        # length of the trailing window judged for instability
STABILITY_ARM_TIMEOUT_S = 120.0   # seconds allowed to first reach the tolerance band (e.g. filling a dry line)
STABILITY_OCCUPANCY = 0.7         # fraction of the trailing window that must be out-of-band to flag;
                                   # tolerates brief spikes/troughs the PID corrects on its own

now=datetime.datetime.now()
timestamp=now.strftime("%Y%m%d%H%M%S")
resultfilename="result"+timestamp
homedir=expanduser("~")

# operating=0;
class _StdoutRedirect:
    """Forwards sys.stdout writes to a QPlainTextEdit widget."""
    def __init__(self, widget):
        self._widget = widget
        self._buf = ''
    def _stamp(self, line):
        ts = datetime.datetime.now().strftime('%Y,%m/%d, %H:%M')
        return f'{ts}; {line}'
    def _prepend(self, line):
        cursor = QtGui.QTextCursor(self._widget.document())
        cursor.movePosition(QtGui.QTextCursor.Start)
        cursor.insertText(self._stamp(line) + '\n')
        self._widget.moveCursor(QtGui.QTextCursor.Start)
        self._widget.ensureCursorVisible()
    def write(self, text):
        self._buf += text
        while '\n' in self._buf:
            line, self._buf = self._buf.split('\n', 1)
            if line:
                self._prepend(line)
    def flush(self):
        if self._buf:
            self._prepend(self._buf)
            self._buf = ''


class SerialWorker(QtCore.QThread):
    data_ready = QtCore.pyqtSignal(float, object, bool, float)
    error      = QtCore.pyqtSignal(str)
    ai8_ready  = QtCore.pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True
        self._paused = False

    def run(self):
        while self._running:
            if not self._paused:
                try:
                    status = NI.ArduinoStatusCheck()
                    if status == 'R':
                        t, c, r = NI.ArduinoAI()
                        f = NI.ArduinoI2C() if conf.FLOW_SENSOR else -1.0
                        self.data_ready.emit(t, c, r, f)
                        ai8 = NI.ArduinoAI8()
                        self.ai8_ready.emit(ai8)
                except Exception as e:
                    self.error.emit(str(e))
            self.msleep(20 if conf.FLOW_SENSOR else 30)

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def stop(self):
        self._running = False
        self.wait()


class AcquisitionWorker(QtCore.QThread):
    finished = QtCore.pyqtSignal()
    failed = QtCore.pyqtSignal(str)

    def __init__(self, mda_file, pos_file, parent=None):
        super().__init__(parent)
        self._mda_file = mda_file
        self._pos_file = pos_file

    def run(self):
        try:
            acq = acq_pycromanager(self._mda_file, self._pos_file)
            acq.acquire_image()
            self.finished.emit()
        except Exception as e:
            self.failed.emit(str(e))


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        global ui
        super(MainWindow, self).__init__(parent=parent)
        ui = Ui_Droplet_formation()
        # must be set before any self.log_message() call (e.g. open_single_valve() below)
        ui.stability_mode = None      # 'a'=abort, 'l'=log-only; None = watchdog disabled for current step
        ui.stability_tolerance = None # fraction (e.g. 0.5=+/-50%)
        ui.stability_sustain_s = STABILITY_SUSTAIN_S # seconds out-of-band before flagging, per-step override
        ui.stability_armed = False    # becomes True once flow first enters the tolerance band
        ui.stability_history = deque() # (timestamp, in_band) samples over the trailing window, once armed
        ui.stability_notified = False # guards against log spam in 'l' mode / while unarmed
        ui.pressure_limit_mode = None      # 'a'=abort, 'l'=log-only; None = disabled (no header line)
        ui.pressure_limit_kpa = None       # threshold, parsed from the sequence file's first line
        ui.pressure_limit_duration_s = None
        ui.pressure_limit_since = None     # timestamp pressure first went above threshold, or None
        ui.pressure_limit_notified = False # guards against log spam in 'l' mode
        ui.ai8_limit_mode = None           # 'a'=abort, 'l'=log-only; None = disabled
        ui.ai8_limit_value = None          # raw AI8 threshold
        ui.ai8_limit_duration_s = None
        ui.ai8_limit_since = None          # timestamp AI8 first exceeded threshold, or None
        ui.ai8_limit_notified = False
        ui.log_filepath = None # text mirror of the on-screen log, set per RunSequence() call
        ui.seq_file_name = ''  # basename of the loaded sequence file, set by openSeqFile()
        ui.seq_file_path = ''  # full path of the loaded sequence file, set by openSeqFile()
        ui.slack_mention_user_id = '' # optional Slack user ID header line, set by openSeqFile()
        ui.send_step_image = False # per-step opt-in for a Slack screenshot, set by read_seq_commands()
        ui.slack_thread_ts = None # parent message ts for this run's Slack thread, set by RunSequence()
        ui.number_of_commands = 0 # number of commands; re-set to 0 again below in its original spot
        ui.MXsII=conf.SELECT_VALVE  # selector valve True/False  ##change for HybISS version
        ui.UseThermoPlate=conf.THERMO_PLATE
        ui.t = [] # time
        ui.dt = [] # time difference
        ui.c = [] # voltage of pressure
        ui.f = [] # flow rate
        ui.target_flow = [] # flow rate setpoint (0 when not in closed-loop 'u' mode)
        ui.valve_nums = np.array([], dtype=int) # valve number per sample
        ui.voltage = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0] # voltage to pressre regulator
        ui.setupUi(self)
        ui.actionOn.setChecked(conf.SELECT_VALVE)
        ui.actionOff.setChecked(not conf.SELECT_VALVE)
        sys.stdout = _StdoutRedirect(ui.messageBox)
        ui.comboBox.addItems(
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']) # valve/channel number
        ui.comboBox_2.addItems(
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']) # valve channel number
        ui.graphwidget = MatplotlibWidget(ui.centralwidget,
                                          xlim=None, ylim=None, xscale='linear', yscale='linear',
                                          width=12, height=5, dpi=95)

        NI.ArduinoReset()

        if(conf.FLOW_SENSOR):
            unit=NI.ArduinoAFU()
            ui.base_flow_unit = unit if unit != "" else "uL/min"
            ui.unit_display.setText(ui.base_flow_unit)
        else:
            ui.base_flow_unit = "uL/min"
            ui.unit_display.setText("(no flow sensor)")
            self.log_message("No flow sensor")


        self.worker = SerialWorker(self)
        self.worker.data_ready.connect(self.update_figure)
        self.worker.ai8_ready.connect(self._on_ai8)
        self.worker.start()

        ui.last_temp = -1.0
        self.thermo_timer = QtCore.QTimer(self)
        self.thermo_timer.setInterval(2000)
        self.thermo_timer.timeout.connect(self.update_temperature)
        if ui.UseThermoPlate:
            self.thermo_timer.start()
        ui.save = False  # Record data or not
        # valve initialization
        ui.valve_state = [False, False, False, False,
                      False, False, False, False, False, False, False, False]
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
        ui.current_valve_num = 0 # valve number for logging
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
        ui.actionload_log_file.triggered.connect(self.openLogFile)
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
        if ui.UseThermoPlate:
            try:
                ui.ThermoPlate.settemp(250)  # 250 = 25.0°C
            except Exception:
                pass
        ui.magnitude=0.1
        ui.magnitude_initialize=False
        ui.initsum=0.0
        ui.initcount=0
        self._acq_running = False


    def open_single_valve(self, index):
        for i in range(len(ui.valve_state)):
            if i != index-1:
                ui.valve_state[i] = False
            else:
                ui.valve_state[i] = True
            NI.ArduinoDO(i, ui.valve_state[i])
        valve_label = f"P{index:02X} " if index > 0 else ""
        if any(ui.valve_state):  # open the check valve
            #NI.ArduinoDO(10, True)
            NI.ArduinoDO(12, False)
            NI.ArduinoDO(11, True)
            time.sleep(1)
            NI.ArduinoDO(11, False)
            self.log_message(f'{valve_label}LSV is open')
        else:
            #s=NI.ArduinoDO(10, False)
            #NI.ArduinoDO(10, False)
            NI.ArduinoDO(12, True)
            NI.ArduinoDO(11, False)
            time.sleep(1)
            NI.ArduinoDO(12, False)
            self.log_message(f'{valve_label}LSV is closed')

    def check_selectorvalve(self,index): #JM added
        if index == 0:
            ui.MXsII = True
            self.log_message('Selector valve: On')
        else:
            ui.MXsII = False
            self.log_message('Selector valve: Off')

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
                self._check_flow_stability()
            elif self._acq_running:
                pass  # hold until acquisition finishes
            else:
            #if residual <0:
                # proceeds when the ui.residual time is less than 0 (wh\en negative)
                if ui.command > 0:  # a previous step in this run actually finished
                    finished_text = ui.tableWidget.item(ui.command - 1, 0).text().strip()
                    self.log_message(f"Step {ui.command}/{ui.number_of_commands} complete: {finished_text}")
                    if ui.send_step_image:
                        self._upload_slack_image(
                            self._grab_window_png(), f"step_{ui.command}.png", ui.slack_thread_ts,
                            f"Step {ui.command}/{ui.number_of_commands} complete")
                starting_text = ui.tableWidget.item(ui.command, 0).text().strip()
                remaining_s = self._estimate_remaining_time_s(ui.command)
                self.log_message(
                    f"[START] Step {ui.command + 1}/{ui.number_of_commands} starting: {starting_text} "
                    f"| est. remaining: {self._format_duration(remaining_s)}"
                )
                mode, valve, valve_num, pressure, duration,volume = self.read_seq_commands(
                    ui.command)
                ui.current_valve=valve
                ui.current_valve_num=valve_num
                ui.current_pressure=pressure # pressure/flow rate
                ui.duration = duration
                ui.volume=volume
                # ui.current_duration=duration
                ui.voltage[valve_num-1] = int(pressure)  # register pressure value; ui.voltage feeds QSlider.setValue(), which requires int


                #close valveFile ~/github/pressure_control/main.py:387, in MainWindow.update_figure(self)

                self.worker.pause()

                self.open_single_valve(-1)
                if ui.MXsII==True:
                    #MXsII.FTWrite(str(valve) + '\r')  # switch the valve
                    valve_hex = f"P{valve_num:02X}"  #convert 10 to 16 #JM added
                    MXsII.FTWrite(str(valve_hex) + '\r')  #switch the valve #JM added

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
                        ui.stability_armed = False
                        ui.stability_history.clear()
                        ui.stability_notified = False
                        # operating=1
                    else:
                        NI.ArduinoFB(False,ui.vNumA,ui.current_pressure,Kp,Ki,Kd)
                        NI.ArduinoAO(ui.vNumA, False, 0)
                        # operating =0
                elif mode=="a": #acquire image
                    mda_file = self.MDA_file_path
                    pos_file = self.Pos_file_path
                    self.log_message(f'Acquiring: {mda_file}')
                    self._acq_running = True
                    self._acq_worker = AcquisitionWorker(mda_file, pos_file, self)
                    self._acq_worker.finished.connect(self._on_acq_finished)
                    self._acq_worker.failed.connect(self._on_acq_failed)
                    self._acq_worker.start()
                elif mode=="c": #temperature set
                    if(ui.UseThermoPlate):
                        ui.ThermoPlate.settemp(int(pressure))

                self.worker.resume()

                ui.start = time.time()
                ui.qstart=ui.q[-1]
                if mode != "a":
                    # proceedsd ui.command
                    ui.command += 1
                    ui.lcdSeqNumber.display(ui.command)
                    item = ui.tableWidget.item(ui.command, 0)
                    if item is not None:
                        ui.tableWidget.scrollToItem(item, QtWidgets.QAbstractItemView.PositionAtTop)
        else:
            # commands at the end of the sequence (when ui.number_of_commands-ui.command==0)
            if residual > 0:
                value=NI.ArduinoFBStatus(ui.vNumA)
                ui.lcdnumber_1.display(value)
                self._check_flow_stability()

            elif ui.number_of_commands != 0:
            #if ui.number_of_commands !=0 and residual <0 :
                finished_text = ui.tableWidget.item(ui.command - 1, 0).text().strip()
                self.log_message(f"Step {ui.command}/{ui.number_of_commands} complete: {finished_text}")
                if ui.send_step_image:
                    self._upload_slack_image(
                        self._grab_window_png(), f"step_{ui.command}.png", ui.slack_thread_ts,
                        f"Step {ui.command}/{ui.number_of_commands} complete")
                self.log_message(f"All {ui.number_of_commands} sequence steps have completed.")
                self._unblock_system_idle()
                self._upload_slack_image(
                    self._grab_window_png(), "complete.png", ui.slack_thread_ts, "Sequence complete")
                self.worker.pause()
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
                self.worker.resume()

    def _check_flow_stability(self):
        """Opt-in watchdog for closed-loop ('u' mode) steps: see the stability
        spec parsed in read_seq_commands (<a|l><tolerance>per[,<duration>s]).
        Arms once flow first enters the tolerance band (allowing time to fill
        a dry line). Once armed, flags if flow has spent at least
        STABILITY_OCCUPANCY of the trailing stability_sustain_s window outside
        the band -- a rolling occupancy check, not a single unbroken streak, so
        chattering/oscillating flow that only briefly grazes the band can't
        evade detection, while an isolated spike/trough the PID corrects on
        its own (contributing only a sliver of "bad" time) won't false-trigger.
        """
        if ui.command <= 0:  # no step in this run has started yet
            return
        if ui.mode != "u" or ui.current_pressure <= 0:
            return
        if ui.stability_mode not in ('a', 'l'):
            return
        if not ui.f:
            return
        setpoint = ui.current_pressure
        flow = ui.f[-1]
        now = time.time()
        lower = setpoint * (1 - ui.stability_tolerance)
        upper = setpoint * (1 + ui.stability_tolerance)
        in_band = lower <= flow <= upper

        if not ui.stability_armed:
            if in_band:
                ui.stability_armed = True
                ui.stability_history.clear()
                ui.stability_history.append((now, in_band))
                ui.stability_notified = False
            elif now - ui.start > STABILITY_ARM_TIMEOUT_S:
                cmd_text = ui.tableWidget.item(ui.command - 1, 0).text().strip()
                self._flag_instability(
                    f"{cmd_text}: no flow detected at P{ui.current_valve_num:02X} within "
                    f"{STABILITY_ARM_TIMEOUT_S:.0f}s of opening the valve "
                    f"(set flow rate {setpoint:.1f} uL/min, actual flow rate {flow:.1f} uL/min). "
                    "Line may be blocked or empty."
                )
            return

        history = ui.stability_history
        history.append((now, in_band))
        window_start = now - ui.stability_sustain_s
        while len(history) > 1 and history[1][0] <= window_start:
            history.popleft()
        if history[0][0] > window_start:
            return  # not enough history yet to judge a full window

        bad_time = sum(
            t1 - t0 for (t0, was_in_band), (t1, _) in zip(history, list(history)[1:])
            if not was_in_band
        )
        if bad_time >= STABILITY_OCCUPANCY * ui.stability_sustain_s:
            cmd_text = ui.tableWidget.item(ui.command - 1, 0).text().strip()
            self._flag_instability(
                f"{cmd_text}: flow at P{ui.current_valve_num:02X} outside +/-{ui.stability_tolerance*100:.0f}% "
                f"band for {bad_time:.1f} of the last {ui.stability_sustain_s:.0f}s "
                f"(set flow rate {setpoint:.1f} uL/min, actual flow rate {flow:.1f} uL/min)."
            )
        else:
            ui.stability_notified = False

    def _flag_instability(self, reason):
        if ui.stability_mode == 'a':
            self.log_message(f"*** FLOW INSTABILITY (ABORT): {reason}")
            self.abort_program()
            QtWidgets.QMessageBox.critical(self, "Sequence aborted", reason)
        elif not ui.stability_notified:
            self.log_message(f"*** FLOW INSTABILITY (log only): {reason}")
            ui.stability_notified = True

    def _check_pressure_limit(self, pressure_kpa):
        """Sequence-wide safety ceiling, parsed from an optional header line
        in the sequence file (see openSeqFile): aborts (or logs) if pressure
        stays above the threshold for a continuous stretch longer than the
        configured duration, regardless of which step/mode is active --
        protects the sample from prolonged high-pressure exposure."""
        if ui.number_of_commands == 0 or ui.pressure_limit_mode not in ('a', 'l'):
            return
        now = time.time()
        if pressure_kpa > ui.pressure_limit_kpa:
            if ui.pressure_limit_since is None:
                ui.pressure_limit_since = now
            elif now - ui.pressure_limit_since > ui.pressure_limit_duration_s:
                reason = (
                    f"Pressure at P{ui.current_valve_num:02X} has stayed above "
                    f"{ui.pressure_limit_kpa:.1f} kPa for over {ui.pressure_limit_duration_s:.0f}s "
                    f"(current reading {pressure_kpa:.1f} kPa)."
                )
                if ui.pressure_limit_mode == 'a':
                    self.log_message(f"*** PRESSURE LIMIT (ABORT): {reason}")
                    self.abort_program()
                    QtWidgets.QMessageBox.critical(self, "Sequence aborted", reason)
                elif not ui.pressure_limit_notified:
                    self.log_message(f"*** PRESSURE LIMIT (log only): {reason}")
                    ui.pressure_limit_notified = True
        else:
            ui.pressure_limit_since = None
            ui.pressure_limit_notified = False

    def _check_ai8_limit(self, value):
        if ui.number_of_commands == 0 or ui.ai8_limit_mode not in ('a', 'l'):
            return
        now = time.time()
        if value > ui.ai8_limit_value:
            if ui.ai8_limit_since is None:
                ui.ai8_limit_since = now
            elif now - ui.ai8_limit_since > ui.ai8_limit_duration_s:
                reason = (
                    f"AI8 has stayed above {ui.ai8_limit_value:g} for over "
                    f"{ui.ai8_limit_duration_s:.0f}s (current reading {value:g})."
                )
                if ui.ai8_limit_mode == 'a':
                    self.log_message(f"*** AI8 LIMIT (ABORT): {reason}")
                    self.abort_program()
                    QtWidgets.QMessageBox.critical(self, "Sequence aborted", reason)
                elif not ui.ai8_limit_notified:
                    self.log_message(f"*** AI8 LIMIT (log only): {reason}")
                    ui.ai8_limit_notified = True
        else:
            ui.ai8_limit_since = None
            ui.ai8_limit_notified = False

    def _update_flowrate_color(self, flow):
        """Turns the flowrate LCD red when the reading is outside the tolerance
        band configured for the current step (same band _check_flow_stability
        uses); reverts to the default color otherwise, including when no
        tolerance is configured for this step (watchdog field omitted)."""
        setpoint = getattr(ui, 'current_pressure', 0)
        if (ui.mode == "u" and ui.stability_tolerance is not None
                and setpoint > 0):
            lower = setpoint * (1 - ui.stability_tolerance)
            upper = setpoint * (1 + ui.stability_tolerance)
            if not (lower <= float(flow) <= upper):
                ui.flowrate.setStyleSheet("color: red;")
                return
        ui.flowrate.setStyleSheet("")

    def _update_sequence_labels(self):
        """During a running sequence, swaps static unit/caption labels for
        live status: the flow/pressure unit labels grow a '| X' suffix with
        the setpoint for the mode currently driving the feedback loop, and
        the '1st valve' caption becomes the valve actually being controlled.
        Reverts to the static defaults once no sequence is running."""
        if ui.number_of_commands != 0:
            ui.label_11.setText(f"P{ui.current_valve_num:02X}")
            if ui.mode == "p" and ui.current_pressure > 0:
                ui.label.setText(f"kPa | {ui.current_pressure:.1f} kPa")
            else:
                ui.label.setText("kPa")
            if ui.mode == "u" and ui.current_pressure > 0:
                ui.unit_display.setText(
                    f"{ui.base_flow_unit} | {ui.current_pressure:.1f} {ui.base_flow_unit}")
            else:
                ui.unit_display.setText(ui.base_flow_unit)
        else:
            ui.label_11.setText("   1st valve")
            ui.label.setText("kPa")
            ui.unit_display.setText(ui.base_flow_unit)

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
            self.log_message('Single pressure')
            ui.valveButton_2.hide()
            ui.valveLcd_2.hide()
            ui.horizontalSlider_2.hide()
            ui.comboBox_2.hide()
            ui.label_8.hide()
            ui.label_10.hide()
            ui.lcdnumber_2.hide()
            ui.line.hide()

        elif ui.Numpre == 1:
            self.log_message('Double pressure')
            ui.valveButton_2.show()
            ui.valveLcd_2.show()
            ui.horizontalSlider_2.show()
            ui.comboBox_2.show()
            ui.label_8.show()
            ui.label_10.show()
            ui.lcdnumber_2.show()
            ui.line.show()

    def _estimate_step_duration_s(self, text):
        """Best-effort estimate of one sequence step's duration in seconds,
        from its raw text, without touching any run state. A time-based stop
        is used directly; a volume-based stop is estimated as volume/flow
        rate (only meaningful for 'u' mode, where parameter1 is a flow rate).
        Returns 0.0 when it can't be estimated (e.g. an acquire step)."""
        message = text.strip().split(',')
        if len(message) < 3:
            return 0.0
        try:
            parameter = float(message[1][:-1])
            mode = message[1][-1]
            terminal = message[2].strip()
            if terminal[-1] == 's':
                return float(terminal[:-1])
            elif terminal[-1] == 'u':
                volume = float(terminal[:-1])
                if mode == "u" and parameter > 0:
                    return volume / parameter * 60.0
        except (ValueError, IndexError):
            pass
        return 0.0

    def _estimate_remaining_time_s(self, from_row):
        """Sums _estimate_step_duration_s over every remaining row, from
        from_row (inclusive) through the end of the loaded sequence."""
        total = 0.0
        for row in range(from_row, ui.number_of_commands):
            item = ui.tableWidget.item(row, 0)
            if item is not None:
                total += self._estimate_step_duration_s(item.text())
        return total

    def _format_duration(self, seconds):
        if seconds < 60:
            return f"{seconds:.0f}s"
        minutes = seconds / 60.0
        if minutes < 60:
            return f"{minutes:.1f}min"
        return f"{minutes / 60.0:.2f}h"

    def read_seq_commands(self, command):
        text = ui.tableWidget.item(command, 0).text()
        message = text.split(',')

        # optional trailing image flag: literal 'img' as the last field,
        # after any other optional fields (PID, stability watchdog). Opts
        # this step's completion into a Slack screenshot; default off.
        ui.send_step_image = False
        if message and message[-1].strip().lower() == 'img':
            ui.send_step_image = True
            message = message[:-1]

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
        #valve_num = int(valve[-1], 16)
        valve_num = int(valve[1:])  ##JM modified
        ui.termination_mode=terminal[-1]
        ui.mode=mode

        #read PID parameters
        if len(message) > 3:
            Kp,Ki,Kd = map(float,message[3].split(';'))
            ui.pid_parameters[command] = (Kp,Ki,Kd)
            ui.last_pid = (Kp,Ki,Kd)

        # optional flow-stability watchdog: <a|l><tolerance>per[,<duration>s]
        # 'a' aborts the sequence, 'l' only logs a warning; omit to leave disabled
        ui.stability_mode = None
        ui.stability_tolerance = None
        ui.stability_sustain_s = STABILITY_SUSTAIN_S
        if len(message) > 4 and message[4].strip() != '':
            spec = message[4].strip()
            letter, rest = spec[0], spec[1:]
            if letter in ('a', 'l') and rest.endswith('per'):
                ui.stability_mode = letter
                ui.stability_tolerance = float(rest[:-3]) / 100.0
                if len(message) > 5 and message[5].strip() != '':
                    dur_str = message[5].strip()
                    if dur_str.endswith('s'):
                        dur_str = dur_str[:-1]
                    ui.stability_sustain_s = float(dur_str)
            else:
                self.log_message(f"Ignoring malformed stability spec '{spec}' on line {command+1}")
        return (mode,valve, valve_num, parameter, duration,volume)

    def initialize_magnitude(self):
        NI.ArduinoAO(ui.vNumA, True, 254)
        ui.magnitude_initialize=True
    

    def initialize_end(self):
        return 1;


    def _on_acq_finished(self):
        self.log_message('Acquisition complete')
        self._acq_running = False
        self._acq_worker.deleteLater()
        ui.command += 1
        ui.lcdSeqNumber.display(ui.command)
        item = ui.tableWidget.item(ui.command, 0)
        if item is not None:
            ui.tableWidget.scrollToItem(item, QtWidgets.QAbstractItemView.PositionAtTop)

    def _on_acq_failed(self, msg):
        self.log_message(f'*** ACQUISITION FAILED: {msg}')
        self.log_message('Sequence aborted. Waiting for operator action.')
        self._acq_running = False
        ui.number_of_commands = 0
        ui.lcdSeqNumber.display(0)
        Kp, Ki, Kd = ui.last_pid
        NI.ArduinoFB(False, ui.vNumA, ui.current_pressure, Kp, Ki, Kd)
        NI.ArduinoAO(ui.vNumA, False, 0)
        self.open_single_valve(-1)
        if ui.save:
            ui.save = False

    def log_message(self, msg):
        print(msg)
        self._write_log_file(msg)
        self._notify_slack(msg)

    def _write_log_file(self, msg):
        if not ui.log_filepath:
            return
        ts = datetime.datetime.now().strftime('%Y,%m/%d, %H:%M')
        try:
            with open(ui.log_filepath, 'a', encoding='utf-8') as f:
                f.write(f'{ts}; {msg}\n')
        except OSError:
            pass  # avoid crashing the sequence over a logging failure

    def _new_log_filepath(self):
        """Create this run's text log, in the same folder as the current exp
        data file (ui.Filename, set by recordIO()/DefFile()) so the two live
        side by side. Falls back to ui.Foldername if recording hasn't been
        started (ui.Filename still the ' ' placeholder) or that folder can't
        be written to. Returns (path, error), error is None on success."""
        filename = datetime.datetime.now().strftime('%Y%m%d%H%M') + 'MiSA.log.txt'
        exp_dir = os.path.dirname(ui.Filename.strip()) if ui.Filename.strip() else ''
        target_dir = exp_dir if exp_dir else ui.Foldername
        path = os.path.join(target_dir, filename)
        try:
            os.makedirs(target_dir, exist_ok=True)
            with open(path, 'a', encoding='utf-8'):
                pass
            return path, None
        except OSError as e:
            fallback = os.path.join(ui.Foldername, filename)
            return fallback, str(e)

    def _slack_error(self, msg):
        """Reports a Slack-related failure without touching any Qt widget --
        these methods run on background threads (see _run_async below), and
        Qt widgets may only be touched from the main/GUI thread. Writes to
        the real stderr (bypassing sys.stdout's GUI-log redirect) and the
        text log file (plain file I/O, thread-safe enough for an appended
        line); never routes through log_message/_notify_slack, which would
        recurse back into Slack over a Slack failure."""
        sys.__stderr__.write(msg + "\n")
        self._write_log_file(msg)

    def _run_async(self, target, *args):
        """Fires a background daemon thread for a Slack network call so it
        can never block the GUI thread (the sequence timer, valve timing,
        etc). Fire-and-forget: callers don't need the result."""
        threading.Thread(target=target, args=args, daemon=True).start()

    def _slack_post(self, text, thread_ts=None):
        """POSTs one message via chat.postMessage (config.py SLACK_BOT_TOKEN
        / SLACK_CHANNEL). Returns the message's ts on success (usable as a
        thread_ts for replies), or None on failure. Never raises. Runs
        synchronously in whatever thread calls it -- callers that don't need
        the ts back should go through _run_async instead of calling this
        directly, to keep the GUI thread unblocked."""
        try:
            payload = {"channel": conf.SLACK_CHANNEL, "text": text}
            if thread_ts:
                payload["thread_ts"] = thread_ts
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                "https://slack.com/api/chat.postMessage", data=data,
                headers={"Content-Type": "application/json; charset=utf-8",
                         "Authorization": f"Bearer {conf.SLACK_BOT_TOKEN}"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                result = json.loads(resp.read().decode('utf-8'))
            if result.get("ok"):
                return result.get("ts")
            self._slack_error(f"Slack post failed: {result.get('error')}")
        except Exception as e:
            self._slack_error(f"Slack post failed: {e}")
        return None

    def _start_slack_thread(self):
        """Posts this run's thread header ('YYYYMMDDHHMM <seqfile> at
        <instrument>', optionally prefixed with an @-mention if the sequence
        file's leading headers included a Slack user ID), and remembers its
        ts in ui.slack_thread_ts so every subsequent _notify_slack() call
        replies into the same thread. This one call is made synchronously
        (blocking, ~1 call, only once per RunSequence()) because everything
        downstream needs the resulting thread_ts; the sequence file's full
        content, posted as a second message, doesn't gate anything else so
        it's dispatched asynchronously like every other Slack call. No-op
        (thread_ts stays None -> _notify_slack falls back to the plain
        webhook, unthreaded) if no bot token/channel is configured."""
        ui.slack_thread_ts = None
        if not (conf.SLACK_BOT_TOKEN and conf.SLACK_CHANNEL):
            return
        header = (f"{datetime.datetime.now().strftime('%Y%m%d%H%M')} "
                  f"{ui.seq_file_name} at {conf.INSTRUMENT_NAME}")
        if ui.slack_mention_user_id:
            header = f"<@{ui.slack_mention_user_id}> {header}"
        ui.slack_thread_ts = self._slack_post(header)
        if not ui.slack_thread_ts:
            return
        self._run_async(self._post_seq_file_content, ui.seq_file_path, ui.slack_thread_ts)

    def _post_seq_file_content(self, seq_file_path, thread_ts):
        try:
            with open(seq_file_path, 'r') as f:
                content = f.read()
        except OSError as e:
            content = f"(could not read sequence file: {e})"
        if len(content) > 3900:
            content = content[:3900] + "\n... (truncated)"
        self._slack_post(f"```{content}```", thread_ts=thread_ts)

    def _grab_window_png(self):
        """Renders the whole main window (not just the plot) to PNG bytes,
        via QWidget.grab() -> QPixmap -> PNG-encoded QBuffer. Must run on the
        GUI thread (Qt widgets aren't thread-safe) -- callers grab synchronously
        and hand the resulting bytes off to _upload_slack_image, which does
        the actual network I/O asynchronously."""
        pixmap = self.grab()
        byte_array = QtCore.QByteArray()
        buffer = QtCore.QBuffer(byte_array)
        buffer.open(QtCore.QIODevice.WriteOnly)
        pixmap.save(buffer, "PNG")
        buffer.close()
        return bytes(byte_array)

    def _upload_slack_image(self, png_bytes, filename, thread_ts, title):
        """Uploads a PNG to Slack and shares it into thread_ts, via the
        3-step external-upload flow (files:write scope required on the bot
        token). No-ops if unconfigured or no thread is active. Dispatched
        onto a background thread (_run_async) -- 3 sequential HTTP round
        trips would otherwise visibly freeze the GUI on every step."""
        if not (conf.SLACK_BOT_TOKEN and conf.SLACK_CHANNEL) or not thread_ts:
            return
        self._run_async(self._upload_slack_image_sync, png_bytes, filename, thread_ts, title)

    def _upload_slack_image_sync(self, png_bytes, filename, thread_ts, title):
        try:
            params = urllib.parse.urlencode(
                {"filename": filename, "length": len(png_bytes)}).encode('utf-8')
            req = urllib.request.Request(
                "https://slack.com/api/files.getUploadURLExternal", data=params,
                headers={"Content-Type": "application/x-www-form-urlencoded",
                         "Authorization": f"Bearer {conf.SLACK_BOT_TOKEN}"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode('utf-8'))
            if not result.get("ok"):
                self._slack_error(f"Slack image upload (get URL) failed: {result.get('error')}")
                return
            upload_url, file_id = result["upload_url"], result["file_id"]

            boundary = "----MiSABoundary"
            body = (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
                f"Content-Type: image/png\r\n\r\n"
            ).encode('utf-8') + png_bytes + f"\r\n--{boundary}--\r\n".encode('utf-8')
            req2 = urllib.request.Request(
                upload_url, data=body,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
            urllib.request.urlopen(req2, timeout=15)

            payload = {"files": [{"id": file_id, "title": title}],
                       "channel_id": conf.SLACK_CHANNEL, "thread_ts": thread_ts}
            data3 = json.dumps(payload).encode('utf-8')
            req3 = urllib.request.Request(
                "https://slack.com/api/files.completeUploadExternal", data=data3,
                headers={"Content-Type": "application/json; charset=utf-8",
                         "Authorization": f"Bearer {conf.SLACK_BOT_TOKEN}"})
            with urllib.request.urlopen(req3, timeout=10) as resp3:
                result3 = json.loads(resp3.read().decode('utf-8'))
            if not result3.get("ok"):
                self._slack_error(f"Slack image upload (complete) failed: {result3.get('error')}")
        except Exception as e:
            self._slack_error(f"Slack image upload failed: {e}")

    def _notify_slack(self, text):
        """Best-effort Slack notification, called from log_message() to
        mirror every log line. Prefers the threaded bot-token path (replies
        into ui.slack_thread_ts, started by _start_slack_thread() at the
        top of RunSequence()); falls back to the plain incoming-webhook
        (config.py SLACK_WEBHOOK_URL, unthreaded) if no bot token/channel is
        configured. No-ops silently if neither is configured, or if no
        sequence is currently running -- manual/ad-hoc actions (jogging a
        valve, tuning) outside a sequence run stay off Slack. Dispatched
        onto a background thread (_run_async) since log_message() is called
        constantly from the GUI thread and must never block on network I/O."""
        if ui.number_of_commands == 0:
            return
        if conf.SLACK_BOT_TOKEN and conf.SLACK_CHANNEL:
            self._run_async(self._slack_post, text, ui.slack_thread_ts)
            return
        if not conf.SLACK_WEBHOOK_URL:
            return
        self._run_async(self._notify_slack_webhook, text)

    def _notify_slack_webhook(self, text):
        try:
            data = json.dumps({"text": text}).encode('utf-8')
            req = urllib.request.Request(
                conf.SLACK_WEBHOOK_URL, data=data,
                headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=5)
        except Exception as e:
            self._slack_error(f"Slack notification failed: {e}")

    def _add_valve_axis(self, ax, t, valve_nums):
        t = np.asarray(t, dtype=float).ravel()
        v = np.asarray(valve_nums, dtype=int).ravel()
        if len(t) < 2:
            return
        axv = ax.twinx()
        axv.step(t, v, where='post', color='gray', alpha=0.5, linewidth=1)
        axv.set_ylabel('Valve', color='gray', fontsize=8)
        axv.tick_params(axis='y', colors='gray', labelsize=7)

    def draw_graph(self): #update JM
        ui.graphwidget.figure.clear()

        ui.graphwidget.axes1 = ui.graphwidget.figure.add_subplot(221, xlabel='Time [s]', ylabel='Pressure [kPa]')
        ca1_arr = np.array(ui.CA1)
        ui.graphwidget.axes1.plot(ui.dt, ca1_arr[:, :ui.Numpre+1])
        self._add_valve_axis(ui.graphwidget.axes1, ui.dt, ui.valve_nums)

        ui.graphwidget.axes2 = ui.graphwidget.figure.add_subplot(222, xlabel='Time [s]', ylabel='Flow rate [μL/min]')
        ui.graphwidget.axes2.plot(ui.dt, ui.f, label='actual')
        ui.graphwidget.axes2.plot(ui.dt, ui.target_flow, '--', label='target')
        ui.graphwidget.axes2.legend(fontsize=8)

        ui.graphwidget.axes3 = ui.graphwidget.figure.add_subplot(223, xlabel='Time [s]', ylabel='Pumped volume [μL]')
        ui.graphwidget.axes3.plot(ui.dt, ui.q)
        self._add_valve_axis(ui.graphwidget.axes3, ui.dt, ui.valve_nums)

        ui.graphwidget.axes4 = ui.graphwidget.figure.add_subplot(224, xlabel='Time [s]', ylabel='Temperature [C]')
        ui.graphwidget.axes4.plot(ui.dt, ui.temperature)
        self._add_valve_axis(ui.graphwidget.axes4, ui.dt, ui.valve_nums)

        ui.graphwidget.figure.tight_layout()
        ui.graphwidget.draw()

    def draw_log_graph(self, data):
        ncols  = data.shape[1]
        t      = data[:, 0]
        p1     = data[:, 1]
        p2     = data[:, 2]
        f      = data[:, 3]
        q      = data[:, 4]
        temp   = data[:, 5] if ncols > 5 else None
        valve  = data[:, 6] if ncols > 6 else None

        ui.graphwidget.figure.clear()

        ax1 = ui.graphwidget.figure.add_subplot(221, xlabel='Time [s]', ylabel='Pressure [kPa]')
        ax1.plot(t, p1, label='ch1')
        ax1.plot(t, p2, label='ch2')
        ax1.legend(fontsize=8)
        self._add_valve_axis(ax1, t, valve if valve is not None else [])

        ax2 = ui.graphwidget.figure.add_subplot(222, xlabel='Time [s]', ylabel='Flow rate [µL/min]')
        ax2.plot(t, f)
        self._add_valve_axis(ax2, t, valve if valve is not None else [])

        ax3 = ui.graphwidget.figure.add_subplot(223, xlabel='Time [s]', ylabel='Volume [µL]')
        ax3.plot(t, q)
        self._add_valve_axis(ax3, t, valve if valve is not None else [])

        ax4 = ui.graphwidget.figure.add_subplot(224, xlabel='Time [s]', ylabel='Temperature [°C]')
        if temp is not None:
            ax4.plot(t, temp)
        self._add_valve_axis(ax4, t, valve if valve is not None else [])

        ui.graphwidget.axes1 = ax1
        ui.graphwidget.axes2 = ax2
        ui.graphwidget.axes3 = ax3
        ui.graphwidget.axes4 = ax4

        ui.graphwidget.figure.tight_layout()
        ui.graphwidget.draw()

    def function_change(self,index):
        ui.reg = index

    def _on_ai8(self, value):
        self.setWindowTitle(f'MiSA   |   AI8 = {value:g}')
        self._check_ai8_limit(value)

    def update_temperature(self):
        if ui.UseThermoPlate:
            try:
                ui.last_temp = float(ui.ThermoPlate.readtemp())
            except Exception:
                pass

    def update_figure(self, arduino_time, c, r, f):
        if ui.tuning_is_running:
            self.tuningCore()
        temp = ui.last_temp
        if r:
            g = [0.1208, 1.097, -0.1208, 0.0610]
            h = [-23.75, -223.75, 23.78, -12.5]
            c[0] = g[ui.reg] * c[0] + h[ui.reg]
            c[1] = g[ui.reg] * c[1] + h[ui.reg]
            ui.valveLcd_1.display(c[0])
            ui.valveLcd_2.display(c[1]) #add JM
            self._check_pressure_limit(c[0])
            if(c[0]>0 and ui.magnitude_initialize and ui.initcount<10):
                ui.initsum+=c[0]
                ui.initcount+=1
            if(ui.initcount==10):
                ui.initcount=0
                ui.magnitude=ui.initsum/10.0
                ui.initsum=0.0
                ui.magnitude_initialize=False
                NI.ArduinoAO(ui.vNumA,True,0)
                self.log_message(f"Tuning complete. Magnitude: {ui.magnitude:.3f}")
            if ui.save == True:
                # add Hiroyuki
                if ui.count != 0:
                    ui.dt.append(arduino_time - ui.t)
                    ui.CA1.append(list(c))
                    ui.f.append(float(f))
                    ui.temperature.append(float(temp))
                    ui.valve_nums.append(ui.current_valve_num)
                    target = ui.current_pressure if (ui.mode == "u" and ui.current_pressure > 0) else 0.0
                    ui.target_flow.append(target)
                    if ui.count != 1:  # compute integrated flow quantity at t > 1
                        q = ui.q[-1]+np.median([ui.f[-3], ui.f[-2], ui.f[-1]])*(ui.dt[-1]-ui.dt[-2])/60
                    else:  # compute integrated flow quantity at t=1
                        q = float(f)*(ui.dt[-1])/60
                    ui.q.append(q)

                    c_row = np.array([round(ui.dt[-1], 6)] + list(c) + [float(f), float(q), float(temp), float(ui.current_valve_num)])
                    if arduino_time - ui.t - ui._last_graph_update >= 1.0:
                        self.draw_graph()
                        ui._last_graph_update = arduino_time - ui.t

                    file = open(ui.Filename, 'a')
                else:
                    ui.t = arduino_time  # initial time
                    ui.dt = [0.0]
                    ui.CA1 = [list(c)]
                    ui.f = [float(f)]
                    ui.q = [0.0]
                    ui.temperature = [float(temp)]
                    ui.valve_nums = [ui.current_valve_num]
                    target = ui.current_pressure if (ui.mode == "u" and ui.current_pressure > 0) else 0.0
                    ui.target_flow = [target]
                    ui._last_graph_update = 0.0
                    file = open(ui.Filename, 'w')
                    c_row = np.array([0.0] + list(c) + [float(f), 0.0, float(temp), float(ui.current_valve_num)])

                ui.count = ui.count + 1

                for i in c_row:
                    jp = (str(i))
                    file.write(jp)
                    file.write(',')  # コンマ
                file.write('\n')  # 改行コード
                file.close()

            else:
                ui.count = 0  # add Hiroyuki
            ui.flowrate.display(f)
            self._update_flowrate_color(f)
            self._update_sequence_labels()
            # counter Display
            #
            if ui.number_of_commands != 0 and len(ui.f) > 4:
                self.SequenceControlTime()


    def RunSequence(self):
        ui.command = 0
        ui.number_of_commands = ui.tableWidget.rowCount()
        # clear state left over from any previous run so the first tick of this
        # run doesn't compute a stale residual or reference a nonexistent step
        ui.mode = ""
        ui.termination_mode = ""
        ui.duration = 0
        ui.volume = 0
        ui.qstart = 0
        ui.residualtime = 0
        ui.stability_mode = None
        ui.stability_tolerance = None
        ui.stability_armed = False
        ui.stability_history.clear()
        ui.stability_notified = False
        ui.pressure_limit_since = None
        ui.pressure_limit_notified = False
        ui.ai8_limit_since = None
        ui.ai8_limit_notified = False
        self._block_system_idle()
        self._start_slack_thread()
        path, error = self._new_log_filepath()
        ui.log_filepath = path
        if error:
            self.log_message(f"Could not write log next to the exp file ({error}); logging to {path} instead")
        self.log_message(f"Sequence started. Logging to {path}")

    def openSeqFile(self):
        iDir = os.path.abspath(os.path.dirname(__file__))
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open sequence file", iDir, "Sequence files (*.txt);;All files (*.*)")
        if not file_name:
            return
        ui.seq_file_name = os.path.basename(file_name)
        ui.seq_file_path = file_name
        self.log_message(f"Sequence file: {file_name}")
        f = open(file_name, 'r')
        lines = list(f)
        f.close()

        # optional leading header lines, in any order, each consumed and not
        # shown as a step. Stops at the first line matching neither pattern.
        #   <a|l><kPa value>kPa,<duration>s -- sequence-wide pressure ceiling,
        #     checked regardless of step/mode (distinguishable from a normal
        #     step because valve tokens always start with uppercase P/A).
        #   <Slack user ID> (e.g. U06SFM9T6R3) -- mentioned in the thread's
        #     first message (see _start_slack_thread). Distinguishable from
        #     a valve token because valve tokens are never all-uppercase
        #     with no comma.
        ui.pressure_limit_mode = None
        ui.pressure_limit_kpa = None
        ui.pressure_limit_duration_s = None
        ui.ai8_limit_mode = None
        ui.ai8_limit_value = None
        ui.ai8_limit_duration_s = None
        ui.slack_mention_user_id = ''
        while lines:
            candidate = lines[0].strip()
            if candidate[:1] in ('a', 'l') and 'kPa' in candidate:
                letter, rest = candidate[0], candidate[1:]
                try:
                    value_part, dur_part = rest.split(',', 1)
                    dur_part = dur_part.strip()
                    if value_part.endswith('kPa') and dur_part.endswith('s'):
                        ui.pressure_limit_mode = letter
                        ui.pressure_limit_kpa = float(value_part[:-3])
                        ui.pressure_limit_duration_s = float(dur_part[:-1])
                        lines = lines[1:]
                        self.log_message(
                            f"Pressure limit ({'abort' if letter == 'a' else 'log only'}): "
                            f">{ui.pressure_limit_kpa:.1f} kPa for {ui.pressure_limit_duration_s:.0f}s"
                        )
                        continue
                except ValueError:
                    pass  # not a valid header; fall through
            if candidate[:1] in ('a', 'l') and 'AI8' in candidate:
                letter, rest = candidate[0], candidate[1:]
                try:
                    value_part, dur_part = rest.split(',', 1)
                    dur_part = dur_part.strip()
                    if value_part.endswith('AI8') and dur_part.endswith('s'):
                        ui.ai8_limit_mode = letter
                        ui.ai8_limit_value = float(value_part[:-3])
                        ui.ai8_limit_duration_s = float(dur_part[:-1])
                        lines = lines[1:]
                        self.log_message(
                            f"AI8 limit ({'abort' if letter == 'a' else 'log only'}): "
                            f">{ui.ai8_limit_value:g} for {ui.ai8_limit_duration_s:.0f}s"
                        )
                        continue
                except ValueError:
                    pass  # not a valid header; fall through
            if (candidate.startswith('U') and len(candidate) >= 9
                    and candidate.isalnum() and candidate.isupper()):
                ui.slack_mention_user_id = candidate
                lines = lines[1:]
                self.log_message(f"Slack mention: <@{candidate}>")
                continue
            break  # first line that isn't a recognized header -> steps start here

        # ui.tableWidget.setRowCount(0)

        ui.tableWidget.setColumnCount(1)
        ui.tableWidget.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        ui.tableWidget.setWordWrap(True)
        rowPosition = 0
        ui.tableWidget.setRowCount(0)
        for x in lines:
            ui.tableWidget.insertRow(rowPosition)
            item = QtWidgets.QTableWidgetItem(x)
            item.setToolTip(x)
            ui.tableWidget.setItem(rowPosition, 0, item)
            rowPosition += 1
        ui.tableWidget.resizeRowsToContents()

    def openLogFile(self):
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open log file", ui.Foldername,
            "Log files (*.txt);;All files (*.*)")
        if not file_name:
            return
        try:
            data = np.genfromtxt(file_name, delimiter=',')
            if data.ndim == 1:
                data = data[np.newaxis, :]
            if np.all(np.isnan(data[:, -1])):  # strip trailing NaN from trailing comma
                data = data[:, :-1]
            self.draw_log_graph(data)
        except Exception as e:
            self.log_message(f"Failed to open log file: {e}")

    def openMDAFile(self):
        iDir = os.path.abspath(os.path.dirname(__file__))
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open MDA file", iDir, "MDA files (*.txt);;All files (*.*)")
        if not file_name:
            return
        self.MDA_file_path = file_name
        self.log_message(f"MDA file: {self.MDA_file_path}")

    def openPosFile(self):
        iDir = os.path.abspath(os.path.dirname(__file__))
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open position file", iDir, "Position files (*.pos);;All files (*.*)")
        if not file_name:
            return
        self.Pos_file_path = file_name
        self.log_message(f"Position file: {self.Pos_file_path}")

    def tuning_resistanse_rate(self): # click tuning event
        #ui.timer.timeout.connect(self.check_tuning)
        ui.magnitude_initialize=True
        NI.ArduinoAO(ui.vNumA, True, 254)
        self.log_message("Tuning started")
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
        minflowrate = max(20,63.4*potentio-13.6)
        ui.maxflowrate.display(str(round(maxflowrate,1)))
        ui.minflowrate.display(str(round(minflowrate,1)))


    def valve_number_changed(self, index):
        #ui.selected_valve_index_index = index
        ui.valveindex1=index
        valvenum = str(hex(index+1).upper())
        message = 'P0' + valvenum[-1] + '\r'
        ui.lcdnumber_1.display(ui.voltage[index])
        ui.horizontalSlider.setValue(int(ui.voltage[index]))
        if hasattr(ui, 'valve_1'):
            if ui.valve_state[index]==True:
                ui.valveButton_1.setText('ON')
            else:
                ui.valveButton_1.setText('OFF')

        ui.current_valve_num = index + 1
        self.log_message(f"Selector valve 1 → P{index+1:02X}")
        if ui.MXsII==True:
            MXsII.FTWrite(message)

    #add JM
    def valve2_number_changed(self, index):
        #ui.selected_valve_index_index = index
        ui.valveindex2=index
        valvenum = str(hex(index+1).upper())
        message = 'P0' + valvenum[-1] + '\r'
        ui.lcdnumber_2.display(ui.voltage[index])
        ui.horizontalSlider_2.setValue(int(ui.voltage[index]))
        if hasattr(ui, 'valve_1'):
            if ui.valve_state[index]==True:
                ui.valveButton_2.setText('ON')
            else:
                ui.valveButton_2.setText('OFF')

        ui.current_valve_num = index + 1
        self.log_message(f"Selector valve 2 → P{index+1:02X}")
        if ui.MXsII==True:
            MXsII.FTWrite(message)

    def recordIO(self):
        ui.save = not ui.save
        if ui.save == True:
            ui.Filename = NI.DefFile(ui.Foldername)
            ui.recordButton.testAttribute

    # ValveBotton_1
    def ValveOC(self):

        ui.valve_state[ui.valveindex1] = not ui.valve_state[ui.valveindex1]
        ui.current_valve_num = ui.valveindex1 + 1 if ui.valve_state[ui.valveindex1] else 0
        NI.ArduinoDO(ui.valveindex1,
                          ui.valve_state[ui.valveindex1])
        if ui.valve_state[ui.valveindex1]==True:
            ui.valveButton_1.setText('ON')
            self.log_message(f"Solenoid valve P{ui.valveindex1+1:02X} opened")
        else:
            ui.valveButton_1.setText('OFF')
            self.log_message(f"Solenoid valve P{ui.valveindex1+1:02X} closed")
        valve_label = f"P{ui.valveindex1+1:02X} "
        if any(ui.valve_state):  # open the check valve
            #s = NI.ArduinoDO(10, True)
            #NI.ArduinoDO(10, True)
            NI.ArduinoDO(12, False)
            NI.ArduinoDO(11, True)
            time.sleep(0.1)
            NI.ArduinoDO(11, False)
            self.log_message(f'{valve_label}LSV is open')
        else:
            #s = NI.ArduinoDO(10, False)
            #NI.ArduinoDO(10, False)
            NI.ArduinoDO(12, True)
            NI.ArduinoDO(11, False)
            time.sleep(0.1)
            NI.ArduinoDO(12, False)
            self.log_message(f'{valve_label}LSV is closed')

    # add JM ValveButton_2  # can be combined with ValveOC
    def ValveOC2(self):

        ui.valve_state[ui.valveindex2] = not ui.valve_state[ui.valveindex2]
        ui.current_valve_num = ui.valveindex2 + 1 if ui.valve_state[ui.valveindex2] else 0
        NI.ArduinoDO(ui.valveindex2,
                             ui.valve_state[ui.valveindex2])
        if ui.valve_state[ui.valveindex2]==True:
            ui.valveButton_2.setText('ON')
            self.log_message(f"Solenoid valve P{ui.valveindex2+1:02X} opened")
        else:
            ui.valveButton_2.setText('OFF')
            self.log_message(f"Solenoid valve P{ui.valveindex2+1:02X} closed")
        valve_label = f"P{ui.valveindex2+1:02X} "
        if any(ui.valve_state):  # open the check valve
           #s = NI.ArduinoDO(10, True)
           #NI.ArduinoDO(10, True)
           NI.ArduinoDO(12, False)
           NI.ArduinoDO(11, True)
           time.sleep(0.1)
           NI.ArduinoDO(11, False)
           self.log_message(f'{valve_label}LSV is open')
        else:
           #s = NI.ArduinoDO(10, False)
           #NI.ArduinoDO(10, False)
           NI.ArduinoDO(12, True)
           NI.ArduinoDO(11, False)
           time.sleep(0.1)
           NI.ArduinoDO(12, False)
           self.log_message(f'{valve_label}LSV is closed')

    def svalue_changed(self):

        ui.voltage[ui.valveindex1] = ui.horizontalSlider.value()
        ui.lcdnumber_1.display(ui.horizontalSlider.value())
        NI.ArduinoAO(ui.vNumA, True, ui.voltage[ui.valveindex1])

    def svalue2_changed(self):

        ui.voltage[ui.valveindex2] = ui.horizontalSlider_2.value()
        ui.lcdnumber_2.display(ui.horizontalSlider_2.value())
        NI.ArduinoAO(ui.vNumB, True, ui.voltage[ui.valveindex2])


    def closeEvent(self, event):
        self._unblock_system_idle()
        sys.stdout = sys.__stdout__
        self.worker.stop()
        self.thermo_timer.stop()
        if ui.UseThermoPlate:
            ui.ThermoPlate.client.close()
        self.open_single_valve(-1)
        NI.Arduinobye()
        event.accept()

    def _block_system_idle(self):
        hwnd = int(self.winId())
        ctypes.windll.kernel32.SetThreadExecutionState(
            _ES_CONTINUOUS | _ES_SYSTEM_REQUIRED | _ES_DISPLAY_REQUIRED)
        ctypes.windll.user32.ShutdownBlockReasonCreate(
            hwnd, ctypes.c_wchar_p("MiSA sequence is running"))

    def _unblock_system_idle(self):
        hwnd = int(self.winId())
        ctypes.windll.kernel32.SetThreadExecutionState(_ES_CONTINUOUS)
        ctypes.windll.user32.ShutdownBlockReasonDestroy(hwnd)

    def abort_program(self):
        self._unblock_system_idle()
        self.log_message('Aborted. Valves closed, pressure off. Waiting for operator action.')
        if ui.UseThermoPlate:
            try:
                ui.ThermoPlate.settemp(250)  # 250 = 25.0°C
                self.log_message('ThermoPlate set to 25°C.')
            except Exception as e:
                self.log_message(f'ThermoPlate cool-down failed: {e}')
        self._upload_slack_image(
            self._grab_window_png(), "abort.png", ui.slack_thread_ts, "Sequence aborted")
        if self._acq_running:
            self._acq_running = False
        ui.number_of_commands = 0
        ui.lcdSeqNumber.display(0)
        Kp, Ki, Kd = ui.last_pid
        current_pressure = getattr(ui, 'current_pressure', 0)
        NI.ArduinoFB(False, ui.vNumA, current_pressure, Kp, Ki, Kd)
        NI.ArduinoAO(ui.vNumA, False, 0)
        self.open_single_valve(-1)
        if ui.save:
            ui.save = False

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    #print("app insert")
    w = MainWindow()
    #print("w insert")
    w.show()
    #print("show")
    sys.exit(app.exec_())
