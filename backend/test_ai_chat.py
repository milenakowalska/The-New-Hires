import requests
import sys

BASE_URL = "http://localhost:8000/api"

# Use the testuser_v1 created earlier or register a new one
username = "testuser_ai_debug"
password = "password123"

def test_ai():
    # 1. Register/Login
    print("Logging in...")
    auth_res = requests.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password})
    if auth_res.status_code != 200:
        print("User not found, registering...")
        auth_res = requests.post(f"{BASE_URL}/auth/register", json={"username": username, "password": password})
    
    if auth_res.status_code != 200:
        print(f"Auth failed: {auth_res.text}")
        sys.exit(1)
        
    token = auth_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Send Message
    msg = "Hello team, how is it going?"
    print(f"Sending message: '{msg}'")
    res = requests.post(f"{BASE_URL}/messages", headers=headers, json={
        "channel": "general",
        "content": msg
    })
    
    if res.status_code == 200:
        print("Message sent successfully.")
        print(res.json())
    else:
        print(f"Failed to send message: {res.text}")

if __name__ == "__main__":
    test_ai()
