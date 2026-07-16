"""Custom exceptions for demo-cli."""


class CLIError(Exception):
    """Base exception for CLI errors."""

    pass


class CalculationError(CLIError, ValueError):
    """Exception raised for calculation errors."""

    pass


class DivisionByZeroError(CalculationError):
    """Exception raised for division by zero."""

    def __init__(self, message: str = "Division by zero is not allowed.") -> None:
        self.message = message
        super().__init__(self.message)


class UnknownOperationError(CalculationError):
    """Exception raised for unknown operations."""

    def __init__(self, operation: str) -> None:
        self.operation = operation
        self.message = f"Unknown operation: {operation}"
        super().__init__(self.message)


class ConfigurationError(CLIError):
    """Exception raised for configuration errors."""

    pass
