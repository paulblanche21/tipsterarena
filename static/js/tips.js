// tips.js
import { getCSRFToken } from './pages/utils.js';
import { applyFormatting, showGifModal, showEmojiPicker } from './pages/post.js';

// Move fetchComments to top level
function fetchComments(tipId, list, callback) {
    console.log(`Fetching comments for tipId: ${tipId}`);
    fetch(`/api/tip/${tipId}/comments/`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    })
    .then(response => {
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        return response.json();
    })
    .then(data => {
        console.log('Comments data:', data);
        if (!data.success) {
            list.innerHTML = '<p>Error loading comments: ' + (data.error || 'Unknown error') + '</p>';
            return;
        }
        list.innerHTML = '';
        if (data.comments && data.comments.length > 0) {
            data.comments.forEach(comment => {
                const avatarUrl = comment.avatar_url || window.default_avatar_url;
                const commentDiv = document.createElement('div');
                commentDiv.className = 'comment';
                if (comment.parent_id) commentDiv.classList.add('reply-comment');
                commentDiv.setAttribute('data-comment-id', comment.id);
                commentDiv.setAttribute('data-parent-id', comment.parent_id || '');
                commentDiv.innerHTML = `
                    <img src="${avatarUrl}" alt="${comment.user__username} Avatar" class="comment-avatar" onerror="this.src='${window.default_avatar_url}'">
                    <div class="comment-content">
                        <a href="/profile/${comment.user__username}/" class="comment-username"><strong>${comment.user__username}</strong></a>
                        ${comment.parent_id ? `<span class="reply-to">Replying to <a href="/profile/${comment.parent_username}/">@${comment.parent_username}</a></span>` : ''}
                        <p>${comment.content}</p>
                        ${comment.image ? `<img src="${comment.image}" alt="Comment Image" class="comment-image">` : ''}
                        ${comment.gif_url ? `<img src="${comment.gif_url}" alt="Comment GIF" class="comment-image" width="582" height="300">` : ''}
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
                list.appendChild(commentDiv);
            });
            attachCommentActionListeners();
            if (callback) callback();
        } else {
            list.innerHTML = '<p>No comments yet.</p>';
        }
    })
    .catch(error => {
        console.error('Error fetching comments:', error);
        list.innerHTML = '<p>Error loading comments: ' + error.message + '</p>';
    });
}

function setupTipInteractions() {
    console.log('Setting up tip interactions');
    const tips = document.querySelectorAll('.tip');
    const commentModal = document.getElementById('comment-modal');
    const commentSubmit = commentModal ? commentModal.querySelector('.post-reply-submit') : null;
    const commentModalClose = commentModal ? commentModal.querySelector('.comment-modal-close') : null;

    if (!tips.length) console.warn('No .tip elements found');
    if (!commentModal) console.warn('Comment modal not found');
    if (!commentSubmit) console.warn('Comment submit button not found');
    if (!commentModalClose) console.warn('Comment modal close button not found');

    tips.forEach(tip => {
        tip.removeEventListener('click', handleTipClick);
        tip.addEventListener('click', handleTipClick);
    });

    let currentUserData = { avatarUrl: window.default_avatar_url, handle: window.currentUser || 'You' };
    fetch('/api/current-user/', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            currentUserData = {
                avatarUrl: data.avatar_url || window.default_avatar_url,
                handle: data.handle || window.currentUser || 'You'
            };
        }
    })
    .catch(error => console.error('Error fetching current user data:', error));

    setupReplyModal();

    if (commentSubmit) {
        console.log('Attaching event listener to comment submit button');
        commentSubmit.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Reply button clicked');
            const tipId = this.dataset.tipId;
            const parentId = this.dataset.parentId;
            const commentInput = commentModal.querySelector('.post-reply-input');
            const commentText = commentInput.value.trim();
            const hasGif = !!commentInput.dataset.gifUrl;

            console.log('Submitting reply:', { tipId, parentId, commentText, gifUrl: commentInput.dataset.gifUrl });

            if (!commentText && !hasGif) {
                showCustomAlert('Please enter a reply or select a GIF.');
                return;
            }

            const formData = new FormData();
            formData.append('tip_id', tipId);
            formData.append('comment_text', commentText);
            if (parentId) formData.append('parent_id', parentId);

            const imageInput = commentModal.querySelector('.post-reply-image-input');
            if (commentInput.dataset.imageFile && imageInput && imageInput.files[0]) {
                formData.append('image', imageInput.files[0]);
            }
            if (hasGif) {
                formData.append('gif', commentInput.dataset.gifUrl);
                console.log('Sending GIF URL:', commentInput.dataset.gifUrl);
            }
            const locationData = commentInput.dataset.locationData || '';
            if (locationData) {
                formData.append('location', locationData);
            }
            formData.append('poll', '{}');
            formData.append('emojis', '{}');

            fetch('/api/comment-tip/', {
                method: 'POST',
                body: formData,
                headers: { 'X-CSRFToken': getCSRFToken() },
                credentials: 'include'
            })
            .then(response => {
                console.log('Fetch response status:', response.status);
                if (!response.ok) {
                    return response.json().then(err => {
                        throw new Error(`Server error: ${response.status} - ${err.error || 'Unknown error'}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                console.log('Fetch response data:', data);
                if (data.success) {
                    const tip = document.querySelector(`.tip[data-tip-id="${tipId}"]`);
                    const commentCount = tip.querySelector('.comment-count');
                    commentCount.textContent = data.comment_count;
                    const commentList = commentModal.querySelector('.comment-list');
                    const newComment = document.createElement('div');
                    newComment.className = 'comment';
                    if (data.data.parent_id) newComment.classList.add('reply-comment');
                    newComment.setAttribute('data-comment-id', data.comment_id);
                    newComment.innerHTML = `
                        <img src="${currentUserData.avatarUrl}" alt="${currentUserData.handle} Avatar" class="comment-avatar" onerror="this.src='${window.default_avatar_url}'">
                        <div class="comment-content">
                            <a href="/profile/${window.currentUser}/" class="comment-username"><strong>${currentUserData.handle}</strong></a>
                            ${data.data.parent_id ? `<span class="reply-to">Replying to <a href="/profile/${data.data.parent_username}/">@${data.data.parent_username}</a></span>` : ''}
                            <p>${data.data.content}</p>
                            ${data.data.image ? `<img src="${data.data.image}" alt="Comment Image" class="comment-image">` : ''}
                            ${data.data.gif_url ? `<img src="${data.data.gif_url}" alt="Comment GIF" class="comment-image" width="582" height="300">` : ''}
                            <small>${new Date(data.data.created_at).toLocaleString()}</small>
                            <div class="comment-actions">
                                <div class="comment-action-group">
                                    <a href="#" class="comment-action comment-action-like" data-action="like"><i class="fas fa-heart"></i></a>
                                    <span class="comment-action-count like-count">${data.data.like_count || 0}</span>
                                </div>
                                <div class="comment-action-group">
                                    <a href="#" class="comment-action comment-action-share" data-action="share"><i class="fas fa-retweet"></i></a>
                                    <span class="comment-action-count share-count">${data.data.share_count || 0}</span>
                                </div>
                                <div class="comment-action-group">
                                    <a href="#" class="comment-action comment-action-comment" data-action="comment"><i class="fas fa-comment-dots"></i></a>
                                    <span class="comment-action-count comment-count">${data.data.reply_count || 0}</span>
                                </div>
                            </div>
                        </div>
                    `;
                    commentList.insertBefore(newComment, commentList.firstChild);
                    attachCommentActionListeners();

                    // Update the .tip-feed under the original post
                    const tipFeed = document.querySelector(`.tip[data-tip-id="${tipId}"] .tip-content`);
                    const tipComments = tipFeed.querySelector('.tip-actions .comment-count');
                    tipComments.textContent = data.comment_count;

                    // Dynamically append the comment to the .tip-feed (simplified for level 1 nesting)
                    const tipCommentsContainer = tipFeed.querySelector('.tip-comments');
                    if (!tipCommentsContainer) {
                        const commentsDiv = document.createElement('div');
                        commentsDiv.className = 'tip-comments';
                        tipFeed.appendChild(commentsDiv);
                    }
                    const newCommentInFeed = document.createElement('div');
                    newCommentInFeed.className = 'comment';
                    if (data.data.parent_id) newCommentInFeed.classList.add('reply-comment');
                    newCommentInFeed.setAttribute('data-comment-id', data.comment_id);
                    newCommentInFeed.innerHTML = `
                        <img src="${currentUserData.avatarUrl}" alt="${currentUserData.handle} Avatar" class="comment-avatar" onerror="this.src='${window.default_avatar_url}'">
                        <div class="comment-content">
                            <a href="/profile/${window.currentUser}/" class="comment-username"><strong>${currentUserData.handle}</strong></a>
                            ${data.data.parent_id ? `<span class="reply-to">Replying to <a href="/profile/${data.data.parent_username}/">@${data.data.parent_username}</a></span>` : ''}
                            <p>${data.data.content}</p>
                            ${data.data.image ? `<img src="${data.data.image}" alt="Comment Image" class="comment-image">` : ''}
                            ${data.data.gif_url ? `<img src="${data.data.gif_url}" alt="Comment GIF" class="comment-image" width="582" height="300">` : ''}
                            <small>${new Date(data.data.created_at).toLocaleString()}</small>
                        </div>
                    `;
                    tipFeed.querySelector('.tip-comments').appendChild(newCommentInFeed);

                    fetchComments(tipId, commentList); // Immediate refresh to sync with server
                } else {
                    showCustomAlert('Error: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error commenting on tip:', error);
                showCustomAlert('An error occurred while commenting: ' + error.message);
            });
        });
    } else {
        console.error('Failed to attach event listener to comment submit button');
    }

    if (commentModalClose) {
        commentModalClose.addEventListener('click', function() {
            commentModal.style.display = 'none';
            const commentInput = commentModal.querySelector('.post-reply-input');
            const previewDiv = commentModal.querySelector('.post-reply-preview');
            commentInput.value = '';
            commentInput.dataset.imageFile = '';
            commentInput.dataset.gifUrl = '';
            commentInput.dataset.locationData = '';
            if (previewDiv) previewDiv.style.display = 'none';
        });
    }

    window.addEventListener('click', function(event) {
        if (event.target === commentModal) {
            commentModal.style.display = 'none';
            const commentInput = commentModal.querySelector('.post-reply-input');
            const previewDiv = commentModal.querySelector('.post-reply-preview');
            commentInput.value = '';
            commentInput.dataset.imageFile = '';
            commentInput.dataset.gifUrl = '';
            commentInput.dataset.locationData = '';
            if (previewDiv) previewDiv.style.display = 'none';
        }
    });
}

