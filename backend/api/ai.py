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
    if not ELEVENLABS_API_KEY:
        return {"audio_url": "https://storage.googleapis.com/mock-bucket/mock-audio.mp3"}
        
    # Call ElevenLabs API
    # Return mock URL for now
    return {"audio_url": "https://storage.googleapis.com/mock-bucket/generated-audio.mp3"}
