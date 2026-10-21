from backend.tools.base import Tool
from backend.tools.registry import ToolRegistry, registry
from backend.tools.calculator import CalculatorTool
from backend.tools.web_search import WebSearchTool
from backend.tools.image_generation import ImageGenerationTool

registry.register(CalculatorTool())
registry.register(WebSearchTool())
registry.register(ImageGenerationTool())
__all__ = ["Tool", "ToolRegistry", "registry", "CalculatorTool", "WebSearchTool", "ImageGenerationTool"]