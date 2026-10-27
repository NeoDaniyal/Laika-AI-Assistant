from backend.tools.base import Tool
from backend.tools.registry import ToolRegistry, registry
from backend.tools.calculator import CalculatorTool
from backend.tools.web_search import WebSearchTool
from backend.tools.image_generation import ImageGenerationTool
from backend.tools.image_to_image import ImageToImageTool
from backend.tools.video_generation import VideoGenerationTool

registry.register(CalculatorTool())
registry.register(WebSearchTool())
registry.register(ImageGenerationTool())
registry.register(ImageToImageTool())
registry.register(VideoGenerationTool())
__all__ = ["Tool", "ToolRegistry", "registry", "CalculatorTool", "WebSearchTool", "ImageGenerationTool", "ImageToImageTool", "VideoGenerationTool"]