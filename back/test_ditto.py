import os
from dotenv import load_dotenv

# Load env vars BEFORE importing modules that use them
load_dotenv()

from ditto_client import ditto

def test_connection():
    print("Testing Ditto Connection...")
    print(f"URL: {os.getenv('DITTO_API_URL')}")
    
    # Try to write a test document
    test_data = {
        "test": True,
        "message": "Hello from Shavzak Backend!",
        "timestamp": "now"
    }
    
    print("Attempting to upsert to 'test_collection'...")
    result = ditto.upsert("test_collection", test_data)
    
    if result:
        print("✅ Success! Document written to Ditto.")
        print(result)
    else:
        print("❌ Failed to write to Ditto.")

if __name__ == "__main__":
    test_connection()
