from google import genai
from fastapi import HTTPException
import os
import json
import asyncio
from gtts import gTTS
import io
import httpx

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY, http_options={'api_version': 'v1beta'})

async def analyze_diff(diff: str, pr_title: str) -> dict:
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API Key not configured")

    try:

        
        prompt = f"""
        Act as a Passionate, Senior Human Developer. Do NOT sound like an AI. 
        
        PR Title: {pr_title}
        
        **Instructions:**
        1. **Be Opinionated**: Write in the first person ("I"). Tell me what you *honestly* think.
        2. **Be Personal**: "I love how you did X" or "This part makes me nervous".
        3. **Comprehensive Review**: Do NOT be brief. I want a detailed analysis.
        4. **Clean Code Focus**: If there are no bugs, focus entirely on readability/elegance.
        
        **Your Output:**
        Return a JSON object with this structure:
        {{
            "summary": "Your personal take on this PR. 3-4 sentences. Be thorough.",
            "comments": [
                {{
                    "file": "filename",
                    "line": line_number_int,
                    "category": "Opinion|Security|Performance|Pro-Tip",
                    "message": "Your personal thought on this specific line.",
                    "suggestion": "Optional code snippet if you have a better idea"
                }}
            ]
        }}
        
        Diff:
        {diff}
        """
        
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )
        
        content = response.text
        # Clean up potential markdown formatting
        if content.strip().startswith("```json"):
            content = content.strip()[7:]
        if content.strip().startswith("```"):
            content = content.strip()[3:]
        if content.strip().endswith("```"):
            content = content.strip()[:-3]
            
        return json.loads(content)
        
    except Exception as e:
        print(f"Gemini Error: {e}")
        return {"summary": f"Yikes! I hit a snag while reading your code. (Error: {str(e)})", "comments": []}

async def fetch_pr_diff(pr_url: str) -> str:
    """
    Fetches the diff of a GitHub PR. Validates URL and checks for existence.
    """
    if "github.com" not in pr_url or "/pull/" not in pr_url:
        return "Error: Invalid GitHub PR URL. Please provide a link like `https://github.com/owner/repo/pull/123`."

    diff_url = pr_url
    if not diff_url.endswith(".diff"):
        diff_url = f"{diff_url}.diff"
        
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(diff_url, follow_redirects=True)
            
            if response.status_code == 404:
                return "Error: Repo not found or private. I can only review public repositories."
            
            if response.status_code == 200:
                return response.text
            else:
                return f"Error fetching diff: HTTP {response.status_code}"
    except Exception as e:
        return f"Error fetching diff: {str(e)}"

async def process_pr_link(pr_url: str) -> str:
    """
    Fetches diff and generates a detailed review summary for chat.
    """
    diff_text = await fetch_pr_diff(pr_url)
    
    if diff_text.startswith("Error"):
        # Explicitly return the error message to the user
        return f"⚠️ {diff_text}"
        
    # If the diff is huge, truncate it
    if len(diff_text) > 40000:
        diff_text = diff_text[:40000] + "...(truncated)"
    
    # Analyze the diff
    analysis = await analyze_diff(diff_text, f"PR: {pr_url}")
    
    summary = analysis.get("summary", "No summary provided.")
    comments = analysis.get("comments", [])
    
    message = f"## 🕵️ AI Code Review\n**PR:** {pr_url}\n\n"
    message += f"### 💭 Reviewer's Opinion\n{summary}\n\n"
    
    if comments:
        message += "### 🔍 Key Findings\n"
        # Prioritize security, performance, opinion, then pro-tips
        sorted_comments = sorted(comments, key=lambda x: 0 if x.get('category') == 'Security' else 1 if x.get('category') == 'Performance' else 2 if x.get('category') == 'Opinion' else 3)
        
        for comment in sorted_comments[:6]:
            icon = "🗣️"
            cat = comment.get('category', 'Opinion')
            
            if cat == 'Security': icon = "🔒"
            elif cat == 'Performance': icon = "⚡"
            elif cat == 'Opinion': icon = "💬"
            elif 'Pro-Tip' in cat: icon = "💡"
            
            message += f"- {icon} **{comment.get('file')}** (Line {comment.get('line')}): {comment.get('message')}\n"
            if comment.get('suggestion'):
                 message += f"  > Suggestion: `{comment.get('suggestion')}`\n"
    
        if len(comments) > 6:
            message += f"\n*...and {len(comments) - 6} more improvements found.*"
    elif "Error" in summary or "Yikes" in summary:
        message += "\n❌ **Review Interrupted**: See my opinion above for what went wrong."
    else:
        message += "✅ **Code looks clean!** I honestly couldn't find anything to complain about."

    return message

# Voice Mapping
VOICE_MAP = {
    "Sarah": "nova",
    "Mike": "onyx",
    "Alex": "echo",
    "Emily": "shimmer",
    "David": "fable"
}

