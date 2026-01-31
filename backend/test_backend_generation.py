
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_generate_repo():
    print("Triggering repo generation via Backend API...")
    
    # login first to get user id (or just assume user_id=8 from logs)
    # The logs showed user_id=8 active.
    user_id = 8 
    
    payload = {
        "project_description": "A task management system",
        "backend_stack": "Python FastAPI",
        "frontend_stack": "React"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/onboarding/generate-repo?user_id={user_id}", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_generate_repo()
