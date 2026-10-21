import os
import time
import urllib.parse
import requests
from typing import Any, Dict
from backend.tools.base import Tool

IMAGE_OUTPUT_DIR = "generated_images"
os.makedirs(IMAGE_OUTPUT_DIR, exist_ok=True)


class ImageGenerationTool(Tool):
    """Tool for generating images from text prompts using Pollinations API with retry handling."""

    @property
    def name(self) -> str:
        return "image_generation"

    @property
    def description(self) -> str:
        return "Generate a static image based on a descriptive text prompt."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "A detailed text description of the desired image.",
                },
                "width": {
                    "type": "integer",
                    "default": 1024,
                },
                "height": {
                    "type": "integer",
                    "default": 1024,
                },
            },
            "required": ["prompt"],
        }

    def execute(self, arguments: Dict[str, Any]) -> str:
        prompt = arguments.get("prompt")
        width = int(arguments.get("width", 1024))
        height = int(arguments.get("height", 1024))

        if not prompt:
            raise ValueError("Argument 'prompt' is required for image_generation.")

        encoded_prompt = urllib.parse.quote(prompt)
        
        # Try primary URL, then fallback to model parameters or smaller size if overloaded
        urls_to_try = [
            f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&seed={int(time.time())}",
            f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&nologo=true&model=flux",
        ]

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        last_error = None
        for attempt, url in enumerate(urls_to_try, start=1):
            try:
                # Add retry loop
                for retry in range(2):
                    response = requests.get(url, headers=headers, timeout=30)
                    if response.status_code == 200:
                        timestamp = int(time.time())
                        safe_prompt = "".join([c for c in prompt[:20] if c.isalnum()]).strip()
                        filename = f"generated_{timestamp}_{safe_prompt}.png"
                        file_path = os.path.join(IMAGE_OUTPUT_DIR, filename)

                        with open(file_path, "wb") as f:
                            f.write(response.content)

                        return f"Image generated successfully and saved at: {file_path}"
                    
                    time.sleep(2)  # Short pause before retry
            except Exception as e:
                last_error = e

        raise RuntimeError(
            f"Pollinations AI service is currently overloaded (503). "
            f"Please try again in a few moments. Details: {str(last_error or 'Server Unavailable')}"
        )