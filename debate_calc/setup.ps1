# PowerShell setup script for Debate Calculator on Windows
# Run this script to set up the development environment

Write-Host "=== Debate Calculator Setup Script ===" -ForegroundColor Cyan
Write-Host "Setting up the AI vs AI Mathematical Debate Calculator..." -ForegroundColor Green

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.11+ first." -ForegroundColor Red
    exit 1
}

# Check Python version
$versionMatch = $pythonVersion -match "Python (\d+)\.(\d+)"
if ($versionMatch) {
    $majorVersion = [int]$matches[1]
    $minorVersion = [int]$matches[2]
    
    if ($majorVersion -lt 3 -or ($majorVersion -eq 3 -and $minorVersion -lt 11)) {
        Write-Host "✗ Python 3.11+ required. Found: $pythonVersion" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n1. Installing package dependencies..." -ForegroundColor Yellow
try {
    # Install core dependencies first
    pip install pydantic-settings
    pip install -e .
    pip install -e ".[dev]"
    Write-Host "✓ Package dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to install package dependencies" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host "Trying to install pydantic-settings separately..." -ForegroundColor Yellow
    pip install pydantic-settings
    exit 1
}

Write-Host "`n2. Installing Dear PyGui from local repository..." -ForegroundColor Yellow
$dearPyGuiPath = "D:\science_projects\agent_vs_agent\DearPyGui-master"
if (Test-Path $dearPyGuiPath) {
    try {
        pip install -e $dearPyGuiPath
        Write-Host "✓ Dear PyGui installed from local repository" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Failed to install Dear PyGui from local path" -ForegroundColor Yellow
        Write-Host "Trying to install from PyPI..." -ForegroundColor Yellow
        try {
            pip install dearpygui
            Write-Host "✓ Dear PyGui installed from PyPI" -ForegroundColor Green
        } catch {
            Write-Host "✗ Failed to install Dear PyGui" -ForegroundColor Red
            Write-Host "GUI interface may not work" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "⚠ Local Dear PyGui path not found: $dearPyGuiPath" -ForegroundColor Yellow
    Write-Host "Installing from PyPI..." -ForegroundColor Yellow
    try {
        pip install dearpygui
        Write-Host "✓ Dear PyGui installed from PyPI" -ForegroundColor Green
    } catch {
        Write-Host "✗ Failed to install Dear PyGui" -ForegroundColor Red
        Write-Host "GUI interface may not work" -ForegroundColor Yellow
    }
}

Write-Host "`n3. Setting up environment configuration..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "⚠ .env file already exists" -ForegroundColor Yellow
} else {
    try {
        Copy-Item ".env.example" ".env"
        Write-Host "✓ Created .env file from template" -ForegroundColor Green
        Write-Host "📝 Please edit .env with your API keys:" -ForegroundColor Cyan
        Write-Host "   - OPENAI_API_KEY=your_openai_api_key_here" -ForegroundColor White
        Write-Host "   - ANTHROPIC_API_KEY=your_anthropic_api_key_here" -ForegroundColor White
    } catch {
        Write-Host "✗ Failed to create .env file" -ForegroundColor Red
    }
}

Write-Host "`n4. Running installation verification..." -ForegroundColor Yellow
try {
    python test_installation.py
    Write-Host "✓ Installation verification completed" -ForegroundColor Green
} catch {
    Write-Host "⚠ Installation verification had issues" -ForegroundColor Yellow
    Write-Host "You can run it manually with: python test_installation.py" -ForegroundColor White
}

Write-Host "`n5. Running unit tests..." -ForegroundColor Yellow
try {
    pytest tests/ -v --tb=short
    Write-Host "✓ Unit tests completed" -ForegroundColor Green
} catch {
    Write-Host "⚠ Some tests failed or pytest not available" -ForegroundColor Yellow
    Write-Host "You can run tests manually with: pytest tests/ -v" -ForegroundColor White
}

Write-Host "`n=== Setup Complete ===" -ForegroundColor Cyan
Write-Host "Next steps:" -ForegroundColor Green
Write-Host "1. Edit .env file with your API keys" -ForegroundColor White
Write-Host "2. Test CLI: python -m debate_calc.app.ui_cli `"1 + 1`"" -ForegroundColor White
Write-Host "3. Test GUI: python -m debate_calc.app.ui_dpg" -ForegroundColor White
Write-Host "`nFor help: python -m debate_calc.app.ui_cli --help" -ForegroundColor White
