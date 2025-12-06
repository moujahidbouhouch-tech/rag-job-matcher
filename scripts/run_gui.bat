@echo off
REM Launch the GUI with the repo's virtualenv activated.

set ROOT_DIR=%~dp0..
set VENV_DIR=%ROOT_DIR%\.venv

if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Virtualenv not found at %VENV_DIR%. Create it first.
    exit /b 1
)

call "%VENV_DIR%\Scripts\activate.bat"
cd /d "%ROOT_DIR%"
python -m rag_project.rag_gui.main