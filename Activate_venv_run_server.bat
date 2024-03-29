@echo off

rem Set the path to your virtual environment
set VENV_DIR=C:\Python312\venv

rem Activate the virtual environment
call %VENV_DIR%\Scripts\activate

rem Run the Django development server in the same window
start /B python manage.py runserver

rem Wait for a moment to allow the server to start (adjust as needed)
timeout /t 5 /nobreak >nul

rem Prompt the user to press a key to stop the Django development server
echo Press Ctrl+C to stop the Django development server.
pause

rem Terminate the Django development server process
taskkill /im "python.exe" /fi "windowtitle eq Django Server" /f

rem Change directory to the specified path
cd /D C:\Users\Administrator\Desktop\VueProjects\dvg\backend

rem Keep the Command Prompt open
cmd /k









