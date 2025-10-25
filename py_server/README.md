# Agent Server

This is a combined web server and relay server for the LLM chat application.

## Purpose
- Serves the HTML UI files (chat.html, chat.css, chat.js)
- Bypasses browser CORS restrictions by acting as a middleman between the frontend and your LLM API

## How to Run

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python agent_server.py
```

The server will start on `http://192.168.68.65:8080`

## Endpoints
- `GET /` - Serve chat.html (main UI)
- `GET /chat.html` - Serve HTML file
- `GET /chat.css` - Serve CSS file  
- `GET /chat.js` - Serve JavaScript file
- `POST /chat/completions` - Forward requests to your LLM API
- `GET /health` - Health check endpoint

## Testing
You can test the server using:
```bash
python test_client.py
```

## Configuration
Update `LLM_API_URL` in `agent_server.py` with your actual LLM API endpoint.
