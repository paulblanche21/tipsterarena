// tips.js
import { getCSRFToken } from './utils.js';
import { applyFormatting, showGifModal } from './post.js'; // Import utilities from post.js

function setupTipInteractions() {
    const tips = document.querySelectorAll('.tip');
    const commentModal = document.getElementById('comment-modal');
    const commentSubmit = commentModal.querySelector('.post-reply-submit');
    const commentModalClose = commentModal.querySelector('.comment-modal-close');

    tips.forEach(tip => {
        tip.removeEventListener('click', handleTipClick);
        tip.addEventListener('click', handleTipClick);
    });

    // Fetch current user data (avatar and handle) on page load
    let currentUserData = { avatarUrl: DEFAULT_AVATAR_URL, handle: window.currentUser || 'You' };
    fetch('/api/current-user/', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            currentUserData = {
                avatarUrl: data.avatar_url || DEFAULT_AVATAR_URL,
                handle: data.handle || window.currentUser || 'You'
            };
        }
    })
    .catch(error => {
        console.error('Error fetching current user data:', error);
    });

    // Initialize the reply modal's post action buttons
    setupReplyModal();

    commentSubmit.addEventListener('click', function(e) {
        e.preventDefault();
        const tipId = this.dataset.tipId;
        const parentId = this.dataset.parentId;
        const commentInput = commentModal.querySelector('.post-reply-input');
        const commentText = commentInput.value.trim();

        if (!commentText) {
            alert('Please enter a reply.');
            return;
        }

        const formData = new FormData();
        formData.append('tip_id', tipId);
        formData.append('comment_text', commentText);
        if (parentId) formData.append('parent_id', parentId);

        // Append optional fields (image, GIF, location, etc.)
        const imageInput = commentModal.querySelector('.post-reply-image-input');
        if (commentInput.dataset.imageFile && imageInput && imageInput.files[0]) {
            formData.append('image', imageInput.files[0]);
        }
        if (commentInput.dataset.gifUrl) {
            formData.append('gif', commentInput.dataset.gifUrl);
        }
        const locationData = commentInput.dataset.locationData || '';
        if (locationData) {
            formData.append('location', locationData);
        }
        formData.append('poll', '{}');
        formData.append('emojis', '{}');

        const endpoint = parentId ? '/api/reply-to-comment/' : '/api/comment-tip/';
        fetch(endpoint, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCSRFToken(),
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const tip = document.querySelector(`.tip[data-tip-id="${tipId}"]`);
                const commentCount = tip.querySelector('.comment-count');
                commentCount.textContent = data.comment_count;
                const commentList = commentModal.querySelector('.comment-list');
                const newComment = document.createElement('div');
                newComment.className = 'comment';
                newComment.setAttribute('data-comment-id', data.comment_id);
                newComment.innerHTML = `
                    <img src="${currentUserData.avatarUrl}" alt="${currentUserData.handle} Avatar" class="comment-avatar" onerror="this.src='${DEFAULT_AVATAR_URL}'">
                    <div class="comment-content">
                        <a href="/profile/${window.currentUser}/" class="comment-username"><strong>${currentUserData.handle}</strong></a>
                        <p>${commentText}</p>
                        ${data.image ? `<img src="${data.image}" alt="Comment Image" class="comment-image">` : ''}
                        ${data.gif ? `<img src="${data.gif}" alt="Comment GIF" class="comment-image">` : ''}
                        <small>${new Date().toLocaleString()}</small>
                        <div class="comment-actions">
                            <div class="comment-action-group">
                                <a href="#" class="comment-action comment-action-like" data-action="like"><i class="fas fa-heart"></i></a>
                                <span class="comment-action-count like-count">0</span>
                            </div>
                            <div class="comment-action-group">
                                <a href="#" class="comment-action comment-action-share" data-action="share"><i class="fas fa-retweet"></i></a>
                                <span class="comment-action-count share-count">0</span>
                            </div>
                            <div class="comment-action-group">
                                <a href="#" class="comment-action comment-action-comment" data-action="comment"><i class="fas fa-comment-dots"></i></a>
                                <span class="comment-action-count comment-count">0</span>
                            </div>
                        </div>
                    </div>
                `;
                commentList.insertBefore(newComment, commentList.firstChild);
                commentInput.value = '';
                commentInput.dataset.imageFile = '';
                commentInput.dataset.gifUrl = '';
                commentInput.dataset.locationData = '';
                const previewDiv = commentModal.querySelector('.post-reply-preview');
                if (previewDiv) previewDiv.style.display = 'none';
                if (parentId) commentModal.querySelector('.reply-to-header').style.display = 'none';
                attachCommentActionListeners();
            } else {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error commenting on tip:', error);
            alert('An error occurred while commenting.');
        });
    });

    commentModalClose.addEventListener('click', function() {
        commentModal.style.display = 'none';
    });

    window.addEventListener('click', function(event) {
        if (event.target === commentModal) {
            commentModal.style.display = 'none';
        }
    });
}

