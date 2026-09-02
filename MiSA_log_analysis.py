# -*- coding: utf-8 -*-
"""
Batch analysis of droplet-formation / pressure-control logs.

Each log is a header-less CSV with a trailing comma on every line, written by
the PyQt control software. Column order (per saved row):
    0: dt           elapsed time since acquisition start [s]
    1: pressure1    pressure ch1 [kPa]
    2: pressure2    pressure ch2 [kPa]
    3: flowrate     flow rate [uL/min]    (-1 when no flow sensor)
    4: volume       cumulative pumped volume [uL]
    5: temperature  plate temperature [C] (-1 when no thermo plate)

The acquisition start time is parsed from the file name. Two formats are
recognized:
    20260622103045        (YYYYMMDDHHMMSS, 14 contiguous digits)
    20260621_200214       (YYYYMMDD_HHMMSS, underscore-separated)
That stamp is reused in each output figure name, so one figure is produced
per log.

How to use in Spyder:
    1. Set LOG_PATH below. It can be EITHER
         - a folder that holds several log files, OR
         - a single log file.
    2. (Optional) adjust LOG_GLOB when LOG_PATH is a folder.
    3. Press F5 to run.
A figure is saved per log, and a one-line summary table is printed/saved.
"""

import os
import re
import glob
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ----------------------------------------------------------------------
# Configuration  --  edit these
# ----------------------------------------------------------------------
# LOG_PATH may be a folder (then LOG_GLOB selects the files inside it) or a
# single log file (then LOG_GLOB is ignored).
LOG_PATH = "/home/samba/IX83-CSUX/Minegishi/260620_no622_RNAmovie_MiSA/20260621/20260621_200214_exp0001"
LOG_GLOB = "*"            # filename pattern, used only when LOG_PATH is a folder

# Where figures go. Set this to the folder on the other file server.
# None -> a "figures" folder next to the logs.
OUT_DIR = "/home/other-server/path/to/figures"   # <- edit to the target server folder

# Figure filename:
#   "source"    -> same base name as the log file (e.g. 20260621_200214_exp0001.png)
#   "timestamp" -> fig_YYYYMMDD_HHMMSS.png from the parsed start time
NAME_MODE = "source"

MASK_SENTINEL = True   # treat -1 (no sensor connected) as NaN so it is not plotted
FIG_DPI       = 150
FIG_FORMAT    = "png"  # png / pdf / svg
SAVE_SUMMARY  = True   # write a summary CSV across all logs

COLUMNS = ["dt", "pressure1", "pressure2", "flowrate", "volume", "temperature"]


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def parse_start_time(path):
    """Return (datetime, 'YYYYMMDDHHMMSS') parsed from the file name.

    Accepts both 'YYYYMMDDHHMMSS' (14 contiguous digits) and
    'YYYYMMDD_HHMMSS' (underscore-separated). Falls back to the file
    modification time if neither is found.
    """
    name = os.path.basename(path)

    # 1) underscore-separated: 20260621_200214
    m = re.search(r"(\d{8})_(\d{6})", name)
    if m:
        stamp = m.group(1) + m.group(2)
        try:
            return datetime.strptime(stamp, "%Y%m%d%H%M%S"), stamp
        except ValueError:
            pass

    # 2) 14 contiguous digits: 20260622103045
    m = re.search(r"(\d{14})", name)
    if m:
        stamp = m.group(1)
        try:
            return datetime.strptime(stamp, "%Y%m%d%H%M%S"), stamp
        except ValueError:
            pass

    # 3) fallback: file modification time
    dt = datetime.fromtimestamp(os.path.getmtime(path))
    print("  [warn] no timestamp in name; using file mtime instead")
    return dt, dt.strftime("%Y%m%d%H%M%S")


def load_log(path):
    """Read one log file into a DataFrame with named columns.

    The trailing comma produces an extra empty column, which is dropped.
    Values that fail to parse as numbers become NaN.
    """
    df = pd.read_csv(path, header=None)
    # keep only the first 6 data columns (drop trailing-comma empty column, etc.)
    df = df.iloc[:, :len(COLUMNS)].copy()
    df.columns = COLUMNS[:df.shape[1]]
    # coerce to numeric, drop fully-empty rows
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(how="all").reset_index(drop=True)

    if MASK_SENTINEL:
        # -1 is the "no sensor" sentinel for flow rate and temperature
        for col in ("flowrate", "temperature"):
            if col in df.columns:
                df.loc[df[col] == -1, col] = np.nan
    return df


