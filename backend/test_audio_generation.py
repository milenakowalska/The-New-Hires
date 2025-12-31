import os
import asyncio
import sys

# Add current directory to path so we can import from api
sys.path.append(os.getcwd())

try:
    from api.ai_utils import generate_voice
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

async def test_generation():
    print("--- Testing gTTS generation ---")
    text = "Hello, this is a test of the emergency broadcast system."
    print(f"Generating voice for text: '{text}'")
    
    try:
        audio_bytes = await generate_voice(text, "Sarah")
        print(f"Generated {len(audio_bytes)} bytes.")
        
        if len(audio_bytes) == 0:
            print("ERROR: Generated 0 bytes.")
            return

        # Determine path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        static_dir = os.path.join(current_dir, "static")
        os.makedirs(static_dir, exist_ok=True)
        
        filename = "test_audio_gen.mp3"
        filepath = os.path.join(static_dir, filename)
        
        print(f"Writing to: {filepath}")
        
        with open(filepath, "wb") as f:
            f.write(audio_bytes)
            
        if os.path.exists(filepath):
            print(f"SUCCESS: File created at {filepath}")
            print(f"File size: {os.path.getsize(filepath)} bytes")
        else:
            print("ERROR: File not found after writing!")
            
    except Exception as e:
        print(f"EXCEPTION during generation: {e}")

if __name__ == "__main__":
    asyncio.run(test_generation())
