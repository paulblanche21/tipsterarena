// Elements
let messagesFeed;
let messageThread;
let messageInput;
let sendMessageBtn;
let messagesList;
let messagesFeedList;
let newMessageBtn;
let modal;
let userSearch;
let searchResults;
let selectedUsers;
let nextBtn;

// State
let currentThread = null;
let currentUser = null;

// Modal functions
function showModal(modalId) {
    console.log('Showing modal:', modalId);
    const modal = document.getElementById(modalId);
    if (modal) {
        // First ensure the modal has the correct base class
        if (!modal.classList.contains('messages-modal')) {
            modal.classList.add('messages-modal');
        }
        // Then add the show class
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
        console.log('Modal classes after show:', modal.className);
    } else {
        console.error('Modal element not found:', modalId);
    }
}

function hideModal(modalId) {
    console.log('Hiding modal:', modalId);
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = '';
        console.log('Modal classes after hide:', modal.className);
    } else {
        console.error('Modal element not found:', modalId);
    }
}

// Initialize modal elements
function initializeModals() {
    console.log('Initializing modals...');
    modal = document.getElementById('newMessageModal');
    userSearch = document.getElementById('userSearch');
    searchResults = document.getElementById('searchResults');
    selectedUsers = document.getElementById('selectedUsers');
    nextBtn = document.querySelector('.next-btn');

    if (!modal || !userSearch || !searchResults || !selectedUsers || !nextBtn) {
        console.error('Missing modal elements:', {
            modal: !!modal,
            userSearch: !!userSearch,
            searchResults: !!searchResults,
            selectedUsers: !!selectedUsers,
            nextBtn: !!nextBtn
        });
        return;
    }

    // Ensure modal has the correct class
    if (!modal.classList.contains('messages-modal')) {
        modal.classList.add('messages-modal');
    }

    // Add event listeners for modal
    const closeButtons = modal.querySelectorAll('.close-modal, .cancel-btn');
    closeButtons.forEach(button => {
        button.addEventListener('click', () => hideModal('newMessageModal'));
    });

    // Close modal when clicking outside
    modal.addEventListener('click', (event) => {
        if (event.target === modal) {
            hideModal('newMessageModal');
        }
    });

    console.log('Modal elements initialized successfully');
}