def plot_log(df, start_dt, out_path):
    """Make the 4-panel figure (pressure / flow / volume / temperature)."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 7))
    t = df["dt"].values

    # Pressure (both channels)
    ax = axes[0, 0]
    ax.plot(t, df["pressure1"], label="ch1")
    if "pressure2" in df and df["pressure2"].notna().any():
        ax.plot(t, df["pressure2"], label="ch2", alpha=0.8)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Pressure [kPa]")
    ax.legend(loc="best", fontsize=8)

    # Flow rate
    ax = axes[0, 1]
    ax.plot(t, df["flowrate"], color="tab:green")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Flow rate [uL/min]")

    # Cumulative volume
    ax = axes[1, 0]
    ax.plot(t, df["volume"], color="tab:orange")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Pumped volume [uL]")

    # Temperature
    ax = axes[1, 1]
    ax.plot(t, df["temperature"], color="tab:red")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Temperature [C]")

    fig.suptitle("Start: " + start_dt.strftime("%Y-%m-%d %H:%M:%S"))
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(out_path, dpi=FIG_DPI)
    plt.close(fig)


def summarize(df, start_dt, stamp, name):
    """One-row summary for the across-logs table."""
    duration = float(df["dt"].iloc[-1]) if len(df) else np.nan
    return {
        "file": name,
        "start_time": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "stamp": stamp,
        "n_points": len(df),
        "duration_s": round(duration, 2),
        "pressure1_max_kPa": round(np.nanmax(df["pressure1"]), 3) if len(df) else np.nan,
        "flow_mean_uL_min": round(np.nanmean(df["flowrate"]), 3) if len(df) else np.nan,
        "total_volume_uL": round(np.nanmax(df["volume"]), 3) if len(df) else np.nan,
        "temp_mean_C": round(np.nanmean(df["temperature"]), 2) if len(df) else np.nan,
    }


def resolve_inputs(log_path, log_glob):
    """Return (list_of_files, base_dir).

    log_path may point to a single file or to a folder. base_dir is the
    folder used to anchor the default output location.
    """
    if os.path.isfile(log_path):
        return [log_path], os.path.dirname(log_path)
    if os.path.isdir(log_path):
        files = sorted(glob.glob(os.path.join(log_path, log_glob)))
        files = [p for p in files if os.path.isfile(p)]
        return files, log_path
    # path does not exist
    return [], log_path


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    paths, base_dir = resolve_inputs(LOG_PATH, LOG_GLOB)

    if not paths:
        print("No log files found for %r" % LOG_PATH)
        return

    out_dir = OUT_DIR if OUT_DIR else os.path.join(base_dir, "figures")
    os.makedirs(out_dir, exist_ok=True)

    print("Found %d log file(s)." % len(paths))
    rows = []
    for path in paths:
        name = os.path.basename(path)
        print("Processing:", name)
        try:
            start_dt, stamp = parse_start_time(path)
            df = load_log(path)
            if len(df) == 0:
                print("  [skip] no usable rows")
                continue
            if NAME_MODE == "source":
                # same base name as the log file, with the figure extension
                stem = os.path.splitext(name)[0]
                out_name = "%s.%s" % (stem, FIG_FORMAT)
            else:
                out_name = "fig_%s.%s" % (start_dt.strftime("%Y%m%d_%H%M%S"), FIG_FORMAT)
            out_path = os.path.join(out_dir, out_name)
            plot_log(df, start_dt, out_path)
            print("  -> saved", out_path)
            rows.append(summarize(df, start_dt, stamp, name))
        except Exception as e:
            print("  [error]", e)

    if SAVE_SUMMARY and rows:
        summary = pd.DataFrame(rows)
        summary_path = os.path.join(out_dir, "summary.csv")
        summary.to_csv(summary_path, index=False)
        print("\nSummary:")
        print(summary.to_string(index=False))
        print("\nSummary table saved to", summary_path)


if __name__ == "__main__":
    main()
