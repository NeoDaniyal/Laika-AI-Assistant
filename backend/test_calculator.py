import sys
import os

# Ensure root backend directory is available in Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.tools.calculator import CalculatorTool


def test_calculator():
    calc = CalculatorTool()

    print("=== Testing CalculatorTool Metadata ===")
    schema = calc.to_schema()
    print(f"Name: {schema['name']}")
    print(f"Description: {schema['description']}")
    print(f"Parameters Schema: {schema['parameters']}\n")

    print("=== Testing Successful Operations ===")
    assert calc.execute({"operation": "add", "a": 10, "b": 5}) == 15.0
    print("✓ 10 + 5 = 15")

    assert calc.execute({"operation": "subtract", "a": 10, "b": 5}) == 5.0
    print("✓ 10 - 5 = 5")

    assert calc.execute({"operation": "multiply", "a": 10, "b": 5}) == 50.0
    print("✓ 10 * 5 = 50")

    assert calc.execute({"operation": "divide", "a": 10, "b": 5}) == 2.0
    print("✓ 10 / 5 = 2.0")

    print("\n=== Testing Error Handling ===")
    
    # Test Division by Zero
    try:
        calc.execute({"operation": "divide", "a": 10, "b": 0})
    except ValueError as e:
        print(f"✓ Division by Zero handled safely -> ValueError: '{e}'")

    # Test Unsupported Operation
    try:
        calc.execute({"operation": "power", "a": 10, "b": 5})
    except ValueError as e:
        print(f"✓ Unknown operation handled safely -> ValueError: '{e}'")

    # Test Invalid Operand Type
    try:
        calc.execute({"operation": "add", "a": "invalid", "b": 5})
    except TypeError as e:
        print(f"✓ Invalid operand handled safely -> TypeError: '{e}'")

    print("\nAll CalculatorTool tests passed successfully! 🎉")


if __name__ == "__main__":
    test_calculator()