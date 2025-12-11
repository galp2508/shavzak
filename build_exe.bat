@echo off
echo Building Shavzak Server EXE...
pyinstaller --name ShavzakServer --onefile --paths back back/api.py
echo.
echo Build Complete! Look in the 'dist' folder.
pause
