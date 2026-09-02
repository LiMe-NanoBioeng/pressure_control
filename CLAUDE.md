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
- `SLACK_WEBHOOK_URL` / `SLACK_BOT_TOKEN` / `SLACK_CHANNEL` — read from `slack.txt` (`KEY=value` per line, next to `config.py`; `_load_slack_config`), which is gitignored and kept out of this public repo. Missing file/keys default to `''` (disabled). `log_message()` calls `_notify_slack()` for every line, so Slack mirrors the on-screen log and the text log file 1:1 -- valve toggles, step start/complete, aborts, everything -- threaded into one message-per-run when a bot token + channel are set (`_start_slack_thread`, called at the top of `RunSequence()`), else falls back to plain (unthreaded) webhook posts.

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
<valve>,<value><mode>,<stop><unit>[,<Kp>;<Ki>;<Kd>[,<a|l><tolerance>per[,<duration>s]]]
```

- `<valve>`: `P01`–`P0A` (hex, P=pressure-driven) or `A04` (acquire at this valve position)
- `<mode>`: `u` = µL/min flow rate, `p` = raw Pa pressure (open-loop), `a` = acquire images, `c` = Celsius (×10 for ThermoPlate)
- `<unit>`: `s` = seconds (time-based stop), `u` = µL (volume-based stop)
- PID parameters are optional per-step overrides; defaults are (0.1, 0.001, 0.1)
- Stability watchdog (optional, `u` mode only, requires the PID field to be present): `<a|l><tolerance>per[,<duration>s]`, e.g. `a50per,10s`. `a` aborts the sequence (via `abort_program()` + a blocking `QMessageBox`) if flow strays outside ±`tolerance`% of setpoint for more than `duration` seconds (default 10s); `l` only logs a warning (`_flag_instability`, dedup'd so it won't spam). The watchdog only arms once flow first enters the tolerance band — so a dry line filling up doesn't trip it — within `STABILITY_ARM_TIMEOUT_S` (120s) of opening the valve, else it flags as if unstable (blocked/empty line). Omitting the field disables the watchdog for that step (default; all pre-existing sequence files are unaffected). See `seqfiles/priming_30uLmin.txt` for an example.

An optional **first line** in the file, before any step, sets a sequence-wide pressure ceiling (parsed in `openSeqFile`, checked every tick in `_check_pressure_limit` regardless of which step/mode is active): `<a|l><kPa value>kPa,<duration>s`, e.g. `a30kPa,60s` aborts if channel-1 pressure (`valveLcd_1`, the channel the sequence engine drives) stays above 30 kPa for a continuous 60s — protects the sample from prolonged high-pressure exposure. Distinguished from a normal step because valve tokens always start with uppercase `P`/`A`. Omit to leave disabled (default).

### Sequence State Machine

`SequenceControlTime()` is called from the 30 ms timer when `ui.number_of_commands != 0`. It tracks `ui.command` (current step index) and `ui.residualtime`/volume to decide when to advance. On step transition: closes all valves, optionally moves the selector valve, sets PID parameters, applies pressure, then opens the target valve.

### Data Recording

When recording is active (`ui.save = True`), each timer tick appends a CSV row: `[elapsed_time, pressure_ch1, pressure_ch2, flow_rate, cumulative_volume]`. Files are saved to `~/YYYYMMDD/YYYYMMDD_HHMMSSNNNN.csv` via `ArduinoDAQ.AI.DefFile()`.

### Event Log File

`log_message()` prints to the on-screen log (via `_StdoutRedirect`), mirrors every line to a text file (`_write_log_file`), and posts every line to Slack (`_notify_slack`). A fresh log file is created each time `RunSequence()` starts (`_new_log_filepath`): `<same folder as the current exp CSV, i.e. os.path.dirname(ui.Filename)>\YYYYMMDDHHMMMiSA.log.txt`. If recording hasn't been started yet (`ui.Filename` still the `' '` placeholder) or that folder can't be written to, it falls back to `ui.Foldername` and logs a warning. `ui.log_filepath` stays pointed at that run's file until the next `RunSequence()` call.

### Pressure Conversion

Raw Arduino analog values are converted to kPa using regulator-specific coefficients in `update_figure()`:
```python
g = [0.1208, 1.097, -0.1208]
h = [-23.75, -223.75, 23.78]
c[i] = g[ui.reg] * c[i] + h[ui.reg]
```
`ui.reg` maps to `REG_TYPE` from `config.py` (0=ITV0010, 1=ITV0050, 2=ITV0090).
