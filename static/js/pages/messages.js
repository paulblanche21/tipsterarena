// static/js/pages/messages.js
import { showEmojiPicker, showGifModal } from './post.js';

let defaultMessageContent = ''; // Store the default content of the messageContent area

function init() {
    console.log('messages.js init() called');
    console.log('Document readyState in init():', document.readyState);

    // Store the default content of the messageContent area
    const messageContent = document.getElementById('messageContent');
    if (messageContent) {
        defaultMessageContent = messageContent.innerHTML;
        console.log('Default message content stored:', defaultMessageContent);
    } else {
        console.log('messageContent not found on initial load');
    }

    // Modal Event Listeners
    const newMessageBtn = document.getElementById('newMessageBtn');
    const newMessageSidebarBtn = document.getElementById('newMessageSidebarBtn');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const recipientInput = document.getElementById('recipientUsername');
    const settingsBtn = document.getElementById('settingsBtn');

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
    if (settingsBtn) {
        console.log('Attaching event listener to settings button');
        settingsBtn.addEventListener('click', () => {
            console.log('Settings button clicked');
            fetch('/messages/settings/', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            })
            .then(response => {
                console.log('Fetch response status:', response.status);
                return response.text();
            })
            .then(html => {
                const messageContent = document.getElementById('messageContent');
                console.log('Message content element:', messageContent);
                console.log('Fetched HTML:', html);
                if (messageContent) {
                    messageContent.innerHTML = html;
                    const closeSettingsBtn = document.getElementById('closeSettingsBtn');
                    if (closeSettingsBtn) {
                        closeSettingsBtn.addEventListener('click', () => {
                            console.log('Close settings button clicked');
                            if (messageContent) {
                                messageContent.innerHTML = defaultMessageContent;
                                console.log('Restored default message content');
                                const newMessageSidebarBtn = document.getElementById('newMessageSidebarBtn');
                                if (newMessageSidebarBtn) {
                                    newMessageSidebarBtn.addEventListener('click', openNewMessageModal);
                                }
                            }
                        });
                    }
                }
            })
            .catch(error => {
                console.error('Fetch error:', error);
            });
        });
    }

    // Function to initialize action buttons (photo, GIF, emoji)
    function initializeActionButtons() {
        const photoBtn = document.querySelector('.action-btn[title="Add image"]');
        const gifBtn = document.querySelector('.action-btn[title="Add GIF"]');
        const emojiBtn = document.querySelector('.action-btn[title="Add emoji"]');
        const messageInput = document.getElementById('messageInput');
        const previewDiv = document.querySelector('.msg-message-preview');

        if (!messageInput || !previewDiv) {
            console.log('messageInput or msg-message-preview not found');
            return;
        }

        // Photo functionality
        if (photoBtn) {
            const photoInput = document.createElement('input');
            photoInput.type = 'file';
            photoInput.accept = 'image/*';
            photoInput.style.display = 'none';
            document.body.appendChild(photoInput);

            photoBtn.addEventListener('click', () => {
                photoInput.click();
            });

            photoInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = (event) => {
                        const previewImg = previewDiv.querySelector('.msg-preview-media');
                        previewImg.src = event.target.result;
                        previewDiv.style.display = 'block';
                        messageInput.dataset.imageFile = 'true';
                        messageInput.dataset.image = file; // Store the file for sending
                        messageInput.dataset.gifUrl = ''; // Clear any GIF URL
                    };
                    reader.readAsDataURL(file);
                }
            });
        }

        // GIF functionality
        if (gifBtn) {
            gifBtn.addEventListener('click', () => {
                showGifModal(messageInput, previewDiv);
            });
        }

        // Emoji functionality
        if (emojiBtn) {
            emojiBtn.addEventListener('click', () => {
                showEmojiPicker(messageInput, emojiBtn);
            });
        }

        // Remove preview functionality
        const removePreviewBtn = previewDiv.querySelector('.msg-remove-preview');
        if (removePreviewBtn) {
            removePreviewBtn.addEventListener('click', () => {
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

    // Initialize action buttons on initial load (if a thread is already selected)
    initializeActionButtons();

    // Thread Card Event Listeners
    const threadCards = document.querySelectorAll('.card[data-thread-id]');
    console.log('Thread cards found:', threadCards.length);
    threadCards.forEach(card => {
        card.addEventListener('click', () => {
            threadCards.forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');

            const threadId = card.getAttribute('data-thread-id');
            console.log('Thread card clicked, threadId:', threadId);
            fetch(`/messages/${threadId}/`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            })
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
            });
        });
    });

    // Send Message Event Listener
    const sendMessageBtn = document.getElementById('sendMessageBtn');
    if (sendMessageBtn) {
        const threadId = sendMessageBtn.getAttribute('data-thread-id');
        sendMessageBtn.addEventListener('click', () => sendMessage(threadId));
    }

    const messagesList = document.getElementById('messagesList');
    if (messagesList) {
        messagesList.scrollTop = messagesList.scrollHeight;
    }
}

function appendMessage(data) {
    const messagesList = document.getElementById('messagesList');
    if (!messagesList) {
        console.log('messagesList not found');
        return;
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message sent';
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

function sendMessage(threadId) {
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendMessageBtn');
    const previewDiv = document.querySelector('.msg-message-preview');
    const content = messageInput.value.trim();

    if (!content && !messageInput.dataset.imageFile && !messageInput.dataset.gifUrl) {
        alert('Message content, image, or GIF must be provided');
        return;
    }

    sendButton.disabled = true;
    sendButton.textContent = 'Sending...';

    const formData = new FormData();
    formData.append('thread_id', threadId);
    formData.append('content', content);
    if (messageInput.dataset.imageFile && messageInput.dataset.image) {
        const photoInput = document.querySelector('input[type="file"][accept="image/*"]');
        if (photoInput && photoInput.files[0]) {
            formData.append('image', photoInput.files[0]);
        }
    }
    if (messageInput.dataset.gifUrl) {
        formData.append('gif_url', messageInput.dataset.gifUrl);
    }

    fetch('/send-message/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
        },
        body: formData,
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(text => {
                throw new Error(`HTTP error! Status: ${response.status}, Response: ${text}`);
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            appendMessage(data);
            messageInput.value = '';
            messageInput.dataset.imageFile = '';
            messageInput.dataset.gifUrl = '';
            previewDiv.style.display = 'none';
            const photoInput = document.querySelector('input[type="file"][accept="image/*"]');
            if (photoInput) photoInput.value = '';
        } else {
            alert('Error sending message: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error sending message:', error);
        alert('Failed to send message. Please try again.');
    })
    .finally(() => {
        sendButton.disabled = false;
        sendButton.textContent = 'Send';
    });
}

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
                        const nextBtn = document.getElementById('nextBtn');
                        if (nextBtn) {
                            nextBtn.disabled = false;
                        }
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
            window.location.href = `/messages/${data.thread_id}/`;
        } else {
            alert(data.error);
        }
    });
}

function getCsrfToken() {
    const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!tokenElement) {
        console.log('CSRF token element not found');
    }
    return tokenElement ? tokenElement.value : '';
}

export { init };