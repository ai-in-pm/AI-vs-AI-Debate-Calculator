"""
Debate Calculator: AI vs AI Mathematical Reasoning System

A sophisticated calculator where Terrence (GPT-5) and Neil (Claude 3.7 Sonnet)
engage in structured mathematical debates with configurable pacing and rhythm.
"""

__version__ = "1.0.0"
__author__ = "AI Agent"
__description__ = "AI vs AI Mathematical Debate Calculator with Pacing Control"

from .app.settings import Settings
from .app.orchestrator import DebateOrchestrator

__all__ = ["Settings", "DebateOrchestrator"]
