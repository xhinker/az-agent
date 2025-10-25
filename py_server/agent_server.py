#!/usr/bin/env python3
"""
Agent server that serves the chat UI and acts as a relay for LLM API requests.
This combines both web serving and CORS handling in one server.
"""

import aiohttp
from aiohttp import web
import os

# Configuration - Update this with your actual LLM API endpoint  
LLM_API_URL = "http://192.168.68.77:1234/v1/chat/completions"

# Directory where HTML files are stored
HTML_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'html_ui'))

async def forward_request(request):
    """
    Forward requests from the frontend to your LLM API
    This handles CORS by making the request server-side instead of client-side
    """
    try:
        # Get the JSON data from the frontend request
        data = await request.json()
        
        # Make the actual API call to your LLM server
        async with aiohttp.ClientSession() as session:
            async with session.post(LLM_API_URL, json=data) as response:
                # Get the response from your LLM
                llm_response = await response.json()
                
        # Return the LLM's response to the frontend
        return web.json_response(llm_response)
        
    except Exception as e:
        # Handle any errors and return them to the frontend
        error_response = {"error": str(e)}
        return web.json_response(error_response, status=500)

async def health_check(request):
    """Simple health check endpoint"""
    return web.json_response({"status": "healthy"})

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
app.router.add_post('/chat/completions', forward_request)
app.router.add_get('/health', health_check)

# Handle favicon.ico request with a proper 404 response
app.router.add_get('/favicon.ico', lambda r: web.Response(status=404))

if __name__ == '__main__':
    # Run the server on your specified IP and port
    web.run_app(app, host='192.168.68.65', port=8080)
