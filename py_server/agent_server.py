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

# Load configuration from config.json
config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.json'))
with open(config_path, 'r') as config_file:
    config = json.load(config_file)

# Configuration - Update this with your actual LLM API endpoint  
LLM_API_URL = config.get("llm_api_url", "http://192.168.68.61:1234/v1/chat/completions")
LLM_API_KEY = config.get("llm_api_key", "")
SERVER_IP   = config.get("server_ip", "192.168.68.65")
SERVER_PORT = config.get("server_port", 8080)

# Directory where HTML files are stored
HTML_DIR    = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'html_ui'))

# In-memory storage for chat sessions
sessions    = {}

async def create_session(request):
    """
    Create a new chat session and return its ID
    """
    session_id = str(uuid.uuid4())
    sessions[session_id] = []
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
        
        # Make the actual API call to your LLM server
        print(f"llm_messages: {llm_messages}")
        request_data['messages'] = llm_messages
        
        # Prepare headers with API key if available
        headers = {}
        if LLM_API_KEY:
            headers['Authorization'] = f'Bearer {LLM_API_KEY}'
        
        async with aiohttp.ClientSession() as session:
            # async with session.post(LLM_API_URL, json={**request_data, 'messages': llm_messages}) as response:
            async with session.post(LLM_API_URL, json={**request_data}, headers=headers) as response:
                # Get the response from your LLM
                llm_response = await response.json()
                
        # Add bot response to session history if we got a valid response
        if 'choices' in llm_response and len(llm_response['choices']) > 0:
            bot_message = llm_response['choices'][0]['message']
            conversation_history.append(bot_message)
        
        sessions[request_session_id] = conversation_history
        
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
    return web.json_response({
        "llm_api_url": LLM_API_URL,
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
