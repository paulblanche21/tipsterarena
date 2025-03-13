document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded');

    // Function to get CSRF token
    function getCSRFToken() {
        const tokenElement = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (!tokenElement) {
            console.warn("CSRF token not found on page");
            return null;
        }
        return tokenElement.value;
    }

    // Function to attach follow button listeners
    function attachFollowButtonListeners() {
        const followButtons = document.querySelectorAll('.follow-btn');
        followButtons.forEach(button => {
            button.addEventListener('click', function() {
                const username = this.getAttribute('data-username');
                followUser(username, this);
            });
        });
    }

    // Function to follow a user via AJAX
    function followUser(username, button) {
        const formData = new FormData();
        formData.append('username', username);
        fetch('/api/follow/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCSRFToken(),
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                button.textContent = 'Following';
                button.disabled = true;
                button.classList.add('followed');
                console.log(data.message);
            } else {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error following user:', error);
            alert('An error occurred while following.');
        });
    }

    // Attach follow button listeners on initial page load
    attachFollowButtonListeners();

     // Show More Button Logic (Sport-Specific Central Feed)
     const showMoreButtons = document.querySelectorAll('.show-more');
     showMoreButtons.forEach(button => {
         button.addEventListener('click', function(e) {
             e.preventDefault();
             const target = this.getAttribute('data-target');
             const content = document.querySelector('.content');
             let previousUrl = window.location.pathname;
 
             content.innerHTML = '';
 
             switch (target) {
                 case 'upcoming-events':
                     content.innerHTML = getEventList(window.location.pathname, target);
                     break;
                 case 'trending-tips':
                     content.innerHTML = `
                         <div class="follow-card">
                             <h2>Trending Tips</h2>
                             <p>Hot tips for today’s big tournaments in Tipster Arena:</p>
                             <div class="tip-list">
                                 <div class="tip-item">
                                     <img src="${DEFAULT_AVATAR_URL}" alt="User Avatar" class="tip-avatar">
                                     <div class="tip-details">
                                         <strong>User 1</strong> - Rory McIlroy to win The Players Championship (Odds: 10.0) - Likes: 150
                                     </div>
                                 </div>
                                 <div class="tip-item">
                                     <img src="${DEFAULT_AVATAR_URL}" alt="User Avatar" class="tip-avatar">
                                     <div class="tip-details">
                                         <strong>User 2</strong> - Scottie Scheffler top 10 at Masters (Odds: 2.5) - Likes: 120
                                     </div>
                                 </div>
                             </div>
                             <a href="#" class="show-less" data-target="${target}">Show less</a>
                         </div>
                     `;
                     break;

            
                case 'trending-tips':
                    content.innerHTML = `
                        <div class="follow-card">
                            <h2>Trending Tips</h2>
                            <p>Hot tips for today’s big tournaments in Tipster Arena:</p>
                            <div class="tip-list">
                                <div class="tip-item">
                                    <img src="${DEFAULT_AVATAR_URL}" alt="User Avatar" class="tip-avatar">
                                    <div class="tip-details">
                                        <strong>User 1</strong> - Rory McIlroy to win The Players Championship (Odds: 10.0) - Likes: 150
                                    </div>
                                </div>
                                <div class="tip-item">
                                    <img src="${DEFAULT_AVATAR_URL}" alt="User Avatar" class="tip-avatar">
                                    <div class="tip-details">
                                        <strong>User 2</strong> - Scottie Scheffler top 10 at Masters (Odds: 2.5) - Likes: 120
                                    </div>
                                </div>
                            </div>
                            <a href="#" class="show-less" data-target="${target}">Show less</a>
                        </div>
                    `;
                    break;
                case 'who-to-follow':
                    content.innerHTML = `
                        <div class="follow-card">
                            <h2>Who to Follow</h2>
                            <p>Suggested tipsters for you to follow in Tipster Arena:</p>
                            <div class="follow-list" id="follow-list">
                                <p>Loading suggestions...</p>
                            </div>
                            <a href="#" class="show-less" data-target="${target}">Show less</a>
                        </div>
                    `;
                    fetch('/api/suggested-users/', {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        const followList = document.getElementById('follow-list');
                        followList.innerHTML = '';
                        if (data.users && data.users.length > 0) {
                            data.users.forEach(user => {
                                followList.innerHTML += `
                                    <div class="follow-item">
                                        <img src="${user.avatar_url}" alt="${user.username}" class="follow-avatar">
                                        <div class="follow-details">
                                            <a href="${user.profile_url}" class="follow-username">@${user.username}</a>
                                            <p class="follow-bio">${user.bio}</p>
                                        </div>
                                        <button class="follow-btn" data-username="${user.username}">Follow</button>
                                    </div>
                                `;
                            });
                            attachFollowButtonListeners();
                        } else {
                            followList.innerHTML = '<p>No suggestions available.</p>';
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching suggested users:', error);
                        document.getElementById('follow-list').innerHTML = '<p>Error loading suggestions.</p>';
                    });
                    break;
            }

            const showLessButtons = document.querySelectorAll('.show-less');
            showLessButtons.forEach(lessButton => {
                lessButton.addEventListener('click', function(e) {
                    e.preventDefault();
                    content.innerHTML = '';
                    window.location.href = previousUrl;
                });
            });
        });
    });

    // Post Tip Logic (for central feed)
    const postSubmitBtn = document.querySelector('.post-submit');
    const postInput = document.querySelector('.post-input');
    const postAudience = document.querySelector('.post-audience');

    console.log('Post Submit Btn:', postSubmitBtn);
    console.log('Post Input:', postInput);
    console.log('Post Audience:', postAudience);

    if (postSubmitBtn && postInput && postAudience) {
        postSubmitBtn.addEventListener('click', function() {
            console.log('Central feed post button clicked');
            const text = postInput.value.trim();
            const audience = postAudience.value;

            if (!text) {
                alert('Please enter a tip before posting.');
                return;
            }

            const formData = new FormData();
            formData.append('text', text);
            formData.append('audience', audience);
            formData.append('sport', 'golf');

            fetch('/api/post-tip/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCSRFToken(),
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Tip posted successfully!');
                    postInput.value = '';
                    location.reload();
                } else {
                    alert('Error posting tip: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error posting tip:', error);
                alert('An error occurred while posting the tip.');
            });
        });
    } else {
        console.warn('One or more central feed post elements not found:', { postSubmitBtn, postInput, postAudience });
    }

    // Tip Feed Interaction Logic
    const tips = document.querySelectorAll('.tip');
    const commentModal = document.getElementById('comment-modal');
    const modalTip = commentModal.querySelector('.modal-tip');
    const modalTipAvatar = modalTip.querySelector('.modal-tip-avatar');
    const modalTipContent = modalTip.querySelector('.modal-tip-content');
    const commentList = commentModal.querySelector('.comment-list');
    const replyToHeader = commentModal.querySelector('.reply-to-header');
    const replyToUsername = commentModal.querySelector('.reply-to-username');
    const commentInput = commentModal.querySelector('.post-reply-input');
    const commentSubmit = commentModal.querySelector('.post-reply-submit');
    const commentModalClose = commentModal.querySelector('.comment-modal-close');

    // Function to open the comment modal
    function openCommentModal(tip, tipId, parentId = null) {
        // Debug: Log the tip element
        console.log('Tip element:', tip);

        // Extract avatar URL
        const avatarElement = tip.querySelector('.tip-avatar');
        const avatarUrl = avatarElement ? avatarElement.src : DEFAULT_AVATAR_URL;
        console.log('Avatar URL:', avatarUrl); // Debug: Log the avatar URL

        if (!avatarElement) {
            console.warn('No avatar element found in tip:', tip);
        }

        // Extract tip content details
        const tipContent = tip.querySelector('.tip-content');
        if (!tipContent) {
            console.error('Tip content not found in tip:', tip);
            return;
        }

        const usernameElement = tipContent.querySelector('.tip-username strong');
        const handleElement = tipContent.querySelector('.user-handle');
        // Extract sport emoji more reliably
        const sportEmojiNode = Array.from(tipContent.childNodes).find(node => node.nodeType === 3 && node.textContent.trim().match(/^[⚽⛳🎾🏇]$/));
        const sportEmoji = sportEmojiNode ? sportEmojiNode.textContent.trim() : '';
        const textElement = tipContent.querySelector('p');
        const text = textElement ? textElement.textContent : '';
        const timestamp = tipContent.querySelector('small').textContent;
        const likeCount = tipContent.querySelector('.like-count').textContent;
        const shareCount = tipContent.querySelector('.share-count').textContent;
        const commentCount = tipContent.querySelector('.comment-count').textContent;
        const engagementCount = tipContent.querySelector('.tip-action-engagement + .tip-action-count')?.textContent || '0';

        // Debug: Log extracted values
        console.log('Extracted values:', {
            username: usernameElement?.textContent,
            handle: handleElement?.textContent,
            sportEmoji,
            text,
            timestamp,
            likeCount,
            shareCount,
            commentCount,
            engagementCount
        });

        // Clear existing content to prevent duplication
        if (modalTipAvatar) {
            modalTipAvatar.src = avatarUrl; // Set avatar URL
            modalTipAvatar.style.display = 'block'; // Ensure avatar is visible
            console.log('Avatar set to:', modalTipAvatar.src);
        } else {
            console.error('modalTipAvatar element not found in modal:', modalTip);
        }

        if (modalTipContent) {
            modalTipContent.innerHTML = ''; // Clear existing content
            console.log('Cleared modalTipContent');
        } else {
            console.error('modalTipContent element not found in modal:', modalTip);
            return;
        }

        // Populate modal-tip content
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
                <div class="tip-action-spacer"></div>
                <div class="tip-action-group">
                    <a href="#" class="tip-action tip-action-engagement"><i class="fas fa-users"></i></a>
                    <span class="tip-action-count">${engagementCount}</span>
                </div>
                <div class="tip-action-spacer-large"></div>
                <div class="tip-action-group">
                    <a href="#" class="tip-action tip-action-bookmark"><i class="fas fa-bookmark"></i></a>
                </div>
                <div class="tip-action-group">
                    <a href="#" class="tip-action tip-action-share-link"><i class="fas fa-arrow-up"></i></a>
                </div>
            </div>
        `;
        console.log('Populated modalTipContent:', modalTipContent.innerHTML);

        commentList.innerHTML = '<p>Loading comments...</p>';

        if (parentId) {
            const parentComment = tip.querySelector(`.comment[data-comment-id="${parentId}"]`);
            if (parentComment) {
                replyToHeader.style.display = 'block';
                replyToUsername.textContent = parentComment.querySelector('.comment-username strong').textContent;
            }
        } else {
            replyToHeader.style.display = 'none';
        }

        fetch(`/api/tip/${tipId}/comments/`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                commentList.innerHTML = '';
                if (data.comments && data.comments.length > 0) {
                    data.comments.forEach(comment => {
                        const avatarUrl = comment.user__avatar ? comment.user__avatar : DEFAULT_AVATAR_URL;
                        const commentDiv = document.createElement('div');
                        commentDiv.className = 'comment';
                        commentDiv.setAttribute('data-comment-id', comment.id);
                        commentDiv.innerHTML = `
                            <img src="${avatarUrl}" alt="${comment.user__username} Avatar" class="comment-avatar" onerror="this.src='${DEFAULT_AVATAR_URL}'">
                            <div class="comment-content">
                                <a href="#" class="comment-username"><strong>${comment.user__username}</strong></a>
                                <p>${comment.content}</p>
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
                                    <div class="comment-action-spacer"></div>
                                    <div class="comment-action-spacer-large"></div>
                                </div>
                            </div>
                        `;
                        commentList.appendChild(commentDiv);
                    });
                    attachCommentActionListeners();
                } else {
                    commentList.innerHTML = '<p>No comments yet.</p>';
                }
            })
            .catch(error => {
                console.error('Error fetching comments:', error);
                commentList.innerHTML = '<p>Error loading comments.</p>';
            });

        commentModal.style.display = 'block';
        commentSubmit.dataset.tipId = tipId; // Store tip ID for submission
        if (parentId) commentSubmit.dataset.parentId = parentId; // Store parent ID for nested reply
    }

    // Function to attach event listeners to comment actions
    function attachCommentActionListeners() {
        const commentActions = commentList.querySelectorAll('.comment-action');
        commentActions.forEach(action => {
            action.addEventListener('click', function(e) {
                e.preventDefault();
                const commentId = this.closest('.comment').getAttribute('data-comment-id');
                const actionType = this.getAttribute('data-action');
                const tipId = commentSubmit.dataset.tipId;

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
                    // Open modal to reply to this comment
                    openCommentModal(this.closest('.tip'), tipId, commentId);
                }
            });
        });
    }

    // Function to handle tip click
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

    // Remove existing listeners and add new ones to prevent duplicates
    tips.forEach(tip => {
        tip.removeEventListener('click', handleTipClick);
        tip.addEventListener('click', handleTipClick);
    });

    // Comment Submit Logic (Post a Reply or Nested Reply)
    commentSubmit.addEventListener('click', function(e) {
        e.preventDefault();
        const tipId = this.dataset.tipId;
        const parentId = this.dataset.parentId;
        const commentText = commentInput.value.trim();

        if (!commentText) {
            alert('Please enter a reply.');
            return;
        }

        const formData = new FormData();
        formData.append('tip_id', tipId);
        formData.append('comment_text', commentText);
        if (parentId) formData.append('parent_id', parentId);

        const endpoint = parentId ? '/api/reply-to-comment/' : '/api/comment-tip/';
        fetch(endpoint, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCSRFToken(),
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                const tip = document.querySelector(`.tip[data-tip-id="${tipId}"]`);
                const commentCount = tip.querySelector('.comment-count');
                commentCount.textContent = data.comment_count;
                const avatarUrl = DEFAULT_AVATAR_URL; // Replace with dynamic avatar URL if available
                const newComment = document.createElement('div');
                newComment.className = 'comment';
                newComment.setAttribute('data-comment-id', data.comment_id);
                newComment.innerHTML = `
                    <img src="${avatarUrl}" alt="${window.currentUser || 'You'} Avatar" class="comment-avatar" onerror="this.src='${DEFAULT_AVATAR_URL}'">
                    <div class="comment-content">
                        <a href="#" class="comment-username"><strong>${window.currentUser || 'You'}</strong></a>
                        <p>${commentText}</p>
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
                            <div class="comment-action-spacer"></div>
                            <div class="comment-action-spacer-large"></div>
                        </div>
                    </div>
                `;
                commentList.insertBefore(newComment, commentList.firstChild);
                commentInput.value = '';
                if (parentId) replyToHeader.style.display = 'none'; // Reset reply-to header after posting
                attachCommentActionListeners(); // Reattach listeners to new comment
            } else {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error commenting on tip:', error);
            alert('An error occurred while commenting.');
        });
    });

    // Close Comment Modal
    commentModalClose.addEventListener('click', function() {
        commentModal.style.display = 'none';
    });

    window.addEventListener('click', function(event) {
        if (event.target === commentModal) {
            commentModal.style.display = 'none';
        }
    });

    // Toggle User Dropdown Menu
    const navUserContent = document.querySelector('.nav-user-content');
    const navUserDropdown = document.querySelector('.nav-user-dropdown');
    const navMenuIcon = document.querySelector('.nav-menu-icon');

    if (navUserContent && navUserDropdown && navMenuIcon) {
        let isDropdownOpen = false;

        navMenuIcon.addEventListener('click', function(e) {
            e.preventDefault();
            isDropdownOpen = !isDropdownOpen;
            navUserDropdown.style.display = isDropdownOpen ? 'block' : 'none';
        });

        document.addEventListener('click', function(e) {
            if (isDropdownOpen && !navUserContent.contains(e.target)) {
                navUserDropdown.style.display = 'none';
                isDropdownOpen = false;
            }
        });

        const dropdownItems = navUserDropdown.querySelectorAll('.nav-dropdown-item');
        dropdownItems.forEach(item => {
            item.addEventListener('click', function(e) {
                console.log('Dropdown item clicked:', item.textContent);
                navUserDropdown.style.display = 'none';
                isDropdownOpen = false;
            });
        });
    }

    // Logout Logic using Global Variables
    const logoutBtn = document.querySelector('.nav-logout-btn[data-logout]');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Logout button clicked');
            fetch(window.LOGOUT_URL, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken(),
                },
            })
            .then(response => {
                if (response.ok) {
                    console.log('Logged out successfully');
                    window.location.href = window.LANDING_URL;
                } else {
                    console.error('Logout failed:', response.status);
                    alert('Error logging out');
                }
            })
            .catch(error => {
                console.error('Logout error:', error);
                alert('An error occurred while logging out');
            });
        });
    }

    // Edit Profile Modal Logic
    const editProfileModal = document.getElementById("editProfileModal");
    const editProfileBtn = document.getElementById("editProfileBtn");
    const editCloseBtn = editProfileModal ? editProfileModal.getElementsByClassName("profile-edit-modal-close")[0] : null;

    if (editProfileBtn) {
        editProfileBtn.onclick = function() {
            if (editProfileModal) {
                editProfileModal.style.display = "block";
            }
        };
    }

    if (editCloseBtn) {
        editCloseBtn.onclick = function() {
            if (editProfileModal) {
                editProfileModal.style.display = "none";
            }
        };
    }

    window.addEventListener('click', function(event) {
        if (editProfileModal && event.target === editProfileModal) {
            editProfileModal.style.display = "none";
        }
    });

    // Handle form submission via AJAX to prevent page reload
    const editProfileForm = document.getElementById('editProfileForm');
    if (editProfileForm) {
        editProfileForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            fetch('/profile/' + encodeURIComponent("{{ user.username }}") + '/edit/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCSRFToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Profile updated successfully!');
                    if (editProfileModal) {
                        editProfileModal.style.display = "none";
                    }
                    location.reload();
                } else {
                    alert('Error updating profile: ' + data.error);
                }
            })
            .catch(error => {
                alert('An error occurred: ' + error);
            });
        });
    }

    // Banner and Avatar Upload/Deletion
    const bannerInput = document.createElement('input');
    bannerInput.type = 'file';
    bannerInput.accept = 'image/*';
    bannerInput.style.display = 'none';
    document.body.appendChild(bannerInput);

    const avatarInput = document.createElement('input');
    avatarInput.type = 'file';
    avatarInput.accept = 'image/*';
    avatarInput.style.display = 'none';
    document.body.appendChild(avatarInput);

    const addBannerBtn = document.querySelector('.profile-edit-action-btn[data-action="add-banner"]');
    const deleteBannerBtn = document.querySelector('.profile-edit-action-btn[data-action="delete-banner"]');
    const addAvatarBtn = document.querySelector('.profile-edit-action-btn[data-action="add-avatar"]');

    if (addBannerBtn) {
        addBannerBtn.addEventListener('click', function() {
            bannerInput.click();
        });
    }

    if (deleteBannerBtn) {
        deleteBannerBtn.addEventListener('click', function() {
            if (confirm('Are you sure you want to delete your banner?')) {
                const form = document.getElementById('editProfileForm');
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'banner-clear';
                input.value = '1';
                form.appendChild(input);
                document.querySelector('.profile-edit-banner img').src = 'https://via.placeholder.com/650x200';
                form.submit();
            }
        });
    }

    if (addAvatarBtn) {
        addAvatarBtn.addEventListener('click', function() {
            avatarInput.click();
        });
    }

    bannerInput.addEventListener('change', function(e) {
        if (e.target.files && e.target.files[0]) {
            const form = document.getElementById('editProfileForm');
            const formData = new FormData(form);
            formData.append('banner', e.target.files[0]);
            fetch('/profile/' + encodeURIComponent("{{ user.username }}") + '/edit/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCSRFToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.querySelector('.profile-edit-banner img').src = URL.createObjectURL(e.target.files[0]);
                    alert('Banner updated successfully!');
                } else {
                    alert('Error updating banner: ' + data.error);
                }
            })
            .catch(error => {
                alert('An error occurred: ' + error);
            });
        }
    });

    avatarInput.addEventListener('change', function(e) {
        if (e.target.files && e.target.files[0]) {
            const form = document.getElementById('editProfileForm');
            const formData = new FormData(form);
            formData.append('avatar', e.target.files[0]);
            fetch('/profile/' + encodeURIComponent("{{ user.username }}") + '/edit/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCSRFToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.querySelector('.profile-edit-avatar img').src = URL.createObjectURL(e.target.files[0]);
                    alert('Avatar updated successfully!');
                } else {
                    alert('Error updating avatar: ' + data.error);
                }
            })
            .catch(error => {
                alert('An error occurred: ' + error);
            });
        }
    });

    // Bio Character Count
    const bioInput = document.getElementById('id_bio');
    const charCount = document.querySelector('.char-count');

    if (bioInput && charCount) {
        bioInput.addEventListener('input', function() {
            const length = this.value.length;
            charCount.textContent = length + ' / 160 characters';
            charCount.style.color = length > 160 ? '#ff4136' : '#666666';
        });
    }

    // Toggle Post Modal and Bind Posting Logic
    const postTipBtn = document.querySelector('.nav-post-btn[data-toggle="post-modal"]');
    const postModal = document.getElementById('post-modal');

    console.log('Post Tip Button:', postTipBtn);
    console.log('Post Modal:', postModal);

    if (postTipBtn && postModal) {
        postTipBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Toggling post modal');
            postModal.style.display = postModal.style.display === 'block' ? 'none' : 'block';

            // Bind posting logic to modal's post-submit button
            const modalSubmitBtn = postModal.querySelector('.post-submit');
            const modalInput = postModal.querySelector('.post-input');
            const modalAudience = postModal.querySelector('.post-audience');

            console.log('Modal Submit Btn:', modalSubmitBtn);
            console.log('Modal Input:', modalInput);
            console.log('Modal Audience:', modalAudience);

            if (modalSubmitBtn && modalInput && modalAudience) {
                // Remove existing listener to prevent duplicates
                modalSubmitBtn.removeEventListener('click', handleModalPostSubmit);
                modalSubmitBtn.addEventListener('click', handleModalPostSubmit);
            } else {
                console.warn('Modal post elements not found:', { modalSubmitBtn, modalInput, modalAudience });
            }
        });

        // Close modal when clicking outside
        window.addEventListener('click', function(event) {
            if (event.target === postModal) {
                console.log('Closing modal by clicking outside');
                postModal.style.display = 'none';
            }
        });

        // Ensure the close button works
        const postModalClose = postModal.querySelector('.post-modal-close');
        console.log('Post Modal Close Button:', postModalClose);
        if (postModalClose) {
            postModalClose.addEventListener('click', function() {
                console.log('Closing modal with close button');
                postModal.style.display = 'none';
            });
        }
    } else {
        console.warn('Post modal elements not found:', { postTipBtn, postModal });
    }

    // Shared handler for modal post submit
    function handleModalPostSubmit() {
        console.log('Modal post button clicked');
        const modalInput = this.closest('.post-modal-content').querySelector('.post-input');
        const modalAudience = this.closest('.post-modal-content').querySelector('.post-audience');
        const text = modalInput.value.trim();
        const audience = modalAudience.value;

        if (!text) {
            alert('Please enter a tip before posting.');
            return;
        }

        const formData = new FormData();
        formData.append('text', text);
        formData.append('audience', audience);
        formData.append('sport', 'golf'); // Adjust dynamically if needed

        fetch('/api/post-tip/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCSRFToken(),
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Tip posted successfully!');
                modalInput.value = '';
                postModal.style.display = 'none';
                location.reload();
            } else {
                alert('Error posting tip: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error posting tip:', error);
            alert('An error occurred while posting the tip.');
        });
    }
});