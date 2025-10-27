// Chat application functionality
document.addEventListener('DOMContentLoaded', function() {
    const chatBox       = document.getElementById('chat-box');
    const messageInput  = document.getElementById('message-input');
    const sendButton    = document.getElementById('send-button');

    // Initialize highlight.js
    if (typeof hljs !== 'undefined') {
        hljs.initHighlightingOnLoad();
    }

    // Session ID management
    let currentSessionId = localStorage.getItem('chat_session_id');
    console.log("currentSessionId:"+ currentSessionId)
    
    // Create a new session if one doesn't exist
    if (!currentSessionId) {
        createNewSession();
    }

    // Function to create a new session
    async function createNewSession() {
        try {
            const response = await fetch('http://192.168.68.65:8080/session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                currentSessionId = data.session_id;
                localStorage.setItem('chat_session_id', currentSessionId);
            }
        } catch (error) {
            console.error('Failed to create session:', error);
        }
    }

    // Function to add a message to the chat box
    function addMessage(message, isUser = true) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');
        messageElement.classList.add(isUser ? 'user-message' : 'bot-message');
        
        // For bot messages, parse markdown and highlight code
        if (!isUser) {
            // Check if marked is available before parsing
            if (typeof marked !== 'undefined' && marked.parse) {
                messageElement.innerHTML = marked.parse(message);
            } else {
                // Fallback to plain text if markdown parser isn't available
                messageElement.textContent = message;
            }
            
            // Highlight any code blocks if hljs is available
            if (typeof hljs !== 'undefined') {
                setTimeout(() => {
                    hljs.highlightAll();
                }, 0);
            }
            
            // Render LaTeX after everything else is processed
            setTimeout(() => {
                if (typeof MathJax !== 'undefined') {
                    MathJax.typeset();
                }
            }, 0);
        } else {
            messageElement.textContent = message;
        }
        
        chatBox.appendChild(messageElement);
        
        // Scroll to the bottom
        chatBox.scrollTop = chatBox.scrollHeight;
        
        return messageElement; // Return the created element so it can be referenced later
    }

    // Function to call the relay server
    async function getBotResponse(userMessage) {
        console.log("user message:"+userMessage)
        try {
            const response = await fetch('http://192.168.68.65:8080/chat/completions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: "default",
                    session_id: currentSessionId,
                    messages: [
                        { role: "user", content: userMessage }
                    ],
                    temperature: 0.7
                })
            });
            
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            
            const data = await response.json();
            // Update session ID if it's returned (for new sessions)
            if (data.session_id && data.session_id !== currentSessionId) {
                currentSessionId = data.session_id;
                localStorage.setItem('chat_session_id', currentSessionId);
            }
            
            return data.choices[0].message.content;
        } catch (error) {
            console.error('Error calling API:', error);
            return "Sorry, I encountered an error processing your request.";
        }
    }

    // Function to handle sending a message
    async function sendMessage() {
        const message = messageInput.value.trim();
        if (message) {
            // Add user message
            addMessage(message, true);
            
            // Clear input
            messageInput.value = '';
            
            // Show loading indicator while waiting for response
            const loadingMessage = addMessage("Thinking...", false);
            
            try {
                // Get response from API
                const botResponse = await getBotResponse(message);
                
                // Remove loading message and add actual response
                chatBox.removeChild(loadingMessage);
                addMessage(botResponse, false);
            } catch (error) {
                // Remove loading message and show error
                chatBox.removeChild(loadingMessage);
                addMessage("Error: Unable to get response from LLM.", false);
            }
        }
    }

    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
});
