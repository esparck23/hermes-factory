import pytest
from demo_cli.cli import greet, calculate, main, parse_args


def test_greet_unit():
    assert greet("Alice") == "Hello, Alice!"
    assert greet("Bob", greeting="Welcome") == "Welcome, Bob!"


def test_calculate_unit():
    assert calculate("add", 2, 3) == 5.0
    assert calculate("sub", 5, 2) == 3.0
    assert calculate("mul", 4, 3) == 12.0
    assert calculate("div", 10, 2) == 5.0

    with pytest.raises(ValueError, match="Division by zero"):
        calculate("div", 10, 0)

    with pytest.raises(ValueError, match="Unknown operation"):
        calculate("unknown", 1, 2)


def test_parse_args():
    parsed = parse_args(["greet", "Alice"])
    assert parsed.command == "greet"
    assert parsed.name == "Alice"
    assert parsed.greeting == "Hello"

    parsed = parse_args(["calc", "add", "1.5", "2"])
    assert parsed.command == "calc"
    assert parsed.operation == "add"
    assert parsed.x == 1.5
    assert parsed.y == 2.0


def test_main_no_args(capsys):
    exit_code = main([])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "No command specified" in captured.err


def test_main_help(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "demo-cli: A scaffolded Python Command Line Interface" in captured.out


def test_main_version(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "demo-cli 0.1.0" in captured.out


def test_main_greet(capsys):
    exit_code = main(["greet", "Alice"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "Hello, Alice!"


def test_main_greet_verbose(capsys):
    exit_code = main(["-v", "greet", "Alice", "-g", "Hi"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "Hi, Alice!"
    assert "[DEBUG]" in captured.err


def test_main_calc(capsys):
    exit_code = main(["calc", "mul", "3", "4"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "12.0"


def test_main_calc_division_by_zero(capsys):
    exit_code = main(["calc", "div", "5", "0"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Error: Division by zero" in captured.err


def test_greet_formal_unit():
    assert (
        greet("Alice", formal=True)
        == "Dear Alice, we extend our most sincere hello and welcome you to our esteemed organization."
    )
    assert (
        greet("Bob", greeting="Greetings", formal=True)
        == "Dear Bob, we extend our most sincere greetings and welcome you to our esteemed organization."
    )


def test_main_greet_formal(capsys):
    exit_code = main(["greet", "Alice", "--formal"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert (
        captured.out.strip()
        == "Dear Alice, we extend our most sincere hello and welcome you to our esteemed organization."
    )


def test_main_greet_formal_with_greeting(capsys):
    exit_code = main(["greet", "Bob", "--formal", "--greeting", "Greetings"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert (
        captured.out.strip()
        == "Dear Bob, we extend our most sincere greetings and welcome you to our esteemed organization."
    )
