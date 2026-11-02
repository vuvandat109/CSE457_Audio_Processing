@echo off
cd /d "%~dp0"
py -3.12 -m venv .venv
if errorlevel 1 goto fail
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if errorlevel 1 goto fail
python Lab04.py
if errorlevel 1 goto fail
python scripts\verify_submission.py
if errorlevel 1 goto fail
echo Hoan thanh. Mo audio_output, figures va report de xem ket qua.
pause
exit /b 0
:fail
echo Co loi. Giu cua so nay va gui noi dung loi de kiem tra.
pause
exit /b 1
