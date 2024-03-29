@echo off
setlocal

:: Define the path to OpenPype
set "path=%USERPROFILE%\AppData\Local\Programs\OpenPype"

:: Find the latest version directory
for /f "tokens=*" %%i in ('dir /b /ad /o-n "%path%"') do (
    set "latest=%%i"
    goto :execute
)
:execute

:: Construct the path to the executable
set "exe=%path%\%latest%\openpype_console.exe"

:: Check if there are any command-line arguments
if "%~1"=="" (
    echo No command flags provided. Exiting.
    exit /b 1
)

:: Run the executable with provided command flags
"%exe%" %*

endlocal
