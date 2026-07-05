@echo off
REM ==========================================================================
REM  run_aifia.bat  -  aifia (conda, Python 3.11) + ChipWhisperer 6.0.0
REM                    launch Jupyter Lab rooted at this folder.
REM  - Dedicated port 8899 (avoids collision with the CW bundle's run_cw.bat
REM    server on 8888).
REM  - use_redirect_file=False : open the http URL directly in the browser
REM    (instead of the open.html redirect file, which fails if .html is not
REM    associated with a browser).
REM  - Window always stays open so you can see the URL / any error.
REM  - In the notebook, select kernel "Python (aifia)".
REM ==========================================================================
setlocal
title aifia - ChipWhisperer Jupyter (HAETAE FI)

REM --- folder this script lives in (= Jupyter root); strip trailing backslash ---
set "NBDIR=%~dp0"
if "%NBDIR:~-1%"=="\" set "NBDIR=%NBDIR:~0,-1%"

set "CONDABAT=%USERPROFILE%\miniconda3\condabin\conda.bat"
set "PORT=8899"

if not exist "%CONDABAT%" (
    echo [ERROR] conda.bat not found: %CONDABAT%
    pause & exit /b 1
)

echo ============================================================
echo   aifia [Python 3.11] + ChipWhisperer  --  Jupyter Lab
echo   port: %PORT%    root: %NBDIR%
echo ============================================================

call "%CONDABAT%" activate aifia
if errorlevel 1 (
    echo [ERROR] cannot activate conda env "aifia".
    pause & exit /b 1
)

python -c "import chipwhisperer as cw; print('  chipwhisperer', cw.__version__, '(aifia OK)')"
if errorlevel 1 (
    echo [ERROR] chipwhisperer import failed in aifia.
    echo         run:  pip install -e c:\Users\NSRSGW\ChipWhisperer\chipwhisperer
    pause & exit /b 1
)

cd /d "%NBDIR%"
echo.
echo   Browser should open http://localhost:%PORT%/lab automatically.
echo   If it does NOT, copy the  http://localhost:%PORT%/lab?token=...  URL
echo   printed below into your browser.   [Stop: Ctrl+C twice here]
echo.

jupyter lab --ServerApp.root_dir="%NBDIR%" --ServerApp.open_browser=True --ServerApp.use_redirect_file=False --port=%PORT%

echo.
echo   ===== Jupyter stopped. Press any key to close this window. =====
pause >nul
endlocal
