"""Data models for demo-cli."""

from demo_cli.models.greeting import GreetingConfig, GreetingMessage
from demo_cli.models.calculation import Calculation, CalculationResult, OperationType

__all__ = [
    "GreetingConfig",
    "GreetingMessage",
    "Calculation",
    "CalculationResult",
    "OperationType",
]

