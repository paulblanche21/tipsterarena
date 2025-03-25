// static/js/messages.js
function init() {
    // Modal Event Listeners
    const newMessageBtn = document.getElementById('newMessageBtn');
    const newMessageSidebarBtn = document.getElementById('newMessageSidebarBtn');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const recipientInput = document.getElementById('recipientUsername');
    const startConversationBtn = document.getElementById('startConversationBtn');

    if (newMessageBtn) {
        newMessageBtn.addEventListener('click', openNewMessageModal);
    }
    if (newMessageSidebarBtn) {
        newMessageSidebarBtn.addEventListener('click', openNewMessageModal);
    }
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', closeNewMessageModal);
    }
    if (recipientInput) {
        recipientInput.addEventListener('input', (e) => searchUsers(e.target.value));
    }
    if (startConversationBtn) {
        startConversationBtn.addEventListener('click', startNewConversation);
    }

    // Thread Card Event Listeners
    const threadCards = document.querySelectorAll('.card[data-thread-id]');
    threadCards.forEach(card => {
        card.addEventListener('click', () => {
            const threadId = card.getAttribute('data-thread-id');
            loadThread(threadId);
        });
    });

    // Send Message Event Listener
    const sendMessageBtn = document.getElementById('sendMessageBtn');
    if (sendMessageBtn) {
        const threadId = sendMessageBtn.getAttribute('data-thread-id');
        sendMessageBtn.addEventListener('click', () => sendMessage(threadId));
    }

    // Auto-scroll to the bottom of the messages list
    const messagesList = document.getElementById('messagesList');
    if (messagesList) {
        messagesList.scrollTop = messagesList.scrollHeight;
    }
}

// Modal Functions
function openNewMessageModal() {
    const modal = document.getElementById('newMessageModal');
    if (modal) {
        modal.style.display = 'block';
    }
}

function closeNewMessageModal() {
    const modal = document.getElementById('newMessageModal');
    const recipientInput = document.getElementById('recipientUsername');
    const suggestionsDiv = document.getElementById('userSuggestions');
    if (modal) {
        modal.style.display = 'none';
    }
    if (recipientInput) {
        recipientInput.value = '';
    }
    if (suggestionsDiv) {
        suggestionsDiv.innerHTML = '';
    }
}

function searchUsers(query) {
    if (query.length < 2) {
        const suggestionsDiv = document.getElementById('userSuggestions');
        if (suggestionsDiv) {
            suggestionsDiv.innerHTML = '';
        }
        return;
    }
    fetch(`/suggested-users/`, { method: 'GET' })
        .then(response => response.json())
        .then(data => {
            const suggestions = data.users.filter(user => user.username.toLowerCase().includes(query.toLowerCase()));
            const suggestionsDiv = document.getElementById('userSuggestions');
            if (suggestionsDiv) {
                suggestionsDiv.innerHTML = '';
                suggestions.forEach(user => {
                    const div = document.createElement('div');
                    div.className = 'suggestion';
                    div.innerHTML = `<img src="${user.avatar_url}" class="avatar-small"> ${user.username}`;
                    div.addEventListener('click', () => {
                        const recipientInput = document.getElementById('recipientUsername');
                        if (recipientInput) {
                            recipientInput.value = user.username;
                        }
                        suggestionsDiv.innerHTML = '';
                    });
                    suggestionsDiv.appendChild(div);
                });
            }
        });
}

function startNewConversation() {
    const recipientInput = document.getElementById('recipientUsername');
    const recipientUsername = recipientInput ? recipientInput.value : '';
    if (!recipientUsername) {
        alert('Please select a user to message.');
        return;
    }
    fetch('/send-message/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCsrfToken(),
        },
        body: `recipient_username=${recipientUsername}&content=Hello! Let's start a conversation.`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            closeNewMessageModal();
            loadThread(data.thread_id);
        } else {
            alert(data.error);
        }
    });
}

// Thread Functions
function loadThread(threadId) {
    fetch(`/messages/${threadId}/`)
        .then(response => response.text())
        .then(html => {
            const messageContent = document.getElementById('messageContent');
            if (messageContent) {
                messageContent.innerHTML = html;
                // Re-attach the send message event listener after loading new content
                const sendMessageBtn = document.getElementById('sendMessageBtn');
                if (sendMessageBtn) {
                    const newThreadId = sendMessageBtn.getAttribute('data-thread-id');
                    sendMessageBtn.addEventListener('click', () => sendMessage(newThreadId));
                }
                // Auto-scroll to the bottom of the messages list
                const messagesList = document.getElementById('messagesList');
                if (messagesList) {
                    messagesList.scrollTop = messagesList.scrollHeight;
                }
            }
        });
}

function sendMessage(threadId) {
    const messageInput = document.getElementById('messageInput');
    const content = messageInput ? messageInput.value : '';
    if (!content) {
        alert('Please enter a message.');
        return;
    }

    fetch('/send-message/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCsrfToken(),
        },
        body: `thread_id=${threadId}&content=${encodeURIComponent(content)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const messagesList = document.getElementById('messagesList');
            if (messagesList) {
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message sent';
                messageDiv.innerHTML = `<p>${data.content}</p><small>${new Date(data.created_at).toLocaleString()}</small>`;
                messagesList.appendChild(messageDiv);
                messageInput.value = '';
                messagesList.scrollTop = messagesList.scrollHeight;
            }
        } else {
            alert(data.error);
        }
    });
}

// Utility Function to Get CSRF Token
function getCsrfToken() {
    const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
    return tokenElement ? tokenElement.value : '';
}

// Export the init function for dynamic import in main.js
export { init };

// Run init when DOM is loaded
document.addEventListener('DOMContentLoaded', init);