import { getCSRFToken } from './pages/utils.js';
import { applyFormatting, showGifModal } from './pages/post.js';

// Global user data to avoid scope issues
let currentUserData = { avatarUrl: window.default_avatar_url, handle: window.currentUser || 'You', isAdmin: false };

function fetchComments(tipId, list, callback) {
    console.log(`Fetching comments for tipId: ${tipId}`);
    fetch(`/api/tips/${tipId}/comments/`)
    .then(response => response.json())
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
                
                // Ensure usernames are properly handled
                const username = comment.user__username || '';
                const parentUsername = comment.parent_username || '';
                
                // Only include reply-to section if both usernames are valid and not 'None'
                const replyToSection = (comment.parent_id && parentUsername && parentUsername !== 'None') 
                    ? `<span class="reply-to">Replying to <a href="/profile/${parentUsername}/">@${parentUsername}</a></span>` 
                    : '';
                
                // Only create profile link if username is valid and not 'None'
                const profileLink = username && username !== 'None'
                    ? `<a href="/profile/${username}/" class="comment-username"><strong>${username}</strong></a>`
                    : `<span class="comment-username"><strong>Unknown User</strong></span>`;
                
                commentDiv.innerHTML = `
                    <img src="${avatarUrl}" alt="${username} Avatar" class="comment-avatar" onerror="this.src='${window.default_avatar_url}'">
                    <div class="comment-content">
                        ${profileLink}
                        ${replyToSection}
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
        if (callback) callback();
    });
}

function setupTipInteractions() {
    const tips = document.querySelectorAll('.tip');
    const commentModal = document.getElementById('comment-modal');
    const commentSubmit = commentModal ? commentModal.querySelector('.post-reply-submit') : null;
    const commentModalClose = commentModal ? commentModal.querySelector('.comment-modal-close') : null;

    if (!tips.length) console.warn('No .tip elements found');
    if (!commentModal) console.warn('Comment modal not found');
    if (!commentSubmit) console.warn('Comment submit button not found');
    if (!commentModalClose) console.warn('Comment modal close button not found');

    // Prevent duplicate event listeners
    tips.forEach(tip => {
        tip.removeEventListener('click', handleTipClick);
        tip.addEventListener('click', handleTipClick);
    });

    // Fetch user data once
    fetch('/api/current-user/', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    })
    .then(response => {
        if (!response.ok) {
            console.warn(`Failed to fetch current user data: ${response.status}`);
            if (response.status === 401) {
                console.log('User not authenticated');
            }
            return { success: false, error: response.status === 401 ? 'User not authenticated' : 'Request failed' };
        }
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            console.warn('Received non-JSON response from /api/current-user/');
            return { success: false, error: 'Invalid response format' };
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            currentUserData = {
                avatarUrl: data.avatar_url || window.default_avatar_url,
                handle: data.handle || window.currentUser || 'You',
                isAdmin: data.is_admin || false,
                profile: data.profile || {
                    display_name: window.currentUser || 'You',
                    avatar: window.default_avatar_url,
                    description: '',
                    kyc_completed: false,
                    profile_completed: false,
                    payment_completed: false
                }
            };
            console.log('Current user data:', currentUserData);
        } else {
            console.warn(`Failed to fetch current user data: ${data.error}`);
            // Set default values if fetch fails
            currentUserData = {
                avatarUrl: window.default_avatar_url,
                handle: window.currentUser || 'You',
                isAdmin: false,
                profile: {
                    display_name: window.currentUser || 'You',
                    avatar: window.default_avatar_url,
                    description: '',
                    kyc_completed: false,
                    profile_completed: false,
                    payment_completed: false
                }
            };
        }
    })
    .catch(error => {
        console.error('Error fetching current user data:', error);
        // Set default values if fetch fails
        currentUserData = {
            avatarUrl: window.default_avatar_url,
            handle: window.currentUser || 'You',
            isAdmin: false,
            profile: {
                display_name: window.currentUser || 'You',
                avatar: window.default_avatar_url,
                description: '',
                kyc_completed: false,
                profile_completed: false,
                payment_completed: false
            }
        };
    });

    setupReplyModal();

    if (commentSubmit) {
        commentSubmit.removeEventListener('click', handleCommentSubmit);
        commentSubmit.addEventListener('click', handleCommentSubmit);
    }

    function handleCommentSubmit(e) {
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

                // Update the comment count in the tip feed
                const tipFeed = document.querySelector(`.tip[data-tip-id="${tipId}"] .tip-content`);
                const tipComments = tipFeed.querySelector('.tip-actions .comment-count');
                tipComments.textContent = data.comment_count;

                // Close modal after successful submission
                commentModal.classList.add('hidden');
                commentModal.classList.remove('active');
                commentInput.value = '';
                commentInput.dataset.imageFile = '';
                commentInput.dataset.gifUrl = '';
                commentInput.dataset.locationData = '';
            } else {
                showCustomAlert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error commenting on tip:', error);
            showCustomAlert('An error occurred while commenting: ' + error.message);
        });
    }

    if (commentModalClose) {
        commentModalClose.removeEventListener('click', closeModalHandler);
        commentModalClose.addEventListener('click', closeModalHandler);
    }

    function closeModalHandler() {
        commentModal.classList.add('hidden');
        commentModal.classList.remove('active');
        const commentInput = commentModal.querySelector('.post-reply-input');
        const previewDiv = commentModal.querySelector('.post-reply-preview');
        commentInput.value = '';
        commentInput.dataset.imageFile = '';
        commentInput.dataset.gifUrl = '';
        commentInput.dataset.locationData = '';
        if (previewDiv) previewDiv.style.display = 'none';
    }

    window.removeEventListener('click', windowClickHandler);
    window.addEventListener('click', windowClickHandler);

    function windowClickHandler(event) {
        const commentModal = document.getElementById('comment-modal');
        if (!commentModal) return;

        if (event.target === commentModal) {
            commentModal.classList.add('hidden');
            commentModal.classList.remove('active');
            const commentInput = commentModal.querySelector('.post-reply-input');
            const previewDiv = commentModal.querySelector('.post-reply-preview');
            commentInput.value = '';
            commentInput.dataset.imageFile = '';
            commentInput.dataset.gifUrl = '';
            commentInput.dataset.locationData = '';
            if (previewDiv) previewDiv.style.display = 'none';
        }
    }

    setupTipOptionsMenu();
}

function setupReplyModal() {
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
        import('./pages/post.js').then(module => {
            const commentModal = document.getElementById('comment-modal');
            module.showEmojiPicker(replyInput, emojiBtn, commentModal);
        });
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
        if (action.classList.contains('tip-action-bookmark')) {
            return;
        }
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
                    const likeCount = action.closest('.tip-action-group').querySelector('.like-count');
                    if (likeCount) {
                        likeCount.textContent = data.likes_count;
                    }
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
                console.log('Retweet response:', data);
                if (data.success) {
                    const shareCount = action.closest('.tip-action-group').querySelector('.share-count');
                    if (shareCount && data.share_count !== undefined) {
                        shareCount.textContent = data.share_count;
                    }
                    
                    // Toggle the retweeted state
                    if (data.is_retweeted) {
                        action.classList.add('shared');
                        action.setAttribute('aria-label', 'Undo retweet');
                    } else {
                        action.classList.remove('shared');
                        action.setAttribute('aria-label', 'Retweet');
                    }
                    
                    // Update all instances of this tip's retweet count across the page
                    const allShareCounts = document.querySelectorAll(`.tip[data-tip-id="${tipId}"] .share-count`);
                    allShareCounts.forEach(count => {
                        count.textContent = data.share_count;
                    });
                    
                    // If this was a retweet, refresh the page to show the new retweet in feeds
                    if (data.is_retweeted && data.retweet_id) {
                        // Optionally refresh the page to show the new retweet
                        // location.reload();
                    }
                } else {
                    showCustomAlert('Error: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error retweeting tip:', error);
                showCustomAlert('An error occurred while retweeting the tip.');
            });
        } else if (actionType === 'comment') {
            openCommentModal(this, tipId);
        }
        return;
    }

    e.preventDefault();
    const tipId = this.getAttribute('data-tip-id');
    openCommentModal(this, tipId);
}

function openCommentModal(tip, tipId, parentId = null) {
    const commentModal = document.getElementById('comment-modal');
    if (!commentModal) {
        console.error('Comment modal element not found');
        return;
    }

    // Remove hidden class and add active class
    commentModal.classList.remove('hidden');
    commentModal.classList.add('active');

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
    const currentStatus = tip.querySelector('.tip-meta .status')?.textContent?.split(': ')[1] || 'Unknown';
    const tipBody = tipContent.querySelector('.tip-body');

    // Instead of just tipBody, clone the entire tip-content
    const tipContentClone = tipContent.cloneNode(true);
    tipContentClone.classList.add('modal-tip-content-clone');

    const updateTipStatus = () => {
        // Clear modalTipContent and insert full tip-content
        modalTipContent.innerHTML = '';
        // Username, handle, and sport emoji (optional, since already in tipContentClone)
        // Insert the full tip-content clone
        modalTipContent.appendChild(tipContentClone);
        // Timestamp (if not already present in the clone)
        if (!tipContentClone.querySelector('.modal-tip-timestamp')) {
            const small = document.createElement('small');
            small.className = 'modal-tip-timestamp';
            small.textContent = timestamp;
            modalTipContent.appendChild(small);
        }

        fetch(`/api/tip/${tipId}/`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        })
        .then(response => {
            console.log(`Fetch response for tip ${tipId}:`, response.status);
            if (!response.ok) {
                console.warn(`Tip ${tipId} not found, using current status: ${currentStatus}`);
                return { success: true, tip: { status: currentStatus, odds: '', bet_type: '', each_way: false, confidence: '' }, responseOk: false };
            }
            return response.json().then(data => ({ ...data, responseOk: true }));
        })
        .then(data => {
            if (data.success) {
                const status = data.tip.status || currentStatus;
                const odds = data.tip.odds || '';
                const betType = data.tip.bet_type || '';
                const eachWay = data.tip.each_way ? 'yes' : 'no';
                const confidence = data.tip.confidence || '';

                modalTipAvatar.src = avatarUrl;
                modalTipContent.innerHTML = `
                    <a href="#" class="tip-username">
                        <strong class="modal-tip-username">${usernameElement ? usernameElement.textContent : 'Unknown'}</strong>
                        <span class="user-handle modal-tip-handle">${handleElement ? handleElement.textContent : ''}</span>
                    </a>
                    <span class="modal-tip-sport">${sportEmoji}</span>
                    <p class="modal-tip-text">${text}</p>
                    <div class="tip-meta">
                        <span>Odds: ${odds}</span>
                        <span>Bet Type: ${betType}</span>
                        ${eachWay === 'yes' ? '<span>Each Way: Yes</span>' : ''}
                        ${confidence ? `<span>Confidence: ${confidence}</span>` : ''}
                        <span class="status">Status: ${status}</span>
                    </div>
                    <small class="modal-tip-timestamp">${timestamp}</small>
                    ${data.data && data.data.image ? `<img src="${data.data.image}" alt="Tip Image" class="comment-image">` : ''}
                    ${data.data && data.data.gif_url ? `<img src="${data.data.gif_url}" alt="Tip GIF" class="comment-image" width="582" height="300" onerror="this.src='/static/img/default-image.png'">` : ''}
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

                if (currentUserData.isAdmin && data.responseOk) {
                    const statusIndex = eachWay === 'yes' ? 5 : 4;
                    const tipFeedStatus = tip.querySelector(`.tip-meta span:nth-child(${statusIndex})`);
                    if (tipFeedStatus) tipFeedStatus.textContent = `Status: ${status}`;
                }
            }
        })
        .catch(error => {
            console.error('Error fetching tip status:', error);
        });
    };

    try {
        updateTipStatus();
        commentList.innerHTML = '<p>Loading comments...</p>';

        // Load comments regardless of parentId
        fetchComments(tipId, commentList, () => {
            if (parentId) {
                replyToHeader.style.display = 'block';
                const parentComment = commentList.querySelector(`.comment[data-comment-id="${parentId}"]`);
                if (parentComment) replyToUsername.textContent = parentComment.querySelector('.comment-username strong').textContent;
            } else {
                replyToHeader.style.display = 'none';
            }
        });

        let pollingInterval = setInterval(() => {
            updateTipStatus();
            fetchComments(tipId, commentList);
        }, 30000);

        const stopPolling = () => clearInterval(pollingInterval);
        window.addEventListener('click', (event) => {
            if (event.target === commentModal) {
                stopPolling();
                commentModal.classList.add('hidden');
                commentModal.classList.remove('active');
            }
        });

        console.log('Opening modal for tipId:', tipId);
        commentModal.classList.remove('hidden');
        commentModal.classList.add('active');
        console.log('Modal classes:', commentModal.classList);
        console.log('Modal computed display:', window.getComputedStyle(commentModal).display);
        commentSubmit.dataset.tipId = tipId;
        if (parentId) commentSubmit.dataset.parentId = parentId;
    } catch (error) {
        console.error('Error in openCommentModal:', error);
        commentModal.classList.remove('hidden');
        commentModal.classList.add('active');
    }
}

