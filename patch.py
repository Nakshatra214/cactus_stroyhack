import os

# Update scene_builder.py
sb_path = r"backend\video\scene_builder.py"
with open(sb_path, "r", encoding="utf-8") as f:
    sb_text = f.read()

sb_text = sb_text.replace(
    '["ffmpeg", "-version"]',
    r'[r"C:\Users\Nilima Gautam\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe", "-version"]'
)
sb_text = sb_text.replace(
    'cmd = [\n            "ffmpeg",',
    r'cmd = [\n            r"C:\Users\Nilima Gautam\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe",'
)
sb_text = sb_text.replace(
    'cmd = [\r\n            "ffmpeg",',
    r'cmd = [\r\n            r"C:\Users\Nilima Gautam\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe",'
)

with open(sb_path, "w", encoding="utf-8") as f:
    f.write(sb_text)

# Update frontend/app/page.tsx
page_path = r"frontend\app\page.tsx"
with open(page_path, "r", encoding="utf-8") as f:
    page_text = f.read()

page_text = page_text.replace(
    "import { useState, useCallback } from 'react';",
    "import { useState, useCallback, useEffect } from 'react';"
)

old_pattern = """    }, [file, textContent, title, router, setProject, setScenes, setScriptData, setPipelineStep]);

    return ("""
new_pattern = """    }, [file, textContent, title, router, setProject, setScenes, setScriptData, setPipelineStep]);

    // Auto-trigger generation right after a file is selected via Dropzone
    useEffect(() => {
        if (file && !isProcessing) {
            handleProcess();
        }
    }, [file]); // Exclude handleProcess/isProcessing to prevent re-triggering loop

    return ("""
page_text = page_text.replace(old_pattern.replace("\r", ""), new_pattern)
page_text = page_text.replace(old_pattern, new_pattern)

with open(page_path, "w", encoding="utf-8") as f:
    f.write(page_text)

print("Patched successfully!")
