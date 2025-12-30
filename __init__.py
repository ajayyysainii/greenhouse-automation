"""Greenhouse job application automation module"""

from .greenhouse_automation import run_automation

# Alias for backward compatibility
run_greenhouse_automation = run_automation

__all__ = ['run_automation', 'run_greenhouse_automation']

