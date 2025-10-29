#!/usr/bin/env python3
"""
Agent server that serves the chat UI and acts as a relay for LLM API requests.
This combines both web serving and CORS handling in one server.
"""

import aiohttp
from aiohttp import web
import os
import uuid
import json
import glob

# Load configuration from config.json
config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.json'))
with open(config_path, 'r') as config_file:
    config = json.load(config_file)

# Configuration - Support multiple LLM models
LLM_MODELS = config.get("llm_models", {})
SERVER_IP = config.get("server_ip", "192.168.68.65")
SERVER_PORT = config.get("server_port", 8080)

# set target model
# TARGET_MODEL_NAME_KEY = "deepseek-chat"
TARGET_MODEL_NAME_KEY = "qwen3-coder-30b-a3b-instruct-mlx"

MODEL_CONFIG = {}

# get the configured model name
for model_name_key, model_config_value in LLM_MODELS.items():
    if model_name_key == TARGET_MODEL_NAME_KEY:
        MODEL_CONFIG = model_config_value
        break

# Determine which model to use
model_name  = MODEL_CONFIG.get('model_name', 'default')
llm_api_url = MODEL_CONFIG.get("llm_api_url")
llm_api_key = MODEL_CONFIG.get("llm_api_key", "")

# Directory where HTML files are stored
HTML_DIR    = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'html_ui'))

# Directory where chat history will be stored
DATA_DIR    = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))

# In-memory storage for chat sessions
sessions    = {}

def save_session_to_file(session_id, messages):
    """Save a session's messages to a JSON file"""
    try:
        session_file = os.path.join(DATA_DIR, f"{session_id}.json")
        with open(session_file, 'w') as f:
            json.dump({
                "session_id": session_id,
                "messages": messages
            }, f, indent=2)
    except Exception as e:
        print(f"Error saving session {session_id}: {e}")

def load_sessions_from_files():
    """Load all chat sessions from JSON files in the data directory"""
    sessions = {}
    try:
        # Ensure data directory exists
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Find all JSON files in the data directory
        session_files = glob.glob(os.path.join(DATA_DIR, "*.json"))
        
        for session_file in session_files:
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                    session_id = session_data.get("session_id")
                    messages = session_data.get("messages", [])
                    
                    if session_id:
                        sessions[session_id] = messages
                        print(f"Loaded session: {session_id} with {len(messages)} messages")
            except Exception as e:
                print(f"Error loading session file {session_file}: {e}")
        
        print(f"Loaded {len(sessions)} chat sessions from disk")
    except Exception as e:
        print(f"Error loading sessions: {e}")
    
    return sessions

async def create_session(request):
    """
    Create a new chat session and return its ID
    """
    session_id = str(uuid.uuid4())
    sessions[session_id] = []
    # Save empty session to file
    save_session_to_file(session_id, [])
    return web.json_response({"session_id": session_id})

async def list_sessions(request):
    """Return a list of known chat sessions."""
    session_items = [
        {"session_id": session_id, "title": session_id}
        for session_id in sessions.keys()
    ]
    return web.json_response({"sessions": session_items})

async def get_session_history(request):
    """Return the stored message history for a session."""
    session_id = request.match_info.get("session_id")
    if session_id not in sessions:
        return web.json_response({"error": "Session not found"}, status=404)

    return web.json_response({
        "session_id": session_id,
        "title": session_id,
        "messages": sessions.get(session_id, []),
    })

