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

function connectWebSocket() {
    socket = new WebSocket(wsPath);

    socket.onopen = function() {
        console.log('Chat WebSocket connected');
    };

    socket.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'chat_message') {
                addMessageToFeed(data.username, data.message, data.image_url, data.gif_url, data.emoji, data.avatar_url);
            }
        } catch (e) {
            console.error('Error parsing chat message:', e);
        }
    };

    socket.onclose = function() {
        console.log('Chat WebSocket closed, reconnecting in 2s...');
        setTimeout(connectWebSocket, 2000);
    };

    socket.onerror = function(error) {
        console.error('WebSocket error:', error);
    };
}

connectWebSocket();

// DOM Elements
const chatForm = document.querySelector('.chat-input-form');
const chatInput = document.querySelector('.chat-input');
const chatMessages = document.querySelector('.chat-messages');
const emojiBtn = document.querySelector('.chat-action-btn.emoji');
const gifBtn = document.querySelector('.chat-action-btn.gif');
const imageBtn = document.querySelector('.chat-action-btn.image');
const imageInput = document.querySelector('.chat-image-input');

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

const onlineUsersSidebar = document.querySelector('.online-users-sidebar .profile-content');

// Helper to update online users list
function updateOnlineUsers(users) {
    const list = onlineUsersSidebar.querySelector('.online-users-list');
    list.innerHTML = '';
    users.forEach(([username, avatarUrl]) => {
        const li = document.createElement('li');
        li.style.marginBottom = '16px';
        li.style.display = 'flex';
        li.style.alignItems = 'center';
        li.innerHTML = `
            <img src="${avatarUrl}" alt="Avatar" style="width:28px;height:28px;border-radius:50%;object-fit:cover;margin-right:10px;">
            <span>${username === window.currentUsername ? '<strong>(You)</strong>' : username}</span>
        `;
        list.appendChild(li);
    });
}

// Listen for user_list events
if (socket) {
    socket.addEventListener('message', function(event) {
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'user_list') {
                updateOnlineUsers(data.users);
            }
        } catch (e) {}
    });
}

// Send message (with GIF/image support)
chatForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    const message = chatInput.value.trim();
    if (!message && !selectedGifUrl && !selectedImageFile) return;
    let payload = {
        type: 'chat_message',
        message: message,
        username: window.currentUsername || 'Anonymous',
        avatar_url: window.currentAvatarUrl || window.default_avatar_url,
    };
    if (selectedGifUrl) {
        payload.gif_url = selectedGifUrl;
    }
    if (selectedImageFile) {
        // Upload image to backend
        const formData = new FormData();
        formData.append('image', selectedImageFile);
        try {
            chatForm.querySelector('.chat-send-btn').disabled = true;
            const resp = await fetch('/api/upload-chat-image/', {
                method: 'POST',
                body: formData,
                credentials: 'same-origin',
            });
            const data = await resp.json();
            if (data.success && data.url) {
                payload.image_url = data.url;
            } else {
                alert('Image upload failed: ' + (data.error || 'Unknown error'));
                chatForm.querySelector('.chat-send-btn').disabled = false;
                return;
            }
        } catch (err) {
            alert('Image upload failed.');
            chatForm.querySelector('.chat-send-btn').disabled = false;
            return;
        }
    }
    socket.send(JSON.stringify(payload));
    chatInput.value = '';
    selectedGifUrl = '';
    selectedImageFile = null;
    chatPreviewDiv.style.display = 'none';
    chatPreviewDiv.querySelector('.preview-media').src = '';
    chatForm.querySelector('.chat-send-btn').disabled = false;
    imageInput.value = '';
});

// Add message to chat feed
function addMessageToFeed(username, message, imageUrl = null, gifUrl = null, emoji = null, avatarUrl = null) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'chat-message';
    msgDiv.style.marginBottom = '16px';
    const avatar = avatarUrl || window.default_avatar_url;
    msgDiv.innerHTML = `
        <img src="${avatar}" alt="Avatar" style="width:32px;height:32px;border-radius:50%;object-fit:cover;display:inline-block;vertical-align:middle;margin-right:10px;" onerror="this.src=window.default_avatar_url;">
        <span style="font-weight: bold;vertical-align:middle;">${escapeHtml(username)}:</span> ${escapeHtml(message)}
    `;
    if (imageUrl) {
        msgDiv.innerHTML += `<br><img src="${imageUrl}" alt="Image" style="max-width: 200px; max-height: 200px; border-radius: 8px; margin-top: 8px;">`;
    }
    if (gifUrl) {
        msgDiv.innerHTML += `<br><img src="${gifUrl}" alt="GIF" style="max-width: 200px; max-height: 200px; border-radius: 8px; margin-top: 8px;">`;
    }
    if (emoji) {
        msgDiv.innerHTML += ` <span>${emoji}</span>`;
    }
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
} 