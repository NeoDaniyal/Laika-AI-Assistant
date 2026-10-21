from typing import Any, Dict
from backend.tools.base import Tool


class CalculatorTool(Tool):
    """Tool for performing basic arithmetic operations strictly without eval()."""

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return (
            "Perform basic arithmetic calculations (addition, subtraction, "
            "multiplication, division) on two numbers."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide"],
                    "description": "The arithmetic operation to perform.",
                },
                "a": {
                    "type": "number",
                    "description": "The first numeric operand.",
                },
                "b": {
                    "type": "number",
                    "description": "The second numeric operand.",
                },
            },
            "required": ["operation", "a", "b"],
        }

    def execute(self, arguments: Dict[str, Any]) -> float:
        operation = arguments.get("operation")
        a = arguments.get("a")
        b = arguments.get("b")

        if a is None or b is None or operation is None:
            raise TypeError("Missing required arguments: 'operation', 'a', and 'b'.")

        try:
            a = float(a)
            b = float(b)
        except (ValueError, TypeError):
            raise TypeError("Operands 'a' and 'b' must be valid numbers.")

        if operation == "add":
            return a + b
        elif operation == "subtract":
            return a - b
        elif operation == "multiply":
            return a * b
        elif operation == "divide":
            if b == 0:
                raise ValueError("Division by zero is not allowed.")
            return a / b
        else:
            raise ValueError(
                f"Unsupported operation '{operation}'. Supported operations: add, subtract, multiply, divide."
            )