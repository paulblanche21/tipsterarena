// DOM Elements
let messagesFeed;
let messageThread;
let messageInput;
let sendMessageBtn;
let messagesList;
let messagesFeedList;
let newMessageBtn;
let imageBtn;
let emojiBtn;
let gifBtn;
let userSearch;
let searchResults;
let selectedUsersContainer;
let nextBtn;
let imageInput;
let newMessageModal;
let settingsModal;
let messageSocket = null;

// State
let currentThread = null;
let currentUser = null;
let isInitialized = false;
let searchTimeout = null;

// Giphy API Key
const GIPHY_API_KEY = 'Lpfo7GvcccncunU2gvf0Cy9N3NCzrg35';

// Modal functions
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) {
        console.error(`Modal with id ${modalId} not found`);
        return;
    }
    modal.classList.add('show');
    console.log(`Showing modal: ${modalId}`);
    console.log('Modal classes after show:', modal.className);
}

function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) {
        console.error(`Modal with id ${modalId} not found`);
        return;
    }
    modal.classList.remove('show');
    console.log(`Hiding modal: ${modalId}`);
}

// Initialize modal elements
function initializeModals() {
    console.log('Initializing modals...');
    
    // Initialize new message modal
    if (newMessageModal) {
        const closeBtn = newMessageModal.querySelector('.close-modal');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => hideModal('newMessageModal'));
        }
    }

    // Initialize settings modal
    if (settingsModal) {
        const closeBtn = settingsModal.querySelector('.close-settings');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => hideModal('settingsModal'));
        }
    }

    // Initialize search functionality
    if (userSearch) {
        userSearch.addEventListener('input', (e) => {
            searchUsers(e.target.value);
        });
    }

    console.log('Modal elements initialized successfully');
}

// Initialize elements
function initializeElements() {
    messagesFeed = document.querySelector('.messages-feed');
    messageThread = document.querySelector('.message-thread');
    messageInput = document.getElementById('messageInput');
    sendMessageBtn = document.getElementById('sendMessageBtn');
    messagesList = document.getElementById('messagesList');
    messagesFeedList = document.getElementById('messagesFeedList');
    newMessageBtn = document.querySelector('.messages-new');
    imageBtn = document.querySelector('.action-btn[title="Add image"]');
    emojiBtn = document.querySelector('.action-btn[title="Add emoji"]');
    gifBtn = document.querySelector('.action-btn[title="Add GIF"]');
    userSearch = document.getElementById('userSearch');
    searchResults = document.getElementById('searchResults');
    selectedUsersContainer = document.getElementById('selectedUsers');
    nextBtn = document.querySelector('.next-btn');
    newMessageModal = document.getElementById('newMessageModal');
    settingsModal = document.getElementById('settingsModal');
    
    imageInput = document.createElement('input');
    imageInput.type = 'file';
    imageInput.accept = 'image/*';
    imageInput.style.display = 'none';
    document.body.appendChild(imageInput);

    return {
        messagesFeed: !!messagesFeed,
        messageThread: !!messageThread,
        messageInput: !!messageInput,
        sendMessageBtn: !!sendMessageBtn,
        messagesList: !!messagesList,
        messagesFeedList: !!messagesFeedList,
        newMessageBtn: !!newMessageBtn,
        imageBtn: !!imageBtn,
        emojiBtn: !!emojiBtn,
        gifBtn: !!gifBtn,
        userSearch: !!userSearch,
        searchResults: !!searchResults,
        selectedUsersContainer: !!selectedUsersContainer,
        nextBtn: !!nextBtn,
        newMessageModal: !!newMessageModal,
        settingsModal: !!settingsModal
    };
}

