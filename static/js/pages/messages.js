// static/js/pages/messages.js
import { showEmojiPicker, showGifModal } from './post.js';

let defaultMessageContent = ''; // Store the default content of the messageContent area
let socket = null;

function init() {
    console.log('=== messages.js init() called ===');
    console.log('Document readyState:', document.readyState);
    console.log('Current URL:', window.location.href);
    console.log('All buttons in document:', document.querySelectorAll('button'));
    console.log('All elements with ID containing "Message":', document.querySelectorAll('[id*="Message"]'));
    console.log('Message content element:', document.getElementById('messageContent'));
    console.log('New message button:', document.getElementById('newMessageBtn'));
    console.log('Settings button:', document.getElementById('settingsBtn'));
    console.log('Send message button:', document.getElementById('sendMessageBtn'));

    const messageContent = document.getElementById('messageContent');
    if (messageContent) {
        defaultMessageContent = messageContent.innerHTML;
        console.log('Default message content stored:', defaultMessageContent);
    } else {
        console.log('messageContent not found on initial load');
    }

    // Handle new message button in header
    const newMessageBtn = document.getElementById('newMessageBtn');
    console.log('newMessageBtn element:', newMessageBtn);
    if (newMessageBtn) {
        console.log('Found newMessageBtn in header');
        newMessageBtn.addEventListener('click', function(e) {
            console.log('New message button clicked (header)');
            e.preventDefault();
            e.stopPropagation();
            openNewMessageModal();
        });
        console.log('Added click listener to newMessageBtn');
    }

    // Handle new message button in sidebar
    const newMessageSidebarBtn = document.getElementById('newMessageSidebarBtn');
    console.log('newMessageSidebarBtn element:', newMessageSidebarBtn);
    if (newMessageSidebarBtn) {
        console.log('Found newMessageSidebarBtn in sidebar');
        newMessageSidebarBtn.addEventListener('click', function(e) {
            console.log('New message button clicked (sidebar)');
            e.preventDefault();
            e.stopPropagation();
            openNewMessageModal();
        });
        console.log('Added click listener to newMessageSidebarBtn');
    }

    // Handle envelope icon
    const envelopeIcon = document.querySelector('.fa-envelope');
    console.log('envelopeIcon element:', envelopeIcon);
    if (envelopeIcon) {
        console.log('Found envelope icon');
        envelopeIcon.addEventListener('click', function(e) {
            console.log('Envelope icon clicked');
            e.preventDefault();
            e.stopPropagation();
            openNewMessageModal();
        });
        console.log('Added click listener to envelope icon');
    }

    // Rest of the init function...
    const closeModalBtn = document.getElementById('closeModalBtn');
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', closeNewMessageModal);
    }

    const recipientInput = document.getElementById('recipientUsername');
    if (recipientInput) {
        recipientInput.addEventListener('input', inputHandler);
    }

    const settingsBtn = document.getElementById('settingsBtn');
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

    const nextBtn = document.getElementById('nextBtn');
    if (nextBtn) {
        nextBtn.addEventListener('click', startNewConversation);
        console.log('Next button listener attached');
    }

    // Document-level delegation for thread cards
    document.addEventListener('click', (e) => {
        const threadCardTarget = e.target.closest('.card[data-thread-id]');
        if (threadCardTarget) {
            const threadCards = document.querySelectorAll('.card[data-thread-id]');
            threadCards.forEach(c => c.classList.remove('selected'));
            threadCardTarget.classList.add('selected');
            const threadId = threadCardTarget.getAttribute('data-thread-id');
            console.log('Thread card clicked, threadId:', threadId);
            
            // Connect to WebSocket for this thread
            connectWebSocket(threadId);
            
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
    console.log('Document-level delegation listener attached for thread cards');

    initializeActionButtons();

    const threadCards = document.querySelectorAll('.card[data-thread-id]');
    console.log('Thread cards found:', threadCards.length);
    // Remove duplicate event listeners since we're using document-level delegation

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

function connectWebSocket(threadId) {
    const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsPath = `${wsScheme}://${window.location.host}/ws/messages/${threadId}/`;
    
    if (socket) {
        socket.close();
    }
    
    socket = new WebSocket(wsPath);
    
    socket.onopen = function() {
        console.log('Direct message WebSocket connected');
    };
    
    socket.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'direct_message') {
                appendMessage({
                    content: data.message,
                    image: data.image_url,
                    gif_url: data.gif_url,
                    created_at: data.created_at,
                    thread_id: threadId
                });
            }
        } catch (e) {
            console.error('Error parsing direct message:', e);
        }
    };
    
    socket.onclose = function() {
        console.log('Direct message WebSocket closed');
    };
    
    socket.onerror = function(error) {
        console.error('Direct message WebSocket error:', error);
    };
}

async function sendMessage(threadId) {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    const sendBtn = document.querySelector('.send-btn');
    
    if (!message && !previewDiv.querySelector('img')) return;

    try {
        sendBtn.classList.add('loading');
        sendBtn.disabled = true;

        const formData = new FormData();
        formData.append('message', message);
        
        const imageFile = document.querySelector('input[type="file"]')?.files[0];
        if (imageFile) {
            formData.append('image', imageFile);
        }

        const response = await fetch(`/messages/send/${threadId}/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        if (!response.ok) {
            throw new Error('Failed to send message');
        }

        const data = await response.json();
        
        // Send via WebSocket if connected
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                'message': message,
                'image_url': data.image_url || null,
                'gif_url': data.gif_url || null
            }));
        }

        // Clear input and preview
        messageInput.value = '';
        messageInput.style.height = 'auto';
        previewDiv.innerHTML = '';
        previewDiv.style.display = 'none';
        
        // Refresh messages
        await fetchMessages(threadId);
    } catch (error) {
        console.error('Error sending message:', error);
        alert('Failed to send message. Please try again.');
    } finally {
        sendBtn.classList.remove('loading');
        sendBtn.disabled = false;
    }
}

function openNewMessageModal() {
    console.log('Opening new message modal...');
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
    }
    
    // Clear the search input
    if (searchInput) {
        searchInput.value = '';
    }
    
    // Clear any previous suggestions
    const suggestionsList = document.getElementById('userSuggestions');
    if (suggestionsList) {
        suggestionsList.innerHTML = '';
    }
    
    console.log('Modal opened successfully');
}

function closeNewMessageModal() {
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