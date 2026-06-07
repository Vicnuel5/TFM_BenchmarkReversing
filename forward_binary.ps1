Param(
    [string]$Binary,
    [string]$IP = "192.168.56.107",
    [string]$TaskFolder = "/home/kali/Benchmark/task/"
)

ssh -i "$env:USERPROFILE\.ssh\benchmark" "kali@$IP" "rm -rf ${TaskFolder}*"
scp -i "$env:USERPROFILE\.ssh\benchmark" $Binary "kali@${IP}:${TaskFolder}/crackme"