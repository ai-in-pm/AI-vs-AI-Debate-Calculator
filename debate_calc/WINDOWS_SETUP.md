# Windows Setup Guide for Debate Calculator

This guide provides step-by-step instructions for setting up the Debate Calculator on Windows systems.

## Prerequisites

- **Python 3.11+** installed and added to PATH
- **PowerShell** or **Command Prompt**
- **OpenAI API Key** (for Terrence/GPT-5)
- **Anthropic API Key** (for Neil/Claude 3.7 Sonnet)

## Quick Setup (Recommended)

### Option 1: PowerShell Script
```powershell
# Navigate to the project directory
cd D:\science_projects\agent_vs_agent\debate_calc

# Run the setup script
.\setup.ps1
```

### Option 2: Batch Script
```cmd
# Navigate to the project directory
cd D:\science_projects\agent_vs_agent\debate_calc

# Run the setup script
setup.bat
```

## Manual Setup

If the automated scripts don't work, follow these manual steps:

### 1. Install Package Dependencies
```powershell
# Install critical dependency first (fixes Pydantic v2 issue)
pip install pydantic-settings

# Install the main package in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

### 2. Install Dear PyGui
```powershell
# Try local installation first
pip install -e "D:\science_projects\agent_vs_agent\DearPyGui-master"

# If that fails, install from PyPI
pip install dearpygui
```

### 3. Configure Environment
```powershell
# Copy the environment template
copy .env.example .env

# Edit the .env file with your API keys
notepad .env
```

Add your API keys to the `.env` file:
```env
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### 4. Test Installation
```powershell
# Run tests
pytest tests/ -v

# Test CLI interface
python -m debate_calc.app.ui_cli "1 + 1" --pace fast

# Test GUI interface
python -m debate_calc.app.ui_dpg
```

## Usage Examples

### Command Line Interface
```powershell
# Simple calculation
python -m debate_calc.app.ui_cli "2 + 3 * 4"

# With custom settings
python -m debate_calc.app.ui_cli "sqrt(16)" --pace fast --timing

# Interactive mode
python -m debate_calc.app.ui_cli --interactive --pace medium

# Show help
python -m debate_calc.app.ui_cli --help
```

### GUI Interface
```powershell
# Launch the GUI
python -m debate_calc.app.ui_dpg
```

## Troubleshooting

### Common Issues

1. **"make is not recognized"**
   - Use the PowerShell/Batch scripts instead of make commands
   - Or install make for Windows: `choco install make` (requires Chocolatey)

2. **"Module not found" errors**
   - Ensure you're in the correct directory: `D:\science_projects\agent_vs_agent\debate_calc`
   - Try reinstalling: `pip install -e .`

3. **Dear PyGui import errors**
   - Install from PyPI: `pip install dearpygui`
   - Check Python version compatibility

4. **Pydantic import errors**
   - Install pydantic-settings: `pip install pydantic-settings`
   - For Pydantic v1: `pip install "pydantic<2.0.0"`
   - Check version: `pip show pydantic pydantic-settings`

5. **API key errors**
   - Verify `.env` file exists and contains valid keys
   - Check API key permissions and quotas

6. **Permission errors**
   - Run PowerShell as Administrator
   - Check file permissions in the project directory

### Dependency Issues

If you encounter dependency conflicts:

```powershell
# Create a virtual environment
python -m venv debate_calc_env

# Activate it
debate_calc_env\Scripts\activate

# Install dependencies
pip install -e .
pip install -e ".[dev]"
```

### Testing Your Setup

Run this quick test to verify everything works:

```powershell
# Test basic functionality
python -c "from debate_calc.app.settings import settings; print('✓ Settings loaded')"

# Test with a simple calculation (requires API keys)
python -m debate_calc.app.ui_cli "1 + 1" --pace fast
```

## Performance Tips

- Use SSD storage for better I/O performance
- Ensure stable internet connection for API calls
- Close unnecessary applications to free up memory
- Use `--pace fast` for quicker testing

## Getting Help

If you encounter issues:

1. Check the main README.md for detailed documentation
2. Review error messages carefully
3. Verify all prerequisites are installed
4. Test with simple expressions first
5. Check API key validity and quotas

## Alternative Installation Methods

### Using Poetry (if available)
```powershell
# Install Poetry first: https://python-poetry.org/docs/#installation
poetry install
poetry run python -m debate_calc.app.ui_cli "1 + 1"
```

### Using Conda
```powershell
# Create conda environment
conda create -n debate_calc python=3.11
conda activate debate_calc

# Install dependencies
pip install -e .
pip install -e ".[dev]"
```

## Next Steps

After successful installation:

1. **Configure API Keys**: Edit `.env` with your OpenAI and Anthropic API keys
2. **Test Basic Functionality**: Run a simple calculation
3. **Explore Features**: Try different pace modes and interfaces
4. **Read Documentation**: Review the main README.md for advanced usage
5. **Run Tests**: Execute the test suite to verify everything works

Happy debating! 🤖 vs 🤖
