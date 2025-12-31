import sys
import os

print(f"CWD: {os.getcwd()}")
print("sys.path:")
for p in sys.path:
    print(f"  {p}")

print("\nAttempting to import api.features...")
try:
    import api.features
    print(f"SUCCESS: api.features loaded from: {api.features.__file__}")
    
    # Check content of the file
    with open(api.features.__file__, 'r') as f:
        content = f.read()
        if "logging.info" in content:
             print("VERIFICATION: File contains 'logging.info' (NEW CODE)")
        else:
             print("VERIFICATION: File DOES NOT contain 'logging.info' (OLD CODE)")
             
        if "time.time()" in content:
             print("VERIFICATION: File contains 'time.time()' (NEW CODE)")
        else:
             print("VERIFICATION: File DOES NOT contain 'time.time()' (OLD CODE)")

except ImportError as e:
    print(f"ERROR: Could not import api.features: {e}")
