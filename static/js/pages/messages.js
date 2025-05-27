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

// Giphy API Key
const GIPHY_API_KEY = 'Lpfo7GvcccncunU2gvf0Cy9N3NCzrg35';

// Modal functions
function showModal(modalId) {
    console.log('Showing modal:', modalId);
    const modal = document.getElementById(modalId);
    if (modal) {
        // Remove any existing modal classes first
        modal.classList.remove('modal');
        // Ensure the modal has the correct base class
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
        // Remove the show class first
        modal.classList.remove('show');
        // Keep only the messages-modal class
        modal.classList.remove('modal');
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

    // Ensure modal has only the correct class
    modal.classList.remove('modal');
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

    // Initialize search functionality
    if (userSearch) {
        userSearch.addEventListener('input', (e) => {
            searchUsers(e.target.value);
        });
    }

    console.log('Modal elements initialized successfully');
}

// Search functions
function searchUsers(query) {
    if (query.length < 2) {
        searchResults.innerHTML = '';
        return;
    }

    fetch(`/api/users/search/?q=${encodeURIComponent(query)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            searchResults.innerHTML = '';
            if (data.users && data.users.length > 0) {
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
            } else {
                searchResults.innerHTML = '<div class="no-results">No users found</div>';
            }
        })
        .catch(error => {
            console.error('Error searching users:', error);
            searchResults.innerHTML = '<div class="error-message">Error searching users. Please try again.</div>';
        });
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
            openThread(data.thread_id);
            // Clear selected users and reset next button
            selectedUsers.innerHTML = '';
            nextBtn.disabled = true;
            
            // Update thread header with user information
            const threadHeader = document.querySelector('.thread-header');
            if (threadHeader && data.user) {
                const avatarUrl = data.user.avatar || '/static/images/default-avatar.png';
                const username = data.user.username || 'Unknown User';
                
                threadHeader.innerHTML = `
                    <img src="${avatarUrl}" alt="Avatar" class="avatar">
                    <h3 class="thread-header-name">${username}</h3>
                `;
            }
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
            // Update thread header with user information
            const threadHeader = document.querySelector('.thread-header');
            if (threadHeader) {
                const avatarUrl = data.user?.avatar || '/static/images/default-avatar.png';
                const username = data.user?.username || 'Unknown User';
                
                threadHeader.innerHTML = `
                    <img src="${avatarUrl}" alt="Avatar" class="avatar">
                    <h3 class="thread-header-name">${username}</h3>
                `;
            }
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
    
    messagesList.innerHTML = '';
    if (data.messages && Array.isArray(data.messages)) {
        data.messages.forEach(message => {
            const messageElement = createMessageElement(message);
            messagesList.appendChild(messageElement);
        });
    }

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
        content: messageInput.value.trim()
    };

    fetch(`/api/messages/send/${currentThread}/`, {
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
            const messageElement = createMessageElement({
                content: data.content,
                sender: data.sender,
                created_at: data.created_at,
                is_sent: true
            });
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

// Function to show the emoji picker
async function showEmojiPicker(textarea, triggerButton, container = document.body) {
    // Remove any existing emoji picker in the container
    const existing = container.querySelector('#emoji-picker');
    if (existing) existing.remove();

    let emojiPicker = document.createElement('div');
    emojiPicker.id = 'emoji-picker';
    emojiPicker.className = 'emoji-picker';
    emojiPicker.innerHTML = `
        <div class="emoji-picker-content">
            <span class="emoji-picker-close">×</span>
            <input type="text" class="emoji-search" placeholder="Search emojis...">
            <div class="emoji-tabs">
                <button class="emoji-tab active" data-category="recent" title="Recent">🕒</button>
                <button class="emoji-tab" data-category="Smileys & Emotion" title="Smileys & People">😊</button>
                <button class="emoji-tab" data-category="Animals & Nature" title="Animals & Nature">🐾</button>
                <button class="emoji-tab" data-category="Food & Drink" title="Food & Drink">🍔</button>
                <button class="emoji-tab" data-category="Activities" title="Activities">⚽</button>
                <button class="emoji-tab" data-category="Travel & Places" title="Travel & Places">✈️</button>
                <button class="emoji-tab" data-category="Objects" title="Objects">💡</button>
                <button class="emoji-tab" data-category="Symbols" title="Symbols">❤️</button>
                <button class="emoji-tab" data-category="Flags" title="Flags">🏳️</button>
            </div>
            <div class="emoji-category-title"></div>
            <div class="emoji-grid"></div>
        </div>
    `;

    // Position the emoji picker above the message input
    const messageInput = document.querySelector('.message-input');
    const messageInputRect = messageInput.getBoundingClientRect();
    const triggerRect = triggerButton.getBoundingClientRect();
    
    emojiPicker.style.position = 'absolute';
    emojiPicker.style.bottom = `${window.innerHeight - messageInputRect.top + 10}px`;
    emojiPicker.style.left = `${triggerRect.left}px`;
    emojiPicker.style.zIndex = '1000';

    container.appendChild(emojiPicker);

    // Remove hidden class if it exists
    emojiPicker.classList.remove('hidden');

    const emojiGrid = emojiPicker.querySelector('.emoji-grid');
    const categoryTitle = emojiPicker.querySelector('.emoji-category-title');
    const searchInput = emojiPicker.querySelector('.emoji-search');
    const tabs = emojiPicker.querySelectorAll('.emoji-tab');
    let allEmojis = [];
    let recentEmojis = JSON.parse(localStorage.getItem('recentEmojis')) || [];

    // Fetch emoji data
    const loadEmojis = async () => {
        try {
            const response = await fetch('https://unpkg.com/emoji.json@14.0.0/emoji.json');
            const emojiData = await response.json();
            return emojiData;
        } catch (error) {
            return [
                { char: '😀', category: 'Smileys & Emotion', name: 'grinning face' },
                { char: '😂', category: 'Smileys & Emotion', name: 'face with tears of joy' },
                { char: '😍', category: 'Smileys & Emotion', name: 'smiling face with heart-eyes' },
                { char: '😢', category: 'Smileys & Emotion', name: 'crying face' },
                { char: '😡', category: 'Smileys & Emotion', name: 'pouting face' },
                { char: '👍', category: 'Smileys & Emotion', name: 'thumbs up' },
                { char: '👎', category: 'Smileys & Emotion', name: 'thumbs down' },
                { char: '❤️', category: 'Symbols', name: 'red heart' },
                { char: '🔥', category: 'Symbols', name: 'fire' },
                { char: '✨', category: 'Symbols', name: 'sparkles' }
            ];
        }
    };

    allEmojis = await loadEmojis();

    function renderEmojis(emojis) {
        emojiGrid.innerHTML = '';
        if (emojis.length === 0) {
            emojiGrid.innerHTML = '<p>No emojis found.</p>';
        } else {
            emojis.forEach(emoji => {
                const span = document.createElement('span');
                span.textContent = emoji.char;
                span.className = 'emoji-item';
                span.title = emoji.name;
                emojiGrid.appendChild(span);
            });
        }

        // Attach event delegation for emoji insertion
        emojiGrid.addEventListener('click', function(e) {
            const emojiItem = e.target.closest('.emoji-item');
            if (emojiItem) {
                const cursorPos = textarea.selectionStart;
                const textBefore = textarea.value.substring(0, cursorPos);
                const textAfter = textarea.value.substring(cursorPos);
                textarea.value = textBefore + emojiItem.textContent + textAfter;
                textarea.focus();
                textarea.selectionStart = textarea.selectionEnd = cursorPos + emojiItem.textContent.length;
                
                // Add to recent emojis
                recentEmojis = recentEmojis.filter(e => e !== emojiItem.textContent);
                recentEmojis.unshift(emojiItem.textContent);
                if (recentEmojis.length > 20) recentEmojis.pop();
                localStorage.setItem('recentEmojis', JSON.stringify(recentEmojis));
                
                emojiPicker.classList.add('hidden');
            }
        });
    }

    // Update category title
    function updateCategoryTitle(category) {
        const titles = {
            recent: 'Recent',
            'Smileys & Emotion': 'Smileys & People',
            'People & Body': 'People & Body',
            'Animals & Nature': 'Animals & Nature',
            'Food & Drink': 'Food & Drink',
            'Activities': 'Activities',
            'Travel & Places': 'Travel & Places',
            'Objects': 'Objects',
            'Symbols': 'Symbols',
            'Flags': 'Flags'
        };
        categoryTitle.textContent = titles[category] || '';
    }

    // Initial render (default to recent emojis)
    const activeTab = emojiPicker.querySelector('.emoji-tab.active');
    const initialCategory = activeTab ? activeTab.dataset.category : 'recent';
    if (initialCategory === 'recent') {
        renderEmojis(recentEmojis.map(char => ({ char })));
        updateCategoryTitle('recent');
    } else {
        const filteredEmojis = allEmojis.filter(emoji => {
            const topLevelCategory = emoji.category.split(' (')[0];
            return topLevelCategory === initialCategory;
        });
        renderEmojis(filteredEmojis);
        updateCategoryTitle(initialCategory);
    }

    // Tab switching
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            const category = tab.dataset.category;
            let filteredEmojis;
            if (category === 'recent') {
                filteredEmojis = recentEmojis.map(char => ({ char }));
            } else {
                filteredEmojis = allEmojis.filter(emoji => {
                    const topLevelCategory = emoji.category.split(' (')[0];
                    return topLevelCategory === category;
                });
            }
            renderEmojis(filteredEmojis);
            updateCategoryTitle(category);
            searchInput.value = '';
        });
    });

    // Search functionality
    searchInput.addEventListener('input', debounce((e) => {
        const query = e.target.value.toLowerCase().trim();
        const activeTab = emojiPicker.querySelector('.emoji-tab.active');
        const category = activeTab.dataset.category;
        let emojisToSearch = category === 'recent' 
            ? recentEmojis.map(char => ({ char, name: char }))
            : allEmojis.filter(emoji => {
                const topLevelCategory = emoji.category.split(' (')[0];
                return topLevelCategory === category;
            });
        
        if (query) {
            emojisToSearch = allEmojis.filter(emoji => 
                emoji.name.toLowerCase().includes(query) ||
                emoji.char.toLowerCase().includes(query) ||
                emoji.char.charCodeAt(0).toString(16).includes(query)
            );
            updateCategoryTitle('');
        } else {
            emojisToSearch = category === 'recent' 
                ? recentEmojis.map(char => ({ char, name: char }))
                : allEmojis.filter(emoji => {
                    const topLevelCategory = emoji.category.split(' (')[0];
                    return topLevelCategory === category;
                });
            updateCategoryTitle(category);
        }
        renderEmojis(emojisToSearch);
    }, 300));

    // Close button functionality
    const closeBtn = emojiPicker.querySelector('.emoji-picker-close');
    closeBtn.onclick = () => emojiPicker.classList.add('hidden');

    // Close on escape key
    window.addEventListener('keydown', function escHandler(e) {
        if (e.key === 'Escape') {
            emojiPicker.classList.add('hidden');
            window.removeEventListener('keydown', escHandler);
        }
    });

    // Close when clicking outside
    document.addEventListener('click', function outsideClickHandler(e) {
        if (!emojiPicker.contains(e.target) && e.target !== triggerButton) {
            emojiPicker.classList.add('hidden');
            document.removeEventListener('click', outsideClickHandler);
        }
    });
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

function setupEventListeners() {
    console.log('Setting up event listeners...');

    if (sendMessageBtn && messageInput) {
        sendMessageBtn.addEventListener('click', sendMessage);
        console.log('Send message event listeners attached');

        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        console.log('Message input event listeners attached');
    }

    if (newMessageBtn) {
        newMessageBtn.addEventListener('click', () => showModal('newMessageModal'));
        console.log('New message button event listener attached');
    }

    // Add emoji picker functionality
    const emojiBtn = document.querySelector('.action-btn[title="Add emoji"]');
    if (emojiBtn) {
        emojiBtn.addEventListener('click', (e) => {
            e.preventDefault();
            showEmojiPicker(messageInput, emojiBtn);
        });
        console.log('Emoji button event listener attached');
    }

    // Add click event listeners to message cards
    if (messagesFeedList) {
        messagesFeedList.addEventListener('click', (e) => {
            const card = e.target.closest('.card');
            if (card && card.dataset.threadId) {
                openThread(card.dataset.threadId);
            }
        });
        console.log('Message cards event listeners attached');
    }

    // Add hover effects to cards
    if (messagesFeedList) {
        messagesFeedList.addEventListener('mouseover', (e) => {
            const card = e.target.closest('.card');
            if (card) {
                card.classList.add('hover');
            }
        });

        messagesFeedList.addEventListener('mouseout', (e) => {
            const card = e.target.closest('.card');
            if (card) {
                card.classList.remove('hover');
            }
        });
        console.log('Card hover effects attached');
    }

    console.log('Event listeners setup completed');
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

    // Log initialization status
    console.log('Elements initialized:', {
        messagesFeed: !!messagesFeed,
        messageThread: !!messageThread,
        messageInput: !!messageInput,
        sendMessageBtn: !!sendMessageBtn,
        messagesList: !!messagesList,
        messagesFeedList: !!messagesFeedList,
        newMessageBtn: !!newMessageBtn
    });

    // Initialize modals
    initializeModals();

    // Setup event listeners
    setupEventListeners();

    // Load initial messages
    loadMessages();

    // Initialize WebSocket
    initializeWebSocket();

    console.log('Messages page initialized successfully');
}

// Make functions available globally for onclick handlers
window.showModal = showModal;
window.hideModal = hideModal;
window.searchUsers = searchUsers;
window.startNewConversation = startNewConversation; 