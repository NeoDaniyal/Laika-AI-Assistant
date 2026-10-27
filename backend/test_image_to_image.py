
from backend.tools.image_to_image import ImageToImageTool

tool = ImageToImageTool()

result = tool.execute({
    "image_url": "generated_images/generated_1792994449.png",
    "prompt": (
        "Change the background to a snowy forest. "
        "Preserve the original cat's appearance, pose, and identity."
    ),
})

print(result)
