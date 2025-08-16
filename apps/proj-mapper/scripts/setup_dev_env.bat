@echo off
:: Project Mapper Development Environment Setup
:: This script creates a virtual environment and installs all dependencies for development

echo [33mProject Mapper Development Environment Setup[0m

:: Get the directory of the script and navigate to project root
set "SCRIPT_DIR=%~dp0"
cd %SCRIPT_DIR%..

:: Check if Python 3.8+ is available
echo [33mChecking for Python 3.8+...[0m
python --version 2>nul || goto :NoPython

:: Extract version number and check if it's 3.8+
for /f "tokens=2 delims= " %%a in ('python --version 2^>^&1') do set "PYTHON_VERSION=%%a"
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set "PYTHON_MAJOR=%%a"
    set "PYTHON_MINOR=%%b"
)

if %PYTHON_MAJOR% LSS 3 goto :OldPython
if %PYTHON_MAJOR% EQU 3 if %PYTHON_MINOR% LSS 8 goto :OldPython

echo [32mFound Python %PYTHON_VERSION%[0m

:: Create and activate a virtual environment
echo [33mCreating a virtual environment...[0m

if exist venv (
    echo [33mVirtual environment already exists. Do you want to recreate it? [y/N][0m
    set /p RECREATE=""
    if /i "%RECREATE%"=="y" (
        echo [33mRemoving existing virtual environment...[0m
        rmdir /s /q venv
    ) else (
        echo [32mUsing existing virtual environment[0m
    )
)

if not exist venv (
    python -m venv venv
    echo [32mVirtual environment created[0m
)

:: Activate virtual environment
echo [33mActivating virtual environment...[0m
call venv\Scripts\activate.bat

:: Upgrade pip
echo [33mUpgrading pip...[0m
python -m pip install --upgrade pip

:: Install dependencies
echo [33mInstalling development dependencies...[0m
pip install -e .[dev]

:: Install pre-commit hooks
echo [33mInstalling pre-commit hooks...[0m
pre-commit install

:: Validate the setup
echo [33mValidating setup...[0m
echo Checking Black...
black --version
echo Checking isort...
isort --version
echo Checking flake8...
flake8 --version
echo Checking mypy...
mypy --version
echo Checking pytest...
pytest --version
echo Checking pre-commit...
pre-commit --version

echo [32mDevelopment environment setup successfully![0m
echo [33mActivate the virtual environment with: venv\Scripts\activate[0m
goto :eof

:NoPython
echo [31mError: Python not found. Please install Python 3.8 or higher.[0m
exit /b 1

:OldPython
echo [31mError: Python 3.8 or higher is required. Found Python %PYTHON_VERSION%[0m
exit /b 1 