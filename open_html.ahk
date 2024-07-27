#NoEnv
SendMode Input
SetWorkingDir %A_ScriptDir%

; Define the relative paths to the HTML files
htmlFile1 := A_ScriptDir . "\contexts_80_percent.html"
htmlFile2 := A_ScriptDir . "\contexts_90_percent.html"
htmlFile3 := A_ScriptDir . "\contexts_99_percent.html"

; Path to Chrome executable
chromePath := "C:\Program Files\Google\Chrome\Application\chrome.exe"

; Open the first HTML file in a new window
Run, %chromePath% "file:///%htmlFile1%" --new-window
Sleep, 2000  ; Wait for Chrome to open the new window

; Open the second HTML file in a new tab in the same window
Run, %chromePath% --new-tab "file:///%htmlFile2%"
Sleep, 1000

; Open the third HTML file in a new tab in the same window
Run, %chromePath% --new-tab "file:///%htmlFile3%"
Sleep, 1000

; MsgBox, Chrome should now be open with the specified HTML files.