// Search functions
function searchUsers(query) {
    if (!searchResults) {
        console.error('Search results container not found');
        return;
    }

    if (!query || query.length < 2) {
        searchResults.innerHTML = '';
        return;
    }

    // Clear any existing timeout
    if (searchTimeout) {
        clearTimeout(searchTimeout);
    }

    // Set a new timeout to debounce the search
    searchTimeout = setTimeout(() => {
        fetch(`/api/search-users/?q=${encodeURIComponent(query)}`)
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
                        userElement.className = 'search-result-item';
                        userElement.innerHTML = renderSearchResult(user);
                        userElement.onclick = () => selectUser(user);
                        searchResults.appendChild(userElement);
                    });
                } else {
                    searchResults.innerHTML = '<div class="no-results">No users found</div>';
                }
            })
            .catch(error => {
                console.error('Error searching users:', error);
                if (searchResults) {
                    searchResults.innerHTML = '<div class="error">Error searching users</div>';
                }
            });
    }, 300); // Wait 300ms after the user stops typing before searching
}

function renderSearchResult(user) {
    return `
        <div class="search-result-item" data-user-id="${user.id}">
            <img src="${user.avatar || '/static/img/default-avatar.png'}" alt="Avatar" class="avatar">
            <div class="user-info">
                <span class="message-username">${user.username}</span>
                <span class="message-handle">@${user.handle || user.username}</span>
            </div>
        </div>
    `;
}

function selectUser(user) {
    // Check if user is already selected
    const existingUser = selectedUsersContainer.querySelector(`[data-user-id="${user.id}"]`);
    if (existingUser) {
        existingUser.remove();
    } else {
        const userElement = document.createElement('div');
        userElement.className = 'selected-user';
        userElement.dataset.userId = user.id;
        userElement.innerHTML = renderSelectedUser(user);
        selectedUsersContainer.appendChild(userElement);
    }
    
    // Enable/disable next button based on selection
    nextBtn.disabled = selectedUsersContainer.children.length === 0;
}

function renderSelectedUser(user) {
    return `
        <div class="selected-user" data-user-id="${user.id}">
            <img src="${user.avatar || '/static/img/default-avatar.png'}" alt="Avatar" class="avatar">
            <span class="message-username">${user.username}</span>
            <button class="remove-user" onclick="removeSelectedUser(${user.id})">&times;</button>
        </div>
    `;
}

function removeUser(userId) {
    const userElement = selectedUsersContainer.querySelector(`[data-user-id="${userId}"]`);
    if (userElement) {
        userElement.remove();
    }
    nextBtn.disabled = selectedUsersContainer.children.length === 0;
}

async function startNewConversation() {
    const selectedUsers = Array.from(document.querySelectorAll('.selected-user')).map(el => el.dataset.userId);
    if (selectedUsers.length === 0) {
        alert('Please select at least one user to start a conversation');
        return;
    }

    try {
        const response = await fetch('/api/start-thread/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                user_ids: selectedUsers
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (data.success) {
            // Hide the modal
            hideModal('newMessageModal');
            
            // Clear selected users
            const selectedUsersContainer = document.getElementById('selectedUsers');
            if (selectedUsersContainer) {
                selectedUsersContainer.innerHTML = '';
            }
            
            // Clear search input
            const searchInput = document.getElementById('userSearch');
            if (searchInput) {
                searchInput.value = '';
            }
            
            // Clear search results
            const searchResults = document.getElementById('searchResults');
            if (searchResults) {
                searchResults.innerHTML = '';
            }

            // Update the message thread view
            const messageThread = document.querySelector('.message-thread');
            const threadHeader = messageThread.querySelector('.thread-header');
            const messagesList = document.getElementById('messagesList');
            const sendButton = document.getElementById('sendMessageBtn');

            if (threadHeader && data.user) {
                threadHeader.innerHTML = `
                    <img src="${data.user.avatar || '/static/img/default-avatar.png'}" alt="Avatar" class="avatar">
                    <h3 class="thread-header-name">${data.user.username}</h3>
                `;
            }

            // Set the thread ID on the send button
            if (sendButton) {
                sendButton.dataset.threadId = data.thread_id;
            }

            // Clear and load messages
            if (messagesList) {
                messagesList.innerHTML = '';
                await loadThread(data.thread_id);
            }

            // Update the messages feed
            await loadMessages();
        }
    } catch (error) {
        console.error('Error starting conversation:', error);
        alert('Failed to start conversation. Please try again.');
    }
}

// Message handling functions
function loadMessages() {
    fetch('/api/get-messages/')
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
                messagesFeedList.innerHTML = '<div class="error">Error loading messages</div>';
            }
        });
}

