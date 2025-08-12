.PHONY: install install-dev test lint format clean run-cli run-gui

# Installation targets
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pip install -e "D:\science_projects\agent_vs_agent\DearPyGui-master"

install-dearpygui:
	pip install -e "D:\science_projects\agent_vs_agent\DearPyGui-master"

# Development targets
test:
	pytest tests/ -v

test-coverage:
	pytest tests/ --cov=debate_calc --cov-report=html

lint:
	black --check debate_calc/ tests/
	isort --check-only debate_calc/ tests/
	mypy debate_calc/

format:
	black debate_calc/ tests/
	isort debate_calc/ tests/

# Runtime targets
run-cli:
	python -m debate_calc.app.ui_cli

run-gui:
	python -m debate_calc.app.ui_dpg

# Utility targets
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf build/ dist/ *.egg-info/ .coverage htmlcov/

setup-env:
	cp .env.example .env
	@echo "Please edit .env with your API keys"

# Quick start
quickstart: install-dev setup-env
	@echo "Setup complete! Edit .env with your API keys, then run 'make run-gui' or 'make run-cli'"
