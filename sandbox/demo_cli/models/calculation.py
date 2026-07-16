"""Calculation data models for demo-cli."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Union


class OperationType(Enum):
    """Enumeration of supported arithmetic operations."""

    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"

    @classmethod
    def from_string(cls, operation: str) -> "OperationType":
        """Create an OperationType from a string.

        Args:
            operation: The operation string.

        Returns:
            OperationType instance.

        Raises:
            ValueError: If the operation is not supported.
        """
        try:
            return cls(operation)
        except ValueError:
            raise ValueError(
                f"Unknown operation: {operation}. Supported operations: {list(cls._value2member_keys_())}"
            )


@dataclass
class Calculation:
    """Represents an arithmetic calculation to perform.

    Attributes:
        operation: The arithmetic operation (add, sub, mul, div).
        x: The first operand.
        y: The second operand.
        verbose: Whether to enable verbose/debug logging (default: False).
    """

    operation: OperationType
    x: float
    y: float
    verbose: bool = False

    def to_dict(self) -> dict:
        """Convert the calculation to a dictionary.

        Returns:
            Dictionary representation of the calculation.
        """
        return {
            "operation": self.operation.value,
            "x": self.x,
            "y": self.y,
            "verbose": self.verbose,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Calculation":
        """Create a Calculation from a dictionary.

        Args:
            data: Dictionary containing calculation data.

        Returns:
            Calculation instance.
        """
        return cls(
            operation=OperationType(data.get("operation", "add")),
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            verbose=data.get("verbose", False),
        )

    @classmethod
    def from_args(cls, operation: str, x: float, y: float, verbose: bool = False) -> "Calculation":
        """Create a Calculation from individual arguments.

        Args:
            operation: The operation string.
            x: The first operand.
            y: The second operand.
            verbose: Whether to enable verbose logging.

        Returns:
            Calculation instance.
        """
        return cls(
            operation=OperationType.from_string(operation),
            x=x,
            y=y,
            verbose=verbose,
        )


@dataclass
class CalculationResult:
    """Represents the result of an arithmetic calculation.

    Attributes:
        value: The result of the calculation.
        operation: The operation that was performed.
        x: The first operand.
        y: The second operand.
        success: Whether the calculation was successful (default: True).
        error: Error message if calculation failed (default: None).
    """

    value: float
    operation: OperationType
    x: float
    y: float
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert the calculation result to a dictionary.

        Returns:
            Dictionary representation of the calculation result.
        """
        result = {
            "value": self.value,
            "operation": self.operation.value,
            "x": self.x,
            "y": self.y,
            "success": self.success,
        }
        if self.error:
            result["error"] = self.error
        return result

    def __str__(self) -> str:
        """Return the string representation of the result."""
        return str(self.value)

    @classmethod
    def error_result(cls, operation: str, x: float, y: float, error: str) -> "CalculationResult":
        """Create an error result for a failed calculation.

        Args:
            operation: The operation that failed.
            x: The first operand.
            y: The second operand.
            error: The error message.

        Returns:
            CalculationResult with success=False.
        """
        try:
            op_type = OperationType.from_string(operation)
        except ValueError:
            op_type = OperationType.ADD  # Default fallback

        return cls(
            value=0.0,
            operation=op_type,
            x=x,
            y=y,
            success=False,
            error=error,
        )