// Search functions
function searchUsers(query) {
    if (query.length < 2) {
        searchResults.innerHTML = '';
        return;
    }

    fetch(`/api/users/search/?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            searchResults.innerHTML = '';
            data.users.forEach(user => {
                const userElement = document.createElement('div');
                userElement.className = 'user-result';
                userElement.innerHTML = `
                    <img src="${user.avatar || '/static/images/default-avatar.png'}" alt="${user.username}">
                    <div class="user-info">
                        <span class="username">${user.username}</span>
                        <span class="handle">@${user.username}</span>
                    </div>
                `;
                userElement.addEventListener('click', () => selectUser(user));
                searchResults.appendChild(userElement);
            });
        })
        .catch(error => console.error('Error searching users:', error));
}

function selectUser(user) {
    const selectedUser = document.createElement('div');
    selectedUser.className = 'selected-user';
    selectedUser.dataset.userId = user.id;
    selectedUser.innerHTML = `
        <img src="${user.avatar || '/static/images/default-avatar.png'}" alt="${user.username}">
        <span>${user.username}</span>
        <button class="remove-user">&times;</button>
    `;
    
    selectedUser.querySelector('.remove-user').addEventListener('click', () => {
        selectedUser.remove();
        nextBtn.disabled = selectedUsers.children.length === 0;
    });
    
    selectedUsers.appendChild(selectedUser);
    nextBtn.disabled = false;
    userSearch.value = '';
    searchResults.innerHTML = '';
}

function startNewConversation() {
    const userIds = Array.from(selectedUsers.children).map(el => el.dataset.userId);
    
    fetch('/api/messages/start/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            user_ids: userIds
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            hideModal('newMessageModal');
            loadMessageThread(data.thread_id);
        }
    })
    .catch(error => console.error('Error starting conversation:', error));
}

// Message handling functions
function loadMessages() {
    fetch('/api/messages/')
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
            if (messagesFeedList) {
                messagesFeedList.innerHTML = `
                    <div class="error-message">
                        <p>Unable to load messages. Please try again later.</p>
                        <button class="retry-btn" onclick="loadMessages()">Retry</button>
                    </div>
                `;
            }
        });
}

function renderMessagesFeed(messages) {
    if (!messagesFeedList) return;

    messagesFeedList.innerHTML = '';

    if (!messages || messages.length === 0) {
        messagesFeedList.innerHTML = `
            <div class="no-messages">
                <p>No messages yet. Start a conversation!</p>
            </div>
        `;
        return;
    }

    messages.forEach(message => {
        const card = createMessageCard(message);
        messagesFeedList.appendChild(card);
    });
}

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

function openThread(threadId) {
    if (!threadId) return;
    
    currentThread = threadId;
    
    document.querySelectorAll('.card').forEach(card => {
        card.classList.toggle('active', card.dataset.threadId === threadId);
    });

    fetch(`/api/messages/thread/${threadId}/`)
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

function renderThread(data) {
    if (!messagesList) return;
    
    currentUser = data.user;
    
    const threadHeader = document.querySelector('.thread-header');
    if (threadHeader) {
        threadHeader.innerHTML = `
            <img src="${data.user.avatar || '/static/images/default-avatar.png'}" alt="Avatar" class="avatar">
            <h3 class="thread-header-name">${data.user.username}</h3>
        `;
    }

    messagesList.innerHTML = '';
    data.messages.forEach(message => {
        const messageElement = createMessageElement(message);
        messagesList.appendChild(messageElement);
    });

    messagesList.scrollTop = messagesList.scrollHeight;
}

function createMessageElement(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${message.is_sent ? 'sent' : 'received'}`;
    
    messageDiv.innerHTML = `
        <p>${message.content}</p>
        <small>${formatDate(message.timestamp)}</small>
    `;

    return messageDiv;
}

function sendMessage() {
    if (!currentThread || !messageInput || !messageInput.value.trim()) return;

    const message = {
        thread_id: currentThread,
        content: messageInput.value.trim()
    };

    fetch('/api/messages/send/', {
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
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = 'Failed to send message. Please try again.';
        messagesList.appendChild(errorDiv);
    });
}

function setupEventListeners() {
    if (!sendMessageBtn || !messageInput) return;

    sendMessageBtn.addEventListener('click', sendMessage);

    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    if (newMessageBtn) {
        newMessageBtn.addEventListener('click', () => showModal('newMessageModal'));
    }

    // Close modal when clicking outside
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                hideModal('newMessageModal');
            }
        });
    }
}

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
            if (data.type === 'message') {
                if (currentThread === data.thread_id) {
                    const messageElement = createMessageElement(data.message);
                    messagesList.appendChild(messageElement);
                    messagesList.scrollTop = messagesList.scrollHeight;
                }
                loadMessages();
            }
        } catch (error) {
            console.error('Error processing WebSocket message:', error);
        }
    };

    messagesSocket.onclose = function(e) {
        console.log('WebSocket disconnected for messages');
        setTimeout(initializeWebSocket, 5000);
    };

    messagesSocket.onerror = function(error) {
        console.error('WebSocket error:', error);
    };
}

// Helper functions
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

function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 24 * 60 * 60 * 1000) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    if (diff < 7 * 24 * 60 * 60 * 1000) {
        return date.toLocaleTimeString([], { weekday: 'short' });
    }
    
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

// Initialize
export function init() {
    console.log('Initializing messages page...');
    
    // Initialize elements
    messagesFeed = document.querySelector('.messages-feed');
    messageThread = document.querySelector('.message-thread');
    messageInput = document.getElementById('messageInput');
    sendMessageBtn = document.getElementById('sendMessageBtn');
    messagesList = document.getElementById('messagesList');
    messagesFeedList = document.getElementById('messagesFeedList');
    newMessageBtn = document.querySelector('.messages-new');

    // Initialize modals
    initializeModals();

    // Setup event listeners
    setupEventListeners();

    // Load initial messages
    loadMessages();

    console.log('Messages page initialized successfully');
}

// Make functions available globally for onclick handlers
window.showModal = showModal;
window.hideModal = hideModal;
window.searchUsers = searchUsers;
window.startNewConversation = startNewConversation; 