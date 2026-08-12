Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
pythonScript = scriptDir & "\mimi.py"

' 0 = hidden window, False = do not wait for the script to finish
shell.Run """pythonw.exe"" """ & pythonScript & """", 0, False
