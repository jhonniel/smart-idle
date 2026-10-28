Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
pythonScript = scriptDir & "\mimi.py"
stopFile = scriptDir & "\mimi.stop"
pythonw = "C:\Users\user\scoop\apps\python\current\pythonw.exe"
restartDelayMs = 5000

If Not fso.FileExists(pythonw) Then
    pythonw = "pythonw.exe"
End If

Do
    If fso.FileExists(stopFile) Then
        fso.DeleteFile stopFile
        Exit Do
    End If

    ' 0 = hidden window, True = wait until pythonw exits
    shell.Run """" & pythonw & """ """ & pythonScript & """", 0, True

    If fso.FileExists(stopFile) Then
        fso.DeleteFile stopFile
        Exit Do
    End If

    WScript.Sleep restartDelayMs
Loop
