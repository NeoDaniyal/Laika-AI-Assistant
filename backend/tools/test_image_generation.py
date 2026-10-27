from backend.tools.image_generation import ImageGenerationTool

tool = ImageGenerationTool()

result = tool.execute({
    "prompt": "A small orange cat sitting beside a window",
    "width": 512,
    "height": 512,
})

print(result)