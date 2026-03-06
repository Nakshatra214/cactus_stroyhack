import os
import asyncio
from config import settings
from agents.visual_agent import _generate_with_gemini

print("TESTING GEMINI WITH KEY:", settings.GEMINI_API_KEY[:5] + "...")
try:
    path = _generate_with_gemini("A beautiful cactus in the desert", 0, 999)
    print("Result path:", path)
    if os.path.exists("./" + path):
        print("Image successfully saved!")
    elif path.startswith("/storage") and "placeholder" not in path:
        print("Returned a path but couldn't verify local file.")
except Exception as e:
    print("Exception occurred:", e)
