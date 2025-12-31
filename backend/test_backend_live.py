import requests
import json

try:
    print("Testing http://localhost:8000/api/features/standups/daily-update-v2")
    response = requests.get("http://localhost:8000/api/features/standups/daily-update-v2")
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Response Data:")
        print(json.dumps(data, indent=2))
        
        url = data.get("audio_url", "")
        if "coworker_" in url:
            if "_" in url.split("coworker_")[-1] and len(url.split("_")[-1].split(".")[0]) > 6:
                 print("\nVERIFICATION: Filename uses timestamp (NEW CODE)")
            else:
                 print("\nVERIFICATION: Filename looks like random int (OLD CODE)")
    else:
        print("Error: Request failed")

except Exception as e:
    print(f"Exception: {e}")
