import json
import sys
import time
import os
import signal
import threading
from flask import Flask, request, jsonify
from datetime import datetime
from pathlib import Path

from process_logs import process_comns
from process_logs import process_tools

app = Flask(__name__)

ANSWER = None
METADATA = {
    "task": None,
    "mcp": None,
    "model": None
}
LOG = {
    "date": None,
    "success": False,
    "resolved": False,
    "tokens": 0,
    "cost": 0,
    "attempts": {},
    "comns": {},
    "total_comns": 0,
    "tools": {},
    "total_tools": 0
}

TOTAL_ATTEMPTS = 3
TOTAL_TIME = 5 * 60

ATTEMPTS = 0
TIME = None

BLOCKED = False
def check_block(f):
    from functools import wraps
    @wraps(f)
    def foo(*args, **kwargs):
        global BLOCKED
        if BLOCKED:
            return jsonify({
                "status": "blocked",
                "message": "The test has already finished. The oracle doesn't accept more petitions."
            }), 403
        return f(*args, **kwargs)
    return foo

@app.route('/start', methods=['GET'])
@check_block
def start():
    global TIME
    
    if TIME is not None:
        return jsonify({
            "status": "error",
            "message": "Timer is already running. The server should have been reset."
        }), 400 

    if {'model', 'mcp'} - set(request.args.keys()):
        return jsonify({
            "status": "error",
            "message": "Missing required query parameters."
        }), 400
    
    info = request.args.to_dict()
    METADATA["mcp"] = info["mcp"]
    METADATA["model"] = info["model"]

    TIME = time.time()
    
    return jsonify({
        "status": "success",
        "message": "Timer started successfully. The oracle have started."
    }), 200

@app.route('/guess', methods=['GET'])
@check_block
def guess():
    global ATTEMPTS

    if TIME is None:
        return jsonify({
            "status": "error",
            "message": "Timer is not running. The oracle have not been started yet."
        }), 400 

    guess = request.args.to_dict()
    
    if not guess:
        return jsonify({"error": "Incorrect petition format. No parameters provided."}), 400
    
    guess_keys = guess.keys()
    for key in ANSWER.keys():
        if key not in guess_keys:
            return jsonify({
                "error": "Missing parameters",
                "message": f"Incorrect petition format. Not all parameters were provided."
            }), 400
        
    ATTEMPTS += 1
    time_spent = time.time() - TIME

    message = None
        
    for key, value in guess.items():
        if ANSWER[key] != value:
            message = {}
            message["continue"] = True
            message["status"] = "fail"
            message["message"] = "Wrong answer! "
            if (ATTEMPTS == TOTAL_ATTEMPTS):
                message["continue"] = False
                message["message"] += "You have run out of attempts."
            if (time_spent > TOTAL_TIME):
                message["continue"] = False
                message["message"] += "You have run out of time."
            if message["continue"]:
                message["message"] += "Try again."
            break

    if not message:
        message = {}
        message["continue"] = False
        if (time_spent > TOTAL_TIME):      
            message["status"] = "fail"
            message["message"] = "The answer is correct, but you have run out of time."
        else:
            message["status"] = "success"
            message["message"] = "Congratulations! The answer is correct."
        LOG["resolved"] = True

    message["spent_attempts"] = ATTEMPTS
    message["spent_time"] = time.strftime("%M:%S", time.gmtime(time_spent))

    LOG["success"] |= message["status"] == "success"
    LOG["attempts"][message["spent_time"]] = str(guess)

    if not message["continue"]:
        threading.Timer(0.5, __shutdown_server).start()
  
    return jsonify(message), 200

def __shutdown_server():
    global BLOCKED
    BLOCKED = True

    LOG["tokens"] = input("[INPUT] Tokens consumed: ")
    LOG["cost"] = input("[INPUT] Total cost: ")
    LOG["comns"], LOG["total_comns"] = process_comns()
    LOG["tools"], LOG["total_tools"] = process_tools()
    LOG["date"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    file_path = Path("./benchmark.json")
    with open(file_path, "r") as file:
        benchmark = json.load(file)

    benchmark.setdefault(METADATA["task"], {}) \
        .setdefault(METADATA["mcp"], {})[METADATA["model"]] = LOG
    
    with open(file_path, "w") as file:
        json.dump(benchmark, file, indent=4)

    print("[INFO] The test is over. Closing oracle...")
    os.kill(os.getpid(), signal.SIGINT)

if __name__ == '__main__':

    if len(sys.argv) < 2:
        print("[ERROR] You must pass an argument when running the script.")
        print("Examples:\n  python oracle.py 0\n  python oracle.py crackme")
        sys.exit(1) 

    with open(Path("./answers.json"), 'r') as file:
        tasks = json.load(file).get("tasks", [])

    arg = sys.argv[1]

    if arg.isdigit():
        idx = int(arg)
        if 0 <= idx < len(tasks):
            task = tasks[idx]
            ANSWER = task.get("answer")
            METADATA["task"] = task.get("name")
        else:
            print(f"[ERROR] Index {idx} does not exist in the table.")
            sys.exit(1)
    else:
        for task in tasks:
            if task["name"] == arg:
                ANSWER = task.get("answer")
                METADATA["task"] = arg
                break
        if not ANSWER:
            print(f"[ERROR] No task found named '{arg}'.")
            sys.exit(1)

    app.run(host='0.0.0.0', port=5000)