import os
from google import genai
from config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)

try:
    print("Testing imagen-3.0-generate-001...")
    result = client.models.generate_images(
        model='imagen-3.0-generate-001',
        prompt="A beautiful cactus in the desert",
        config=genai.types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio="16:9",
            output_mime_type="image/png"
        )
    )
    print("SUCCESS 3.0-001")
except Exception as e:
    print("FAIL 3.0-001:", e)
    
try:
    print("Testing imagen-3.0-generate-002...")
    result = client.models.generate_images(
        model='imagen-3.0-generate-002',
        prompt="A beautiful cactus in the desert",
        config=genai.types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio="16:9",
            output_mime_type="image/png"
        )
    )
    print("SUCCESS 3.0-002")
except Exception as e:
    print("FAIL 3.0-002:", e)
    
try:
    print("Testing imagen-4.0-generate-001 with simple config...")
    result = client.models.generate_images(
        model='imagen-4.0-generate-001',
        prompt="A beautiful cactus in the desert",
        config=genai.types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio="16:9"
        )
    )
    print("SUCCESS 4.0-001")
except Exception as e:
    print("FAIL 4.0-001:", e)