function setupReplyModal() {
    console.log('Setting up reply modal');
    const commentModal = document.getElementById('comment-modal');
    if (!commentModal) {
        console.warn('Comment modal not found in setupReplyModal');
        return;
    }
    const replyInput = commentModal.querySelector('.post-reply-input');
    const boldBtn = commentModal.querySelector('.post-reply-box .post-action-btn.bold');
    const italicBtn = commentModal.querySelector('.post-reply-box .post-action-btn.italic');
    const imageBtn = commentModal.querySelector('.post-reply-box .post-action-btn.image');
    const gifBtn = commentModal.querySelector('.post-reply-box .post-action-btn.gif');
    const locationBtn = commentModal.querySelector('.post-reply-box .post-action-btn.location');
    const pollBtn = commentModal.querySelector('.post-reply-box .post-action-btn.poll');
    const scheduleBtn = commentModal.querySelector('.post-reply-box .post-action-btn.schedule');
    const emojiBtn = commentModal.querySelector('.post-reply-box .post-action-btn.emoji');
    const previewDiv = commentModal.querySelector('.post-reply-box .post-reply-preview') || document.createElement('div');

    if (!previewDiv.className) {
        previewDiv.className = 'post-reply-preview';
        previewDiv.style.display = 'none';
        previewDiv.innerHTML = `
            <img src="" alt="Preview" class="preview-media">
            <button class="remove-preview">×</button>
        `;
        replyInput.parentNode.insertBefore(previewDiv, replyInput.nextSibling);
    }

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

    gifBtn.addEventListener('click', (e) => {
        e.preventDefault();
        showGifModal(replyInput, previewDiv);
    });

    emojiBtn.addEventListener('click', (e) => {
        e.preventDefault();
        showEmojiPicker(replyInput, emojiBtn);
    });

    const removePreviewBtn = previewDiv.querySelector('.remove-preview');
    removePreviewBtn.addEventListener('click', () => {
        previewDiv.style.display = 'none';
        replyInput.dataset.gifUrl = '';
        replyInput.dataset.imageFile = '';
        imageInput.value = '';
    });

    boldBtn.addEventListener('click', (e) => {
        e.preventDefault();
        applyFormatting(replyInput, 'b');
    });

    italicBtn.addEventListener('click', (e) => {
        e.preventDefault();
        applyFormatting(replyInput, 'i');
    });

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
                    showCustomAlert('Unable to retrieve location: ' + error.message);
                }
            );
        } else {
            showCustomAlert('Geolocation is not supported by your browser.');
        }
    });

    pollBtn.addEventListener('click', (e) => {
        e.preventDefault();
        showCustomAlert('Poll functionality coming soon!');
    });

    scheduleBtn.addEventListener('click', (e) => {
        e.preventDefault();
        showCustomAlert('Schedule functionality coming soon!');
    });
}

