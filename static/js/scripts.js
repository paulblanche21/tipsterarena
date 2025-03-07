// scripts.js
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded');

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

    // Show more button logic
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
                    content.innerHTML = `
                        <div class="follow-card">
                            <div class="back-arrow-container">
                                <a href="#" class="back-arrow"><i class="fas fa-arrow-left"></i></a>
                                <h2>Upcoming Events</h2>
                            </div>
                            <p>Here are the latest upcoming events in Tipster Arena:</p>
                            <div class="event-list">
                                <div class="event-item">
                                    <p>Football Match: Premier League - Manchester United vs. Tottenham, March 12, 2025</p>
                                </div>
                            </div>
                            <a href="#" class="show-less" data-target="${target}">Show less</a>
                        </div>
                    `;
                    break;
                case 'trending-tips':
                    content.innerHTML = `
                        <div class="follow-card">
                            <div class="back-arrow-container">
                                <a href="#" class="back-arrow"><i class="fas fa-arrow-left"></i></a>
                                <h2>Trending Tips</h2>
                            </div>
                            <p>Hot tips for today’s big events in Tipster Arena:</p>
                            <div class="tip-list">
                                <div class="tip-item">
                                    <img src="${DEFAULT_AVATAR_URL}" alt="User Avatar" class="tip-avatar">
                                    <div class="tip-details">
                                        <strong>User 1</strong> - Solanke to score first in Manchester United vs. Tottenham (Odds: 2.5) - Likes: 150
                                    </div>
                                </div>
                                <div class="tip-item">
                                    <img src="${DEFAULT_AVATAR_URL}" alt="User Avatar" class="tip-avatar">
                                    <div class="tip-details">
                                        <strong>User 2</strong> - Kane to score in Manchester United vs. Tottenham (Odds: 2.0) - Likes: 120
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
                            <div class="back-arrow-container">
                                <a href="#" class="back-arrow"><i class="fas fa-arrow-left"></i></a>
                                <h2>Who to Follow</h2>
                            </div>
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
                });
            });

            const backArrows = document.querySelectorAll('.back-arrow');
            backArrows.forEach(arrow => {
                arrow.addEventListener('click', function(e) {
                    e.preventDefault();
                    if (previousUrl) {
                        window.location.href = previousUrl;
                    } else {
                        window.history.back();
                    }
                });
            });
        });
    });

    // Post Tip Logic (for home.html)
    const postSubmitBtn = document.querySelector('.post-submit');
    const postInput = document.querySelector('.post-input');
    const postAudience = document.querySelector('.post-audience');

    console.log('Post Submit Btn:', postSubmitBtn); // Debug log
    console.log('Post Input:', postInput); // Debug log
    console.log('Post Audience:', postAudience); // Debug log

    if (postSubmitBtn && postInput && postAudience) {
        postSubmitBtn.addEventListener('click', function() {
            console.log('Post button clicked'); // Debug log
            const text = postInput.value.trim();
            const audience = postAudience.value;

            if (!text) {
                alert('Please enter a tip before posting.');
                return;
            }

            const formData = new FormData();
            formData.append('text', text);
            formData.append('audience', audience);
            // Add sport selection if implemented in the future
            // formData.append('sport', sportValue);

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
                    postInput.value = ''; // Clear the input
                    location.reload(); // Refresh the page to show the new tip
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
        console.warn('One or more post modal elements not found:', { postSubmitBtn, postInput, postAudience });
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

    // Toggle Post Modal
    const postTipBtn = document.querySelector('.nav-post-btn[data-toggle="post-modal"]');
    const postModal = document.getElementById('post-modal');

    if (postTipBtn && postModal) {
        postTipBtn.addEventListener('click', function() {
            postModal.style.display = postModal.style.display === 'block' ? 'none' : 'block';
        });

        // Close modal when clicking outside
        window.addEventListener('click', function(event) {
            if (event.target === postModal) {
                postModal.style.display = 'none';
            }
        });

        // Ensure the close button works
        const postModalClose = document.querySelector('.post-modal-close');
        if (postModalClose) {
            postModalClose.addEventListener('click', function() {
                postModal.style.display = 'none';
            });
        }
    }

    // Function to get CSRF token
    function getCSRFToken() {
        const tokenElement = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (!tokenElement) {
            console.warn("CSRF token not found on page");
            return null;
        }
        return tokenElement.value;
    }
});