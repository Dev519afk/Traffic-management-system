@echo off
setlocal
cd /d "%~dp0"
if exist "venv\Scripts\python.exe" (
  set "PYTHON=venv\Scripts\python.exe"
) else (
  set "PYTHON=python"
)
echo AI Traffic Management - starting Streamlit dashboard...
%PYTHON% -m streamlit run dashboard.py
if errorlevel 1 (
  echo.
  echo Could not launch. See README.md and WINDOWS_TROUBLESHOOTING.md.
  pause
)
