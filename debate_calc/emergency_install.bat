@echo off
echo === EMERGENCY INSTALLATION SCRIPT ===
echo Fixing critical dependency issues...

echo.
echo 1. Installing pydantic-settings...
pip install pydantic-settings
if errorlevel 1 (
    echo ERROR: Failed to install pydantic-settings
    pause
    exit /b 1
)

echo.
echo 2. Installing DearPyGui...
pip install dearpygui
if errorlevel 1 (
    echo WARNING: Failed to install DearPyGui from PyPI
    echo Trying local installation...
    pip install -e "D:\science_projects\agent_vs_agent\DearPyGui-master"
    if errorlevel 1 (
        echo WARNING: Local DearPyGui installation also failed
        echo GUI interface will not work, but CLI should work
    )
)

echo.
echo 3. Reinstalling main package...
pip install -e .
if errorlevel 1 (
    echo ERROR: Failed to reinstall main package
    pause
    exit /b 1
)

echo.
echo 4. Testing critical imports...
echo Testing pydantic-settings...
python -c "from pydantic_settings import BaseSettings; print('✓ pydantic-settings OK')"
if errorlevel 1 (
    echo ERROR: pydantic-settings still not working
    pause
    exit /b 1
)

echo Testing basic app imports...
python -c "from debate_calc.app.settings import settings; print('✓ Settings OK')"
if errorlevel 1 (
    echo ERROR: App settings import failed
    pause
    exit /b 1
)

echo.
echo === INSTALLATION COMPLETE ===
echo You can now run:
echo   pytest tests/ -v
echo   python -m debate_calc.app.ui_cli "1 + 1"
echo.
pause
