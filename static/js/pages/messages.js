// static/js/pages/messages.js
import { showEmojiPicker, showGifModal } from './post.js';

let defaultMessageContent = ''; // Store the default content of the messageContent area

function init() {
    console.log('messages.js init() called');
    console.log('Document readyState in init():', document.readyState);

    const messageContent = document.getElementById('messageContent');
    if (messageContent) {
        defaultMessageContent = messageContent.innerHTML;
        console.log('Default message content stored:', defaultMessageContent);
    } else {
        console.log('messageContent not found on initial load');
    }

    const newMessageBtn = document.getElementById('newMessageBtn');
    const newMessageSidebarBtn = document.getElementById('newMessageSidebarBtn');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const recipientInput = document.getElementById('recipientUsername');
    const settingsBtn = document.getElementById('settingsBtn');
    const nextBtn = document.getElementById('nextBtn');

    if (newMessageBtn) {
        newMessageBtn.addEventListener('click', () => {
            console.log('New message button clicked (direct listener)');
            openNewMessageModal();
        });
        console.log('New message button listener attached');
    }
    if (newMessageSidebarBtn) {
        newMessageSidebarBtn.addEventListener('click', openNewMessageModal);
        console.log('New message sidebar button listener attached');
    }
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', closeNewMessageModal);
    }
    if (recipientInput) {
        recipientInput.addEventListener('input', inputHandler);
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
            .then(response => response.text())
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
    if (nextBtn) {
        nextBtn.addEventListener('click', startNewConversation);
        console.log('Next button listener attached');
    }

    document.addEventListener('click', (e) => {
        const newMessageTarget = e.target.closest('#newMessageBtn');
        if (newMessageTarget) {
            console.log('New message button clicked (delegated listener)');
            openNewMessageModal();
            e.preventDefault();
            e.stopPropagation();
        }

        const threadCardTarget = e.target.closest('.card[data-thread-id]');
        if (threadCardTarget) {
            const threadCards = document.querySelectorAll('.card[data-thread-id]');
            threadCards.forEach(c => c.classList.remove('selected'));
            threadCardTarget.classList.add('selected');
            const threadId = threadCardTarget.getAttribute('data-thread-id');
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
            })
            .catch(error => console.error('Error loading thread:', error));
            e.preventDefault();
            e.stopPropagation();
        }
    });
    console.log('Document-level delegation listener attached for #newMessageBtn and thread cards');

    initializeActionButtons();

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
                    messageInput.dataset.image = file;
                    messageInput.dataset.gifUrl = '';
                };
                reader.readAsDataURL(file);
            }
        });
    }

    if (gifBtn) {
        gifBtn.addEventListener('click', () => {
            showGifModal(messageInput, previewDiv);
        });
    }

    if (emojiBtn) {
        emojiBtn.addEventListener('click', () => {
            showEmojiPicker(messageInput, emojiBtn);
        });
    }

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
    console.log('Opening new message modal');
    const modal = document.getElementById('newMessageModal');
    if (modal) {
        modal.style.display = 'block';
        modal.style.zIndex = '10000';
        console.log('Modal display set to block');

        const recipientInput = document.getElementById('recipientUsername');
        if (recipientInput) {
            recipientInput.removeEventListener('input', inputHandler);
            recipientInput.addEventListener('input', inputHandler);
            console.log('Recipient input listener reattached');
        } else {
            console.log('recipientUsername not found in modal');
        }

        const closeModalBtn = document.getElementById('closeModalBtn');
        if (closeModalBtn) {
            closeModalBtn.removeEventListener('click', closeNewMessageModal);
            closeModalBtn.addEventListener('click', closeNewMessageModal);
            console.log('Close modal button listener reattached');
        } else {
            console.log('closeModalBtn not found in modal');
        }

        const nextBtn = document.getElementById('nextBtn');
        if (nextBtn) {
            nextBtn.removeEventListener('click', startNewConversation);
            nextBtn.addEventListener('click', startNewConversation);
            nextBtn.disabled = true;
            console.log('Next button listener reattached and reset to disabled');
        } else {
            console.log('nextBtn not found in modal');
        }
    } else {
        console.log('Modal element not found');
    }
}

function closeNewMessageModal() {
    console.log('Closing new message modal');
    const modal = document.getElementById('newMessageModal');
    const recipientInput = document.getElementById('recipientUsername');
    const suggestionsDiv = document.getElementById('userSuggestions');
    if (modal) {
        modal.style.display = 'none';
        console.log('Modal hidden');
    } else {
        console.log('Modal element not found in closeNewMessageModal');
    }
    if (recipientInput) {
        recipientInput.value = '';
    }
    if (suggestionsDiv) {
        suggestionsDiv.innerHTML = '';
    }
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
    fetch('/send-message/', {
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
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Send message response data:', data);
        if (data.success) {
            closeNewMessageModal();
            fetch(`/messages/${data.thread_id}/`, {
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
                updateMessageFeedCard(data.thread_id, "Hello! Let's start a conversation.");
            })
            .catch(error => console.error('Error loading thread:', error));
        } else {
            alert('Error: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error sending message:', error);
        alert('Failed to start conversation. Check console for details.');
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