async def chat_request(request):
    """
    Forward requests from the frontend to your LLM API
    This handles CORS by making the llm request server-side instead of client-side
    """
    try:
        # Get the JSON data from the frontend request
        request_data = await request.json()
        print(f"request raw data:{json.dumps(request_data,indent=4)}")
        
        # Extract session_id if provided
        request_session_id = request_data.get('session_id', None)
        if not request_session_id:
            error_response = {"error":"request does not include session id"}
            return web.json_response(error_response, status = 400)
        
        # Get conversation history for this session, if not exists, initialize a empty one
        conversation_history = sessions.get(request_session_id,[])
        
        # Add user message to history - make sure we have proper structure
        messages = request_data.get('messages', [])
        
        # Handle empty messages case
        if not messages:
            error_response = {"error": "No messages provided in the request"}
            return web.json_response(error_response, status=400)
        user_message = messages[-1]  # Get last message (should be user)

        # Check role and add message
        if ('role' not in user_message) or (user_message['role'] != 'user'):
            error_response = {"error":"Message role incorrect"}
            return web.json_response(error_response, status = 400)
        conversation_history.append(user_message)
        
        # Prepare messages for LLM - include full history
        llm_messages = conversation_history
        
        # Clean messages for DeepSeek API - remove empty tool_calls arrays
        cleaned_messages = []
        for message in llm_messages:
            cleaned_message = message.copy()
            # Remove tool_calls if it's an empty array
            if 'tool_calls' in cleaned_message and cleaned_message['tool_calls'] == []:
                del cleaned_message['tool_calls']
            cleaned_messages.append(cleaned_message)
        
        llm_messages = cleaned_messages
        
        # Make the actual API call to your LLM server
        request_data['messages'] = llm_messages
        
        # Prepare headers with API key if available
        headers = {}
        if llm_api_key:
            headers['Authorization'] = f'Bearer {llm_api_key}'
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                llm_api_url
                , json      = {**request_data}
                , headers   = headers
            ) as response:
                # Get the response from your LLM
                llm_response = await response.json()
        
        print(f"llm response:{json.dumps(llm_response, indent=4)}")
                
        # Add bot response to session history if we got a valid response
        if 'choices' in llm_response and len(llm_response['choices']) > 0:
            bot_message = llm_response['choices'][0]['message']
            conversation_history.append(bot_message)
        
        # update the whole conversation history
        sessions[request_session_id] = conversation_history
        
        # Save updated session to file
        save_session_to_file(request_session_id, conversation_history)
        
        # Return the LLM's response to the frontend
        return web.json_response({**llm_response, "session_id": request_session_id})
        
    except Exception as e:
        # Handle any errors and return them to the frontend
        error_response = {"error": str(e)}
        print(error_response)
        return web.json_response(error_response, status=500)

async def health_check(request):
    """Simple health check endpoint"""
    return web.json_response({"status": "healthy"})

async def get_config(request):
    """Serve configuration to the frontend"""
    # Prepare model information for frontend
    available_models = {}
    for model_name, model_config in LLM_MODELS.items():
        available_models[model_name] = {
            "model_name": model_config.get("model_name", model_name),
        }
    
    return web.json_response({
        "available_models": available_models,
        "model_name": TARGET_MODEL_NAME_KEY,
        "server_ip": SERVER_IP,
        "server_port": SERVER_PORT
    })

async def serve_file(request):
    """Serve files from the html_ui directory"""
    try:
        # Get requested file path
        filename = request.path

        # remove the leading / if exists
        if filename.startswith('/'):
            filename = filename[1:]
        
        # Basic safety check to avoid directory traversal
        if '..' in filename or filename.startswith('/'):
            return web.HTTPForbidden()
            
        # Build full file path  
        filepath = os.path.join(HTML_DIR, filename)
        
        # Verify we're in the allowed directory
        if not filepath.startswith(HTML_DIR):
            return web.HTTPForbidden()
        
        # Check if file exists
        if not os.path.exists(filepath):
            return web.HTTPNotFound()
            
        # Return the file content with appropriate content type
        with open(filepath, 'r') as f:
            content = f.read()
            
        # Set appropriate content type
        if filename.endswith('.css'):
            content_type = 'text/css'
        elif filename.endswith('.js'):
            content_type = 'application/javascript' 
        else:
            content_type = 'text/html'
            
        return web.Response(text=content, content_type=content_type)
        
    except Exception as e:
        return web.HTTPInternalServerError(reason=str(e))

# Create the aiohttp application
app = web.Application()

# Load existing chat sessions on startup
sessions.update(load_sessions_from_files())

# Add routes for serving files and API endpoints  
app.router.add_get('/', serve_file)  # Serve chat.html by default
app.router.add_get('/chat.html', serve_file)
app.router.add_get('/chat.css', serve_file)
app.router.add_get('/chat.js', serve_file)
app.router.add_post('/chat/completions', chat_request)
app.router.add_get('/health', health_check)
app.router.add_post('/session', create_session)
app.router.add_get('/sessions', list_sessions)
app.router.add_get('/session/{session_id}', get_session_history)
app.router.add_get('/config', get_config)

# Handle favicon.ico request with a proper 404 response
app.router.add_get('/favicon.ico', lambda r: web.Response(status=404))

if __name__ == '__main__':
    # Run the server on your specified IP and port
    web.run_app(app, host=SERVER_IP, port=SERVER_PORT)
