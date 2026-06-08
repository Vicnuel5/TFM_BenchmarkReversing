Param(
    [string]$IP = "192.168.56.107",
    [string]$LogPath = "/home/kali/Benchmark/src/tools.log"
)

ssh -i "$env:USERPROFILE\.ssh\benchmark" "kali@$IP" "rm $LogPath" 