import os
import time
import uuid
import urllib.parse
import requests

from typing import Any, Dict
from dotenv import load_dotenv
from backend.tools.base import Tool

load_dotenv()

VIDEO_OUTPUT_DIR = "generated_videos"

class VideoGenerationTool(Tool):
    """Generating videos using Pollinations API."""
    @property
    def name(self)->str:
        return "video_generation"

    @property
    def description(self):
        return (
            "Generate a video from a descriptive text prompt"
            "Support choosing video duration."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties":{
                "prompt": {
                    "type": "string",
                    "description": "Description of the video to generate."
                },
                "duration": {
                    "type": "integer",
                    "description": "Requested video duration in seconds.",
                    "default": 4,
                },
                "model": {
                    "type": "string",
                    "description": "Pollinations video model identifier.",
                    "default": "google/veo-3.1-fast",
                },
            },
            "request": ["prompt"],
        }

    def execute(self, arguments: Dict[str, Any]) -> str:
        prompt = arguments.get("prompt", "").strip()
        duration = int(arguments.get("duration", 4))
        model = arguments.get(
            "model",
            "google/veo-3.1-fast",
        ).strip()

        if not prompt:
            raise ValueError("The video prompt cannot be empty.")

        if not (1<=duration<=20):
            raise ValueError(
                "Video duration must be 1 and 20 seconds."
                "The selected model may support smaller range."
            )

        if not model:
            raise ValueError("The video model cannot be empty.")

        api_key = os.getenv("POLLINATIONS_API_KEY")
        
        if not api_key:
            raise RuntimeError("POLLINATION API KEY IS MISSING OR NOT WORKING")
        
        encoded_prompt = urllib.parse.quote(prompt, safe="")
        url = f"https://gen.pollinations.ai/video/{encoded_prompt}"

        header = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "video/mp4",
        }

        params = {
            "model":model,
            "duration": duration,
        }

        filename = f"video_{int(time.time())}_{uuid.uuid4().hex[:8]}.mp4"
        file_path = os.path.join(VIDEO_OUTPUT_DIR, filename)
        temp_path = f"{file_path}.part"

        try:
            with requests.get(url, headers=header, params=params, timeout=(15,300), stream=True) as response:
                if response.status_code != 200:
                    error_body = response.text[:1000]
                    raise RuntimeError(
                        f"Pollination return HTTP"
                        f"{response.status_code}: {error_body}"
                    )
                content_type = response.headers.get("Content-Type: ", "").lower()

                if not content_type.startswith("video/"):
                    raise RuntimeError(
                        "Expected video data from Pollination"
                        f"but recieved Content-Type: {content_type}"
                    )
                bytes_written = 0

                with open(temp_path, "wb") as video_file:
                    for chunk in response.iter_content(chunk_size= 1024*1024):
                        if chunk:
                            video_file.write(chunk)
                            bytes_written += len(chunk)
                    if bytes_written == 0:
                        raise RuntimeError("Pollinations returned an empty video.")

                    os.replace(temp_path, file_path)
                return (f"Video generated successfully and saved at: {file_path}")
        except requests.RequestException as exc:
            raise RuntimeError(f"Pollinations video-generation request failed: {exc}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
