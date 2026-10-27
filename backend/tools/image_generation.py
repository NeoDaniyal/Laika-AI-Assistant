import os
import time
import urllib.parse
import requests

from typing import Any, Dict
from dotenv import load_dotenv
from backend.tools.base import Tool

load_dotenv()

IMAGE_OUTPUT_DIR = "generated_images"
os.makedirs(IMAGE_OUTPUT_DIR, exist_ok=True)


class ImageGenerationTool(Tool):
    """Generate images using the Pollinations API."""

    @property
    def name(self) -> str:
        return "image_generation"

    @property
    def description(self) -> str:
        return "Generate an image from a descriptive text prompt."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Description of the image to generate.",
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
        prompt = arguments.get("prompt", "").strip()
        width = int(arguments.get("width", 1024))
        height = int(arguments.get("height", 1024))

        if not prompt:
            raise ValueError("The image prompt cannot be empty.")

        if not (256 <= width <= 2048 and 256 <= height <= 2048):
            raise ValueError("Image dimensions must be between 256 and 2048.")

        api_key = os.getenv("POLLINATIONS_API_KEY")

        if not api_key:
            raise RuntimeError(
                "POLLINATIONS_API_KEY is missing from your environment."
            )

        encoded_prompt = urllib.parse.quote(prompt, safe="")

        url = f"https://gen.pollinations.ai/image/{encoded_prompt}"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "image/*",
        }

        params = {
            "width": width,
            "height": height,
            "model": "flux",
            "nologo": "true",
            "seed": int(time.time()),
        }

        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=120,
            )

            if response.status_code != 200:
                raise RuntimeError(
                    f"Pollinations returned HTTP {response.status_code}: "
                    f"{response.text[:500]}"
                )

            content_type = response.headers.get("Content-Type", "")

            if not content_type.startswith("image/"):
                raise RuntimeError(
                    f"Expected image data, received: {content_type}"
                )

            timestamp = int(time.time())
            filename = f"generated_{timestamp}.png"
            file_path = os.path.join(IMAGE_OUTPUT_DIR, filename)

            with open(file_path, "wb") as image_file:
                image_file.write(response.content)

            return (
                "Image generated successfully and saved at: "
                f"{file_path}"
            )

        except requests.RequestException as exc:
            raise RuntimeError(
                f"Pollinations request failed: {exc}"
            ) from exc