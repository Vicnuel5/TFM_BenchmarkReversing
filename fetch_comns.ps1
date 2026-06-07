Param(
    [string]$TargetPid = '$(pidof opencode)',
    [string]$IP = "192.168.56.107"
)

ssh -i "$env:USERPROFILE\.ssh\benchmark" -t "kali@$IP" "ausearch -i -m execve -pp $TargetPid"