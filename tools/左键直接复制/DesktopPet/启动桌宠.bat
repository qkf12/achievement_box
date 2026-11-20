@echo off
cd /d "%~dp0"

where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw "desktop_pet.pyw"
    exit /b
)

where pyw >nul 2>nul
if %errorlevel%==0 (
    start "" pyw "desktop_pet.pyw"
    exit /b
)

where python >nul 2>nul
if %errorlevel%==0 (
    start "" python "desktop_pet.pyw"
    exit /b
)

echo.
echo   没有找到 Python 运行时。
echo   请先安装 Python 3.8 或更高版本，安装时勾选 "Add Python to PATH"。
echo.
pause