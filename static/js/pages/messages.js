// static/js/pages/messages.js
import { showEmojiPicker, showGifModal } from './post.js';

let defaultMessageContent = ''; // Store the default content of the messageContent area
let socket = null;
let currentThreadId = null;
let reconnectAttempts = 0;
let heartbeatInterval = null;
const MAX_RECONNECT_ATTEMPTS = 5;
const HEARTBEAT_INTERVAL = 30000; // 30 seconds

export function initializeWebSocket(threadId = null) {
    console.log('Initializing WebSocket connection...');
    const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsPath = threadId 
        ? `${wsScheme}://${window.location.host}/ws/messages/${threadId}/`
        : `${wsScheme}://${window.location.host}/ws/messages/`;
    
    if (socket) {
        console.log('Closing existing WebSocket connection');
        clearInterval(heartbeatInterval);
        socket.close();
    }
    
    try {
        socket = new WebSocket(wsPath);
        
        socket.onopen = function() {
            console.log('WebSocket connected for', threadId ? `thread ${threadId}` : 'messages');
            reconnectAttempts = 0;
            
            // Start heartbeat
            heartbeatInterval = setInterval(() => {
                if (socket.readyState === WebSocket.OPEN) {
                    socket.send(JSON.stringify({ type: 'heartbeat' }));
                }
            }, HEARTBEAT_INTERVAL);
        };
        
        socket.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                
                // Handle heartbeat acknowledgment
                if (data.type === 'heartbeat_ack') {
                    return;
                }
                
                // Handle direct messages
                if (data.type === 'direct_message') {
                    appendMessage({
                        content: data.message,
                        image: data.image_url,
                        gif_url: data.gif_url,
                        created_at: data.created_at,
                        sender: data.sender,
                        thread_id: threadId
                    });
                }
            } catch (e) {
                console.error('Error parsing WebSocket message:', e);
            }
        };
        
        socket.onclose = function() {
            console.log('WebSocket closed');
            clearInterval(heartbeatInterval);
            
            // Attempt to reconnect if we haven't exceeded max attempts
            if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                reconnectAttempts++;
                console.log(`Attempting to reconnect (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`);
                setTimeout(() => initializeWebSocket(threadId), 2000);
            }
        };
        
        socket.onerror = function(error) {
            console.error('WebSocket error:', error);
        };
        
        currentThreadId = threadId;
    } catch (error) {
        console.error('Error initializing WebSocket:', error);
    }
}

export function init() {
    console.log('Initializing messages page...');
    
    // Initialize action buttons if a thread is already selected
    const selectedThread = document.querySelector('.message-thread');
    if (selectedThread) {
        initializeActionButtons();
    }
    
    // Set up event listeners for message threads
    const cards = document.querySelectorAll('.card');
    console.log('Found message cards:', cards.length);
    
    cards.forEach(card => {
        if (card.dataset.threadId) {
            console.log('Setting up click handler for card:', card.dataset.threadId);
            // Remove any existing click handlers
            card.removeEventListener('click', handleCardClick);
            // Add new click handler
            card.addEventListener('click', handleCardClick);
        }
    });
    
    // Set up event listeners for new message buttons
    const newMessageBtn = document.querySelector('.messages-new');
    const newMessageBtnAlt = document.getElementById('newMessageBtn');
    const newMessageSidebarBtn = document.getElementById('newMessageSidebarBtn');
    
    console.log('Found message buttons:', {
        newMessageBtn: newMessageBtn,
        newMessageBtnAlt: newMessageBtnAlt,
        newMessageSidebarBtn: newMessageSidebarBtn
    });
    
    const handleNewMessageClick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        console.log('New message button clicked');
        showNewMessageModal();
    };
    
    // Remove all existing event listeners first
    if (newMessageBtn) {
        newMessageBtn.replaceWith(newMessageBtn.cloneNode(true));
        const newBtn = document.querySelector('.messages-new');
        newBtn.addEventListener('click', handleNewMessageClick);
    }
    
    if (newMessageBtnAlt) {
        newMessageBtnAlt.replaceWith(newMessageBtnAlt.cloneNode(true));
        const newBtnAlt = document.getElementById('newMessageBtn');
        newBtnAlt.addEventListener('click', handleNewMessageClick);
    }
    
    if (newMessageSidebarBtn) {
        newMessageSidebarBtn.replaceWith(newMessageSidebarBtn.cloneNode(true));
        const newSidebarBtn = document.getElementById('newMessageSidebarBtn');
        newSidebarBtn.addEventListener('click', handleNewMessageClick);
    }
    
    // Set up event listener for close modal button
    const closeModalBtn = document.getElementById('closeModalBtn');
    if (closeModalBtn) {
        closeModalBtn.replaceWith(closeModalBtn.cloneNode(true));
        const newCloseBtn = document.getElementById('closeModalBtn');
        newCloseBtn.addEventListener('click', handleCloseModal);
    }
    
    // Set up event listener for settings button
    const settingsBtn = document.getElementById('settingsBtn');
    if (settingsBtn) {
        console.log('Attaching event listener to settings button');
        settingsBtn.replaceWith(settingsBtn.cloneNode(true));
        const newSettingsBtn = document.getElementById('settingsBtn');
        newSettingsBtn.addEventListener('click', handleSettingsClick);
    }
    
    // Initialize WebSocket connection only if we're in a thread view
    if (selectedThread) {
        const threadId = selectedThread.dataset.threadId;
        if (threadId) {
            initializeWebSocket(threadId);
        }
    } else {
        initializeWebSocket();
    }
}

