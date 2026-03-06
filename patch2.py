import os

# Update frontend/lib/api.ts
api_path = r"frontend\lib\api.ts"
with open(api_path, "r", encoding="utf-8") as f:
    api_text = f.read()

api_text = api_text.replace("timeout: 120000,", "timeout: 600000,")

with open(api_path, "w", encoding="utf-8") as f:
    f.write(api_text)

# Update backend/video/scene_builder.py
sb_path = r"backend\video\scene_builder.py"
with open(sb_path, "r", encoding="utf-8") as f:
    sb_text = f.read()

sb_text = sb_text.replace(
    "-vf\", \"scale=8000:-1,zoompan=z='min(zoom+0.0005,1.5)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720\",",
    "-vf\", \"scale=8000:-1,zoompan=z='min(zoom+0.0005,1.5)':d=750:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720\","
)

with open(sb_path, "w", encoding="utf-8") as f:
    f.write(sb_text)

print("Patch 2 applied!")