function renderMessagesFeed(messages) {
    if (!messagesFeedList) return;

    messagesFeedList.innerHTML = '';

    if (!messages || messages.length === 0) {
        messagesFeedList.innerHTML = `
            <div class="empty-state">
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
    
    // Add unread class if there are unread messages
    if (message.unread_count && message.unread_count > 0) {
        card.classList.add('has-unread');
    }
    
    card.innerHTML = `
        <div class="notification-dot"></div>
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

async function openThread(threadId) {
    if (!threadId) return;
    
    currentThread = threadId;
    
    // Remove unread indicator from the clicked card
    document.querySelectorAll('.card').forEach(card => {
        card.classList.toggle('active', card.dataset.threadId === threadId);
        if (card.dataset.threadId === threadId) {
            card.classList.remove('has-unread');
        }
    });

    try {
        const response = await fetch(`/messages/${threadId}/`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        if (data.success) {
            const messagesList = document.getElementById('messagesList');
            const sendButton = document.getElementById('sendMessageBtn');
            const threadHeader = document.querySelector('.thread-header');
            
            if (!messagesList) {
                console.error('Messages list container not found');
                return;
            }
            
            // Set the thread ID on the send button
            if (sendButton) {
                sendButton.dataset.threadId = threadId;
            }
            
            // Update thread header with user information
            if (threadHeader && data.other_participant) {
                const avatarImg = threadHeader.querySelector('.avatar');
                const nameElement = threadHeader.querySelector('.thread-header-name');
                
                if (avatarImg) {
                    avatarImg.src = data.other_participant.avatar || '/static/images/default-avatar.png';
                    avatarImg.alt = `${data.other_participant.username}'s avatar`;
                }
                
                if (nameElement) {
                    nameElement.textContent = data.other_participant.username;
                }
            }
            
            messagesList.innerHTML = '';
            data.messages.forEach(message => {
                const messageElement = createMessageElement({
                    id: message.id,
                    content: message.content,
                    image_url: message.image_url,
                    gif_url: message.gif_url,
                    created_at: message.created_at,
                    sender: message.sender.username,
                    is_sent: message.sender.username === window.currentUser
                });
                messagesList.appendChild(messageElement);
            });
            
            // Scroll to bottom
            messagesList.scrollTop = messagesList.scrollHeight;
            
            // Update WebSocket connection for this thread
            setupWebSocket();
            
            // Mark messages as read by calling the API
            await markMessagesAsRead(threadId);
        }
    } catch (error) {
        console.error('Error loading messages:', error);
        const messagesList = document.getElementById('messagesList');
        if (messagesList) {
            messagesList.innerHTML = '<div class="error">Error loading messages. Please try again.</div>';
        }
    }
}

function createMessageElement(message) {
    const messageDiv = document.createElement('div');
    // Determine if the message is sent by the current user
    const isSent = message.is_sent || message.sender === currentUser?.id;
    messageDiv.className = `message ${isSent ? 'sent' : 'received'}`;
    
    // Add message ID as data attribute
    if (message.id) {
        messageDiv.dataset.messageId = message.id;
    }
    
    let content = '';
    
    // Handle GIF messages
    if (message.gif_url) {
        content = `<img src="${message.gif_url}" alt="GIF" class="msg-message-image">`;
    } 
    // Handle image messages
    else if (message.image_url) {
        content = `<img src="${message.image_url}" alt="Image" class="msg-message-image">`;
    }
    // Handle text messages
    else if (message.content) {
        content = `<p>${message.content}</p>`;
    }
    
    messageDiv.innerHTML = `
        ${content}
        <small>${formatDate(message.timestamp || message.created_at)}</small>
    `;

    return messageDiv;
}

async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendMessageBtn');
    const threadId = sendButton?.dataset.threadId;
    
    if (!messageInput || !sendButton || !threadId) {
        console.error('Required elements not found for sending message:', {
            messageInput: !!messageInput,
            sendButton: !!sendButton,
            threadId: threadId
        });
        return;
    }

    const content = messageInput.value.trim();
    if (!content) return;

    try {
        const formData = new FormData();
        formData.append('content', content);
        formData.append('thread_id', threadId);

        const response = await fetch('/api/send-message/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (data.success) {
            messageInput.value = '';
            const messagesList = document.getElementById('messagesList');
            if (messagesList) {
                const messageElement = createMessageElement({
                    id: data.message_id,
                    content: content,
                    created_at: data.created_at,
                    sender: currentUser?.id,
                    is_sent: true
                });
                messagesList.appendChild(messageElement);
                messagesList.scrollTop = messagesList.scrollHeight;
            }
            
            // Refresh the messages feed to show the new message preview
            loadMessages();
        }
    } catch (error) {
        console.error('Error sending message:', error);
        const messagesList = document.getElementById('messagesList');
        if (messagesList) {
            const errorElement = document.createElement('div');
            errorElement.className = 'error';
            errorElement.textContent = 'Error sending message. Please try again.';
            messagesList.appendChild(errorElement);
        }
    }
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

// Function to show the GIF picker modal
function showGifPicker(textarea, previewDiv) {
    let gifModal = document.getElementById('msg-gif-modal');
    if (!gifModal) {
        gifModal = document.createElement('div');
        gifModal.id = 'msg-gif-modal';
        gifModal.className = 'msg-gif-modal';
        gifModal.innerHTML = `
            <div class="msg-gif-modal-content">
                <span class="msg-gif-modal-close">×</span>
                <input type="text" class="msg-gif-search-input" placeholder="Search GIFs...">
                <div class="msg-gif-results"></div>
            </div>
        `;
        document.body.appendChild(gifModal);
    }

    gifModal.style.display = 'block';
    gifModal.classList.add('show');

    const closeBtn = gifModal.querySelector('.msg-gif-modal-close');
    const searchInput = gifModal.querySelector('.msg-gif-search-input');
    const resultsDiv = gifModal.querySelector('.msg-gif-results');

    closeBtn.onclick = () => {
        gifModal.style.display = 'none';
        gifModal.classList.remove('show');
    };

    window.onclick = (event) => {
        if (event.target === gifModal) {
            gifModal.style.display = 'none';
            gifModal.classList.remove('show');
        }
    };

    searchInput.oninput = debounce((e) => {
        const query = e.target.value.trim();
        if (query) {
            fetch(`https://api.giphy.com/v1/gifs/search?api_key=${GIPHY_API_KEY}&q=${encodeURIComponent(query)}&limit=10`)
                .then(response => response.json())
                .then(data => {
                    resultsDiv.innerHTML = '';
                    if (data.data.length === 0) {
                        resultsDiv.innerHTML = '<p>No GIFs found.</p>';
                        return;
                    }
                    data.data.forEach(gif => {
                        const img = document.createElement('img');
                        img.src = gif.images.fixed_height.url;
                        img.alt = gif.title;
                        img.className = 'msg-gif-result';
                        img.onclick = () => {
                            // Send the GIF URL to the server first
                            console.log('GIF clicked, currentThread:', currentThread);
                            if (currentThread) {
                                const requestData = {
                                    content: '',
                                    gif_url: gif.images.original.url,
                                    thread_id: currentThread
                                };
                                console.log('Sending GIF request:', requestData);
                                
                                fetch(`/api/send-message/`, {
                                    method: 'POST',
                                    headers: {
                                        'Content-Type': 'application/json',
                                        'X-CSRFToken': getCookie('csrftoken')
                                    },
                                    body: JSON.stringify(requestData)
                                })
                                .then(response => {
                                    console.log('GIF response status:', response.status);
                                    return response.json();
                                })
                                .then(data => {
                                    console.log('GIF response data:', data);
                                    if (data.success) {
                                        // Only add the message to the UI after successful server confirmation
                                        const messageElement = createMessageElement({
                                            id: data.message_id,
                                            content: '',
                                            gif_url: gif.images.original.url,
                                            timestamp: data.created_at,
                                            sender: currentUser?.id,
                                            is_sent: true
                                        });
                                        messagesList.appendChild(messageElement);
                                        messagesList.scrollTop = messagesList.scrollHeight;
                                        
                                        // Refresh the messages feed to show the new message preview
                                        loadMessages();
                                    } else {
                                        console.error('Error sending GIF:', data.error);
                                    }
                                })
                                .catch(error => {
                                    console.error('Error sending GIF:', error);
                                });
                            } else {
                                console.error('No currentThread available for GIF');
                            }

                            // Close the modal
                            gifModal.style.display = 'none';
                            gifModal.classList.remove('show');
                        };
                        resultsDiv.appendChild(img);
                    });
                })
                .catch(error => {
                    console.error('Error fetching GIFs:', error);
                    resultsDiv.innerHTML = '<p>Error fetching GIFs. Please try again.</p>';
                });
        } else {
            resultsDiv.innerHTML = '';
        }
    }, 300);
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

    // Add image input change handler
    imageInput.addEventListener('change', handleImageSelect);

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

    // Add image picker functionality
    if (imageBtn) {
        imageBtn.addEventListener('click', (e) => {
            e.preventDefault();
            imageInput.click();
        });
        console.log('Image button event listener attached');
    }

    // Add emoji picker functionality
    if (emojiBtn) {
        emojiBtn.addEventListener('click', (e) => {
            e.preventDefault();
            showEmojiPicker(messageInput, emojiBtn);
        });
        console.log('Emoji button event listener attached');
    }

    // Add GIF picker functionality
    if (gifBtn) {
        gifBtn.addEventListener('click', (e) => {
            e.preventDefault();
            showGifPicker(messageInput, document.querySelector('.msg-message-preview'));
        });
        console.log('GIF button event listener attached');
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

// Handle image selection
function handleImageSelect(e) {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
        alert('Please select an image file');
        return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
        alert('Image size should be less than 5MB');
        return;
    }

    // Create FormData for multipart/form-data
    const formData = new FormData();
    formData.append('content', '');
    formData.append('image', file);
    
    // Add thread_id if we have a current thread
    if (currentThread) {
        formData.append('thread_id', currentThread);
        console.log('Image upload - currentThread:', currentThread);
    } else {
        console.error('No currentThread available for image upload');
        return;
    }

    // Disable the send button while sending
    const sendBtn = document.getElementById('sendMessageBtn');
    if (sendBtn) sendBtn.disabled = true;

    console.log('Sending image request to /api/send-message/');
    fetch('/api/send-message/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: formData
    })
    .then(response => {
        console.log('Image response status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Image response data:', data);
        if (data.success) {
            // Add the message to the UI only after server confirmation
            const messageElement = createMessageElement({
                id: data.message_id,
                content: '',
                image_url: data.image,
                timestamp: data.created_at,
                sender: currentUser?.id,
                is_sent: true
            });
            messagesList.appendChild(messageElement);
            messagesList.scrollTop = messagesList.scrollHeight;
            
            // Refresh the messages feed to show the new message preview
            loadMessages();
        }
    })
    .catch(error => {
        console.error('Error sending image:', error);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = 'Failed to send image. Please try again.';
        messagesList.appendChild(errorDiv);
    })
    .finally(() => {
        // Re-enable the send button
        if (sendBtn) sendBtn.disabled = false;
        // Clear the file input
        imageInput.value = '';
    });
}

// WebSocket functionality
function setupWebSocket() {
    // Close existing connection if any
    if (messageSocket) {
        messageSocket.close();
    }

    // Create new WebSocket connection
    const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsPath = currentThread 
        ? `${wsScheme}://${window.location.host}/ws/messages/${currentThread}/`
        : `${wsScheme}://${window.location.host}/ws/messages/`;
    
    try {
        messageSocket = new WebSocket(wsPath);

        messageSocket.onopen = function(e) {
            console.log('WebSocket connected for messages');
        };

        messageSocket.onmessage = function(e) {
            try {
                const data = JSON.parse(e.data);
                if (data.type === 'direct_message') {
                    // Add message to the UI
                    const messageElement = createMessageElement({
                        id: data.message_id,
                        content: data.message,
                        gif_url: data.gif_url,
                        image_url: data.image_url,
                        timestamp: data.created_at,
                        sender: data.sender,
                        is_sent: false
                    });
                    const messagesList = document.getElementById('messagesList');
                    if (messagesList) {
                        messagesList.appendChild(messageElement);
                        messagesList.scrollTop = messagesList.scrollHeight;
                    }
                    
                    // Update message list
                    updateMessageList();
                }
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        messageSocket.onclose = function(e) {
            console.log('WebSocket disconnected for messages');
            // Only try to reconnect if it wasn't a manual close
            if (e.code !== 1000) {
                setTimeout(setupWebSocket, 5000);
            }
        };

        messageSocket.onerror = function(e) {
            console.error('WebSocket error:', e);
        };
    } catch (error) {
        console.error('Error setting up WebSocket:', error);
    }
}

// Update WebSocket connection when thread changes
async function loadThread(threadId) {
    try {
        const response = await fetch(`/messages/${threadId}/`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        if (data.success) {
            const messagesList = document.getElementById('messagesList');
            if (!messagesList) {
                console.error('Messages list container not found');
                return;
            }
            
            messagesList.innerHTML = '';
            data.messages.forEach(message => {
                const messageElement = createMessageElement({
                    id: message.id,
                    content: message.content,
                    image_url: message.image_url,
                    gif_url: message.gif_url,
                    created_at: message.created_at,
                    sender: message.sender.username,
                    is_sent: message.sender.username === window.currentUser
                });
                messagesList.appendChild(messageElement);
            });
            
            // Scroll to bottom
            messagesList.scrollTop = messagesList.scrollHeight;
        }
    } catch (error) {
        console.error('Error loading messages:', error);
        const messagesList = document.getElementById('messagesList');
        if (messagesList) {
            messagesList.innerHTML = '<div class="error">Error loading messages. Please try again.</div>';
        }
    }
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

// Initialize function
export function init() {
    if (isInitialized) {
        console.log('Messages page already initialized, skipping...');
        return;
    }

    try {
        console.log('Initializing messages page...');
        
        // Initialize current user
        currentUser = window.currentUser;
        
        const elements = initializeElements();
        console.log('Elements initialized:', elements);
        
        if (elements.messagesFeed && elements.messageThread) {
            initializeModals();
            setupEventListeners();
            setupWebSocket();
            loadMessages();
            isInitialized = true;
            console.log('Messages page initialized successfully');
        } else {
            console.error('Required elements not found:', elements);
        }
    } catch (error) {
        console.error('Failed to initialize messages page:', error);
    }
}

// Make functions available globally
window.showModal = showModal;
window.hideModal = hideModal;
window.searchUsers = searchUsers;
window.selectUser = selectUser;
window.removeUser = removeUser;
window.startNewConversation = startNewConversation;
window.setupWebSocket = setupWebSocket;
window.loadThread = loadThread;

// Update message list
function updateMessageList() {
    // Refresh the messages feed
    loadMessages();
}

// Mark messages as read
async function markMessagesAsRead(threadId) {
    try {
        const response = await fetch(`/api/mark-messages-read/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                thread_id: threadId
            })
        });
        
        if (response.ok) {
            // Update the unread count in the messages feed
            loadMessages();
        }
    } catch (error) {
        console.error('Error marking messages as read:', error);
    }
} 