import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.tools import registry


def test_web_search():
    print("=== Testing WebSearchTool Registration ===")
    all_tools = registry.all()
    assert "web_search" in all_tools, "WebSearchTool is not registered!"
    print("✓ 'web_search' successfully found in registry.")

    print("\n=== Testing WebSearchTool Execution ===")
    results = registry.execute("web_search", {"query": "FastAPI python web framework", "max_results": 2})
    print(f"Results returned: {len(results)}")
    print(results)
    assert len(results) > 0
    print("\n✓ WebSearchTool executed successfully! 🎉")


if __name__ == "__main__":
    test_web_search()