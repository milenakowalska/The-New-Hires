import os
import requests
from dotenv import load_dotenv

# Load .env manually to be sure
load_dotenv()

TOKEN = os.getenv("SYSTEM_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")
USERNAME = os.getenv("SYSTEM_GITHUB_USERNAME")

print(f"Token found: {'Yes' if TOKEN else 'No'}")
print(f"Username from env: {USERNAME}")

if not TOKEN:
    print("❌ No token found in .env")
    exit(1)

print("Testing token against GitHub API...")
try:
    # 1. Check User
    res = requests.get("https://api.github.com/user", headers={
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    })
    
    if res.status_code == 200:
        data = res.json()
        print(f"✅ Authenticated as: {data['login']}")
        print(f"   Scopes: {res.headers.get('X-OAuth-Scopes', 'None')}")
        
        if USERNAME and data['login'].lower() != USERNAME.lower():
            print(f"⚠️ Warning: Env username '{USERNAME}' does not match token owner '{data['login']}'")
            
    else:
        print(f"❌ Authentication Failed: {res.status_code}")
        print(res.text)
        exit(1)

    # 2. Check Repo Creation Permission (dry run by checking access to user repos)
    res_repo = requests.get("https://api.github.com/user/repos?per_page=1", headers={
        "Authorization": f"token {TOKEN}"
    })
    if res_repo.status_code == 200:
         print("✅ Can list repositories (Read Access confirmed)")
    else:
         print(f"⚠️ Failed to list repos: {res_repo.status_code}")

except Exception as e:
    print(f"❌ Exception: {e}")
