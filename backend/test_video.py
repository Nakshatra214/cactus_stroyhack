import asyncio
from agents.visual_agent import _generate_placeholder
from agents.voice_agent import _generate_with_edge_tts
from video.scene_builder import build_scene_video

async def test():
    print("Generating image...")
    img = _generate_placeholder('Test scene for animation', 1, 999)
    print(f"Generated image: {img}")
    
    print("Generating voice with edge-tts...")
    aud = await _generate_with_edge_tts('Welcome to the story hack hackathon! This is a test video clip to verify the new zooming animation and the edge tts engine.', 1, 999, 'energetic')
    print(f"Generated audio: {aud}")
    
    print("Building scene video with FFmpeg...")
    vid = build_scene_video(img, aud, 1, 999)
    print(f"Generated Video: {vid}")

if __name__ == "__main__":
    asyncio.run(test())
