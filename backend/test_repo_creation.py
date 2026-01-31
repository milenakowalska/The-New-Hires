import os
import requests
import time
from dotenv import load_dotenv

# Load .env manually
load_dotenv()

TOKEN = os.getenv("SYSTEM_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")

if not TOKEN:
    print("❌ No token found in .env")
    exit(1)

repo_name = f"test-repo-{int(time.time())}"
print(f"Testing creation of repo: {repo_name}...")

try:
    res = requests.post("https://api.github.com/user/repos", headers={
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }, json={
        "name": repo_name,
        "private": False,
        "description": "Probe repo to test token permissions",
        "auto_init": True
    })
    
    if res.status_code == 201:
        print(f"✅ SUCCESS! Created repo: {res.json()['html_url']}")
        print("❗ Deleting probe repo now...")
        
        # Cleanup
        owner = res.json()['owner']['login']
        del_res = requests.delete(f"https://api.github.com/repos/{owner}/{repo_name}", headers={
            "Authorization": f"token {TOKEN}"
        })
        if del_res.status_code == 204:
            print("✅ Probe repo deleted.")
        else:
            print(f"⚠️ Failed to delete probe repo: {del_res.status_code}")
    else:
        print(f"❌ FAILED to create repo: {res.status_code}")
        print(res.text)

except Exception as e:
    print(f"❌ Exception: {e}")
