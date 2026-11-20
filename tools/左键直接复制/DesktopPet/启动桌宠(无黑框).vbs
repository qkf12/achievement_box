' 桌面小宠 - 完全静默启动（不闪黑框）
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
base = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = base
sh.Run "pythonw """ & base & "\desktop_pet.pyw""", 0, False