function attachCommentActionListeners() {
    const commentList = document.getElementById('comment-modal').querySelector('.comment-list');
    const commentActions = commentList.querySelectorAll('.comment-action');
    commentActions.forEach(action => {
        action.addEventListener('click', function (e) {
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

function setupTipOptionsMenu() {
    document.addEventListener('click', function(e) {
        // Close any open dropdowns when clicking outside
        if (!e.target.closest('.tip-options')) {
            document.querySelectorAll('.tip-options-dropdown').forEach(dropdown => {
                dropdown.classList.remove('show');
            });
        }
    });

    // Setup option buttons for each tip
    document.querySelectorAll('.tip-options-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const dropdown = this.nextElementSibling;
            // Close other dropdowns
            document.querySelectorAll('.tip-options-dropdown').forEach(d => {
                if (d !== dropdown) d.classList.remove('show');
            });
            dropdown.classList.toggle('show');
        });
    });

    // Setup edit and delete handlers
    document.querySelectorAll('.tip-option-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.stopPropagation();
            const tip = this.closest('.tip');
            const tipId = tip.dataset.tipId;
            
            if (this.classList.contains('edit')) {
                handleTipEdit(tipId, tip);
            } else if (this.classList.contains('delete')) {
                handleTipDelete(tipId, tip);
            }
            
            // Close the dropdown
            this.closest('.tip-options-dropdown').classList.remove('show');
        });
    });
}

