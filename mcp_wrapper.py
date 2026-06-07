#!/usr/bin/env python3

import sys
import json
import subprocess
import threading
from datetime import datetime
from pathlib import Path

LOG = Path("./src/tools.log")

proc = subprocess.Popen(
    sys.argv[1:],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

def log_tool_call(tool):
    with open(LOG, 'a') as file:
        file.write(f"{tool}\n")

def log_tool_call_extended(tool, args):
    with open(LOG, 'a') as file:
        file.write(f"[{datetime.now().strftime('%H:%M:%S.%f')}] {tool}")
        if args:
            file.write(f" {json.dumps(args)}")
        file.write("\n")

def forward_stdin():

    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            
            proc.stdin.write(line)
            proc.stdin.flush()
            
            try:
                msg = json.loads(line)
                if msg.get("method") == "tools/call":
                    tool = msg.get("params", {}).get("name")
                    # args = msg.get("params", {}).get("arguments", {})
                    # log_tool_call_extended(tool, args)
                    log_tool_call(tool)
            except:
                pass
    except:
        pass
    finally:
        try:
            proc.stdin.close()
        except:
            pass

def forward_stdout():

    try:
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            sys.stdout.write(line)
            sys.stdout.flush()
    except:
        pass

stdin_thread = threading.Thread(target=forward_stdin, daemon=True)
stdout_thread = threading.Thread(target=forward_stdout, daemon=True)

stdin_thread.start()
stdout_thread.start()

proc.wait()