// Event handler functions
function handleCardClick(e) {
    e.preventDefault();
    e.stopPropagation();
    console.log('Card clicked:', this.dataset.threadId);
    loadThread(this.dataset.threadId);
}

function handleCloseModal(e) {
    e.preventDefault();
    e.stopPropagation();
    hideNewMessageModal();
}

function handleSettingsClick(e) {
    e.preventDefault();
    e.stopPropagation();
    console.log('Settings button clicked');
    showSettings();
}

// Call init when the DOM is loaded
document.addEventListener('DOMContentLoaded', init);

function initializeActionButtons() {
    console.log('Initializing action buttons...');
    
    // Use IDs instead of title attributes for more reliable selection
    const photoBtn = document.getElementById('imageBtn');
    const gifBtn = document.getElementById('gifBtn');
    const emojiBtn = document.getElementById('emojiBtn');
    const messageInput = document.getElementById('messageInput');
    const previewDiv = document.querySelector('.msg-message-preview');

    console.log('Found buttons:', {
        photoBtn: photoBtn,
        gifBtn: gifBtn,
        emojiBtn: emojiBtn,
        messageInput: messageInput,
        previewDiv: previewDiv
    });

    // Only initialize if we're in a thread view
    if (!messageInput || !previewDiv) {
        console.log('No thread selected - action buttons not initialized');
        return;
    }

    // Add auto-resize functionality
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    if (photoBtn) {
        console.log('Setting up photo button...');
        const photoInput = document.createElement('input');
        photoInput.type = 'file';
        photoInput.accept = 'image/*';
        photoInput.style.display = 'none';
        document.body.appendChild(photoInput);

        photoBtn.addEventListener('click', () => {
            console.log('Photo button clicked');
            photoInput.click();
        });

        photoInput.addEventListener('change', (e) => {
            console.log('Photo selected');
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    const previewImg = previewDiv.querySelector('.msg-preview-media');
                    previewImg.src = event.target.result;
                    previewDiv.style.display = 'block';
                    messageInput.dataset.imageFile = 'true';
                    messageInput.dataset.image = file;
                    messageInput.dataset.gifUrl = '';
                };
                reader.readAsDataURL(file);
            }
        });
    }

    if (gifBtn) {
        console.log('Setting up GIF button...');
        gifBtn.addEventListener('click', () => {
            console.log('GIF button clicked');
            showGifModal(messageInput, previewDiv);
        });
    }

    if (emojiBtn) {
        console.log('Setting up emoji button...');
        emojiBtn.addEventListener('click', () => {
            console.log('Emoji button clicked');
            showEmojiPicker(messageInput, emojiBtn);
        });
    }

    const removePreviewBtn = previewDiv.querySelector('.msg-remove-preview');
    if (removePreviewBtn) {
        console.log('Setting up remove preview button...');
        removePreviewBtn.addEventListener('click', () => {
            console.log('Remove preview clicked');
            previewDiv.style.display = 'none';
            messageInput.dataset.imageFile = '';
            messageInput.dataset.gifUrl = '';
            if (photoBtn) {
                const photoInput = document.querySelector('input[type="file"][accept="image/*"]');
                if (photoInput) photoInput.value = '';
            }
        });
    }
}

