import asyncio
import os
import sys

# Change to backend dir to access modules correctly
os.chdir(r"c:\Users\Nilima Gautam\Desktop\git hub\cactus_stroyhack\backend")
sys.path.append(os.getcwd())

from database.db import async_session
from services.script_service import generate_video_script
from services.scene_service import create_scenes_from_script
from services.video_service import generate_all_visuals, generate_all_voices, build_all_scene_videos, build_final_video
from database.models import Project

print("Imports successful")

async def run_pipeline():
    print("Starting pipeline...")
    async with async_session() as db:
        print("DB session created")
        # Create a mock project
        project = Project(title="Animation Test", original_content="Cactus is a great plant. It survives in the desert. It is green and spiky.", status="created")
        db.add(project)
        await db.commit()
        await db.refresh(project)
        
        print(f"Created project {project.id}")
        
        print("Generating script...")
        script_data = await generate_video_script(project.original_content)
        
        print(f"Creating scenes... found {len(script_data.get('scenes', []))} scenes")
        await create_scenes_from_script(db, project.id, script_data)
        
        print("Generating visuals...")
        await generate_all_visuals(db, project.id)
        
        print("Generating voices...")
        await generate_all_voices(db, project.id)
        
        print("Building scene videos...")
        await build_all_scene_videos(db, project.id)
        
        print("Building final video...")
        final_url = await build_final_video(db, project.id)
        
        print(f"Final Video URL: {final_url}")

print("Running asyncio...")
asyncio.run(run_pipeline())
print("Pipeline finished")