function setupReplyModal() {
    const commentModal = document.getElementById('comment-modal');
    const replyInput = commentModal.querySelector('.post-reply-input');
    const boldBtn = commentModal.querySelector('.post-reply-box .post-action-btn.bold');
    const italicBtn = commentModal.querySelector('.post-reply-box .post-action-btn.italic');
    const imageBtn = commentModal.querySelector('.post-reply-box .post-action-btn.image');
    const gifBtn = commentModal.querySelector('.post-reply-box .post-action-btn.gif');
    const locationBtn = commentModal.querySelector('.post-reply-box .post-action-btn.location');
    const pollBtn = commentModal.querySelector('.post-reply-box .post-action-btn.poll');
    const scheduleBtn = commentModal.querySelector('.post-reply-box .post-action-btn.schedule');
    const previewDiv = commentModal.querySelector('.post-reply-box .post-reply-preview') || document.createElement('div');

    // Create preview div if it doesn't exist
    if (!previewDiv.className) {
        previewDiv.className = 'post-reply-preview';
        previewDiv.style.display = 'none';
        previewDiv.innerHTML = `
            <img src="" alt="Preview" class="preview-media">
            <button class="remove-preview">×</button>
        `;
        replyInput.parentNode.insertBefore(previewDiv, replyInput.nextSibling);
    }

    // Image functionality
    const imageInput = document.createElement('input');
    imageInput.type = 'file';
    imageInput.accept = 'image/*';
    imageInput.style.display = 'none';
    imageInput.className = 'post-reply-image-input';
    document.body.appendChild(imageInput);

    imageBtn.addEventListener('click', (e) => {
        e.preventDefault();
        imageInput.click();
    });

    imageInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (event) => {
                const previewImg = previewDiv.querySelector('.preview-media');
                previewImg.src = event.target.result;
                previewDiv.style.display = 'block';
                replyInput.dataset.imageFile = 'true';
            };
            reader.readAsDataURL(file);
        }
    });

    // GIF functionality
    gifBtn.addEventListener('click', (e) => {
        e.preventDefault();
        showGifModal(replyInput, previewDiv);
    });

    // Remove preview functionality
    const removePreviewBtn = previewDiv.querySelector('.remove-preview');
    removePreviewBtn.addEventListener('click', () => {
        previewDiv.style.display = 'none';
        replyInput.dataset.gifUrl = '';
        replyInput.dataset.imageFile = '';
        imageInput.value = '';
    });

    // Bold button functionality
    boldBtn.addEventListener('click', (e) => {
        e.preventDefault();
        applyFormatting(replyInput, 'b');
    });

    // Italic button functionality
    italicBtn.addEventListener('click', (e) => {
        e.preventDefault();
        applyFormatting(replyInput, 'i');
    });

    // Location functionality
    locationBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const { latitude, longitude } = position.coords;
                    const locationData = `${latitude.toFixed(2)},${longitude.toFixed(2)}`;
                    replyInput.dataset.locationData = locationData;
                    replyInput.value += ` [Location: ${locationData}]`;
                },
                (error) => {
                    alert('Unable to retrieve location: ' + error.message);
                }
            );
        } else {
            alert('Geolocation is not supported by your browser.');
        }
    });

    // Poll functionality (placeholder for now)
    pollBtn.addEventListener('click', (e) => {
        e.preventDefault();
        alert('Poll functionality coming soon!');
    });

    // Schedule functionality (placeholder for now)
    scheduleBtn.addEventListener('click', (e) => {
        e.preventDefault();
        alert('Schedule functionality coming soon!');
    });
}

function handleTipClick(e) {
    const action = e.target.closest('.tip-action');
    if (action) {
        e.preventDefault();
        const tipId = this.getAttribute('data-tip-id');
        const actionType = action.getAttribute('data-action');

        const formData = new FormData();
        formData.append('tip_id', tipId);

        if (actionType === 'like') {
            fetch('/api/like-tip/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCSRFToken(),
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const likeCount = action.nextElementSibling;
                    likeCount.textContent = data.like_count;
                    action.classList.toggle('liked', data.message === 'Tip liked');
                } else {
                    alert('Error: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error liking tip:', error);
                alert('An error occurred while liking the tip.');
            });
        } else if (actionType === 'share') {
            fetch('/api/share-tip/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCSRFToken(),
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const shareCount = action.nextElementSibling;
                    shareCount.textContent = data.share_count;
                    action.classList.toggle('shared', data.message === 'Tip shared');
                } else {
                    alert('Error: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error sharing tip:', error);
                alert('An error occurred while sharing the tip.');
            });
        } else if (actionType === 'comment') {
            openCommentModal(this, tipId);
        }
        return;
    }

    const tipId = this.getAttribute('data-tip-id');
    openCommentModal(this, tipId);
}

