// Elements
let messagesFeed;
let messageThread;
let messageInput;
let sendMessageBtn;
let messagesList;
let newMessageBtn;

// State
let currentThread = null;
let currentUser = null;

// Initialize
export function init() {
    console.log('Initializing messages page...');
    
    // Initialize elements
    messagesFeed = document.querySelector('.messages-feed');
    messageThread = document.querySelector('.message-thread');
    messageInput = document.getElementById('messageInput');
    sendMessageBtn = document.getElementById('sendMessageBtn');
    messagesList = document.querySelector('.messages-list');
    newMessageBtn = document.querySelector('.messages-new');

    // Only proceed if we have the required elements
    if (!messagesFeed || !messageThread || !messageInput || !sendMessageBtn || !messagesList) {
        console.error('Required message elements not found');
        return;
    }

    // Initialize WebSocket connection
    console.log('Initializing WebSocket connection...');
    initializeWebSocket();

    // Load messages and setup event listeners
    loadMessages();
    setupEventListeners();
}

// Load messages
function loadMessages() {
    fetch('/api/messages/')  // Note the trailing slash
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            renderMessagesFeed(data);
        })
        .catch(error => {
            console.error('Error loading messages:', error);
            // Show error state in UI
            if (messagesFeed) {
                messagesFeed.innerHTML = `
                    <div class="error-message">
                        <p>Unable to load messages. Please try again later.</p>
                        <button class="retry-btn" onclick="loadMessages()">Retry</button>
                    </div>
                `;
            }
        });
}

// Render messages feed
function renderMessagesFeed(messages) {
    if (!messagesFeed) return;
    
    messagesFeed.innerHTML = '';
    
    if (!messages || messages.length === 0) {
        messagesFeed.innerHTML = `
            <div class="no-messages">
                <p>No messages yet. Start a conversation!</p>
            </div>
        `;
        return;
    }
    
    messages.forEach(message => {
        const card = createMessageCard(message);
        messagesFeed.appendChild(card);
    });
}

// Create message card
function createMessageCard(message) {
    const card = document.createElement('div');
    card.className = 'card';
    card.dataset.threadId = message.thread_id;
    
    card.innerHTML = `
        <img src="${message.avatar || '/static/images/default-avatar.png'}" alt="Avatar" class="avatar">
        <div class="card-content">
            <div class="card-header">
                <span class="username">${message.username}</span>
                <span class="message-date">${formatDate(message.last_message_date)}</span>
            </div>
            <div class="message-preview">${message.last_message}</div>
        </div>
    `;

    card.addEventListener('click', () => openThread(message.thread_id));
    return card;
}

// Open thread
function openThread(threadId) {
    if (!threadId) return;
    
    currentThread = threadId;
    
    // Update active state in feed
    document.querySelectorAll('.card').forEach(card => {
        card.classList.toggle('active', card.dataset.threadId === threadId);
    });

    // Load thread messages
    fetch(`/api/messages/${threadId}/`)  // Note the trailing slash
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            renderThread(data);
        })
        .catch(error => {
            console.error('Error loading thread:', error);
            // Show error state in UI
            if (messagesList) {
                messagesList.innerHTML = `
                    <div class="error-message">
                        <p>Unable to load conversation. Please try again later.</p>
                        <button class="retry-btn" onclick="openThread('${threadId}')">Retry</button>
                    </div>
                `;
            }
        });
}

// Render thread
function renderThread(data) {
    if (!messagesList) return;
    
    currentUser = data.user;
    
    // Update thread header
    const threadHeader = document.querySelector('.thread-header');
    if (threadHeader) {
        threadHeader.innerHTML = `
            <img src="${data.user.avatar || '/static/images/default-avatar.png'}" alt="Avatar" class="avatar">
            <h3 class="thread-header-name">${data.user.username}</h3>
        `;
    }

    // Render messages
    messagesList.innerHTML = '';
    data.messages.forEach(message => {
        const messageElement = createMessageElement(message);
        messagesList.appendChild(messageElement);
    });

    // Scroll to bottom
    messagesList.scrollTop = messagesList.scrollHeight;
}

// Create message element
function createMessageElement(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${message.is_sent ? 'sent' : 'received'}`;
    
    messageDiv.innerHTML = `
        <p>${message.content}</p>
        <small>${formatDate(message.timestamp)}</small>
    `;

    return messageDiv;
}

// Send message
function sendMessage() {
    if (!currentThread || !messageInput || !messageInput.value.trim()) return;

    const message = {
        thread_id: currentThread,
        content: messageInput.value.trim()
    };

    fetch('/api/messages/send/', {  // Note the trailing slash
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(message)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            messageInput.value = '';
            const messageElement = createMessageElement(data.message);
            messagesList.appendChild(messageElement);
            messagesList.scrollTop = messagesList.scrollHeight;
        }
    })
    .catch(error => {
        console.error('Error sending message:', error);
        // Show error state in UI
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = 'Failed to send message. Please try again.';
        messagesList.appendChild(errorDiv);
    });
}

// Setup event listeners
function setupEventListeners() {
    if (!sendMessageBtn || !messageInput) return;

    // Send message on button click
    sendMessageBtn.addEventListener('click', sendMessage);

    // Send message on Enter (but allow Shift+Enter for new line)
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // New message button
    if (newMessageBtn) {
        newMessageBtn.addEventListener('click', () => {
            // TODO: Implement new message modal
            console.log('New message clicked');
        });
    }
}

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Helper function to format dates
function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    // Less than 24 hours
    if (diff < 24 * 60 * 60 * 1000) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    // Less than 7 days
    if (diff < 7 * 24 * 60 * 60 * 1000) {
        return date.toLocaleTimeString([], { weekday: 'short' });
    }
    
    // Otherwise show full date
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

// Initialize WebSocket connection
function initializeWebSocket() {
    const ws_scheme = window.location.protocol === "https:" ? "wss" : "ws";
    const ws_path = `${ws_scheme}://${window.location.host}/ws/messages/`;
    const messagesSocket = new WebSocket(ws_path);

    messagesSocket.onopen = function(e) {
        console.log('WebSocket connected for messages');
    };

    messagesSocket.onmessage = function(e) {
        try {
            const data = JSON.parse(e.data);
            // Handle incoming messages
            if (data.type === 'message') {
                if (currentThread === data.thread_id) {
                    const messageElement = createMessageElement(data.message);
                    messagesList.appendChild(messageElement);
                    messagesList.scrollTop = messagesList.scrollHeight;
                }
                // Refresh the messages feed to update the preview
                loadMessages();
            }
        } catch (error) {
            console.error('Error processing WebSocket message:', error);
        }
    };

    messagesSocket.onclose = function(e) {
        console.log('WebSocket disconnected for messages');
        // Attempt to reconnect after 5 seconds
        setTimeout(initializeWebSocket, 5000);
    };

    messagesSocket.onerror = function(error) {
        console.error('WebSocket error:', error);
    };
} 