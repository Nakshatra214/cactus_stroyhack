import os

# Update backend/video/scene_builder.py
# Fixing potential escape issues by using raw strings and forward slashes
sb_path = r"backend\video\scene_builder.py"
with open(sb_path, "r", encoding="utf-8") as f:
    text = f.read()

# Replace with the extremely safe fixed path
text = text.replace(
    'FFMPEG_PATH = "C:/Users/Nilima Gautam/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.0.1-full_build/bin/ffmpeg.exe"',
    'FFMPEG_PATH = r"C:\\Users\\Nilima Gautam\\AppData\\Local\\Microsoft\\WinGet\\Packages\\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\\ffmpeg-8.0.1-full_build\\bin\\ffmpeg.exe"'
)

with open(sb_path, "w", encoding="utf-8") as f:
    f.write(text)

# Update backend/video/video_merger.py
vm_path = r"backend\video\video_merger.py"
with open(vm_path, "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace(
    'FFMPEG_PATH = "C:/Users/Nilima Gautam/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.0.1-full_build/bin/ffmpeg.exe"',
    'FFMPEG_PATH = r"C:\\Users\\Nilima Gautam\\AppData\\Local\\Microsoft\\WinGet\\Packages\\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\\ffmpeg-8.0.1-full_build\\bin\\ffmpeg.exe"'
)

with open(vm_path, "w", encoding="utf-8") as f:
    f.write(text)

print("Final paths updated with raw strings for Windows.")
