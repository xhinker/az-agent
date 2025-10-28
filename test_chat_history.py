#!/usr/bin/env python3
"""
Test script to verify chat history persistence functionality
"""

import os
import sys
import json
import uuid

# Add the py_server directory to the path so we can import the functions
sys.path.append(os.path.join(os.path.dirname(__file__), 'py_server'))

# Import the functions we want to test
from agent_server import save_session_to_file, load_sessions_from_files, DATA_DIR

def test_chat_history_persistence():
    """Test that chat sessions can be saved and loaded correctly"""
    
    print("Testing chat history persistence...")
    
    # Test 1: Create and save a session
    print("\n1. Creating test session...")
    session_id = str(uuid.uuid4())
    test_messages = [
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you! How can I help you today?"}
    ]
    
    save_session_to_file(session_id, test_messages)
    print(f"✓ Saved session {session_id} with {len(test_messages)} messages")
    
    # Test 2: Load sessions and verify our test session is there
    print("\n2. Loading sessions from disk...")
    loaded_sessions = load_sessions_from_files()
    
    if session_id in loaded_sessions:
        print(f"✓ Successfully loaded session {session_id}")
        loaded_messages = loaded_sessions[session_id]
        print(f"✓ Session has {len(loaded_messages)} messages")
        
        # Verify message content
        if len(loaded_messages) == len(test_messages):
            print("✓ Message count matches")
        else:
            print("✗ Message count mismatch")
            return False
            
        # Verify message content
        for i, (original, loaded) in enumerate(zip(test_messages, loaded_messages)):
            if original == loaded:
                print(f"✓ Message {i+1} content matches")
            else:
                print(f"✗ Message {i+1} content mismatch")
                print(f"  Original: {original}")
                print(f"  Loaded: {loaded}")
                return False
    else:
        print(f"✗ Failed to load session {session_id}")
        return False
    
    # Test 3: Create another session and verify both exist
    print("\n3. Creating another session...")
    session_id_2 = str(uuid.uuid4())
    test_messages_2 = [
        {"role": "user", "content": "What's the weather like?"},
        {"role": "assistant", "content": "I'm an AI assistant and don't have access to real-time weather data."}
    ]
    
    save_session_to_file(session_id_2, test_messages_2)
    print(f"✓ Saved second session {session_id_2}")
    
    # Reload and verify both sessions exist
    loaded_sessions_2 = load_sessions_from_files()
    if session_id in loaded_sessions_2 and session_id_2 in loaded_sessions_2:
        print(f"✓ Both sessions loaded successfully")
        print(f"  Total sessions: {len(loaded_sessions_2)}")
    else:
        print("✗ Failed to load both sessions")
        return False
    
    # Test 4: Check that files were created in the data directory
    print("\n4. Verifying file creation...")
    session_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json')]
    print(f"✓ Found {len(session_files)} session files in data directory")
    
    # Clean up test files
    print("\n5. Cleaning up test files...")
    for session_file in [f"{session_id}.json", f"{session_id_2}.json"]:
        file_path = os.path.join(DATA_DIR, session_file)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"✓ Removed {session_file}")
    
    print("\n🎉 All tests passed! Chat history persistence is working correctly.")
    return True

if __name__ == "__main__":
    success = test_chat_history_persistence()
    sys.exit(0 if success else 1)
