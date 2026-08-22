import os
import sys

# Ensure src directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from ast_analyzer import analyze_file_changes


def test_python_ast_function_removed():
    old_code = "def existing_function(a, b):\n    return a + b"
    new_code = "# Function removed"
    res = analyze_file_changes("service.py", old_code, new_code)
    
    assert res["valid"] is True
    assert res["language"] == "python"
    assert res["conflicts_count"] > 0
    assert any("Function 'existing_function' was removed" in b for b in res["breaking_changes"])


def test_python_ast_parameter_reduced():
    old_code = "def calculate_tax(amount, rate, discount):\n    return amount * rate - discount"
    new_code = "def calculate_tax(amount, rate):\n    return amount * rate"
    res = analyze_file_changes("tax.py", old_code, new_code)

    assert res["conflicts_count"] > 0
    assert any("reduced parameter list" in b for b in res["breaking_changes"])


def test_python_ast_class_removed():
    old_code = "class UserSession:\n    pass"
    new_code = "# Class removed"
    res = analyze_file_changes("session.py", old_code, new_code)

    assert res["conflicts_count"] > 0
    assert any("Class 'UserSession' was removed" in b for b in res["breaking_changes"])


def test_async_python_function():
    old_code = "async def fetch_data(url, timeout):\n    pass"
    new_code = "async def fetch_data(url):\n    pass"
    res = analyze_file_changes("async_service.py", old_code, new_code)

    assert res["conflicts_count"] > 0
    assert any("reduced parameter list" in b for b in res["breaking_changes"])


def test_regex_signature_typescript_removed():
    old_code = "export function processOrder(orderId: string) {}"
    new_code = "// Function removed"
    res = analyze_file_changes("order.ts", old_code, new_code)

    assert res["language"] == "typescript"
    assert res["conflicts_count"] > 0
    assert any("processOrder" in b for b in res["breaking_changes"])


def test_sql_drop_table():
    old_code = "SELECT * FROM users;"
    new_code = "DROP TABLE users;"
    res = analyze_file_changes("migration.sql", old_code, new_code)

    assert res["language"] == "sql"
    assert res["conflicts_count"] > 0
    assert any("DROP TABLE 'users'" in b for b in res["breaking_changes"])


def test_no_breaking_changes():
    old_code = "def greet(name):\n    print(f'Hello {name}')"
    new_code = "def greet(name):\n    print(f'Hello, {name}!')"
    res = analyze_file_changes("hello.py", old_code, new_code)

    assert res["conflicts_count"] == 0
    assert len(res["breaking_changes"]) == 0