async def generate_coworker_update(name: str, role: str, context: str) -> str:
    if not GEMINI_API_KEY:
        return f"I am working on {context}. No blockers."
        
    try:
        prompt = f"""
        Act as {name}, a {role} at a tech startup. Give a very short (1-2 sentences) daily standup update.
        Context: {context}.
        Tone: Casual, slightly tired but professional.
        """
        
        response = client.models.generate_content(model=MODEL, contents=prompt)
        return response.text
    except Exception as e:
        print(f"Gemini generation error: {e}")
        return f"I am working on {context}. No blockers."

async def generate_voice(text: str, name: str) -> bytes:
    # We can use gTTS even without an API key config check, but keeping alignment with others
    # Using a simple lock or executor might be needed if this blocks, but gTTS is sync.
    # We'll run it in a thread to keep async happy.
    
    def _create_audio():
        # Map names to accents/tlds if desired, e.g. 'com.au' for Australian
        tld = "com"
        if name == "Mike": tld = "co.uk"
        if name == "Sarah": tld = "com.au"
        
        tts = gTTS(text=text, lang='en', tld=tld)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()

    try:
        loop = asyncio.get_event_loop()
        audio_bytes = await loop.run_in_executor(None, _create_audio)
        return audio_bytes
    except Exception as e:
        print(f"Voice generation failed: {e}")
        return b''

async def transcribe_audio(file_path: str) -> str:
    if not GEMINI_API_KEY:
        return "Mock transcription: I worked on the login feature."
        
    try:
        import time
        # Uploading file to Gemini
        # Determine MIME type
        mime_type = "audio/webm"
        if file_path.endswith(".mp3"):
            mime_type = "audio/mp3"
        elif file_path.endswith(".wav"):
            mime_type = "audio/wav"
            
        print(f"Transcribing {file_path} with mime_type {mime_type}...")
        
        myfile = client.files.upload(file=file_path, config={'mime_type': mime_type})
        
        # Wait for file to be active (required for audio/video)
        import time
        for i in range(10): # Max 20 seconds
            myfile = client.files.get(name=myfile.name)
            if myfile.state.name == "ACTIVE":
                break
            if myfile.state.name == "FAILED":
                raise Exception(f"File processing failed in Gemini: {myfile.name}")
            print(f"Waiting for file {myfile.name} to be ACTIVE... current state: {myfile.state.name}")
            await asyncio.sleep(2)
        else:
            raise Exception("Timeout waiting for file to be ACTIVE")

        result = client.models.generate_content(model=MODEL, contents=[myfile, "Transcribe this audio file accurately. Return ONLY the transcription text, nothing else."])
        return result.text
    except Exception as e:
        import traceback
        print(f"Transcription failed: {str(e)}")
        print(traceback.format_exc())
        return "Error transcribing audio."

