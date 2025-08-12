# DearPyGui Comprehensive Fix Script
Write-Host "=== DearPyGui Comprehensive Fix ===" -ForegroundColor Cyan
Write-Host "Attempting multiple strategies to fix DearPyGui installation..." -ForegroundColor Yellow

# Check Python version
$pythonVersion = python --version
Write-Host "Python version: $pythonVersion" -ForegroundColor Cyan

# Strategy 1: Clean uninstall and reinstall from PyPI
Write-Host "`n1. Clean uninstall and reinstall from PyPI..." -ForegroundColor Yellow
try {
    Write-Host "Uninstalling existing DearPyGui..." -ForegroundColor Cyan
    pip uninstall dearpygui -y 2>$null
    
    Write-Host "Installing DearPyGui from PyPI..." -ForegroundColor Cyan
    pip install dearpygui
    
    # Test the installation
    $testResult = python -c "import dearpygui.dearpygui as dpg; print('✓ DearPyGui PyPI installation successful')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Strategy 1 SUCCESS: DearPyGui working from PyPI" -ForegroundColor Green
        exit 0
    } else {
        Write-Host "✗ Strategy 1 failed: $testResult" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Strategy 1 failed with exception: $_" -ForegroundColor Red
}

# Strategy 2: Try specific DearPyGui version compatible with Python 3.13
Write-Host "`n2. Trying specific DearPyGui version..." -ForegroundColor Yellow
try {
    pip uninstall dearpygui -y 2>$null
    # Try the latest stable version
    pip install "dearpygui==1.11.1"
    
    $testResult = python -c "import dearpygui.dearpygui as dpg; print('✓ DearPyGui specific version successful')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Strategy 2 SUCCESS: DearPyGui working with specific version" -ForegroundColor Green
        exit 0
    } else {
        Write-Host "✗ Strategy 2 failed: $testResult" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Strategy 2 failed with exception: $_" -ForegroundColor Red
}

# Strategy 3: Try pre-release version
Write-Host "`n3. Trying pre-release version..." -ForegroundColor Yellow
try {
    pip uninstall dearpygui -y 2>$null
    pip install --pre dearpygui
    
    $testResult = python -c "import dearpygui.dearpygui as dpg; print('✓ DearPyGui pre-release successful')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Strategy 3 SUCCESS: DearPyGui working with pre-release" -ForegroundColor Green
        exit 0
    } else {
        Write-Host "✗ Strategy 3 failed: $testResult" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Strategy 3 failed with exception: $_" -ForegroundColor Red
}

# Strategy 4: Install Visual C++ Redistributables (often needed for compiled extensions)
Write-Host "`n4. Checking Visual C++ Redistributables..." -ForegroundColor Yellow
Write-Host "DearPyGui requires Visual C++ Redistributables for the compiled components." -ForegroundColor Cyan
Write-Host "Please install Microsoft Visual C++ Redistributable from:" -ForegroundColor Yellow
Write-Host "https://aka.ms/vs/17/release/vc_redist.x64.exe" -ForegroundColor White

# Strategy 5: Try building from source with proper tools
Write-Host "`n5. Attempting local build with proper setup..." -ForegroundColor Yellow
$localPath = "D:\science_projects\agent_vs_agent\DearPyGui-master"
if (Test-Path $localPath) {
    try {
        Write-Host "Checking if build tools are available..." -ForegroundColor Cyan
        
        # Check for CMake
        $cmakeCheck = cmake --version 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "⚠ CMake not found - required for building DearPyGui from source" -ForegroundColor Yellow
        }
        
        # Check for Visual Studio Build Tools
        $vswhereCheck = Get-Command "vswhere.exe" -ErrorAction SilentlyContinue
        if (-not $vswhereCheck) {
            Write-Host "⚠ Visual Studio Build Tools not detected" -ForegroundColor Yellow
        }
        
        Write-Host "Attempting local installation anyway..." -ForegroundColor Cyan
        pip uninstall dearpygui -y 2>$null
        pip install -e $localPath
        
        $testResult = python -c "import dearpygui.dearpygui as dpg; print('✓ DearPyGui local build successful')" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Strategy 5 SUCCESS: DearPyGui working from local build" -ForegroundColor Green
            exit 0
        } else {
            Write-Host "✗ Strategy 5 failed: $testResult" -ForegroundColor Red
        }
    } catch {
        Write-Host "✗ Strategy 5 failed with exception: $_" -ForegroundColor Red
    }
} else {
    Write-Host "✗ Local DearPyGui path not found: $localPath" -ForegroundColor Red
}

# All strategies failed - provide comprehensive guidance
Write-Host "`n❌ All DearPyGui installation strategies failed" -ForegroundColor Red
Write-Host "`n🔧 Manual Resolution Steps:" -ForegroundColor Yellow
Write-Host "1. Install Visual C++ Redistributable:" -ForegroundColor White
Write-Host "   https://aka.ms/vs/17/release/vc_redist.x64.exe" -ForegroundColor Cyan
Write-Host "`n2. Try alternative Python version:" -ForegroundColor White
Write-Host "   DearPyGui may not support Python 3.13 yet" -ForegroundColor Cyan
Write-Host "   Consider using Python 3.11 or 3.12" -ForegroundColor Cyan
Write-Host "`n3. Use CLI-only mode:" -ForegroundColor White
Write-Host "   python -m debate_calc.app.ui_cli" -ForegroundColor Cyan
Write-Host "`n4. Install build tools for local compilation:" -ForegroundColor White
Write-Host "   - Visual Studio Build Tools" -ForegroundColor Cyan
Write-Host "   - CMake" -ForegroundColor Cyan
Write-Host "`n5. Check DearPyGui GitHub for Python 3.13 compatibility:" -ForegroundColor White
Write-Host "   https://github.com/hoffstadt/DearPyGui/issues" -ForegroundColor Cyan

Write-Host "`n✅ The system will work without GUI - CLI interface is fully functional" -ForegroundColor Green
