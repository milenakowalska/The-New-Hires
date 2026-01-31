import requests
import sys

BASE_URL = "http://localhost:8000/api/auth"

def test_auth():
    username = "testuser_v1"
    password = "password123"
    
    # 1. Register
    print(f"Testing Registration for {username}...")
    try:
        reg_res = requests.post(f"{BASE_URL}/register", json={"username": username, "password": password})
        if reg_res.status_code == 200:
            print("✅ Registration Successful")
            print(reg_res.json())
        elif reg_res.status_code == 400 and "already registered" in reg_res.text:
             print("⚠️ User already exists, proceeding to login...")
        else:
            print(f"❌ Registration Failed: {reg_res.status_code} - {reg_res.text}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Connection Error during Registration: {e}")
        sys.exit(1)

    # 2. Login
    print(f"\nTesting Login for {username}...")
    try:
        login_res = requests.post(f"{BASE_URL}/login", json={"username": username, "password": password})
        if login_res.status_code == 200:
            print("✅ Login Successful")
            data = login_res.json()
            token = data.get("access_token")
            print(f"Token received: {token[:15]}...")
            
            # 3. Verify /me
            print("\nTesting /me endpoint...")
            me_res = requests.get(f"{BASE_URL}/me", headers={"Authorization": f"Bearer {token}"})
            if me_res.status_code == 200:
                print("✅ /me Endpoint Successful")
                print(me_res.json())
            else:
                 print(f"❌ /me Failed: {me_res.status_code} - {me_res.text}")
        else:
            print(f"❌ Login Failed: {login_res.status_code} - {login_res.text}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Connection Error during Login: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_auth()
