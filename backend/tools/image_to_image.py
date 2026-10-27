import base64
import os
import time
from pathlib import Path
from urllib.parse import urlparse, unquote
from typing import Any, Dict

import requests
from dotenv import load_dotenv

from backend.tools.base import Tool

PROJECT_ROOT = Path(__file__).resolve().parents[2]
IMAGE_OUTPUT_DIR = PROJECT_ROOT / "generated_images"
UPLOAD_DIR = PROJECT_ROOT / "uploads"
IMAGE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(PROJECT_ROOT / ".env")


class ImageToImageTool(Tool):
    """Edit an existing image using the Pollinations image-editing API."""

    @property
    def name(self) -> str:
        return "image_to_image"

    @property
    def description(self) -> str:
        return (
            "Edit an existing image while using it as the visual reference. "
            "Accepts an image path or URL and a description of the changes."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "image_url": {
                    "type": "string",
                    "description": (
                        "Local path to an existing image or an HTTPS image URL."
                    ),
                },
                "prompt": {
                    "type": "string",
                    "description": (
                        "Describe the changes while preserving the desired "
                        "parts of the original image."
                    ),
                },
            },
            "required": ["image_url", "prompt"],
        }

    def execute(self, arguments: Dict[str, Any]) -> str:
        image_ref = str(arguments.get("image_url", "")).strip()
        prompt = str(arguments.get("prompt", "")).strip()

        if not image_ref or not prompt:
            raise ValueError("Both image_url and prompt are required.")

        api_key = os.getenv("POLLINATIONS_API_KEY")
        if not api_key:
            raise RuntimeError("POLLINATIONS_API_KEY is not configured.")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json, image/*",
        }

        image_bytes = None
        content_type = None
        filename = "reference.png"

        parsed = urlparse(image_ref)

        # Handle HTTP URLs to images served by this Laika backend.
        if parsed.scheme in ("http", "https"):
            if parsed.scheme == "http":
                if parsed.hostname not in ("localhost", "127.0.0.1"):
                    raise ValueError(
                        "Remote image URLs must use HTTPS."
                    )

                allowed_prefixes = ("/generated_images/", "/uploads/")
                if not any(parsed.path.startswith(prefix) for prefix in allowed_prefixes):
                    raise ValueError(
                        "Only generated_images and uploads URLs are allowed over HTTP."
                    )

                # Decode URL-encoded characters (like spaces) from the path
                decoded_path = unquote(parsed.path)
                filename = Path(decoded_path).name

                # Determine correct local folder based on URL prefix
                if parsed.path.startswith("/uploads/"):
                    local_path = UPLOAD_DIR / filename
                else:
                    local_path = IMAGE_OUTPUT_DIR / filename

                if not local_path.is_file():
                    raise FileNotFoundError(
                        f"Reference image not found: {filename}"
                    )

                image_bytes = local_path.read_bytes()
                content_type = (
                    "image/jpeg" if local_path.suffix.lower() in (".jpg", ".jpeg")
                    else "image/webp" if local_path.suffix.lower() == ".webp"
                    else "image/png"
                )

            else:
                # Download the HTTPS reference image.
                with requests.get(
                    image_ref,
                    timeout=30,
                    stream=True,
                ) as response:
                    response.raise_for_status()
                    content_type = response.headers.get(
                        "Content-Type", ""
                    ).split(";")[0].lower()

                    if not content_type.startswith("image/"):
                        raise ValueError(
                            "The reference URL did not return an image."
                        )

                    image_bytes = response.content
                    decoded_path = unquote(parsed.path)
                    filename = Path(decoded_path).name or "reference.png"

        else:
            # Handle local paths, including Windows backslashes.
            normalized = image_ref.replace("\\", "/")
            supplied_path = Path(normalized)

            if not supplied_path.is_absolute():
                supplied_path = PROJECT_ROOT / supplied_path

            local_path = supplied_path.resolve()

            allowed_roots = [
                IMAGE_OUTPUT_DIR.resolve(),
                UPLOAD_DIR.resolve(),
                (PROJECT_ROOT / "uploaded_files").resolve(),
            ]

            if not any(
                local_path == root or root in local_path.parents
                for root in allowed_roots
            ):
                raise ValueError(
                    "Local reference images must be inside generated_images "
                    "or uploads."
                )

            if not local_path.is_file():
                raise FileNotFoundError(
                    f"Reference image not found: {local_path}"
                )

            image_bytes = local_path.read_bytes()
            filename = local_path.name
            content_type = (
                "image/jpeg" if local_path.suffix.lower() in (".jpg", ".jpeg")
                else "image/webp" if local_path.suffix.lower() == ".webp"
                else "image/png"
            )

        if not content_type or not content_type.startswith("image/"):
            raise ValueError("The reference file is not a supported image.")

        url = "https://gen.pollinations.ai/v1/images/edits"

        try:
            response = requests.post(
                url,
                headers=headers,
                data={
                    "prompt": prompt,
                    "model": "kontext",
                    "size": "1024x1024",
                },
                files={
                    "image": (
                        filename,
                        image_bytes,
                        content_type,
                    )
                },
                timeout=180,
            )

            if response.status_code != 200:
                raise RuntimeError(
                    f"Pollinations image editing failed "
                    f"(HTTP {response.status_code}): "
                    f"{response.text[:1000]}"
                )

            result_type = response.headers.get(
                "Content-Type", ""
            ).split(";")[0].lower()

            if result_type.startswith("image/"):
                result_bytes = response.content

            else:
                result = response.json()
                image_data = result["data"][0]

                if image_data.get("b64_json"):
                    result_bytes = base64.b64decode(
                        image_data["b64_json"]
                    )

                elif image_data.get("url"):
                    image_response = requests.get(
                        image_data["url"],
                        timeout=60,
                    )
                    image_response.raise_for_status()

                    if not image_response.headers.get(
                        "Content-Type", ""
                    ).startswith("image/"):
                        raise RuntimeError(
                            "The returned URL did not contain an image."
                        )

                    result_bytes = image_response.content

                else:
                    raise RuntimeError(
                        "The API response did not contain image data or a URL."
                    )

            output_name = f"edited_{int(time.time())}.png"
            output_path = IMAGE_OUTPUT_DIR / output_name
            output_path.write_bytes(result_bytes)

            return (
                "Image edited successfully and saved at: "
                f"{output_path}"
            )

        except requests.RequestException as exc:
            raise RuntimeError(
                f"Image editing request failed: {exc}"
            ) from exc