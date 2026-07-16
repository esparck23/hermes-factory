"""CLI entry point for demo-cli."""

import sys
from typing import List, Optional

import argparse

from demo_cli.core.calculator import calculate
from demo_cli.core.greeting import greet


def main(args: Optional[List[str]] = None) -> int:
    """Main CLI entry point."""
    from demo_cli.cli.parser import parse_args

    if args is None:
        args = sys.argv[1:]

    try:
        parsed_args = parse_args(args)

        if not parsed_args.command:
            print(
                "Error: No command specified. Use --help to see available commands.",
                file=sys.stderr,
            )
            return 1

        if parsed_args.command == "greet":
            result = greet(
                parsed_args.name,
                greeting=parsed_args.greeting,
                verbose=parsed_args.verbose,
                formal=parsed_args.formal,
            )
            print(result)

        elif parsed_args.command == "calc":
            try:
                result = calculate(
                    parsed_args.operation,
                    parsed_args.x,
                    parsed_args.y,
                    verbose=parsed_args.verbose,
                )
                print(result)
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                return 1

        return 0

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