function handleTipClick(e) {
    const action = e.target.closest('.tip-action');
    if (action) {
        e.preventDefault();
        const tipId = this.getAttribute('data-tip-id');
        const actionType = action.getAttribute('data-action');
        console.log(`Action clicked: ${actionType} for tipId: ${tipId}`);

        const formData = new FormData();
        formData.append('tip_id', tipId);

        if (actionType === 'like') {
            fetch('/api/like-tip/', {
                method: 'POST',
                body: formData,
                headers: { 'X-CSRFToken': getCSRFToken() },
                credentials: 'include'
            })
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
                return response.json();
            })
            .then(data => {
                console.log('Like response:', data);
                if (data.success) {
                    const likeCount = action.nextElementSibling;
                    likeCount.textContent = data.like_count;
                    action.classList.toggle('liked', data.message === 'Tip liked');
                } else {
                    showCustomAlert('Error: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error liking tip:', error);
                showCustomAlert('An error occurred while liking the tip.');
            });
        } else if (actionType === 'share') {
            fetch('/api/share-tip/', {
                method: 'POST',
                body: formData,
                headers: { 'X-CSRFToken': getCSRFToken() },
                credentials: 'include'
            })
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
                return response.json();
            })
            .then(data => {
                console.log('Share response:', data);
                if (data.success) {
                    const shareCount = action.nextElementSibling;
                    shareCount.textContent = data.share_count;
                    action.classList.toggle('shared', data.message === 'Tip shared');
                } else {
                    showCustomAlert('Error: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error sharing tip:', error);
                showCustomAlert('An error occurred while sharing the tip.');
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

    const avatarUrl = tip.querySelector('.tip-avatar')?.src || window.default_avatar_url;
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
        replyToHeader.style.display = 'block';
        fetchComments(tipId, commentList, () => {
            const parentComment = commentList.querySelector(`.comment[data-comment-id="${parentId}"]`);
            if (parentComment) replyToUsername.textContent = parentComment.querySelector('.comment-username strong').textContent;
        });
    } else {
        replyToHeader.style.display = 'none';
    }

    let pollingInterval;
    pollingInterval = setInterval(() => fetchComments(tipId, commentList), 30000);
    const stopPolling = () => clearInterval(pollingInterval);

    window.addEventListener('click', (event) => {
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
            const actionType = this.getAttribute('data-action');
            const tipId = document.querySelector('.post-reply-submit').dataset.tipId;
            console.log(`Comment action: ${actionType} for commentId: ${commentId}`);

            const formData = new FormData();
            formData.append('comment_id', commentId);

            if (actionType === 'like') {
                fetch('/api/like-comment/', {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-CSRFToken': getCSRFToken() },
                    credentials: 'include'
                })
                .then(response => {
                    if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
                    return response.json();
                })
                .then(data => {
                    console.log('Like comment response:', data);
                    if (data.success) {
                        const likeCount = this.nextElementSibling;
                        likeCount.textContent = data.like_count;
                        this.classList.toggle('liked', data.message === 'Comment liked');
                    } else {
                        showCustomAlert('Error: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error liking comment:', error);
                    showCustomAlert('An error occurred while liking the comment.');
                });
            } else if (actionType === 'share') {
                fetch('/api/share-comment/', {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-CSRFToken': getCSRFToken() },
                    credentials: 'include'
                })
                .then(response => {
                    if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
                    return response.json();
                })
                .then(data => {
                    console.log('Share comment response:', data);
                    if (data.success) {
                        const shareCount = this.nextElementSibling;
                        shareCount.textContent = data.share_count;
                        this.classList.toggle('shared', data.message === 'Comment shared');
                    } else {
                        showCustomAlert('Error: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error sharing comment:', error);
                    showCustomAlert('An error occurred while sharing the comment.');
                });
            } else if (actionType === 'comment') {
                const tipElement = document.querySelector(`.tip[data-tip-id="${tipId}"]`);
                openCommentModal(tipElement, tipId, commentId);
            }
        });
    });
}

function showCustomAlert(message) {
    let alertModal = document.getElementById('custom-alert');
    if (!alertModal) {
        alertModal = document.createElement('div');
        alertModal.id = 'custom-alert';
        alertModal.className = 'custom-alert';
        alertModal.innerHTML = `
            <div class="custom-alert-content">
                <p class="custom-alert-message"></p>
                <button class="custom-alert-close">OK</button>
            </div>
        `;
        document.body.appendChild(alertModal);
    }

    const messageElement = alertModal.querySelector('.custom-alert-message');
    const closeBtn = alertModal.querySelector('.custom-alert-close');
    messageElement.textContent = message;
    alertModal.style.display = 'block';

    closeBtn.onclick = () => alertModal.style.display = 'none';
    window.onclick = (event) => {
        if (event.target === alertModal) alertModal.style.display = 'none';
    };
}

export { setupTipInteractions, setupReplyModal };