export function appendMessage(data) {
    const messagesList = document.getElementById('messagesList');
    if (!messagesList) {
        console.log('messagesList not found');
        return;
    }

    const messagesContainer = document.querySelector('.messages-container');
    const isCurrentUser = data.sender === messagesContainer.getAttribute('data-username');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isCurrentUser ? 'sent' : 'received'}`;
    messageDiv.innerHTML = `
        <p>${data.content}</p>
        ${data.image ? `<img src="${data.image}" alt="Message Image" class="msg-message-image">` : ''}
        ${data.gif_url ? `<img src="${data.gif_url}" alt="Message GIF" class="msg-message-image">` : ''}
        <small>${new Date(data.created_at).toLocaleString()}</small>
    `;

    messagesList.appendChild(messageDiv);
    messagesList.scrollTop = messagesList.scrollHeight;

    updateMessageFeedCard(data.thread_id, data.content || (data.image ? '[Image]' : '[GIF]'));
}

function updateMessageFeedCard(threadId, latestMessage) {
    const card = document.querySelector(`.card[data-thread-id="${threadId}"]`);
    if (!card) {
        console.log('Card not found for threadId:', threadId);
        return;
    }

    const messagePreview = card.querySelector('.message-preview');
    if (messagePreview) {
        messagePreview.textContent = latestMessage.length > 50 ? latestMessage.substring(0, 47) + '...' : latestMessage;
    }

    const messageDate = card.querySelector('.message-date');
    if (messageDate) {
        messageDate.textContent = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }

    const messagesFeed = document.querySelector('.messages-feed');
    if (messagesFeed) {
        messagesFeed.insertBefore(card, messagesFeed.firstChild.nextSibling);
    }
}

async function sendMessage(threadId) {
    console.log('Sending message to thread:', threadId);
    const messageInput = document.getElementById('messageInput');
    const previewDiv = document.querySelector('.msg-message-preview');
    const previewImg = previewDiv.querySelector('.msg-preview-media');
    
    if (!messageInput || !messageInput.value.trim() && !messageInput.dataset.imageFile && !messageInput.dataset.gifUrl) {
        console.log('No message content to send');
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('content', messageInput.value.trim());
        
        if (messageInput.dataset.imageFile) {
            formData.append('image', messageInput.dataset.image);
        }
        
        if (messageInput.dataset.gifUrl) {
            formData.append('gif_url', messageInput.dataset.gifUrl);
        }
        
        const response = await fetch(`/messages/send/${threadId}/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCsrfToken(),
            },
        });
        
        if (!response.ok) {
            throw new Error('Failed to send message');
        }
        
        const data = await response.json();
        
        if (data.success) {
            // Clear input and preview
            messageInput.value = '';
            messageInput.style.height = 'auto';
            messageInput.dataset.imageFile = '';
            messageInput.dataset.gifUrl = '';
            previewDiv.style.display = 'none';
            previewImg.src = '';
            
            // Re-initialize action buttons
            initializeActionButtons();
            
            // Scroll to bottom
            const messagesList = document.querySelector('.messages-list');
            if (messagesList) {
                messagesList.scrollTop = messagesList.scrollHeight;
            }
        } else {
            throw new Error(data.error || 'Failed to send message');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        alert('Failed to send message. Please try again.');
    }
}

