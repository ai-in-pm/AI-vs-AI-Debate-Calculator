@echo off
REM Batch setup script for Debate Calculator on Windows
REM Run this script to set up the development environment

echo === Debate Calculator Setup Script ===
echo Setting up the AI vs AI Mathematical Debate Calculator...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.11+ first.
    pause
    exit /b 1
)

echo Found Python:
python --version

echo.
echo 1. Installing package dependencies...
pip install -e .
if errorlevel 1 (
    echo ERROR: Failed to install package dependencies
    pause
    exit /b 1
)

pip install -e ".[dev]"
if errorlevel 1 (
    echo WARNING: Failed to install dev dependencies
)

echo Package dependencies installed successfully.

echo.
echo 2. Installing Dear PyGui from local repository...
set DEARPYGUI_PATH=D:\science_projects\agent_vs_agent\DearPyGui-master
if exist "%DEARPYGUI_PATH%" (
    pip install -e "%DEARPYGUI_PATH%"
    if errorlevel 1 (
        echo WARNING: Failed to install Dear PyGui from local path
        echo Trying to install from PyPI...
        pip install dearpygui
        if errorlevel 1 (
            echo ERROR: Failed to install Dear PyGui
            echo GUI interface may not work
        )
    ) else (
        echo Dear PyGui installed from local repository.
    )
) else (
    echo WARNING: Local Dear PyGui path not found: %DEARPYGUI_PATH%
    echo Installing from PyPI...
    pip install dearpygui
    if errorlevel 1 (
        echo ERROR: Failed to install Dear PyGui
        echo GUI interface may not work
    ) else (
        echo Dear PyGui installed from PyPI.
    )
)

echo.
echo 3. Setting up environment configuration...
if exist ".env" (
    echo WARNING: .env file already exists
) else (
    copy ".env.example" ".env" >nul
    if errorlevel 1 (
        echo ERROR: Failed to create .env file
    ) else (
        echo Created .env file from template.
        echo.
        echo IMPORTANT: Please edit .env with your API keys:
        echo    - OPENAI_API_KEY=your_openai_api_key_here
        echo    - ANTHROPIC_API_KEY=your_anthropic_api_key_here
    )
)

echo.
echo 4. Running basic tests...
pytest tests/ -v --tb=short
if errorlevel 1 (
    echo WARNING: Some tests failed or pytest not available
    echo You can run tests manually with: pytest tests/ -v
)

echo.
echo === Setup Complete ===
echo Next steps:
echo 1. Edit .env file with your API keys
echo 2. Test CLI: python -m debate_calc.app.ui_cli "1 + 1"
echo 3. Test GUI: python -m debate_calc.app.ui_dpg
echo.
echo For help: python -m debate_calc.app.ui_cli --help
echo.
pause
