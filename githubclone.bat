@echo off
REM Ollama Server - Windows Clone and Install Script
REM Run this script to clone and set up the ollama-server on your Windows machine

setlocal enabledelayedexpansion

echo ============================================
echo   Ollama Server - Clone and Install
echo ============================================
echo.

REM Check if git is available
where git >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: Git not found.
    echo Please install Git from https://git-scm.com/download/win
    pause
    exit /b 1
)

REM Check if Python is available
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: Python not found.
    echo Please install Python 3 from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Set default install directory
set "INSTALL_DIR=%USERPROFILE%\ollama-server"

REM Ask user for install location
echo Default install location: %INSTALL_DIR%
set /p "CUSTOM_DIR=Press Enter to use default, or type a new path: "
if not "%CUSTOM_DIR%"=="" set "INSTALL_DIR=%CUSTOM_DIR%"

REM Check if directory already exists
if exist "%INSTALL_DIR%" (
    echo.
    echo Directory already exists: %INSTALL_DIR%
    set /p "OVERWRITE=Delete and re-clone? (y/N): "
    if /i "!OVERWRITE!"=="y" (
        echo Removing existing directory...
        rmdir /s /q "%INSTALL_DIR%"
    ) else (
        echo Installation cancelled.
        pause
        exit /b 0
    )
)

echo.
echo Cloning repository to %INSTALL_DIR%...
echo.

REM Clone the repository
REM Replace this URL with your actual GitHub repository URL
git clone https://github.com/YOUR_USERNAME/ollama-server.git "%INSTALL_DIR%"
if %ERRORLEVEL% neq 0 (
    echo.
    echo Error: Failed to clone repository.
    echo Make sure the repository URL is correct and you have access.
    pause
    exit /b 1
)

REM Navigate to install directory
cd /d "%INSTALL_DIR%"

echo.
echo Installing Python dependencies...
python -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo.
    echo Warning: Failed to install some dependencies.
    echo You may need to run: pip install -r requirements.txt
)

REM Create config.json from example
if not exist config.json (
    echo.
    echo Creating config.json from example...
    copy config.example.json config.json
)

echo.
echo ============================================
echo   Installation Complete!
echo ============================================
echo.
echo Installed to: %INSTALL_DIR%
echo.
echo To start the server:
echo   1. Open a command prompt
echo   2. cd "%INSTALL_DIR%"
echo   3. Run: start.bat
echo.
echo Or double-click start.bat in the install folder.
echo.
echo Web UI will be available at: http://localhost:11435
echo.

REM Ask if user wants to start now
set /p "START_NOW=Start the server now? (Y/n): "
if /i not "%START_NOW%"=="n" (
    echo.
    echo Starting Ollama Server...
    call start.bat
)

pause
