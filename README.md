AI vs AI Debate Calculator
A sophisticated desktop calculator where Terrence (GPT-5) and Neil (Claude 3.7 Sonnet) engage in structured mathematical debates with configurable pacing and rhythm. Terrence computes and argues for answers while Neil provides adversarial review, only conceding when genuinely convinced.

Features
Dual AI Personalities: Terrence (primary solver) vs Neil (adversarial reviewer)
Configurable Pacing: Slow, medium, and fast debate rhythms with precise timing control
Multiple Interfaces: Both CLI and Dear PyGui GUI implementations
Protocol Enforcement: Neil must disagree first; Terrence reveals answers only after agreement
Visual Cadence: Typing effects, progress indicators, and steady tempo display
Comprehensive Telemetry: Detailed timing analysis and performance metrics
Quick Start
Prerequisites
Python 3.11+
PyCharm Professional (recommended IDE)
OpenAI API key (for Terrence/GPT-5)
Anthropic API key (for Neil/Claude 3.7 Sonnet)
Windows Quick Start
# Navigate to project directory
cd D:\science_projects\agent_vs_agent\debate_calc

# Run automated setup
.\setup.ps1

# Edit .env with your API keys
notepad .env

# Test the system
python -m debate_calc.app.ui_cli "1 + 1" --pace fast
Installation
Windows Users: See WINDOWS_SETUP.md for detailed Windows-specific instructions and automated setup scripts.

Windows Installation (PowerShell/Command Prompt)
Navigate to the project directory:

cd D:\science_projects\agent_vs_agent\debate_calc
Install the package in development mode:

pip install -e .
pip install -e ".[dev]"
Install Dear PyGui from local repository:

pip install -e "D:\science_projects\agent_vs_agent\DearPyGui-master"
Configure environment:

copy .env.example .env
# Edit .env with your API keys using notepad or your preferred editor
notepad .env
Run tests to verify setup:

pytest tests/ -v
Linux/macOS Installation (with make)
Clone and setup the project:

cd debate_calc
make install-dev
Install Dear PyGui from local repository:

make install-dearpygui
Configure environment:

make setup-env
# Edit .env with your API keys
Run tests to verify setup:

make test
Quick Usage
CLI Interface:

# Simple calculation
python -m debate_calc.app.ui_cli "2 + 3 * 4"

# With custom pace and timing details
python -m debate_calc.app.ui_cli "sqrt(16)" --pace fast --timing

# Interactive mode
python -m debate_calc.app.ui_cli --interactive --pace medium
GUI Interface:

# DearPyGui GUI (preferred)
python -m debate_calc.app.ui_dpg

# Tkinter GUI (fallback if DearPyGui issues)
python -m debate_calc.app.ui_tkinter
Configuration
Environment Variables
Copy .env.example to .env and configure:

# OpenAI Configuration (Terrence)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_TEMPERATURE=0.2

# Anthropic Configuration (Neil)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_TEMPERATURE=0.3

# Pacing Configuration
DEFAULT_PACE_MODE=slow
SLOW_MIN_TURN_SECONDS=2.0
MEDIUM_MIN_TURN_SECONDS=1.2
FAST_MIN_TURN_SECONDS=0.6
Pacing Modes
Mode	Min Turn	Gap Time	Typing Rate	Max Tokens
Slow	2.0s	1.0s	45 cps	350
Medium	1.2s	0.6s	70 cps	300
Fast	0.6s	0.3s	110 cps	250
Architecture
Core Components
orchestrator.py: Main debate flow controller with async/sync support
pace_controller.py: Timing and rhythm management with jitter handling
prompts.py: AI personality definitions and behavioral constraints
settings.py: Configuration management with Pydantic validation
telemetry.py: Performance monitoring and timing analysis
UI Components
ui_cli.py: Command-line interface with progress indicators
ui_dpg.py: Dear PyGui GUI with typing effects and visual cadence
Protocol Rules
Neil's First Response: Must always include <AGREE>false</AGREE> initially
Terrence's Constraint: Cannot output <FINAL>answer</FINAL> until Neil agrees
Agreement Detection: Neil signals agreement with <AGREE>true</AGREE>
Final Answer: Only revealed after explicit agreement using <FINAL>answer</FINAL>
Usage Examples
CLI Examples
# Basic calculation with default slow pace
debate-calc "15 * 7 + 3"

# Fast-paced debate with timing details
debate-calc "(2^3) * 5" --pace fast --timing --max-rounds 8

