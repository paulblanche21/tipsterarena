// scripts.js
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded'); // Confirm script runs

    // Show more button logic
    const showMoreButtons = document.querySelectorAll('.show-more');

    showMoreButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault(); // Prevent default link behavior
            const target = this.getAttribute('data-target');
            const content = document.querySelector('.content');

            // Clear existing content
            content.innerHTML = '';

            // Add dynamic content based on the target
            switch (target) {
                case 'upcoming-events':
                    content.innerHTML = `
                        <h2>Upcoming Events</h2>
                        <p>Here are more details about upcoming events in Tipster Arena:</p>
                        <ul>
                            <li>Football Match: Premier League - Arsenal vs. Manchester City, March 10, 2025</li>
                            <li>Tennis Tournament: Australian Open Finals, March 15, 2025</li>
                            <li>Horse Racing: Grand National, March 20, 2025</li>
                        </ul>
                        <a href="#" class="show-less" data-target="${target}">Show less</a>
                    `;
                    break;
                case 'trending-tips':
                    content.innerHTML = `
                        <h2>Trending Tips</h2>
                        <p>Hot tips for today’s big events in Tipster Arena:</p>
                        <ul>
                            <li>Solanke to score first in Arsenal vs. Manchester City (Odds: 2.5)</li>
                            <li>Federer to win the Grand Slam (Odds: 3.0)</li>
                            <li>McIlroy to win The Masters (Odds: 4.0)</li>
                        </ul>
                        <a href="#" class="show-less" data-target="${target}">Show less</a>
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
                                <div class="follow-list">
                                    <div class="follow-item">
                                        <img src="${DEFAULT_AVATAR_URL}" alt="Mikkel Mortensen" class="follow-avatar">
                                        <div class="follow-details">
                                            <a href="#" class="follow-username">@MMortensen</a>
                                            <p class="follow-bio">Tottenham</p>
                                        </div>
                                        <button class="follow-btn">Follow</button>
                                    </div>
                                    <div class="follow-item">
                                        <img src="${DEFAULT_AVATAR_URL}" alt="Jedo" class="follow-avatar">
                                        <div class="follow-details">
                                            <a href="#" class="follow-username">@theJedo</a>
                                            <p class="follow-bio">Planeswalker, Historian</p>
                                        </div>
                                        <button class="follow-btn">Follow</button>
                                    </div>
                                    <div class="follow-item">
                                        <img src="${DEFAULT_AVATAR_URL}" alt="Bhattg" class="follow-avatar">
                                        <div class="follow-details">
                                            <a href="#" class="follow-username">@bhattg</a>
                                            <p class="follow-bio">I am an active #hive user. My hive user name is @bhattg my referral code:--https://h...</p>
                                        </div>
                                        <button class="follow-btn">Follow</button>
                                    </div>
                                </div>
                                <a href="#" class="show-less" data-target="${target}">Show less</a>
                            </div>
                        `;
                        break;
                                }

            // Add "Show less" button functionality
            const showLessButtons = document.querySelectorAll('.show-less');
            showLessButtons.forEach(lessButton => {
                lessButton.addEventListener('click', function(e) {
                    e.preventDefault();
                    content.innerHTML = ''; // Clear content to show original child templates
                });
            });

            // Add back arrow functionality
            const backArrows = document.querySelectorAll('.back-arrow');
            backArrows.forEach(arrow => {
                arrow.addEventListener('click', function(e) {
                    e.preventDefault();
                    content.innerHTML = ''; // Clear content to show original child templates
                });
            });
        }); // Added closing bracket for click event listener
    }); // Added closing bracket for forEach

    // Post Modal Logic
    const postModal = document.getElementById('post-modal');
    const postBtn = document.querySelector('.post-btn');
    const closeBtn = document.querySelector('.post-modal-close');

    if (postBtn) {
        console.log('Post button found');
        postBtn.addEventListener('click', function() {
            postModal.style.display = 'flex';
        });
    } else {
        console.warn('Post button not found');
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            postModal.style.display = 'none';
        });
    }

    window.addEventListener('click', function(event) {
        if (event.target === postModal) {
            postModal.style.display = 'none';
        }
    });

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
        if (event.target === postModal) {
            postModal.style.display = 'none';
        }
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

    
    // Function to get CSRF token
    function getCSRFToken() {
        return document.querySelector('input[name="csrfmiddlewaretoken"]').value;
    }
}); // Closing DOMContentLoaded event listener