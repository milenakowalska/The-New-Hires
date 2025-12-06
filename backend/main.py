from dotenv import load_dotenv
import os

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api import auth, tickets, messages, onboarding, webhooks, ai, features, activity, gamification
import socketio
import os

app = FastAPI(title="The New Hire API", description="API for The New Hire Job Simulator")

# Create static directory if it doesn't exist
os.makedirs("static", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Specific origin for credentials support
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO
from api.socket_instance import sio
# Mount at /socket.io so uvicorn main:app works
app.mount("/socket.io", socketio.ASGIApp(sio, socketio_path=""))

app.include_router(auth.router, prefix="/api")
app.include_router(tickets.router, prefix="/api")
app.include_router(messages.router, prefix="/api")
app.include_router(onboarding.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(features.router, prefix="/api")
app.include_router(activity.router, prefix="/api")
app.include_router(gamification.router, prefix="/api")

# We need to expose app_sio for Uvicorn to run if we want SIO to work on root
# But usually we wrap the app

@app.get("/")
async def root():
    return {"message": "Welcome to The New Hire API"}
