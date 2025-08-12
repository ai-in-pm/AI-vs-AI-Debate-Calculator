# Emergency dependency fix script
Write-Host "=== Emergency Dependency Fix ===" -ForegroundColor Red
Write-Host "Fixing critical missing dependencies..." -ForegroundColor Yellow

# Fix 1: Install pydantic-settings
Write-Host "`n1. Installing pydantic-settings..." -ForegroundColor Yellow
try {
    pip install pydantic-settings
    Write-Host "✓ pydantic-settings installed successfully" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to install pydantic-settings" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
}

# Fix 2: Install DearPyGui
Write-Host "`n2. Installing DearPyGui..." -ForegroundColor Yellow
$dearPyGuiPath = "D:\science_projects\agent_vs_agent\DearPyGui-master"

if (Test-Path $dearPyGuiPath) {
    Write-Host "Attempting local DearPyGui installation..." -ForegroundColor Cyan
    try {
        pip install -e $dearPyGuiPath
        Write-Host "✓ DearPyGui installed from local path" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Local installation failed, trying PyPI..." -ForegroundColor Yellow
        try {
            pip install dearpygui
            Write-Host "✓ DearPyGui installed from PyPI" -ForegroundColor Green
        } catch {
            Write-Host "✗ DearPyGui installation failed completely" -ForegroundColor Red
            Write-Host "GUI interface will not work" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "Local DearPyGui path not found, installing from PyPI..." -ForegroundColor Cyan
    try {
        pip install dearpygui
        Write-Host "✓ DearPyGui installed from PyPI" -ForegroundColor Green
    } catch {
        Write-Host "✗ DearPyGui installation failed" -ForegroundColor Red
        Write-Host "GUI interface will not work" -ForegroundColor Yellow
    }
}

# Fix 3: Reinstall the package to ensure dependencies are resolved
Write-Host "`n3. Reinstalling package with dependencies..." -ForegroundColor Yellow
try {
    pip install -e .
    Write-Host "✓ Package reinstalled successfully" -ForegroundColor Green
} catch {
    Write-Host "⚠ Package reinstallation had issues" -ForegroundColor Yellow
}

# Verification
Write-Host "`n4. Verifying fixes..." -ForegroundColor Yellow
Write-Host "Testing pydantic-settings import..." -ForegroundColor Cyan
python -c "from pydantic_settings import BaseSettings; print('✓ pydantic-settings working')" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ pydantic-settings import successful" -ForegroundColor Green
} else {
    Write-Host "✗ pydantic-settings import still failing" -ForegroundColor Red
}

Write-Host "Testing DearPyGui import..." -ForegroundColor Cyan
python -c "import dearpygui.dearpygui as dpg; print('✓ DearPyGui working')" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ DearPyGui import successful" -ForegroundColor Green
} else {
    Write-Host "✗ DearPyGui import still failing" -ForegroundColor Red
}

Write-Host "`n=== Fix Complete ===" -ForegroundColor Green
Write-Host "Now try running: pytest tests/ -v" -ForegroundColor White
