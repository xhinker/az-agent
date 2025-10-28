// Configuration object to be loaded from server
let config = {};

var chatBox       = null;
var messageInput  = null;
var sendButton    = null;
var chatList      = null;
var newChatButton = null;
var sidebarToggle = null;
var sidebar       = null;
var chatTitle     = null;

// init UI elements
function init_page(){
    chatBox       = document.getElementById('chat-box');
    messageInput  = document.getElementById('message-input');
    sendButton    = document.getElementById('send-button');
    chatList      = document.getElementById('chat-list');
    newChatButton = document.getElementById('new-chat-button');
    sidebarToggle = document.getElementById('sidebar-toggle');
    sidebar       = document.getElementById('sidebar');
    chatTitle     = document.getElementById('chat-title');
}

// clear all content in the chat box
function clearChat() {
    chatBox.innerHTML = '';
}

// show some init message in the chat box before inputing anything
function showEmptyState() {
    const emptyState        = document.createElement('div');
    emptyState.classList.add('empty-state');
    emptyState.textContent  = 'No messages yet. Start typing to begin the conversation.';
    chatBox.appendChild(emptyState);
}

// remove the empty state notes
function removeEmptyState() {
    const emptyState = chatBox.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }
}

// Function to add a message to the chat box
function addMessage(message, isUser = true) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message');
    messageElement.classList.add(isUser ? 'user-message' : 'bot-message');

    if (!isUser) {
        if (typeof marked !== 'undefined' && marked.parse) {
            messageElement.innerHTML = marked.parse(message);
        } else {
            messageElement.textContent = message;
        }

        if (typeof hljs !== 'undefined') {
            setTimeout(() => {
                hljs.highlightAll();
            }, 0);
        }

        setTimeout(() => {
            if (typeof MathJax !== 'undefined') {
                MathJax.typeset();
            }
        }, 0);
    } else {
        messageElement.textContent = message;
    }

    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;

    return messageElement;
}

function renderChatList() {
    chatList.innerHTML = '';

    sessionsCache.forEach(({ session_id: sessionId, title }) => {
        const item = document.createElement('div');
        item.classList.add('chat-item');
        if (sessionId === currentSessionId) {
            item.classList.add('active');
        }

        item.textContent = title || sessionId;
        item.dataset.sessionId = sessionId;

        item.addEventListener('click', async () => {
            if (sessionId !== currentSessionId) {
                await selectSession(sessionId);
            }
        });

        chatList.appendChild(item);
    });
}

async function createNewSession() {
    try {
        const response = await fetch(`http://${config.server_ip}:${config.server_port}/session`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`Failed to create session (${response.status})`);
        }

        const data = await response.json();
        currentSessionId = data.session_id;
        localStorage.setItem('chat_session_id', currentSessionId);
        return currentSessionId;
    } catch (error) {
        console.error('Failed to create session:', error);
        return null;
    }
}

async function fetchSessionHistory(sessionId) {
    try {
        const response = await fetch(`http://${config.server_ip}:${config.server_port}/session/${sessionId}`);
        if (response.status === 404) {
            return [];
        }
        if (!response.ok) {
            throw new Error(`Failed to fetch session history (${response.status})`);
        }

        const data = await response.json();
        return Array.isArray(data.messages) ? data.messages : [];
    } catch (error) {
        console.error('Failed to load session history:', error);
        return [];
    }
}

async function loadSessionHistory(sessionId) {
    const targetSession = sessionId;
    clearChat();
    const history = await fetchSessionHistory(sessionId);

    if (currentSessionId !== targetSession) {
        return;
    }

    if (!history.length) {
        showEmptyState();
        return;
    }

    history.forEach(message => {
        const isUser = message.role === 'user';
        addMessage(message.content || '', isUser);
    });
}

async function selectSession(sessionId) {
    currentSessionId = sessionId;
    localStorage.setItem('chat_session_id', currentSessionId);
    chatTitle.textContent = sessionId;
    renderChatList();
    await loadSessionHistory(sessionId);
}

