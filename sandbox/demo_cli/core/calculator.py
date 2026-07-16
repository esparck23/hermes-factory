"""Calculator business logic module."""

import sys
from typing import Literal

from demo_cli.exceptions import DivisionByZeroError, UnknownOperationError

OperationType = Literal["add", "sub", "mul", "div"]


def calculate(
    operation: OperationType,
    x: float,
    y: float,
    verbose: bool = False,
) -> float:
    """Perform a simple mathematical calculation.

    Args:
        operation: The arithmetic operation to perform (add, sub, mul, div).
        x: The first operand.
        y: The second operand.
        verbose: Enable verbose/debug logging.

    Returns:
        The result of the calculation.

    Raises:
        DivisionByZeroError: If attempting division by zero.
        UnknownOperationError: If an unknown operation is specified.

    Examples:
        >>> calculate("add", 2, 3)
        5.0
        >>> calculate("sub", 5, 2)
        3.0
        >>> calculate("mul", 4, 3)
        12.0
        >>> calculate("div", 10, 2)
        5.0
    """
    if verbose:
        print(f"[DEBUG] Calculating: {x} {operation} {y}", file=sys.stderr)

    if operation == "add":
        return x + y
    elif operation == "sub":
        return x - y
    elif operation == "mul":
        return x * y
    elif operation == "div":
        if y == 0:
            raise DivisionByZeroError()
        return x / y
    else:
        raise UnknownOperationError(operation)
