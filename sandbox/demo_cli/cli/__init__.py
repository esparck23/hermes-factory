"""CLI configuration and entry point modules."""

from demo_cli.cli.parser import parse_args
from demo_cli.cli.main import main
from demo_cli.core.calculator import calculate
from demo_cli.core.greeting import greet

__all__ = ["parse_args", "main", "calculate", "greet"]
