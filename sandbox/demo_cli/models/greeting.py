"""Greeting data models for demo-cli."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GreetingConfig:
    """Configuration for generating a greeting message.

    Attributes:
        name: The name of the person to greet.
        greeting: The greeting word to use (default: "Hello").
        formal: Whether to use formal corporate template (default: False).
        verbose: Whether to enable verbose/debug logging (default: False).
    """

    name: str
    greeting: str = "Hello"
    formal: bool = False
    verbose: bool = False

    def to_dict(self) -> dict:
        """Convert the configuration to a dictionary.

        Returns:
            Dictionary representation of the greeting configuration.
        """
        return {
            "name": self.name,
            "greeting": self.greeting,
            "formal": self.formal,
            "verbose": self.verbose,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GreetingConfig":
        """Create a GreetingConfig from a dictionary.

        Args:
            data: Dictionary containing greeting configuration.

        Returns:
            GreetingConfig instance.
        """
        return cls(
            name=data.get("name", ""),
            greeting=data.get("greeting", "Hello"),
            formal=data.get("formal", False),
            verbose=data.get("verbose", False),
        )


@dataclass
class GreetingMessage:
    """Represents a formatted greeting message.

    Attributes:
        content: The formatted greeting message text.
        recipient: The name of the person being greeted.
        is_formal: Whether the greeting is formal.
    """

    content: str
    recipient: str
    is_formal: bool = False

    def __str__(self) -> str:
        """Return the greeting content."""
        return self.content

    def to_dict(self) -> dict:
        """Convert the greeting message to a dictionary.

        Returns:
            Dictionary representation of the greeting message.
        """
        return {
            "content": self.content,
            "recipient": self.recipient,
            "is_formal": self.is_formal,
        }
