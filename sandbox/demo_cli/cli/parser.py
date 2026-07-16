"""Argument parser configuration for demo-cli."""

import argparse
from typing import List, Optional

from demo_cli import __version__


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the main argument parser.

    Returns:
        The configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="demo-cli: A scaffolded Python Command Line Interface."
    )

    # Global arguments
    parser.add_argument(
        "--version", "-V", action="version", version=f"demo-cli {__version__}"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose/debug logging"
    )

    # Subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Configure greet command
    _configure_greet_parser(subparsers)

    # Configure calc command
    _configure_calc_parser(subparsers)

    return parser


def _configure_greet_parser(subparsers: argparse._SubParsersAction) -> None:
    """Configure the greet command parser.

    Args:
        subparsers: The subparsers action from the main parser.
    """
    greet_parser = subparsers.add_parser(
        "greet",
        help="Greet a person",
        description="Generate a greeting message for the specified person.",
    )

    greet_parser.add_argument("name", help="Name of the person to greet")

    greet_parser.add_argument(
        "--greeting",
        "-g",
        default="Hello",
        help="Greeting word to use (default: Hello)",
    )

    greet_parser.add_argument(
        "--formal",
        action="store_true",
        help="Use elite corporate template for the greeting",
    )


def _configure_calc_parser(subparsers: argparse._SubParsersAction) -> None:
    """Configure the calc command parser.

    Args:
        subparsers: The subparsers action from the main parser.
    """
    calc_parser = subparsers.add_parser(
        "calc",
        help="Perform simple arithmetic operations",
        description="Perform arithmetic operations: add, sub, mul, div.",
    )

    calc_parser.add_argument(
        "operation",
        choices=["add", "sub", "mul", "div"],
        help="Arithmetic operation to perform",
    )

    calc_parser.add_argument("x", type=float, help="First operand")

    calc_parser.add_argument("y", type=float, help="Second operand")


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments.

    Args:
        args: List of arguments to parse (default: sys.argv[1:])

    Returns:
        The parsed namespace with command and arguments.
    """
    parser = create_parser()
    return parser.parse_args(args)
