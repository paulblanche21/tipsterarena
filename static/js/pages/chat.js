// static/js/pages/chat.js

import { showGifModal, showEmojiPicker } from './post.js';

// Utility to escape HTML (for safe message rendering)
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// WebSocket setup
const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
const wsPath = `${wsScheme}://${window.location.host}/ws/chat/`;
let socket = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 2000;

function connectWebSocket() {
    console.log('Attempting to connect to WebSocket...');
    socket = new WebSocket(wsPath);

    socket.onopen = function() {
        console.log('Chat WebSocket connected successfully');
        reconnectAttempts = 0;
        // Request initial user list immediately after connection
        socket.send(JSON.stringify({ type: 'request_user_list' }));
    };

    socket.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            console.log('Received WebSocket message:', data.type);
            if (data.type === 'chat_message') {
                addMessageToFeed(data.username, data.message, data.image_url, data.gif_url, data.emoji, data.avatar_url);
            } else if (data.type === 'chat_history') {
                // Clear existing messages
                chatMessages.innerHTML = '';
                // Add messages in reverse order (oldest first)
                data.messages.reverse().forEach(msg => {
                    addMessageToFeed(
                        msg.username,
                        msg.message,
                        msg.image_url,
                        msg.gif_url,
                        msg.emoji,
                        msg.avatar_url,
                        msg.created_at
                    );
                });
            } else if (data.type === 'user_list') {
                console.log('Updating user list with:', data.users);
                updateOnlineUsers(data.users);
                // Update online count
                const onlineCount = document.querySelector('.online-count');
                if (onlineCount) {
                    onlineCount.textContent = `${data.users.length} online`;
                }
            }
        } catch (e) {
            console.error('Error parsing chat message:', e);
        }
    };

    socket.onclose = function(event) {
        console.log('Chat WebSocket closed:', event.code, event.reason);
        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            reconnectAttempts++;
            console.log(`Reconnecting in ${RECONNECT_DELAY/1000}s... (Attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);
            setTimeout(connectWebSocket, RECONNECT_DELAY);
        } else {
            console.error('Max reconnection attempts reached');
            showError('Connection lost. Please refresh the page to reconnect.');
        }
    };

    socket.onerror = function(error) {
        console.error('WebSocket error:', error);
        showError('Connection error. Please check your internet connection.');
    };
}

// Error handling
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'chat-error';
    errorDiv.textContent = message;
    document.querySelector('.chat-container').insertBefore(errorDiv, document.querySelector('.chat-messages'));
    setTimeout(() => errorDiv.remove(), 5000);
}

// Connect when the page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Page loaded, connecting to WebSocket...');
    connectWebSocket();
    
    // Request user list again after a short delay to ensure connection is established
    setTimeout(() => {
        if (socket && socket.readyState === WebSocket.OPEN) {
            console.log('Requesting user list after delay...');
            socket.send(JSON.stringify({ type: 'request_user_list' }));
        }
    }, 1000);
});

// DOM Elements
const chatForm = document.querySelector('.chat-input-form');
const chatInput = document.querySelector('.chat-input');
const chatMessages = document.querySelector('.chat-messages');
const emojiBtn = document.querySelector('.chat-action-btn.emoji');
const gifBtn = document.querySelector('.chat-action-btn.gif');
const imageBtn = document.querySelector('.chat-action-btn.image');
const imageInput = document.querySelector('.chat-image-input');
const onlineUsersList = document.querySelector('.online-users-list');

// Add preview div for GIF/image (insert after chat input form if not present)
let chatPreviewDiv = document.querySelector('.chat-preview');
if (!chatPreviewDiv) {
    chatPreviewDiv = document.createElement('div');
    chatPreviewDiv.className = 'chat-preview';
    chatPreviewDiv.style.display = 'none';
    chatPreviewDiv.innerHTML = `
        <img src="" alt="Preview" class="preview-media" style="max-width: 200px; max-height: 200px; border-radius: 8px; margin-top: 8px;">
        <button class="remove-preview" style="margin-left: 8px;">×</button>
    `;
    chatForm.parentNode.insertBefore(chatPreviewDiv, chatForm.nextSibling);
}

let selectedGifUrl = '';
let selectedImageFile = null;

// Remove preview logic
const removePreviewBtn = chatPreviewDiv.querySelector('.remove-preview');
removePreviewBtn.addEventListener('click', () => {
    chatPreviewDiv.style.display = 'none';
    chatPreviewDiv.querySelector('.preview-media').src = '';
    selectedGifUrl = '';
    selectedImageFile = null;
    imageInput.value = '';
});

// Emoji button logic
emojiBtn.addEventListener('click', function(e) {
    e.preventDefault();
    showEmojiPicker(chatInput, emojiBtn);
});

gifBtn.addEventListener('click', function(e) {
    e.preventDefault();
    showGifModal(chatInput, chatPreviewDiv);
    // When a GIF is selected, showGifModal sets chatInput.dataset.gifUrl and preview
    // Listen for changes to chatInput.dataset.gifUrl
    const observer = new MutationObserver(() => {
        if (chatInput.dataset.gifUrl) {
            selectedGifUrl = chatInput.dataset.gifUrl;
            chatPreviewDiv.querySelector('.preview-media').src = selectedGifUrl;
            chatPreviewDiv.style.display = 'block';
        }
    });
    observer.observe(chatInput, { attributes: true, attributeFilter: ['data-gif-url'] });
});

imageBtn.addEventListener('click', function() {
    imageInput.click();
});

imageInput.addEventListener('change', function() {
    if (imageInput.files.length) {
        const file = imageInput.files[0];
        selectedImageFile = file;
        const reader = new FileReader();
        reader.onload = (event) => {
            chatPreviewDiv.querySelector('.preview-media').src = event.target.result;
            chatPreviewDiv.style.display = 'block';
        };
        reader.readAsDataURL(file);
    }
});

// Helper to update online users list
function updateOnlineUsers(users) {
    if (!onlineUsersList) return;
    onlineUsersList.innerHTML = '';
    users.forEach(([username, avatarUrl]) => {
        console.log('Rendering user:', username, 'Avatar URL:', avatarUrl);
        const li = document.createElement('li');
        li.className = 'online-user-item';
        // Use flexbox for alignment, and avoid nested <strong> in <span>
        li.innerHTML = `
            <img src="${avatarUrl}" alt="Avatar" class="online-user-avatar" onerror="this.src='${window.chatData.defaultAvatarUrl}'">
            <div class="user-info-flex">
                <span class="user-name">${username === window.chatData.currentUsername ? '(You)' : username}</span>
            </div>
            <span class="user-status"></span>
        `;
        onlineUsersList.appendChild(li);
    });
}

// Send message (with GIF/image support)
chatForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    const message = chatInput.value.trim();
    if (!message && !selectedGifUrl && !selectedImageFile) return;
    
    const sendButton = chatForm.querySelector('.chat-send-btn');
    sendButton.disabled = true;
    
    try {
        let payload = {
            type: 'chat_message',
            message: message,
            username: window.chatData.currentUsername || 'Anonymous',
            avatar_url: window.chatData.currentAvatarUrl || window.chatData.defaultAvatarUrl,
        };
        
        if (selectedGifUrl) {
            payload.gif_url = selectedGifUrl;
        }
        
        if (selectedImageFile) {
            // Upload image to backend
            const formData = new FormData();
            formData.append('image', selectedImageFile);
            
            const resp = await fetch('/api/upload-chat-image/', {
                method: 'POST',
                body: formData,
                credentials: 'same-origin',
            });
            
            const data = await resp.json();
            if (data.success && data.url) {
                payload.image_url = data.url;
            } else {
                throw new Error(data.error || 'Image upload failed');
            }
        }
        
        socket.send(JSON.stringify(payload));
        
        // Clear form
        chatInput.value = '';
        selectedGifUrl = '';
        selectedImageFile = null;
        chatPreviewDiv.style.display = 'none';
        chatPreviewDiv.querySelector('.preview-media').src = '';
        imageInput.value = '';
        
    } catch (err) {
        console.error('Error sending message:', err);
        showError('Failed to send message. Please try again.');
    } finally {
        sendButton.disabled = false;
    }
});

// Add message to chat feed
function addMessageToFeed(username, message, imageUrl = null, gifUrl = null, emoji = null, avatarUrl = null, timestamp = null) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'chat-message';
    
    // Use provided timestamp or current time
    const timeString = timestamp ? 
        new Date(timestamp).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }) :
        new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
    
    const avatar = avatarUrl || window.chatData.defaultAvatarUrl;
    msgDiv.innerHTML = `
        <img src="${avatar}" alt="Avatar" class="message-avatar" onerror="this.src='${window.chatData.defaultAvatarUrl}'">
        <div class="message-content">
            <div class="message-header">
                <span class="message-username">${escapeHtml(username)}</span>
                <span class="message-time">${timeString}</span>
            </div>
            <div class="message-text">${escapeHtml(message)}</div>
            ${imageUrl ? `<img src="${imageUrl}" alt="Image" class="message-media">` : ''}
            ${gifUrl ? `<img src="${gifUrl}" alt="GIF" class="message-media">` : ''}
            ${emoji ? `<span class="message-emoji">${emoji}</span>` : ''}
        </div>
    `;
    
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
} 