async def generate_project_with_bugs(project_description: str, backend_stack: str = "Vanilla JS", frontend_stack: str = "Vanilla JS") -> dict:
    """
    Generate a professional-grade web project with intentional bugs based on user's description and tech stack.
    Returns files, bugs list, and ticket descriptions.
    """
    if not GEMINI_API_KEY:
        # Return a simple fallback project
        return {
            "project_name": "my-web-app",
            "repo_name": "my-web-app-simulation",
            "is_fallback": True,
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
    
    prompt = f"""You are a code generator that creates professional-grade web projects with INTENTIONAL BUGS for training purposes.
    
    **Project Goal:** {project_description}
    **Backend Stack:** {backend_stack}
    **Frontend Stack:** {frontend_stack}
    
    Generate a project that indeed implements (at least, partially) what the goal says. Do NOT just provide a basic structure.
    
    **Requirements:**
    1. **Complexity:** Create a multi-file project with clear separation of concerns.
    2. **Realism:** Use standard directory structures and best practices for the chosen stacks.
    3. **Implementation:** Actually implement several core features (e.g., if a weather app, include logic for fetching and displaying data, even if mocked or buggy).
    4. **CRITICAL: local_run.md (REQUIRED):** You MUST create an additional file named `local_run.md` in the root of the project. This file MUST contain:
       - PREREQUISITES: Software needed (Node.js, Python, etc.).
       - SETUP COMMANDS: Commands to install dependencies.
       - START COMMAND: The command to run the application.
       - This is where ALL local running instructions MUST reside.
    5. **MANDATORY: Dependency Management:** You MUST include the appropriate dependency file (e.g., `package.json`, `requirements.txt`, `pom.xml`, etc.).
    6. **Intentional Bugs:** Include 8-12 realistic, tricky, yet fixable bugs (logic errors, minor syntax issues, configuration mistakes).
    7. **Jira Tickets:** Create corresponding Jira-style tickets for each bug/feature.
    
    **Output Specification:**
    Return a JSON object with this EXACT structure:
    {{
        "project_name": "short-project-name",
        "repo_name": "short-project-name-simulation",
        "files": {{
            "path/to/file1.ext": "full content",
            "path/to/file2.ext": "full content",
            ...
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
    
    **Critical Guidelines:**
    - Use the correct file extensions and paths for the chosen stacks.
    - Include comments in the code explaining the intended behavior but marking bugs (e.g., "// BUG: Needs investigation").
    - Spread tickets across 7 days.
    - The repository MUST be functional once the bugs are fixed.
    """

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )
        
        content = response.text
        # Clean up potential markdown formatting
        if content.strip().startswith("```json"):
            content = content.strip()[7:]
        if content.strip().startswith("```"):
            content = content.strip()[3:]
        if content.strip().endswith("```"):
            content = content.strip()[:-3]
            
        project_data = json.loads(content)
        project_data["is_fallback"] = False
        return project_data
    except Exception as e:
        print(f"Project generation error: {e}")
        # Return fallback on error
        return {
            "project_name": "simple-web-app",
            "repo_name": "simple-web-app-simulation",
            "is_fallback": True,
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


async def verify_standup_truthfulness(transcript: str, ticket_summary: str) -> dict:
    """
    Verifies if the standup transcript matches the actual ticket status summary.
    Returns score (change) and a reasoning message.
    """
    if not GEMINI_API_KEY:
        return {"score": 0, "reason": "AI verification skipped."}

    prompt = f"""
    You are a Truthfulness Verifier at a tech startup. 
    Compare the user's DAILY STANDUP TRANSCRIPT with their ACTUAL TICKET STATUS.
    
    STANDUP TRANSCRIPT:
    "{transcript}"
    
    ACTUAL TICKET STATUS:
    {ticket_summary}
    
    RULES:
    1. If the user claims they completed a ticket that is NOT 'DONE', 'IN_TEST' or 'PO_REVIEW', they are lying (-5 points). But if they talk about tasks that are not on the board, it means you cannot verify them, so ignore those information.
    2. If the user says they are working on something that matches their 'IN_PROGRESS' tickets, they are honest (+2 points).
    3. If they are vague, stay neutral (0 points).
    4. If they admit to being stuck, give them a minor honesty boost (+1 point).
    5. Return a JSON object: {{"score": int, "explanation": "Short reasoning"}}
    """

    try:
        response = client.models.generate_content(model=MODEL, contents=prompt)
        content = response.text
        # Clean up potential markdown formatting
        if content.strip().startswith("```json"):
            content = content.strip()[7:]
        if content.strip().startswith("```"):
            content = content.strip()[3:]
        if content.strip().endswith("```"):
            content = content.strip()[:-3]
            
        return json.loads(content)
    except Exception as e:
        print(f"Truthfulness Verification Error: {e}")
        return {"score": 0, "reason": "Snag in verification."}

async def analyze_video(file_path: str, duration: str = None) -> str:
    if not GEMINI_API_KEY:
        return "user uploaded sprint review, duration 0:00, AI analysis skipped - API Key missing"
        
    try:
        # Detect MIME type based on extension
        mime_type = "video/mp4" # Default
        if file_path.lower().endswith(".mov"):
            mime_type = "video/quicktime"
        elif file_path.lower().endswith(".webm"):
            mime_type = "video/webm"
            
        print(f"Uploading video {file_path} (mime: {mime_type}) to Gemini...")
        myfile = client.files.upload(file=file_path, config={'mime_type': mime_type})
        
        # Wait for file to be active
        for i in range(20): # Max 40 seconds for video
            myfile = client.files.get(name=myfile.name)
            if myfile.state.name == "ACTIVE":
                break
            if myfile.state.name == "FAILED":
                raise Exception(f"Video processing failed in Gemini: {myfile.name}")
            print(f"Waiting for video {myfile.name} to be ACTIVE... current state: {myfile.state.name}")
            await asyncio.sleep(2)
        else:
            raise Exception("Timeout waiting for video to be ACTIVE")

        duration_instruction = f"The duration of the video is {duration}. Use this value exactly." if duration else "Carefully observe the video playback/timeline to provide the most accurate duration possible."

        prompt = f"""
        You are a highly efficient assistant. Analyze the provided sprint review video.
        
        CRITICAL INSTRUCTIONS:
        1. Return ONLY the final summary sentence. 
        2. DO NOT include any introductory text, prefix, or conversational filler (e.g., "Okay", "Here is", "Sure").
        3. DO NOT use square brackets [] or parentheses () for any values.
        
        EXACT FORMAT REQUIRED:
        user uploaded sprint review, duration M:SS, user presented the feature FEATURE_NAME and explained TECHNICAL_ASPECT
        
        Note: {duration_instruction}
        """
        
        result = client.models.generate_content(model=MODEL, contents=[myfile, prompt])
        
        # Clean up the file from Gemini after analysis
        try:
            client.files.delete(name=myfile.name)
        except:
            pass
            
        return result.text.strip()
    except Exception as e:
        print(f"Video analysis failed: {str(e)}")
        return f"user uploaded sprint review, error: {str(e)}"