function handleTipEdit(tipId, tipElement) {
    // Get the current tip content
    const tipText = tipElement.querySelector('.tip-body p').textContent;
    const tipMeta = tipElement.querySelector('.tip-meta');
    
    // Create and show edit modal
    const editModal = document.createElement('div');
    editModal.className = 'modal edit-tip-modal';
    editModal.innerHTML = `
        <div class="modal-content">
            <span class="modal-close">&times;</span>
            <h2>Edit Tip</h2>
            <textarea class="edit-tip-input">${tipText}</textarea>
            <button class="save-edit-btn">Save Changes</button>
        </div>
    `;
    
    document.body.appendChild(editModal);
    editModal.style.display = 'block';
    
    // Handle close button
    const closeBtn = editModal.querySelector('.modal-close');
    closeBtn.onclick = () => {
        editModal.remove();
    };
    
    // Handle save button
    const saveBtn = editModal.querySelector('.save-edit-btn');
    saveBtn.onclick = () => {
        const newText = editModal.querySelector('.edit-tip-input').value.trim();
        if (!newText) {
            showCustomAlert('Tip text cannot be empty');
            return;
        }
        
        const formData = new FormData();
        formData.append('tip_id', tipId);
        formData.append('text', newText);
        
        fetch('/api/edit-tip/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                tipElement.querySelector('.tip-body p').textContent = newText;
                editModal.remove();
                showCustomAlert('Tip updated successfully');
            } else {
                showCustomAlert('Error updating tip: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error updating tip:', error);
            showCustomAlert('An error occurred while updating the tip');
        });
    };
}

function handleTipDelete(tipId, tipElement) {
    if (confirm('Are you sure you want to delete this tip? This action cannot be undone.')) {
        const formData = new FormData();
        formData.append('tip_id', tipId);
        
        fetch('/api/delete-tip/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                tipElement.remove();
                showCustomAlert('Tip deleted successfully');
            } else {
                showCustomAlert('Error deleting tip: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error deleting tip:', error);
            showCustomAlert('An error occurred while deleting the tip');
        });
    }
}

export { setupTipInteractions, setupReplyModal };