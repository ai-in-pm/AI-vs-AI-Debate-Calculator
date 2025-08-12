#!/usr/bin/env python3
"""
Installation verification script for Debate Calculator.
Run this to verify that all components are properly installed and configured.
"""

import sys
import os
import traceback

def print_status(message, status="info"):
    """Print colored status messages."""
    colors = {
        "success": "\033[92m✓",
        "error": "\033[91m✗", 
        "warning": "\033[93m⚠",
        "info": "\033[94mℹ"
    }
    reset = "\033[0m"
    print(f"{colors.get(status, '')} {message}{reset}")

def test_python_version():
    """Test Python version compatibility."""
    print_status("Testing Python version...", "info")
    
    version = sys.version_info
    if version.major >= 3 and version.minor >= 11:
        print_status(f"Python {version.major}.{version.minor}.{version.micro} - Compatible", "success")
        return True
    else:
        print_status(f"Python {version.major}.{version.minor}.{version.micro} - Requires 3.11+", "error")
        return False

def test_basic_imports():
    """Test basic Python imports."""
    print_status("Testing basic imports...", "info")
    
    try:
        import asyncio
        import threading
        import queue
        import time
        import re
        import json
        print_status("Basic Python modules imported successfully", "success")
        return True
    except Exception as e:
        print_status(f"Basic imports failed: {e}", "error")
        return False

def test_external_dependencies():
    """Test external package imports."""
    print_status("Testing external dependencies...", "info")
    
    success = True
    
    # Test pydantic and pydantic-settings
    try:
        from pydantic import Field, validator
        print_status("Pydantic core imported successfully", "success")
    except Exception as e:
        print_status(f"Pydantic core import failed: {e}", "error")
        success = False

    try:
        from pydantic_settings import BaseSettings
        print_status("pydantic-settings imported successfully", "success")
    except ImportError:
        try:
            from pydantic import BaseSettings
            print_status("BaseSettings imported from pydantic (legacy)", "warning")
        except ImportError:
            print_status("BaseSettings not found - install pydantic-settings", "error")
            success = False
    
    # Test dotenv
    try:
        from dotenv import load_dotenv
        print_status("python-dotenv imported successfully", "success")
    except Exception as e:
        print_status(f"python-dotenv import failed: {e}", "error")
        success = False
    
    # Test tenacity
    try:
        from tenacity import retry, stop_after_attempt, wait_exponential
        print_status("tenacity imported successfully", "success")
    except Exception as e:
        print_status(f"tenacity import failed: {e}", "error")
        success = False
    
    # Test optional dependencies
    try:
        import openai
        print_status("openai imported successfully", "success")
    except Exception as e:
        print_status(f"openai import failed (install with: pip install openai): {e}", "warning")
    
    try:
        import anthropic
        print_status("anthropic imported successfully", "success")
    except Exception as e:
        print_status(f"anthropic import failed (install with: pip install anthropic): {e}", "warning")
    
    try:
        import dearpygui.dearpygui as dpg
        print_status("dearpygui imported successfully", "success")
    except Exception as e:
        print_status(f"dearpygui import failed (GUI won't work): {e}", "warning")
        print_status("Try: pip install dearpygui", "info")
    
    return success

def test_app_modules():
    """Test application module imports."""
    print_status("Testing application modules...", "info")
    
    success = True
    
    # Add current directory to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    modules_to_test = [
        ("debate_calc.app.settings", "settings, PacingProfile"),
        ("debate_calc.app.prompts", "get_terrence_messages, get_neil_messages"),
        ("debate_calc.app.pace_controller", "PaceController, SyncPaceController"),
        ("debate_calc.app.telemetry", "TelemetryLogger"),
        ("debate_calc.app.orchestrator", "DebateOrchestrator")
    ]
    
    for module_name, imports in modules_to_test:
        try:
            exec(f"from {module_name} import {imports}")
            print_status(f"{module_name} imported successfully", "success")
        except Exception as e:
            print_status(f"{module_name} import failed: {e}", "error")
            success = False
    
    return success

def test_configuration():
    """Test configuration loading."""
    print_status("Testing configuration...", "info")
    
    try:
        from debate_calc.app.settings import settings
        
        # Test pace profiles
        slow_profile = settings.get_pacing_profile("slow")
        medium_profile = settings.get_pacing_profile("medium")
        fast_profile = settings.get_pacing_profile("fast")
        
        print_status(f"Pace profiles loaded: slow={slow_profile.min_turn_seconds}s, medium={medium_profile.min_turn_seconds}s, fast={fast_profile.min_turn_seconds}s", "success")
        
        # Check for .env file
        if os.path.exists(".env"):
            print_status(".env file found", "success")
        else:
            print_status(".env file not found - copy .env.example to .env and add API keys", "warning")
        
        return True
    except Exception as e:
        print_status(f"Configuration test failed: {e}", "error")
        traceback.print_exc()
        return False

def test_cli_module():
    """Test CLI module can be imported."""
    print_status("Testing CLI module...", "info")
    
    try:
        from debate_calc.app.ui_cli import main
        print_status("CLI module imported successfully", "success")
        return True
    except Exception as e:
        print_status(f"CLI module import failed: {e}", "error")
        return False

def test_gui_module():
    """Test GUI module can be imported."""
    print_status("Testing GUI module...", "info")

    try:
        # First test if DearPyGui core is available
        import dearpygui.dearpygui as dpg
        print_status("DearPyGui core imported successfully", "success")

        # Then test our GUI module
        from debate_calc.app.ui_dpg import DEARPYGUI_AVAILABLE
        if DEARPYGUI_AVAILABLE:
            from debate_calc.app.ui_dpg import DebateGUI
            print_status("GUI module imported successfully", "success")
            return True
        else:
            print_status("GUI module loaded but DearPyGui marked as unavailable", "warning")
            return False

    except ImportError as e:
        if "_dearpygui" in str(e):
            print_status("DearPyGui compiled module missing (_dearpygui)", "warning")
            print_status("This is a known issue with Python 3.13 or missing Visual C++ Redistributables", "info")
            print_status("Solutions: 1) Install VC++ Redist 2) Use Python 3.11/3.12 3) Run fix_dearpygui.ps1", "info")
        else:
            print_status(f"GUI module import failed: {e}", "warning")
        print_status("GUI interface disabled - CLI interface remains functional", "info")
        return False
    except Exception as e:
        print_status(f"GUI module test failed: {e}", "warning")
        print_status("GUI interface may not work", "warning")
        return False

def main():
    """Run all installation tests."""
    print("=" * 60)
    print("🤖 Debate Calculator Installation Verification")
    print("=" * 60)
    
    tests = [
        ("Python Version", test_python_version),
        ("Basic Imports", test_basic_imports),
        ("External Dependencies", test_external_dependencies),
        ("Application Modules", test_app_modules),
        ("Configuration", test_configuration),
        ("CLI Module", test_cli_module),
        ("GUI Module", test_gui_module)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_status(f"Test {test_name} crashed: {e}", "error")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        color = "success" if result else "error"
        print_status(f"{test_name}: {status}", color)
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print_status("🎉 All tests passed! Installation is complete.", "success")
        print_status("Next steps:", "info")
        print("  1. Edit .env with your API keys")
        print("  2. Test CLI: python -m debate_calc.app.ui_cli \"1 + 1\"")
        print("  3. Test GUI: python -m debate_calc.app.ui_dpg")
        return 0
    else:
        print_status("❌ Some tests failed. Please check the errors above.", "error")
        return 1

if __name__ == "__main__":
    sys.exit(main())
