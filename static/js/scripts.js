// scripts.js
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded'); // Confirm script runs

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

    // Navbar Dropdown Logic (Target three dots)
    const navMenuIcon = document.querySelector('.nav-menu-icon');
    const navUserDropdown = document.querySelector('.nav-user-dropdown');
    const logoutBtn = document.querySelector('.nav-logout-btn');

    if (navMenuIcon) {
        console.log('Nav menu icon found:', navMenuIcon);
        navMenuIcon.addEventListener('click', function(e) {
            console.log('Three dots clicked');
            navUserDropdown.style.display = navUserDropdown.style.display === 'block' ? 'none' : 'block';
            e.stopPropagation();
        });
    } else {
        console.error('Nav menu icon not found');
    }

    if (navUserDropdown) {
        console.log('Nav user dropdown found:', navUserDropdown);
        document.addEventListener('click', function(event) {
            if (!navMenuIcon.contains(event.target) && !navUserDropdown.contains(event.target)) {
                console.log('Clicked outside, hiding dropdown');
                navUserDropdown.style.display = 'none';
            }
        });
    } else {
        console.error('Nav user dropdown not found');
    }

    if (logoutBtn) {
        console.log('Logout button found');
        logoutBtn.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    } else {
        console.warn('Logout button not found');
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
});