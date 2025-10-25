// Chat application functionality
document.addEventListener('DOMContentLoaded', function() {
    const chatBox = document.getElementById('chat-box');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');

    // Function to add a message to the chat box
    function addMessage(message, isUser = true) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');
        messageElement.classList.add(isUser ? 'user-message' : 'bot-message');
        messageElement.textContent = message;
        chatBox.appendChild(messageElement);
        
        // Scroll to the bottom
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Function to handle sending a message
    function sendMessage() {
        const message = messageInput.value.trim();
        if (message) {
            // Add user message
            addMessage(message, true);
            
            // Clear input
            messageInput.value = '';
            
            // Simulate bot response after a short delay
            setTimeout(() => {
                addMessage("This is a simulated response from the LLM.", false);
            }, 1000);
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
