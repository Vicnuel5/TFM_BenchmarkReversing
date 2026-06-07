import re
import subprocess
from collections import defaultdict

ZSH = "zsh"
CURL = "curl"

comn_pattern = re.compile(r"\bcomm=(\S+)")
pid_pattern = re.compile(r"\bpid=(\d+)")

guess_endpoint = "/guess"
start_endpoint = "/start"

def __fetch_comns(pid = None):
    command = ["powershell.exe", "-File", ".\\fetch_comns.ps1"]
    if pid:
        command.append(pid)

    stdout = subprocess.run(
        command,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL).stdout

    if stdout:
        return stdout.splitlines()
    return []

def __process_comns(logs, count : dict):
    for line in logs:
        comn = comn_pattern.search(line)
        if comn:
            comn = comn.group(1)
            if comn == ZSH:
                pid = pid_pattern.search(line)
                if pid:
                    stdout = __fetch_comns(pid.group(1))
                    if stdout:
                        __process_comns(stdout, count)
            else:
                count[comn] += 1

def __delimit_comns(logs):
    reversed_logs = reversed(list(enumerate(logs)))

    top_delimit = 2
    bot_delimit = -7

    for idx, line in reversed_logs:
        if guess_endpoint in line:
            bot_delimit += idx
            break

    for idx, line in reversed_logs:
        if start_endpoint in line:
            top_delimit += idx
            break

    return logs[top_delimit:bot_delimit]

def __process_logs(count : dict):
    logs = {k: v for k, v in sorted(count.items())}
    total = sum(logs.values())
    return logs, total


def process_comns():
    count = defaultdict(int)
    __process_comns(__delimit_comns(__fetch_comns()), count)
    count.pop(CURL, None)
    return __process_logs(count)

def process_tools():
    stdout = subprocess.run(
        ["powershell.exe", "-File", ".\\fetch_tools.ps1"],
        capture_output=True,
        text=True).stdout
    
    count = defaultdict(int)
    if stdout:
        for tool in stdout.splitlines():
            count[tool] += 1 

    return __process_logs(count)

if __name__ == "__main__":
    print(process_tools())


