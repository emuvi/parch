@echo off
setlocal

where py >nul 2>&1
if not errorlevel 1 (
    py -3 "%~dp0keep_screen_awake.py"
) else (
    where python >nul 2>&1
    if errorlevel 1 (
        echo Python 3 was not found. Install Python and add it to PATH.
        pause
        exit /b 1
    )
    python "%~dp0keep_screen_awake.py"
)

if errorlevel 1 (
    echo The script stopped with an error.
    pause
    exit /b 1
)
