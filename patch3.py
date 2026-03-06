import os

# Update backend/video/video_merger.py
merger_path = r"backend\video\video_merger.py"
with open(merger_path, "r", encoding="utf-8") as f:
    merger_text = f.read()

merger_text = merger_text.replace(
    'cmd = [\n            "ffmpeg",',
    r'cmd = [\n            r"C:\Users\Nilima Gautam\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe",'
)
merger_text = merger_text.replace(
    'cmd = [\r\n            "ffmpeg",',
    r'cmd = [\r\n            r"C:\Users\Nilima Gautam\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe",'
)

with open(merger_path, "w", encoding="utf-8") as f:
    f.write(merger_text)

print("Patch 3 applied to video_merger.py")
