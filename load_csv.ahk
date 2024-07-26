#NoEnv
SendMode Input
SetWorkingDir %A_ScriptDir%

; Ensure Excel is already open and active
WinWait, ahk_class XLMAIN
IfWinNotActive, ahk_class XLMAIN, , WinActivate, ahk_class XLMAIN
WinWaitActive, ahk_class XLMAIN

OpenFileDialogAndImport(A_ScriptDir)

OpenFileDialogAndImport(initialDir) {
    ; Open the Data tab
    Send, !a
    Sleep, 100
    
    ; Open the From Text/CSV dialog
    Send, FT
    Sleep, 100
    
    ; Wait for the File Open dialog to appear
    WinWait, ahk_class #32770
    
    ; Set the initial directory in the File Open dialog
    ControlFocus, Edit1, ahk_class #32770
    Sleep, 100
    SendRaw, %initialDir%
    Sleep, 100
    Send, {Enter}
    
    ; Wait for the user to manually select the file
    Sleep, 5000  ; Adjust this sleep duration as needed
}
