New-Item -Path "c:\Users\user\Documents\Projects\mimi\mimi.stop" -ItemType File -Force | Out-Null
Write-Output "Stop signal sent. mimi will exit after the current run."
