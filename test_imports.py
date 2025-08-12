#!/usr/bin/env python3
"""
Quick test script to verify all imports work correctly.
"""

def test_basic_imports():
    """Test basic Python imports."""
    try:
        import os
        import sys
        import time
        import asyncio
        print("✓ Basic Python modules imported successfully")
        return True
    except Exception as e:
        print(f"✗ Basic imports failed: {e}")
        return False

def test_external_dependencies():
    """Test external dependencies."""
    success = True
    
    # Test pydantic
    try:
        from pydantic import Field, validator
        try:
            from pydantic import BaseSettings
        except ImportError:
            from pydantic_settings import BaseSettings
        print("✓ Pydantic imported successfully")
    except Exception as e:
        print(f"✗ Pydantic import failed: {e}")
        success = False
    
    # Test dotenv
    try:
        from dotenv import load_dotenv
        print("✓ python-dotenv imported successfully")
    except Exception as e:
        print(f"✗ python-dotenv import failed: {e}")
        success = False
    
    # Test tenacity
    try:
        from tenacity import retry, stop_after_attempt, wait_exponential
        print("✓ tenacity imported successfully")
    except Exception as e:
        print(f"✗ tenacity import failed: {e}")
        success = False
    
    # Test openai (optional - may not be installed)
    try:
        import openai
        print("✓ openai imported successfully")
    except Exception as e:
        print(f"⚠ openai import failed (optional): {e}")
    
    # Test anthropic (optional - may not be installed)
    try:
        import anthropic
        print("✓ anthropic imported successfully")
    except Exception as e:
        print(f"⚠ anthropic import failed (optional): {e}")
    
    return success

def test_app_imports():
    """Test our app module imports."""
    success = True

    # Add current directory to path for imports
    import sys
    import os
    sys.path.insert(0, os.getcwd())

    try:
        from debate_calc.app.settings import settings, PacingProfile
        print("✓ debate_calc.app.settings imported successfully")
    except Exception as e:
        print(f"✗ debate_calc.app.settings import failed: {e}")
        success = False

    try:
        from debate_calc.app.prompts import get_terrence_messages, get_neil_messages
        print("✓ debate_calc.app.prompts imported successfully")
    except Exception as e:
        print(f"✗ debate_calc.app.prompts import failed: {e}")
        success = False

    try:
        from debate_calc.app.pace_controller import PaceController, SyncPaceController
        print("✓ debate_calc.app.pace_controller imported successfully")
    except Exception as e:
        print(f"✗ debate_calc.app.pace_controller import failed: {e}")
        success = False

    try:
        from debate_calc.app.telemetry import TelemetryLogger
        print("✓ debate_calc.app.telemetry imported successfully")
    except Exception as e:
        print(f"✗ debate_calc.app.telemetry import failed: {e}")
        success = False

    try:
        from debate_calc.app.orchestrator import DebateOrchestrator
        print("✓ debate_calc.app.orchestrator imported successfully")
    except Exception as e:
        print(f"✗ debate_calc.app.orchestrator import failed: {e}")
        success = False

    return success

def test_settings_functionality():
    """Test basic settings functionality."""
    try:
        from debate_calc.app.settings import settings
        
        # Test pace profile retrieval
        slow_profile = settings.get_pacing_profile("slow")
        medium_profile = settings.get_pacing_profile("medium")
        fast_profile = settings.get_pacing_profile("fast")
        
        print(f"✓ Pace profiles loaded: slow={slow_profile.min_turn_seconds}s, medium={medium_profile.min_turn_seconds}s, fast={fast_profile.min_turn_seconds}s")
        return True
    except Exception as e:
        print(f"✗ Settings functionality test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=== Debate Calculator Import Tests ===\n")
    
    all_success = True
    
    print("1. Testing basic imports...")
    all_success &= test_basic_imports()
    
    print("\n2. Testing external dependencies...")
    all_success &= test_external_dependencies()
    
    print("\n3. Testing app module imports...")
    all_success &= test_app_imports()
    
    print("\n4. Testing settings functionality...")
    all_success &= test_settings_functionality()
    
    print(f"\n=== Test Results ===")
    if all_success:
        print("✓ All critical tests passed! The system should work correctly.")
    else:
        print("✗ Some tests failed. Please check the error messages above.")
    
    return 0 if all_success else 1

if __name__ == "__main__":
    exit(main())
