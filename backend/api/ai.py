from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os

# import elevenlabs  # Mocking for now as per minimal requirements or use requests

router = APIRouter(prefix="/ai", tags=["ai"])

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

class CodeReviewRequest(BaseModel):
    diff: str
    pr_title: str

class AudioRequest(BaseModel):
    text: str
    voice_id: str = "21m00Tcm4TlvDq8ikWAM" # Rachel

@router.post("/review/generate")
async def generate_code_review(request: CodeReviewRequest):
    from .ai_utils import analyze_diff
    return await analyze_diff(request.diff, request.pr_title)

@router.post("/audio/generate")
async def generate_audio(request: AudioRequest):
    from .ai_utils import generate_voice
    import uuid
    
    # Generate unique filename
    filename = f"coworker_{uuid.uuid4().hex}.mp3"
    
    # Use absolute path to ensure we write to the correct static directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(current_dir)
    static_dir = os.path.join(backend_dir, "static")
    os.makedirs(static_dir, exist_ok=True)
    
    filepath = os.path.join(static_dir, filename)
    
    # Generate audio bytes
    audio_bytes = await generate_voice(request.text, "Sarah") # Default to Sarah for now or map voice_id
    
    if not audio_bytes:
         return {"audio_url": ""}

    # Save to static folder
    with open(filepath, "wb") as f:
        f.write(audio_bytes)
        
    # Return local URL
    # Assuming running on localhost:8000
    return {"audio_url": f"http://localhost:8000/static/{filename}"}
