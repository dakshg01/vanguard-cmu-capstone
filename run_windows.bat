@echo off
cd /d "%~dp0"
py -3 run.py
if errorlevel 1 (
  echo Run failed. Read the error above. Python 3.10 or newer is required.
) else (
  echo Finished. Open output\quality_report.json and output\csv\coverage.csv.
)
pause
