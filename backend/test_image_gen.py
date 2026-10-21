import sys
import os
from dotenv import load_dotenv

# Ensure root backend directory is available in Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.tools import registry

def test_eden_ai_image_generation():
    print("=== Testing ImageGenerationTool Registration ===")
    all_tools = registry.all()
    assert "image_generation" in all_tools, "ImageGenerationTool is not registered!"
    print("✓ 'image_generation' successfully found in registry.")

    print("\n=== Testing Eden AI ImageGenerationTool Execution ===")
    
    # Check if Eden AI API key is configured
    load_dotenv()
    if not os.getenv("EDEN_AI_API_KEY"):
        print("❌ EDEN_AI_API_KEY is missing in .env file. Cannot run execution test.")
        return

    # Prompt and parameters for testing
    prompt = "A futuristic city with flying cars at sunset, highly detailed, digital art"
    provider = "stabilityai"
    
    print(f"Generating image via Eden AI ({provider}) for prompt:\n'{prompt}'...")

    try:
        # 1. Execute tool via generic registry interface
        result = registry.execute(
            "image_generation",
            {
                "prompt": prompt,
                "provider": provider,
                "resolution": "1024x1024"
            }
        )
        print(f"\n✓ Tool Output: {result}")
        
        # 2. Extract path and verify saved file
        file_path = result.split(": ")[-1].strip()
        
        assert os.path.exists(file_path), f"Generated image file not found at {file_path}!"
        file_size = os.path.getsize(file_path)
        assert file_size > 1000, f"Generated file {file_path} is suspiciously small ({file_size} bytes)."
        
        print(f"✓ File verified at {file_path} (Size: {file_size / 1024:.2f} KB)")
        print("\nEden AI ImageGenerationTool test passed successfully! 🎉")

    except Exception as e:
        print(f"\n❌ Test Failed with Error: {str(e)}")

if __name__ == "__main__":
    test_eden_ai_image_generation()