function showNewMessageModal() {
    console.log('Showing new message modal...');
    const modal = document.getElementById('newMessageModal');
    if (!modal) {
        console.error('Modal element not found');
        return;
    }
    console.log('Found modal element:', modal);
    
    // Show the modal
    modal.style.display = 'block';
    // Force a reflow
    modal.offsetHeight;
    // Add the show class
    modal.classList.add('show');
    
    // Focus the search input
    const searchInput = document.getElementById('recipientUsername');
    if (searchInput) {
        searchInput.focus();
    }
    
    // Clear any previous selections
    const selectedUsers = document.getElementById('selectedUsers');
    if (selectedUsers) {
        selectedUsers.innerHTML = '';
    }
    
    // Reset the next button
    const nextBtn = document.getElementById('nextBtn');
    if (nextBtn) {
        nextBtn.disabled = true;
        nextBtn.addEventListener('click', startNewConversation);
    }
    
    // Clear the search input
    if (searchInput) {
        searchInput.value = '';
    }
    
    // Clear any suggestions
    const suggestionsList = document.getElementById('userSuggestions');
    if (suggestionsList) {
        suggestionsList.innerHTML = '';
    }
    
    // Add event listener for the search input
    if (searchInput) {
        searchInput.addEventListener('input', inputHandler);
    }
}

function hideNewMessageModal() {
    console.log('Closing new message modal...');
    const modal = document.getElementById('newMessageModal');
    if (!modal) {
        console.error('Modal element not found');
        return;
    }
    
    // Remove the show class
    modal.classList.remove('show');
    // Wait for the transition to complete
    setTimeout(() => {
        modal.style.display = 'none';
    }, 300);
    
    // Clear any selections
    const selectedUsers = document.getElementById('selectedUsers');
    if (selectedUsers) {
        selectedUsers.innerHTML = '';
    }
    
    // Reset the next button
    const nextBtn = document.getElementById('nextBtn');
    if (nextBtn) {
        nextBtn.disabled = true;
    }
    
    // Clear the search input
    const searchInput = document.getElementById('recipientUsername');
    if (searchInput) {
        searchInput.value = '';
    }
    
    // Clear any suggestions
    const suggestionsList = document.getElementById('userSuggestions');
    if (suggestionsList) {
        suggestionsList.innerHTML = '';
    }
    
    // Remove event listener for the search input
    if (searchInput) {
        searchInput.removeEventListener('input', inputHandler);
    }
    
    console.log('Modal closed successfully');
}

function inputHandler(e) {
    searchUsers(e.target.value);
}

function searchUsers(query) {
    if (query.length < 2) {
        const suggestionsDiv = document.getElementById('userSuggestions');
        if (suggestionsDiv) {
            suggestionsDiv.innerHTML = '';
        }
        return;
    }
    fetch(`/api/suggested-users/`, { method: 'GET' })
        .then(response => response.json())
        .then(data => {
            console.log('Suggested users fetched:', data);
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
                        const nextBtn = document.getElementById('nextBtn');
                        if (nextBtn) {
                            nextBtn.disabled = false;
                            console.log('Next button enabled');
                        } else {
                            console.log('nextBtn not found in suggestion click');
                        }
                    });
                    suggestionsDiv.appendChild(div);
                });
            }
        })
        .catch(error => console.error('Error fetching suggested users:', error));
}

function startNewConversation() {
    const recipientInput = document.getElementById('recipientUsername');
    const recipientUsername = recipientInput ? recipientInput.value : '';
    if (!recipientUsername) {
        alert('Please select a user to message.');
        return;
    }
    console.log('Starting conversation with:', recipientUsername);
    fetch('/messages/send/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCsrfToken(),
        },
        body: `recipient_username=${recipientUsername}&content=Hello! Let's start a conversation.`
    })
    .then(response => {
        console.log('Send message response status:', response.status);
        if (!response.ok) {
            throw new Error('Failed to send message');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            console.log('Message sent successfully:', data);
            // Hide the new message modal
            hideNewMessageModal();
            
            // Load the thread view
            fetch(`/messages/${data.thread_id}/`)
                .then(response => response.text())
                .then(html => {
                    const messageContent = document.getElementById('messageContent');
                    if (messageContent) {
                        messageContent.innerHTML = html;
                        const sendMessageBtn = document.getElementById('sendMessageBtn');
                        if (sendMessageBtn) {
                            const threadId = sendMessageBtn.getAttribute('data-thread-id');
                            sendMessageBtn.addEventListener('click', () => sendMessage(threadId));
                        }
                        const messagesList = document.getElementById('messagesList');
                        if (messagesList) {
                            messagesList.scrollTop = messagesList.scrollHeight;
                        }
                        initializeActionButtons();
                    }
                    // Update the message feed card
                    updateMessageFeedCard(data.thread_id, "Hello! Let's start a conversation.");
                })
                .catch(error => console.error('Error loading thread:', error));
        } else {
            alert('Error: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error starting conversation:', error);
        alert('Failed to start conversation. Please try again.');
    });
}

