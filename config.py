#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 14 17:41:01 2025

@author: eeprotocol(:K2)
"""

import os


def _load_slack_config():
    """Reads SLACK_WEBHOOK_URL / SLACK_BOT_TOKEN / SLACK_CHANNEL from
    slack.txt (KEY=value per line, next to this file). Kept out of
    config.py -- and out of git via .gitignore -- since this repo is
    public. Missing file or missing keys just default to ''."""
    values = {"SLACK_WEBHOOK_URL": "", "SLACK_BOT_TOKEN": "", "SLACK_CHANNEL": ""}
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "slack.txt")
    try:
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                if key in values:
                    values[key] = value.strip()
    except OSError:
        pass
    return values


class config:
    def __init__(self):
        # Arduino
        self.ARDUINO_PORT="COM3"
        
        # Thermo plate
        self.THERMO_PLATE=True
        self.THERMO_PLATE_PORT="COM6"
        
        # Flow sensor
        self.FLOW_SENSOR=True
        
        # Selector valve
        self.SELECT_VALVE=True
        self.SELECT_VALVE_PORT="COM7"
        
        # Pressure regulator type (you can also change it in GUI)
        # 0=ITV0010
        # 1=ITV0030
        # 2=ITV0090
        # 3=EVL1050
        self.REG_TYPE=0

        # Name shown in the Slack thread header ("YYYYMMDDHHMM <seqfile> at <name>")
        self.INSTRUMENT_NAME = "Nikon-TiE"

        # Slack notification settings, read from slack.txt (see
        # _load_slack_config above). Leave unset/blank to disable.
        #   SLACK_BOT_TOKEN + SLACK_CHANNEL -> threaded posts via chat.postMessage
        #     (one thread per RunSequence() call; every log_message() line
        #     replies into it). Preferred when both are set.
        #   SLACK_WEBHOOK_URL -> plain (non-threaded) posts, used as a fallback
        #     when no bot token/channel is configured.
        slack = _load_slack_config()
        self.SLACK_WEBHOOK_URL = slack["SLACK_WEBHOOK_URL"]
        self.SLACK_BOT_TOKEN = slack["SLACK_BOT_TOKEN"]
        self.SLACK_CHANNEL = slack["SLACK_CHANNEL"]
        
        
        
        
        
        