# Demo CLI

A fully scaffolded, robust, and extensible Python Command Line Interface (CLI) project.

## Project Structure

```text
sandbox/
├── demo_cli/
│   ├── __init__.py
│   └── cli.py              # Core CLI entrypoint and command definition
├── tests/
│   ├── __init__.py
│   └── test_cli.py         # Unit and integration test suite
├── pyproject.toml          # PEP 621 metadata, dependencies, build settings, and entrypoints
└── README.md               # Documentation
```

## Installation

### Prerequisites
- Python 3.8 or higher

### Local Development Installation
To install the CLI in editable mode with development dependencies:

```bash
# Install with development packages
pip install -e .[dev]
```

This will link the script locally and register the global command `demo-cli` which you can run from anywhere.

## Usage

Once installed, you can execute the CLI via `demo-cli`.

### Global Options

*   Show help:
    ```bash
    demo-cli --help
    ```
*   Show version:
    ```bash
    demo-cli --version
    ```
*   Enable verbose debugging logs:
    ```bash
    demo-cli --verbose <command> [args]
    ```

### Subcommands

#### 1. `greet`
Greet a person by name.

```bash
demo-cli greet Alice
# Output: Hello, Alice!

# Custom greeting:
demo-cli greet Bob --greeting Welcome
# Output: Welcome, Bob!
```

#### 2. `calc`
Perform simple mathematical operations: `add`, `sub`, `mul`, `div`.

```bash
demo-cli calc add 5.5 4.5
# Output: 10.0

demo-cli calc div 10 2
# Output: 5.0

demo-cli calc div 5 0
# Output: Error: Division by zero is not allowed.
```

## Running Tests

To run the test suite, ensure you have installed the package with the `[dev]` dependencies, then execute `pytest`:

```bash
pytest
```

To run tests with code coverage or print output verbosely:

```bash
pytest -v
```