function getCsrfToken() {
    const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!tokenElement) {
        console.log('CSRF token element not found');
    }
    return tokenElement ? tokenElement.value : '';
}

async function fetchMessages(threadId) {
    try {
        const response = await fetch(`/messages/${threadId}/`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch messages');
        }
        
        const html = await response.text();
        const messageContent = document.getElementById('messageContent');
        if (messageContent) {
            messageContent.innerHTML = html;
            const messagesList = document.getElementById('messagesList');
            if (messagesList) {
                messagesList.scrollTop = messagesList.scrollHeight;
            }
            initializeActionButtons();
        }
    } catch (error) {
        console.error('Error fetching messages:', error);
    }
}

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

export function loadThread(threadId) {
    console.log('Loading thread:', threadId);
    try {
        fetch(`/messages/${threadId}/`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to load thread');
                }
                return response.text();
            })
            .then(html => {
                // Update the thread content
                const messageContent = document.getElementById('messageContent');
                if (messageContent) {
                    messageContent.innerHTML = html;
                    
                    // Wait for DOM to update
                    setTimeout(() => {
                        // Initialize action buttons after thread content is loaded
                        initializeActionButtons();
                        
                        // Scroll to bottom of messages
                        const messagesList = document.querySelector('.messages-list');
                        if (messagesList) {
                            messagesList.scrollTop = messagesList.scrollHeight;
                        }
                    }, 0);
                }
                
                // Update active state in the feed
                document.querySelectorAll('.card').forEach(card => {
                    card.classList.remove('active');
                    if (card.dataset.threadId === threadId) {
                        card.classList.add('active');
                    }
                });
                
                // Store the current thread ID
                currentThreadId = threadId;
                
                // Connect to thread-specific WebSocket
                initializeWebSocket(threadId);
            })
            .catch(error => {
                console.error('Error loading thread:', error);
                alert('Failed to load thread. Please try again.');
            });
    } catch (error) {
        console.error('Error loading thread:', error);
        alert('Failed to load thread. Please try again.');
    }
}

export function showSettings() {
    console.log('Showing message settings...');
    const settingsModal = document.createElement('div');
    settingsModal.className = 'modal';
    settingsModal.id = 'messageSettingsModal';
    
    // Fetch the message settings template
    fetch('/message-settings/')
        .then(response => response.text())
        .then(html => {
            settingsModal.innerHTML = html;
            document.body.appendChild(settingsModal);
            
            // Show the modal
            settingsModal.style.display = 'block';
            // Force a reflow
            settingsModal.offsetHeight;
            // Add the show class
            settingsModal.classList.add('show');
            
            // Add event listener for close button
            const closeBtn = settingsModal.querySelector('.close-settings');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => {
                    settingsModal.classList.remove('show');
                    setTimeout(() => {
                        settingsModal.remove();
                    }, 300);
                });
            }
            
            // Add event listeners for radio buttons
            const radioButtons = settingsModal.querySelectorAll('input[type="radio"]');
            radioButtons.forEach(radio => {
                radio.addEventListener('change', (e) => {
                    const value = e.target.value;
                    // Save the setting
                    fetch('/api/message-settings/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCsrfToken(),
                        },
                        body: JSON.stringify({
                            allow_messages: value
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            console.log('Message settings updated successfully');
                        } else {
                            console.error('Failed to update message settings:', data.error);
                        }
                    })
                    .catch(error => {
                        console.error('Error updating message settings:', error);
                    });
                });
            });
        })
        .catch(error => {
            console.error('Error loading message settings:', error);
        });
}