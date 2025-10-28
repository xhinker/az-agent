# AZ Agent

## Overview

This project is a web-based chat interface that connects to LLM (Large Language Model) APIs. It provides a simple way to interact with language models through a web browser interface, handling CORS restrictions that might prevent direct API access from browsers.

## Architecture

The system consists of two main components:
1. **Frontend (Client-side)**: A web interface built with HTML, CSS and JavaScript that users interact with
2. **Backend (Server-side)**: A Python-based web server using aiohttp that serves the frontend and acts as a relay for LLM API requests

## How It Works

**Client-side (Frontend):**
- The browser loads the chat interface from `html_ui/chat.html`
- Users type messages in the input field and click "Send" or press Enter
- JavaScript code (`html_ui/chat.js`) sends messages to the server via POST requests to `/chat/completions`
- The frontend manages chat sessions using localStorage and handles markdown rendering for bot responses

**Server-side (Backend):**
- The Python server (`py_server/agent_server.py`) runs on `http://192.168.68.65:8080`
- It serves static files from `html_ui/` directory including HTML, CSS and JavaScript
- It provides an endpoint `/chat/completions` that receives requests from the frontend
- The server forwards these requests to your actual LLM API endpoint (configured in `LLM_API_URL`)
- It handles CORS restrictions by making requests server-side instead of client-side
- Session management is handled in-memory using UUIDs

## Components Directory Structure

- `html_ui/`: Contains frontend files:
  - `chat.html`: Main HTML interface
  - `chat.css`: Styling for the chat interface
  - `chat.js`: JavaScript logic for handling messages and API calls

- `py_server/`: Contains Python server files:
  - `agent_server.py`: Main server implementation using aiohttp
  - `requirements.txt`: Python dependencies needed to run the server
  - `test_client.py`: A test client for manually testing the server

## Running the Project

1. **Prerequisites:**
   - Python 3.7+
   - pip (Python package manager)

2. **Setup:**
   ```bash
   cd py_server
   pip install -r requirements.txt
   ```

3. **Configuration:**
   Update `LLM_API_URL` in `py_server/agent_server.py` with your actual LLM API endpoint.

4. **Running:**
   ```bash
   python agent_server.py
   ```

5. **Access the interface:**
   Open your browser and go to `http://192.168.68.65:8080`

## Testing

You can test the server using:
```bash
python test_client.py
```

## Recent Changes

- Updated `.gitignore` to exclude test files with the pattern `*_test`
