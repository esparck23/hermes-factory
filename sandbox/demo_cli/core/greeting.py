"""Greeting business logic module."""

import sys
from typing import Optional


def greet(
    name: str,
    greeting: str = "Hello",
    verbose: bool = False,
    formal: bool = False,
) -> str:
    """Generate a greeting message.

    Args:
        name: The name of the person to greet.
        greeting: The greeting word to use (default: "Hello").
        verbose: Enable verbose/debug logging.
        formal: Use formal corporate template for the greeting.

    Returns:
        The formatted greeting message.

    Examples:
        >>> greet("Alice")
        'Hello, Alice!'
        >>> greet("Bob", greeting="Welcome")
        'Welcome, Bob!'
        >>> greet("Alice", formal=True)
        'Dear Alice, we extend our most sincere hello and welcome you to our esteemed organization.'
    """
    if verbose:
        print(
            f"[DEBUG] Generating greeting for: {name} with greeting: {greeting}",
            file=sys.stderr,
        )

    if formal:
        return f"Dear {name}, we extend our most sincere {greeting.lower()} and welcome you to our esteemed organization."

    return f"{greeting}, {name}!"
