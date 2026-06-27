# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MiSA (Microfluidic Sequence Automation) is a PyQt5 GUI application for controlling an automated microfluidic system. It communicates with an Arduino via serial (pySerial) to perform pressure-based feedback control of fluid flow, and can integrate with a selector valve (IDEX MXsII), ThermoPlate (Modbus RTU), and a fluorescence microscope (pycromanager/Micro-Manager).

## Environment Setup

Install via conda using the provided environment file:
```
conda env create -f requirement.yml
conda activate MiSAenv
```

Key dependencies: Python 3.12, PyQt5, numpy, matplotlib, pyserial, pymodbus, pycromanager.

## Running the Application

```
python main.py
```

The UI file (`droplet_gui.ui`) is compiled to `droplet_gui.py` using PyQt5's `pyuic5`:
```
pyuic5 -o droplet_gui.py droplet_gui.ui
```
**Do not manually edit `droplet_gui.py`** — it is auto-generated from `droplet_gui.ui`.

## Hardware Configuration

All COM ports and hardware flags are set in `config.py`:
- `ARDUINO_PORT` — Arduino Micro (9600 baud, never change baud rate)
- `SELECT_VALVE_PORT` — IDEX MXsII selector valve (19200 baud, serial)
- `THERMO_PLATE_PORT` — ThermoPlate via Modbus RTU (9600 baud)
- `THERMO_PLATE`, `FLOW_SENSOR`, `SELECT_VALVE` — booleans to enable/disable peripherals
- `REG_TYPE` — pressure regulator type (0=ITV0010, 1=ITV0030, 2=ITV0090, 3=EVL1050)

## Architecture

### Module Roles

- **`main.py`** — Main entry point. `MainWindow(QMainWindow)` contains all application logic: sequence execution, PID feedback loop, data recording, real-time plotting, and hardware event handling. The GUI timer fires every 30 ms to call `update_figure()`, which polls Arduino, updates plots, and drives the sequence state machine.
- **`droplet_gui.py`** — Auto-generated PyQt5 UI class (`Ui_Droplet_formation`). Do not edit directly.
- **`ArduinoDAQ.py`** — Low-level Arduino serial protocol. All methods are static-style on the `AI` class. Sends ASCII command strings to the Arduino (e.g., `AI6,7\n`, `DO0H\n`, `FB9,200,0.16,0.022,0.1\n`). Opens `serial.Serial` at module import time — requires Arduino to be connected on startup.
- **`config.py`** — Single `config` class with hardware port/flag settings. Imported by `ArduinoDAQ.py`, `MXsII.py`, and `ThermoPlate.py` at module load.
- **`MXsII.py`** — Controls the IDEX MXsII 10-position selector valve over serial. `MXsIIt.FTWrite(message)` opens/writes/closes the serial port on each call (not persistent).
- **`ThermoPlate.py`** — Modbus RTU client wrapping `pymodbus` to control the ThermoPlate heater. `settemp(tmp)` and `readtemp()` open/close the connection per call. Temperature values are in tenths of a degree (e.g., 400 = 40.0°C).
- **`pycromanager_pipe.py`** — `acq_pycromanager` class that reads Micro-Manager MDA settings (JSON) and position files (.pos) and runs acquisitions via pycromanager. Used when a sequence step contains the `a` mode (acquire).
- **`matplotlibwidget.py`** — `MatplotlibWidget(FigureCanvasQTAgg)` with three subplots for real-time pressure, flow rate, and cumulative volume.

### Sequence File Format

Sequence files (in `seqfiles/`) are plain text, one command per line:

```
<valve>,<value><mode>,<stop><unit>[,<Kp>;<Ki>;<Kd>]
```

- `<valve>`: `P01`–`P0A` (hex, P=pressure-driven) or `A04` (acquire at this valve position)
- `<mode>`: `u` = µL/min flow rate, `p` = raw Pa pressure (open-loop), `a` = acquire images, `c` = Celsius (×10 for ThermoPlate)
- `<unit>`: `s` = seconds (time-based stop), `u` = µL (volume-based stop)
- PID parameters are optional per-step overrides; defaults are (0.1, 0.001, 0.1)

### Sequence State Machine

`SequenceControlTime()` is called from the 30 ms timer when `ui.number_of_commands != 0`. It tracks `ui.command` (current step index) and `ui.residualtime`/volume to decide when to advance. On step transition: closes all valves, optionally moves the selector valve, sets PID parameters, applies pressure, then opens the target valve.

### Data Recording

When recording is active (`ui.save = True`), each timer tick appends a CSV row: `[elapsed_time, pressure_ch1, pressure_ch2, flow_rate, cumulative_volume]`. Files are saved to `~/YYYYMMDD/YYYYMMDD_HHMMSSNNNN.csv` via `ArduinoDAQ.AI.DefFile()`.

### Pressure Conversion

Raw Arduino analog values are converted to kPa using regulator-specific coefficients in `update_figure()`:
```python
g = [0.1208, 1.097, -0.1208]
h = [-23.75, -223.75, 23.78]
c[i] = g[ui.reg] * c[i] + h[ui.reg]
```
`ui.reg` maps to `REG_TYPE` from `config.py` (0=ITV0010, 1=ITV0050, 2=ITV0090).
