#!/usr/bin/env python3
"""
Test client for the relay server.
This script tests that the relay server properly forwards requests to your LLM API.
"""

import asyncio
import aiohttp
import json

async def test_relay_server():
    """Test the relay server by sending a sample chat completion request"""
    
    # Test data that matches what your frontend would send
    test_data = {
        "model": "default",
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "temperature": 0.7
    }
    
    try:
        # Send request to the relay server
        async with aiohttp.ClientSession() as session:
            print("Sending test request to relay server...")
            async with session.post('http://192.168.68.65:8080/chat/completions', 
                                  json=test_data) as response:
                
                print(f"Status Code: {response.status}")
                
                if response.status == 200:
                    # Success - get the JSON response
                    result = await response.json()
                    print("✅ Relay server working correctly!")
                    print(f"Response: {json.dumps(result, indent=2)}")
                else:
                    # Error response
                    error_text = await response.text()
                    print(f"❌ Server returned error: {error_text}")
                    
    except Exception as e:
        print(f"❌ Failed to connect to relay server: {e}")
        print("Make sure the relay server is running:")
        print("  cd py_server")
        print("  python relay_server.py")

if __name__ == "__main__":
    print("Testing relay server...")
    asyncio.run(test_relay_server())