function openCommentModal(tip, tipId, parentId = null) {
    const commentModal = document.getElementById('comment-modal');
    const modalTip = commentModal.querySelector('.modal-tip');
    const modalTipAvatar = modalTip.querySelector('.modal-tip-avatar');
    const modalTipContent = modalTip.querySelector('.modal-tip-content');
    const commentList = commentModal.querySelector('.comment-list');
    const replyToHeader = commentModal.querySelector('.reply-to-header');
    const replyToUsername = commentModal.querySelector('.reply-to-username');
    const commentSubmit = commentModal.querySelector('.post-reply-submit');

    const avatarUrl = tip.querySelector('.tip-avatar')?.src || DEFAULT_AVATAR_URL;
    const tipContent = tip.querySelector('.tip-content');
    const usernameElement = tipContent.querySelector('.tip-username strong');
    const handleElement = tipContent.querySelector('.user-handle');
    const sportEmojiNode = Array.from(tipContent.childNodes).find(node => node.nodeType === 3 && node.textContent.trim().match(/^[⚽⛳🎾🏇]$/));
    const sportEmoji = sportEmojiNode ? sportEmojiNode.textContent.trim() : '';
    const text = tipContent.querySelector('p')?.textContent || '';
    const timestamp = tipContent.querySelector('small').textContent;
    const likeCount = tipContent.querySelector('.like-count').textContent;
    const shareCount = tipContent.querySelector('.share-count').textContent;
    const commentCount = tipContent.querySelector('.comment-count').textContent;
    const engagementCount = tipContent.querySelector('.tip-action-engagement + .tip-action-count')?.textContent || '0';

    modalTipAvatar.src = avatarUrl;
    modalTipContent.innerHTML = `
        <a href="#" class="tip-username">
            <strong class="modal-tip-username">${usernameElement ? usernameElement.textContent : 'Unknown'}</strong>
            <span class="user-handle modal-tip-handle">${handleElement ? handleElement.textContent : ''}</span>
        </a>
        <span class="modal-tip-sport">${sportEmoji}</span>
        <p class="modal-tip-text">${text}</p>
        <small class="modal-tip-timestamp">${timestamp}</small>
        <div class="tip-actions">
            <div class="tip-action-group">
                <a href="#" class="tip-action tip-action-like" data-action="like"><i class="fas fa-heart"></i></a>
                <span class="tip-action-count like-count">${likeCount}</span>
            </div>
            <div class="tip-action-group">
                <a href="#" class="tip-action tip-action-share" data-action="share"><i class="fas fa-retweet"></i></a>
                <span class="tip-action-count share-count">${shareCount}</span>
            </div>
            <div class="tip-action-group">
                <a href="#" class="tip-action tip-action-comment" data-action="comment"><i class="fas fa-comment-dots"></i></a>
                <span class="tip-action-count comment-count">${commentCount}</span>
            </div>
            <div class="tip-action-group">
                <a href="#" class="tip-action tip-action-engagement"><i class="fas fa-users"></i></a>
                <span class="tip-action-count">${engagementCount}</span>
            </div>
        </div>
    `;

    commentList.innerHTML = '<p>Loading comments...</p>';

    if (parentId) {
        const parentComment = commentList.querySelector(`.comment[data-comment-id="${parentId}"]`);
        if (parentComment) {
            replyToHeader.style.display = 'block';
            replyToUsername.textContent = parentComment.querySelector('.comment-username strong').textContent;
        }
    } else {
        replyToHeader.style.display = 'none';
    }

    // Fetch comments for the tip
    const fetchComments = () => {
        fetch(`/api/tip/${tipId}/comments/`)
            .then(response => response.json())
            .then(data => {
                // Get current comment IDs
                const currentCommentIds = Array.from(commentList.querySelectorAll('.comment')).map(comment => comment.getAttribute('data-comment-id'));
                const newCommentIds = data.comments ? data.comments.map(comment => comment.id.toString()) : [];

                // Only update if there are new or changed comments
                if (JSON.stringify(currentCommentIds) !== JSON.stringify(newCommentIds)) {
                    commentList.innerHTML = '';
                    if (data.comments && data.comments.length > 0) {
                        data.comments.forEach(comment => {
                            const avatarUrl = comment.avatar_url || DEFAULT_AVATAR_URL;
                            const commentDiv = document.createElement('div');
                            commentDiv.className = 'comment';
                            if (comment.parent_id) {
                                commentDiv.classList.add('reply-comment'); // Add a class for styling replies
                            }
                            commentDiv.setAttribute('data-comment-id', comment.id);
                            commentDiv.setAttribute('data-parent-id', comment.parent_id || '');
                            commentDiv.innerHTML = `
                                <img src="${avatarUrl}" alt="${comment.user__username} Avatar" class="comment-avatar" onerror="this.src='${DEFAULT_AVATAR_URL}'">
                                <div class="comment-content">
                                    <a href="/profile/${comment.user__username}/" class="comment-username"><strong>${comment.user__username}</strong></a>
                                    ${comment.parent_id ? `<span class="reply-to">Replying to <a href="#" class="reply-to-username">@${comment.parent_username}</a></span>` : ''}
                                    <p>${comment.content}</p>
                                    ${comment.image ? `<img src="${comment.image}" alt="Comment Image" class="comment-image">` : ''}
                                    ${comment.gif ? `<img src="${comment.gif}" alt="Comment GIF" class="comment-image">` : ''}
                                    <small>${new Date(comment.created_at).toLocaleString()}</small>
                                    <div class="comment-actions">
                                        <div class="comment-action-group">
                                            <a href="#" class="comment-action comment-action-like" data-action="like"><i class="fas fa-heart"></i></a>
                                            <span class="comment-action-count like-count">${comment.like_count || 0}</span>
                                        </div>
                                        <div class="comment-action-group">
                                            <a href="#" class="comment-action comment-action-share" data-action="share"><i class="fas fa-retweet"></i></a>
                                            <span class="comment-action-count share-count">${comment.share_count || 0}</span>
                                        </div>
                                        <div class="comment-action-group">
                                            <a href="#" class="comment-action comment-action-comment" data-action="comment"><i class="fas fa-comment-dots"></i></a>
                                            <span class="comment-action-count comment-count">${comment.reply_count || 0}</span>
                                        </div>
                                    </div>
                                </div>
                            `;
                            commentList.appendChild(commentDiv);
                        });
                        attachCommentActionListeners();
                    } else {
                        commentList.innerHTML = '<p>No comments yet.</p>';
                    }
                }
            })
            .catch(error => {
                console.error('Error fetching comments:', error);
                commentList.innerHTML = '<p>Error loading comments.</p>';
            });
    };

    // Initial fetch
    fetchComments();

    // Set up real-time comment fetching (every 30 seconds)
    const commentInterval = setInterval(fetchComments, 30000);

    // Stop polling when the modal is closed
    const stopPolling = () => {
        clearInterval(commentInterval);
    };

    // Attach stopPolling to modal close events
    const commentModalClose = document.querySelector('.comment-modal-close');
    commentModalClose.addEventListener('click', function() {
        stopPolling();
        commentModal.style.display = 'none';
    });

    window.addEventListener('click', function(event) {
        if (event.target === commentModal) {
            stopPolling();
            commentModal.style.display = 'none';
        }
    });

    commentModal.style.display = 'block';
    commentSubmit.dataset.tipId = tipId;
    if (parentId) commentSubmit.dataset.parentId = parentId;
}

