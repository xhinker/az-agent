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

// Global variables for session management
let currentSessionId = null;
let sessionsCache = [];

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

function renderMarkdownContent(element, content) {
    if (typeof marked !== 'undefined' && marked.parse) {
        element.innerHTML = marked.parse(content);
    } else {
        element.textContent = content;
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
}

// Function to add a message to the chat box
function addMessage(message, isUser = true, options = {}) {
    const { skipMarkdown = false } = options;
    const messageElement = document.createElement('div');
    messageElement.classList.add('message');
    messageElement.classList.add(isUser ? 'user-message' : 'bot-message');

    if (skipMarkdown) {
        messageElement.textContent = message;
    } else {
        renderMarkdownContent(messageElement, message);
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

async function streamBotResponse(userMessage, handlers = {}) {
    const {
        onSession,
        onDelta,
        onDone,
        onError,
        onEvent,
    } = handlers;

    const response = await fetch(`http://${config.server_ip}:${config.server_port}/chat/completions`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            model: config.model_name,
            session_id: currentSessionId,
            messages: [
                { role: 'user', content: userMessage }
            ],
            stream: true,
            temperature: 0.7
        })
    });

    if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
    }

    if (!response.body) {
        throw new Error('Streaming not supported in this browser.');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';
    let finalMessage = null;
    let streamError = null;
    let streamClosed = false;

    const processEvent = (eventPayload) => {
        const { type } = eventPayload;

        if (type === 'session') {
            onSession?.(eventPayload.session_id);
            return;
        }

        if (type === 'delta') {
            if (eventPayload.content) {
                onDelta?.(eventPayload);
            } else {
                onEvent?.(eventPayload);
            }
            return;
        }

        if (type === 'done') {
            finalMessage = eventPayload.message || null;
            onDone?.(eventPayload);
            return;
        }

        if (type === 'error') {
            const error = new Error(eventPayload.message || 'Stream error');
            error.status = eventPayload.status;
            streamError = error;
            onError?.(error);
            return;
        }

        onEvent?.(eventPayload);
    };

    const flushBuffer = async () => {
        while (true) {
            const separatorIndex = buffer.indexOf('\n\n');
            if (separatorIndex === -1) {
                break;
            }

            const rawEvent = buffer.slice(0, separatorIndex);
            buffer = buffer.slice(separatorIndex + 2);

            if (!rawEvent.trim()) {
                continue;
            }

            const dataLines = rawEvent
                .split('\n')
                .filter(line => line.startsWith('data:'))
                .map(line => line.slice(5).trimStart());

            if (!dataLines.length) {
                continue;
            }

            const dataPayload = dataLines.join('\n');

            if (dataPayload === '[DONE]') {
                streamClosed = true;
                return;
            }

            try {
                const parsed = JSON.parse(dataPayload);
                processEvent(parsed);
            } catch (error) {
                console.warn('Failed to parse stream payload:', dataPayload, error);
            }
        }
    };

    try {
        while (!streamClosed) {
            const { value, done } = await reader.read();
            if (done) {
                break;
            }

            buffer += decoder.decode(value, { stream: true });
            await flushBuffer();
        }

        if (!streamClosed) {
            buffer += decoder.decode();
            await flushBuffer();
        }
    } finally {
        reader.releaseLock();
    }

    if (streamError) {
        throw streamError;
    }

    return finalMessage;
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

    const botMessageElement = addMessage('Thinking...', false, { skipMarkdown: true });
    let streamedContent = '';
    let hasReceivedDelta = false;

    const updateSession = (sessionId) => {
        if (sessionId && sessionId !== currentSessionId) {
            currentSessionId = sessionId;
            localStorage.setItem('chat_session_id', currentSessionId);
            renderChatList();
        }
    };

    try {
        const finalMessage = await streamBotResponse(message, {
            onSession: updateSession,
            onDelta: (event) => {
                if (!event.content) {
                    return;
                }

                if (!hasReceivedDelta) {
                    hasReceivedDelta = true;
                    botMessageElement.textContent = '';
                }

                streamedContent += event.content;
                botMessageElement.textContent = streamedContent;
                chatBox.scrollTop = chatBox.scrollHeight;
            },
            onDone: (event) => {
                if (event?.message?.content) {
                    streamedContent = event.message.content;
                }
            },
            onError: (error) => {
                console.error('Stream error:', error);
            }
        });

        const finalContent = (finalMessage && finalMessage.content) || streamedContent;
        if (finalContent) {
            renderMarkdownContent(botMessageElement, finalContent);
            chatBox.scrollTop = chatBox.scrollHeight;
        } else {
            botMessageElement.textContent = 'No response received from the model.';
        }
    } catch (error) {
        console.error('Error streaming response:', error);
        botMessageElement.textContent = 'Error: Unable to get response from LLM. ' + (error.message || error);
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

    currentSessionId = localStorage.getItem('chat_session_id');
    sessionsCache = [];

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
        } else if (e.key === 'Enter' && !e.shiftKey) {
            // Allow Enter for new lines, but prevent default behavior for regular Enter
            // Shift+Enter will still work for new lines
            e.preventDefault();
        }
    });

    // Auto-resize textarea based on content
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 200) + 'px';
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
