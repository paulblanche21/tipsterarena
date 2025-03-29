// static/js/pages/messages.js
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
    const settingsBtn = document.getElementById('settingsBtn'); // New settings button

    if (newMessageBtn) {
        newMessageBtn.addEventListener('click', openNewMessageModal);
    } else {
        console.log('newMessageBtn not found');
    }
    if (newMessageSidebarBtn) {
        newMessageSidebarBtn.addEventListener('click', openNewMessageModal);
    } else {
        console.log('newMessageSidebarBtn not found');
    }
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', closeNewMessageModal);
    } else {
        console.log('closeModalBtn not found');
    }
    if (recipientInput) {
        recipientInput.addEventListener('input', (e) => searchUsers(e.target.value));
    } else {
        console.log('recipientInput not found');
    }
    if (settingsBtn) {
        console.log('Attaching event listener to settings button');
        settingsBtn.addEventListener('click', () => {
            console.log('Settings button clicked');
            fetch('/messages/settings/', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest', // Indicate an AJAX request
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
                    // Add event listener for the close button after loading the settings panel
                    const closeSettingsBtn = document.getElementById('closeSettingsBtn');
                    if (closeSettingsBtn) {
                        closeSettingsBtn.addEventListener('click', () => {
                            console.log('Close settings button clicked');
                            if (messageContent) {
                                messageContent.innerHTML = defaultMessageContent;
                                console.log('Restored default message content');
                                // Reinitialize the new message sidebar button listener
                                const newMessageSidebarBtn = document.getElementById('newMessageSidebarBtn');
                                if (newMessageSidebarBtn) {
                                    newMessageSidebarBtn.addEventListener('click', openNewMessageModal);
                                } else {
                                    console.log('newMessageSidebarBtn not found after restoring default content');
                                }
                            }
                        });
                    } else {
                        console.log('closeSettingsBtn not found after loading settings');
                    }
                } else {
                    console.log('messageContent not found');
                }
            })
            .catch(error => {
                console.error('Fetch error:', error);
            });
        });
    } else {
        console.log('Settings button not found in DOM');
    }

    // Function to initialize action buttons (photo, GIF, emoji)
    function initializeActionButtons() {
        const photoBtn = document.querySelector('.action-btn[title="Add photo"]');
        const gifBtn = document.querySelector('.action-btn[title="Add GIF"]');
        const emojiBtn = document.querySelector('.action-btn[title="Add emoji"]');

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
                    alert(`Selected photo: ${file.name}`);
                }
            });
        } else {
            console.log('photoBtn not found');
        }

        if (gifBtn) {
            gifBtn.addEventListener('click', () => {
                alert('GIF functionality coming soon!');
            });
        } else {
            console.log('gifBtn not found');
        }

        if (emojiBtn) {
            emojiBtn.addEventListener('click', () => {
                alert('Emoji picker coming soon!');
            });
        } else {
            console.log('emojiBtn not found');
        }
    }

    // Initialize action buttons on initial load (if a thread is already selected)
    initializeActionButtons();

    // Thread Card Event Listeners
    const threadCards = document.querySelectorAll('.card[data-thread-id]');
    console.log('Thread cards found:', threadCards.length);
    threadCards.forEach(card => {
        card.addEventListener('click', () => {
            const threadId = card.getAttribute('data-thread-id');
            console.log('Thread card clicked, threadId:', threadId);
            fetch(`/messages/${threadId}/`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest', // Indicate an AJAX request
                },
            })
            .then(response => response.text())
            .then(html => {
                const messageContent = document.getElementById('messageContent');
                if (messageContent) {
                    messageContent.innerHTML = html;
                    // Re-initialize event listeners for the new content
                    const sendMessageBtn = document.getElementById('sendMessageBtn');
                    if (sendMessageBtn) {
                        const threadId = sendMessageBtn.getAttribute('data-thread-id');
                        sendMessageBtn.addEventListener('click', () => sendMessage(threadId));
                    } else {
                        console.log('sendMessageBtn not found after thread load');
                    }
                    const messagesList = document.getElementById('messagesList');
                    if (messagesList) {
                        messagesList.scrollTop = messagesList.scrollHeight;
                    } else {
                        console.log('messagesList not found after thread load');
                    }
                    // Re-initialize action buttons after thread load
                    initializeActionButtons();
                } else {
                    console.log('messageContent not found after thread load');
                }
            });
        });
    });

    // Send Message Event Listener
    const sendMessageBtn = document.getElementById('sendMessageBtn');
    if (sendMessageBtn) {
        const threadId = sendMessageBtn.getAttribute('data-thread-id');
        sendMessageBtn.addEventListener('click', () => sendMessage(threadId));
    } else {
        console.log('sendMessageBtn not found on initial load');
    }

    // Auto-scroll to the bottom of the messages list
    const messagesList = document.getElementById('messagesList');
    if (messagesList) {
        messagesList.scrollTop = messagesList.scrollHeight;
    } else {
        console.log('messagesList not found on initial load');
    }
}

// Modal Functions
function openNewMessageModal() {
    const modal = document.getElementById('newMessageModal');
    if (modal) {
        modal.style.display = 'block';
    } else {
        console.log('newMessageModal not found');
    }
}

function closeNewMessageModal() {
    const modal = document.getElementById('newMessageModal');
    const recipientInput = document.getElementById('recipientUsername');
    const suggestionsDiv = document.getElementById('userSuggestions');
    if (modal) {
        modal.style.display = 'none';
    } else {
        console.log('newMessageModal not found');
    }
    if (recipientInput) {
        recipientInput.value = '';
    } else {
        console.log('recipientInput not found in closeNewMessageModal');
    }
    if (suggestionsDiv) {
        suggestionsDiv.innerHTML = '';
    } else {
        console.log('suggestionsDiv not found in closeNewMessageModal');
    }
}

function searchUsers(query) {
    if (query.length < 2) {
        const suggestionsDiv = document.getElementById('userSuggestions');
        if (suggestionsDiv) {
            suggestionsDiv.innerHTML = '';
        } else {
            console.log('suggestionsDiv not found in searchUsers');
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
                        } else {
                            console.log('recipientInput not found in searchUsers click handler');
                        }
                        suggestionsDiv.innerHTML = '';
                        const nextBtn = document.getElementById('nextBtn');
                        if (nextBtn) {
                            nextBtn.disabled = false;
                        } else {
                            console.log('nextBtn not found in searchUsers click handler');
                        }
                    });
                    suggestionsDiv.appendChild(div);
                });
            } else {
                console.log('suggestionsDiv not found in searchUsers response handler');
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

function sendMessage(threadId) {
    const messageInput = document.getElementById('messageInput');
    const content = messageInput.value.trim();

    if (!content) {
        alert('Message cannot be empty');
        return;
    }

    const requestBody = JSON.stringify({
        thread_id: threadId,
        content: content,
    });
    console.log('Sending request to /send-message/ with body:', requestBody);

    fetch('/send-message/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
        },
        body: requestBody,
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
        } else {
            alert('Error sending message: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error sending message:', error);
        alert('Failed to send message. Please try again.');
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