function attachCommentActionListeners() {
    const commentList = document.getElementById('comment-modal').querySelector('.comment-list');
    const commentActions = commentList.querySelectorAll('.comment-action');
    commentActions.forEach(action => {
        action.addEventListener('click', function(e) {
            e.preventDefault();
            const commentId = this.closest('.comment').getAttribute('data-comment-id');
            const parentId = this.closest('.comment').getAttribute('data-parent-id');
            const actionType = this.getAttribute('data-action');
            const tipId = document.querySelector('.post-reply-submit').dataset.tipId;

            const formData = new FormData();
            formData.append('comment_id', commentId);

            if (actionType === 'like') {
                fetch('/api/like-comment/', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': getCSRFToken(),
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const likeCount = this.nextElementSibling;
                        likeCount.textContent = data.like_count;
                        this.classList.toggle('liked', data.message === 'Comment liked');
                    } else {
                        alert('Error: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error liking comment:', error);
                    alert('An error occurred while liking the comment.');
                });
            } else if (actionType === 'share') {
                fetch('/api/share-comment/', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': getCSRFToken(),
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const shareCount = this.nextElementSibling;
                        shareCount.textContent = data.share_count;
                        this.classList.toggle('shared', data.message === 'Comment shared');
                    } else {
                        alert('Error: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error sharing comment:', error);
                    alert('An error occurred while sharing the comment.');
                });
            } else if (actionType === 'comment') {
                const tipElement = document.querySelector(`.tip[data-tip-id="${tipId}"]`);
                openCommentModal(tipElement, tipId, commentId);
            }
        });
    });
}

// Export the functions required by main.js
export { setupTipInteractions, setupReplyModal };