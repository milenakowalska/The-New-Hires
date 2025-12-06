import openai
from fastapi import HTTPException
import os
import json

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

async def analyze_diff(diff: str, pr_title: str) -> dict:
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API Key not configured")

    try:
        client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        prompt = f"""
        Act as a senior software engineer. Review the following code diff and provide constructive feedback.
        Return the response as a JSON object with a key "comments", which is a list of objects containing "file", "line", and "message".
        IMPORTANT: The "file" must be the filename as seen in the diff. The "line" must be the line number in the new file (right side of diff).
        
        PR Title: {pr_title}
        
        Diff:
        {diff}
        """
        
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        return json.loads(content)
        
    except Exception as e:
        print(f"OpenAI Error: {e}")
        # Return empty comments on error to avoid crashing the webhook
        return {"comments": []}

# Voice Mapping
VOICE_MAP = {
    "Sarah": "nova",
    "Mike": "onyx",
    "Alex": "echo",
    "Emily": "shimmer",
    "David": "fable"
}

async def generate_coworker_update(name: str, role: str, context: str) -> str:
    if not OPENAI_API_KEY:
        return f"I am working on {context}. No blockers."
        
    client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
    prompt = f"""
    Act as {name}, a {role} at a tech startup. Give a very short (1-2 sentences) daily standup update.
    Context: {context}.
    Tone: Casual, slightly tired but professional.
    """
    
    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

async def generate_voice(text: str, name: str) -> bytes:
    if not OPENAI_API_KEY:
        # Return empty bytes - frontend will handle this gracefully
        return b''
    
    try:
        client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
        voice = VOICE_MAP.get(name, "alloy")
        
        response = await client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        return response.content
    except Exception as e:
        print(f"Voice generation failed: {e}")
        # Return empty bytes on error - frontend will show skip button
        return b''

async def transcribe_audio(file_path: str) -> str:
    if not OPENAI_API_KEY:
        return "Mock transcription: I worked on the login feature."
        
    client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
    
    with open(file_path, "rb") as audio_file:
        transcript = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcript.text

async def generate_project_with_bugs(project_description: str) -> dict:
    """
    Generate a beginner-level web project with intentional bugs based on user's description.
    Returns files, bugs list, and ticket descriptions.
    """
    if not OPENAI_API_KEY:
        # Return a simple fallback project
        return {
            "project_name": "my-web-app",
            "repo_name": "my-web-app-simulation",
            "files": {
                "index.html": "<!DOCTYPE html><html><head><title>My App</title></head><body><h1>Hello World</h1></body></html>",
                "styles.css": "body { font-family: sans-serif; }",
                "app.js": "// TODO: Add functionality",
                "README.md": "# My Web App\n\nA simple web application."
            },
            "tickets": [
                {"title": "Add basic styling", "description": "The app needs better CSS styling", "type": "task", "priority": "MEDIUM", "story_points": 2},
                {"title": "Implement main feature", "description": "Add the core functionality", "type": "story", "priority": "HIGH", "story_points": 5}
            ]
        }
    
    client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
    
    prompt = f"""You are a code generator that creates beginner-level web projects with INTENTIONAL BUGS for training purposes.

User wants to build: {project_description}

Generate a simple HTML/CSS/JavaScript web application with these requirements:
1. Keep it simple and beginner-friendly (no frameworks, just vanilla HTML/CSS/JS)
2. Include 8-12 INTENTIONAL BUGS that a new developer would need to fix
3. Add TODO comments marking missing features
4. Create corresponding Jira-style tickets for each bug/feature

Return a JSON object with this EXACT structure:
{{
    "project_name": "short-project-name",
    "repo_name": "short-project-name-simulation",
    "files": {{
        "index.html": "full HTML content here",
        "styles.css": "full CSS content here", 
        "app.js": "full JavaScript content with bugs here",
        "README.md": "project readme"
    }},
    "tickets": [
        {{
            "title": "Short ticket title",
            "description": "Detailed description of what needs to be fixed/implemented",
            "type": "bug or story or task",
            "priority": "CRITICAL or HIGH or MEDIUM or LOW",
            "story_points": 1-5,
            "day": 1-7
        }}
    ]
}}

IMPORTANT:
- Make the bugs realistic but fixable by beginners
- Include comments in the code pointing to bugs like "// BUG: ..." 
- Spread tickets across 7 days (day 1 = most urgent)
- Project name should be lowercase with dashes, max 3-4 words
"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=4000
        )
        
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Project generation error: {e}")
        # Return fallback on error
        return {
            "project_name": "simple-web-app",
            "repo_name": "simple-web-app-simulation",
            "files": {
                "index.html": f"<!DOCTYPE html><html><head><title>{project_description}</title></head><body><h1>{project_description}</h1><p>TODO: Build this app</p></body></html>",
                "styles.css": "/* TODO: Add styles */\nbody { font-family: sans-serif; padding: 20px; }",
                "app.js": "// TODO: Implement functionality\nconsole.log('App loaded');",
                "README.md": f"# {project_description}\n\nA web application.\n\n## TODO\n- Add features\n- Fix bugs"
            },
            "tickets": [
                {"title": "Implement core features", "description": f"Build the main functionality for: {project_description}", "type": "story", "priority": "HIGH", "story_points": 5, "day": 1},
                {"title": "Add styling", "description": "Make the app look good with CSS", "type": "task", "priority": "MEDIUM", "story_points": 3, "day": 2},
                {"title": "Add error handling", "description": "Handle edge cases and errors", "type": "task", "priority": "MEDIUM", "story_points": 2, "day": 3}
            ]
        }