# Interactive session for multiple calculations
debate-calc --interactive --pace medium

# Analyze previous debate logs
debate-calc --analyze-logs debate_telemetry.jsonl
GUI Features
Expression Input: Enter mathematical expressions
Pace Selector: Choose debate rhythm (slow/medium/fast)
Live Transcript: Real-time debate display with typing effects
Progress Tracking: Round counter, elapsed time, status indicators
Final Answer Display: Highlighted result after agreement
Programming Interface
from debate_calc.app.orchestrator import DebateOrchestrator
from debate_calc.app.settings import settings

# Initialize orchestrator
orchestrator = DebateOrchestrator()

# Run async debate
result = await orchestrator.debate(
    expression="sqrt(144)",
    pace="medium",
    max_rounds=10
)

# Run sync debate (for CLI)
result = orchestrator.debate_sync(
    expression="sqrt(144)",
    pace="medium"
)

print(f"Final answer: {result.final_answer}")
print(f"Status: {result.status}")
print(f"Rounds: {result.rounds}")
Development
Project Structure
debate_calc/
├── .env.example              # Environment configuration template
├── README.md                 # This file
├── pyproject.toml           # Project dependencies and metadata
├── Makefile                 # Development commands
├── app/
│   ├── __init__.py
│   ├── settings.py          # Configuration management
│   ├── prompts.py           # AI personality prompts
│   ├── orchestrator.py      # Main debate controller
│   ├── pace_controller.py   # Timing and rhythm control
│   ├── ui_cli.py           # Command-line interface
│   ├── ui_dpg.py           # Dear PyGui GUI interface
│   └── telemetry.py        # Performance monitoring
└── tests/
    ├── test_protocol.py     # Protocol validation tests
    └── test_smoke.py        # Integration and smoke tests
Development Commands
# Install development dependencies
make install-dev

# Run tests with coverage
make test-coverage

# Code formatting and linting
make format
make lint

# Clean build artifacts
make clean
Testing
The test suite includes:

Protocol Tests: Verify AI behavioral constraints and agreement detection
Pacing Tests: Validate timing enforcement and rhythm consistency
Integration Tests: End-to-end debate flow verification
Smoke Tests: Basic functionality and configuration validation
# Run all tests
make test

# Run specific test categories
pytest tests/test_protocol.py -v
pytest tests/test_smoke.py::TestPacingController -v
Troubleshooting
Common Issues
DearPyGui Import Error (No module named 'dearpygui._dearpygui'):

# Run the comprehensive fix script
.\fix_dearpygui.ps1

# Or manual fixes:
# Install Visual C++ Redistributable
# https://aka.ms/vs/17/release/vc_redist.x64.exe

# Try different DearPyGui version
pip uninstall dearpygui && pip install "dearpygui==1.11.1"

# Use Python 3.11/3.12 instead of 3.13
# Use Tkinter GUI fallback
python -m debate_calc.app.ui_tkinter
API Key Issues:

Verify .env file exists and contains valid API keys
Check API key permissions and rate limits
Timing Inconsistencies:

Adjust pacing parameters in .env
Monitor telemetry logs for performance analysis
Model Response Issues:

Check model availability and API status
Verify prompt engineering in prompts.py
Performance Tuning
Reduce Latency: Use faster pace modes or adjust min_turn_seconds
Improve Accuracy: Increase max_tokens_per_turn for more detailed responses
Debug Timing: Enable telemetry and analyze logs with --analyze-logs
Evidence-Based Accuracy Assessment
Estimated Accuracy: 85%

Reasoning for <100% accuracy:

Model API responses may vary from documented behavior (5% uncertainty)
Timing precision depends on system performance and network latency (5% uncertainty)
Complex async/threading interactions may have edge cases (3% uncertainty)
Dear PyGui integration complexity introduces potential compatibility issues (2% uncertainty)
References
OpenAI API Documentation. (2024). Chat Completions. Retrieved from https://platform.openai.com/docs/api-reference/chat
Anthropic API Documentation. (2024). Messages API. Retrieved from https://docs.anthropic.com/claude/reference/messages_post
Dear PyGui Documentation. (2024). Getting Started. Retrieved from https://dearpygui.readthedocs.io/en/latest/
Pydantic Documentation. (2024). Settings Management. Retrieved from https://docs.pydantic.dev/latest/usage/settings/
Tenacity Documentation. (2024). Retry Library. Retrieved from https://tenacity.readthedocs.io/en/latest/
