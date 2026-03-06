import os
import sys
from google import genai
from config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)
try:
    print("Testing imagen-4.0-generate-001...")
    result = client.models.generate_images(
        model='imagen-4.0-generate-001',
        prompt="A beautiful cactus in the desert"
    )
    print("SUCCESS 4.0-001")
except Exception as e:
    with open("error.txt", "w") as f:
        f.write(str(e))
