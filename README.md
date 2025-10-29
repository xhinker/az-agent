# AZ Agent

## Overview

AZ Agent is a web-based chat interface that connects to LLM (Large Language Model) APIs. It provides a simple way to interact with language models through a web browser interface, handling CORS restrictions that might prevent direct API access from browsers. The system supports multiple LLM models and provides persistent chat session management.

## Architecture

The system consists of two main components:
1. **Frontend (Client-side)**: A modern web interface built with HTML, CSS and JavaScript that users interact with
2. **Backend (Server-side)**: A Python-based web server using aiohttp that serves the frontend and acts as a relay for LLM API requests

## Features

- **Multi-Model Support**: Configure and switch between different LLM models (DeepSeek, Qwen, etc.)
- **Persistent Chat Sessions**: Chat history is automatically saved and restored across browser sessions
- **Modern UI**: Clean, responsive interface with collapsible sidebar and dark theme
- **Markdown Support**: Rich text rendering with code syntax highlighting and LaTeX math support
- **Session Management**: Create, switch between, and manage multiple chat sessions
- **CORS Handling**: Server-side API relay to bypass browser CORS restrictions
- **Real-time Chat**: Streamlined chat interface with keyboard shortcuts

## How It Works

### Client-side (Frontend):
- The browser loads the chat interface from `html_ui/chat.html`
- Users type messages in the input field and click "Send" or press Ctrl+Enter
- JavaScript code (`html_ui/chat.js`) sends messages to the server via POST requests to `/chat/completions`
- The frontend manages chat sessions using localStorage and handles markdown rendering for bot responses
- Supports multiple chat sessions with collapsible sidebar navigation

### Server-side (Backend):
- The Python server (`py_server/agent_server.py`) runs on configurable IP and port
- It serves static files from `html_ui/` directory including HTML, CSS and JavaScript
- It provides multiple API endpoints for chat completions, session management, and configuration
- The server forwards requests to configured LLM API endpoints with proper authentication
- It handles CORS restrictions by making requests server-side instead of client-side
- Session management with persistent storage to JSON files in the `data/` directory

## Project Structure

```
az-agent/
├── README.md                    # This file
├── LICENSE                      # License information
├── .gitignore                   # Git ignore rules
├── config.json                  # Main configuration file
├── config_sample.json           # Configuration template
├── data/                        # Chat session storage
│   ├── *.json                  # Individual session files
│   └── chat_history_is_saved_here.txt
├── html_ui/                     # Frontend files
│   ├── chat.html               # Main HTML interface
│   ├── chat.css                # Styling for the chat interface
│   └── chat.js                 # JavaScript logic
└── py_server/                  # Backend server files
    ├── agent_server.py         # Main server implementation
    ├── requirements.txt        # Python dependencies
    ├── test_client.py          # Test client for server
    └── README.md               # Server-specific documentation
```

## API Endpoints

### Chat Operations
- `POST /chat/completions` - Send chat messages to LLM
- `GET /config` - Get server configuration and available models

### Session Management
- `POST /session` - Create a new chat session
- `GET /sessions` - List all available sessions
- `GET /session/{session_id}` - Get session history

### System
- `GET /health` - Health check endpoint
- `GET /*` - Serve static files from html_ui directory

## Configuration

### Main Configuration (config.json)
The system supports multiple LLM models configured in `config.json`:

```json
{
    "llm_models": {
        "deepseek-chat": {
            "model_name": "deepseek-chat",
            "llm_api_url": "https://api.deepseek.com/v1/chat/completions",
            "llm_api_key": "your-api-key-here"
        },
        "qwen3-coder-30b-a3b-instruct-mlx": {
            "model_name": "qwen3-coder-30b-a3b-instruct-mlx",
            "llm_api_url": "http://192.168.68.61:1234/v1/chat/completions",
            "llm_api_key": "lmstudio"
        }
    },
    "server_ip": "192.168.68.65",
    "server_port": 8080
}
```

### Model Selection
The target model is configured in `py_server/agent_server.py` by setting the `TARGET_MODEL_NAME_KEY` variable.

## Installation & Setup

### Prerequisites
- Python 3.7+
- pip (Python package manager)

### Quick Start

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd az-agent
   ```

2. **Install dependencies:**
   ```bash
   cd py_server
   pip install -r requirements.txt
   ```

3. **Configure your models:**
   - Copy `config_sample.json` to `config.json`
   - Edit `config.json` with your LLM API endpoints and keys
   - Update the target model in `py_server/agent_server.py` if needed

4. **Run the server:**
   ```bash
   python agent_server.py
   ```

5. **Access the interface:**
   Open your browser and go to `http://<server_ip>:<server_port>`

## Usage

### Web Interface
- **New Chat**: Click the "+" button in the sidebar to create a new session
- **Send Message**: Type in the input field and press Ctrl+Enter or click Send
- **Switch Sessions**: Click on any session in the sidebar to switch between chats
- **Toggle Sidebar**: Click the "AZAI" button to collapse/expand the sidebar

### Keyboard Shortcuts
- `Ctrl+Enter`: Send message
- `Enter`: New line (when not combined with Ctrl)
- `Shift+Enter`: Force new line

### Testing
You can test the server using the included test client:
```bash
cd py_server
python test_client.py
```

## Dependencies

### Backend (Python)
- `aiohttp>=3.8.0` - Async HTTP server/client
- `jupyterlab` - Development environment (optional)

### Frontend (CDN)
- `marked` - Markdown parsing
- `highlight.js` - Code syntax highlighting
- `MathJax` - LaTeX math rendering

## Session Storage

Chat sessions are automatically saved to JSON files in the `data/` directory. Each session file contains:
- Session ID
- Complete message history
- Timestamp information

Sessions are loaded automatically when the server starts and persist across server restarts.

## Development

### File Structure Details

**Backend (`py_server/`):**
- `agent_server.py` - Main server with session management and API routing
- `test_client.py` - Integration test client
- `requirements.txt` - Python dependencies

**Frontend (`html_ui/`):**
- `chat.html` - Main interface with CDN dependencies
- `chat.css` - Modern dark theme with responsive design
- `chat.js` - Session management and API communication

### Adding New Models
1. Add model configuration to `config.json` under `llm_models`
2. Update `TARGET_MODEL_NAME_KEY` in `agent_server.py` or implement model switching UI

## Troubleshooting

### Common Issues

1. **Server won't start:**
   - Check if port is already in use
   - Verify Python dependencies are installed
   - Ensure `config.json` exists and is valid JSON

2. **API errors:**
   - Verify LLM API URL and key in configuration
   - Check network connectivity to API endpoint
   - Review server logs for detailed error messages

3. **Frontend not loading:**
   - Verify server is running and accessible
   - Check browser console for JavaScript errors
   - Ensure all CDN dependencies load properly

## License

This project is licensed under the terms included in the LICENSE file.

## Recent Changes

- Updated configuration system to support multiple LLM models
- Added persistent session storage to JSON files
- Enhanced UI with collapsible sidebar and session management
- Added markdown rendering with code highlighting and math support
- Improved error handling and logging
