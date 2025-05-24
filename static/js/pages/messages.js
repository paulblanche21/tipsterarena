document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const messagesFeed = document.querySelector('.messages-feed');
    const messageThread = document.querySelector('.message-thread');
    const messageInput = document.getElementById('messageInput');
    const sendMessageBtn = document.getElementById('sendMessageBtn');
    const messagesList = document.querySelector('.messages-list');
    const newMessageBtn = document.querySelector('.messages-new');

    // State
    let currentThread = null;
    let currentUser = null;

    // Initialize
    function init() {
        loadMessages();
        setupEventListeners();
    }

    // Load messages
    function loadMessages() {
        fetch('/api/messages')
            .then(response => response.json())
            .then(data => {
                renderMessagesFeed(data);
            })
            .catch(error => {
                console.error('Error loading messages:', error);
            });
    }

    // Render messages feed
    function renderMessagesFeed(messages) {
        messagesFeed.innerHTML = '';
        
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
        currentThread = threadId;
        
        // Update active state in feed
        document.querySelectorAll('.card').forEach(card => {
            card.classList.toggle('active', card.dataset.threadId === threadId);
        });

        // Load thread messages
        fetch(`/api/messages/${threadId}`)
            .then(response => response.json())
            .then(data => {
                renderThread(data);
            })
            .catch(error => {
                console.error('Error loading thread:', error);
            });
    }

    // Render thread
    function renderThread(data) {
        currentUser = data.user;
        
        // Update thread header
        const threadHeader = document.querySelector('.thread-header');
        threadHeader.innerHTML = `
            <img src="${data.user.avatar || '/static/images/default-avatar.png'}" alt="Avatar" class="avatar">
            <h3 class="thread-header-name">${data.user.username}</h3>
        `;

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
        if (!currentThread || !messageInput.value.trim()) return;

        const message = {
            thread_id: currentThread,
            content: messageInput.value.trim()
        };

        fetch('/api/messages/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(message)
        })
        .then(response => response.json())
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
        });
    }

    // Setup event listeners
    function setupEventListeners() {
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
        newMessageBtn.addEventListener('click', () => {
            // TODO: Implement new message modal
            console.log('New message clicked');
        });
    }

    // Helper function to format dates
    function formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        
        // Less than 24 hours
        if (diff < 24 * 60 * 60 * 1000) {
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
        
        // Less than 7 days
        if (diff < 7 * 24 * 60 * 60 * 1000) {
            return date.toLocaleDateString([], { weekday: 'short' });
        }
        
        // Otherwise show full date
        return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }

    // Initialize the app
    init();
}); 