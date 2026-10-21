import sys
import os

# Ensure root backend directory is available in Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.tools import registry


def test_registry_integration():
    print("=== Testing Tool Registry Setup ===")

    # 1. Verify registered tool count
    all_tools = registry.all()
    print(f"Registered tools: {list(all_tools.keys())}")
    assert "calculator" in all_tools, "Calculator tool was not found in registry!"

    # 2. Verify schema export for LLM prompt context
    schemas = registry.to_schemas()
    print("\n=== Exported Tool Schemas ===")
    print(schemas)
    assert len(schemas) >= 1
    assert schemas[0]["name"] == "calculator"

    # 3. Test execution through generic registry interface
    print("\n=== Executing Tool via Registry ===")
    result = registry.execute(
        "calculator",
        {"operation": "multiply", "a": 12, "b": 4}
    )
    print(f"✓ registry.execute('calculator', {{'operation': 'multiply', 'a': 12, 'b': 4}}) -> {result}")
    assert result == 48.0

    print("\nRegistry integration test passed successfully! 🎉")


if __name__ == "__main__":
    test_registry_integration()