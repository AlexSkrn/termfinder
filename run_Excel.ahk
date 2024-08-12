#NoEnv
SendMode Input
SetWorkingDir %A_ScriptDir%

; Check if Excel is already running
IfWinExist ahk_class XLMAIN
{
    ; If it's running, activate the window
    WinActivate
}
else
{
    ; If it's not running, launch Excel
    Run, excel.exe
}