async function loadSessions(preferredSessionId) {
    try {
        const response = await fetch(`http://${config.server_ip}:${config.server_port}/sessions`);
        if (!response.ok) {
            throw new Error(`Failed to load sessions (${response.status})`);
        }

        const data = await response.json();
        sessionsCache = Array.isArray(data.sessions) ? data.sessions : [];

        if (!sessionsCache.length) {
            const newSessionId = await createNewSession();
            if (!newSessionId) {
                throw new Error('Unable to create initial session.');
            }

            sessionsCache = [{ session_id: newSessionId, title: newSessionId }];
        }

        const knownIds = sessionsCache.map(session => session.session_id);
        let sessionToSelect = preferredSessionId && knownIds.includes(preferredSessionId)
            ? preferredSessionId
            : currentSessionId && knownIds.includes(currentSessionId)
                ? currentSessionId
                : knownIds[0];

        await selectSession(sessionToSelect);
    } catch (error) {
        console.error('Failed to load sessions:', error);
        chatTitle.textContent = 'Unable to load sessions';
        clearChat();
        const errorState = document.createElement('div');
        errorState.classList.add('empty-state');
        errorState.textContent = 'Failed to load chats. Please refresh the page.';
        chatBox.appendChild(errorState);
    }
}

async function getBotResponse(userMessage) {
    try {
        const response = await fetch(`http://${config.server_ip}:${config.server_port}/chat/completions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: 'default',
                session_id: currentSessionId,
                messages: [
                    { role: 'user', content: userMessage }
                ],
                temperature: 0.7
            })
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();
        if (data.session_id && data.session_id !== currentSessionId) {
            currentSessionId = data.session_id;
            localStorage.setItem('chat_session_id', currentSessionId);
            renderChatList();
        }

        return data.choices?.[0]?.message?.content ?? 'No response received from the model.';
    } catch (error) {
        console.error('Error calling API:', error);
        throw error;
    }
}

async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) {
        return;
    }

    if (!currentSessionId) {
        await loadSessions();
        if (!currentSessionId) {
            console.error('No active chat session available.');
            return;
        }
    }

    removeEmptyState();
    addMessage(message, true);
    messageInput.value = '';

    const loadingMessage = addMessage('Thinking...', false);

    try {
        const botResponse = await getBotResponse(message);
        chatBox.removeChild(loadingMessage);
        addMessage(botResponse, false);
    } catch (error) {
        chatBox.removeChild(loadingMessage);
        addMessage('Error: Unable to get response from LLM. ' + error, false);
    }
}

// Initialize chat after configuration is loaded
async function initChat() {
    if (!chatBox || !messageInput || !sendButton || !chatList || !newChatButton || !sidebarToggle || !sidebar || !chatTitle) {
        console.error('Chat UI elements failed to load.');
        return;
    }

    // Initialize highlight.js
    if (typeof hljs !== 'undefined') {
        // hljs.initHighlightingOnLoad();
        hljs.highlightAll();
    }

    let currentSessionId = localStorage.getItem('chat_session_id');
    let sessionsCache = [];

    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
    });

    newChatButton.addEventListener('click', async () => {
        const sessionId = await createNewSession();
        if (sessionId) {
            await loadSessions(sessionId);
        }
    });

    sendButton.addEventListener('click', sendMessage);

    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && e.ctrlKey) {
            sendMessage();
            e.preventDefault(); // Prevent new line insertion
        }
    });

    await loadSessions(currentSessionId);
}

// Chat application functionality
document.addEventListener('DOMContentLoaded', function() {    
    async function loadConfig() {
        try {
            const response = await fetch('/config');
            if (response.ok) {
                config = await response.json();
                init_page()
                await initChat();
            } else {
                console.error('Failed to load configuration');
            }
        } catch (error) {
            console.error('Error loading configuration:', error);
        }
    }

    loadConfig();
});
