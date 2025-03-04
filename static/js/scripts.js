// scripts.js
document.addEventListener('DOMContentLoaded', function() {
    // Post Modal (Post Tip button)
    const postModal = document.getElementById('post-modal');
    const postBtn = document.querySelector('.post-btn');
    const postCloseBtn = document.querySelector('.post-modal-close');

    // Show post modal when Post Tip button is clicked
    if (postBtn) {
        postBtn.addEventListener('click', function() {
            if (postModal) {
                postModal.style.display = 'flex';
            }
        });
    }

    // Hide post modal when close button is clicked
    if (postCloseBtn) {
        postCloseBtn.addEventListener('click', function() {
            if (postModal) {
                postModal.style.display = 'none';
            }
        });
    }

    // Hide post modal when clicking outside
    window.addEventListener('click', function(event) {
        if (postModal && event.target === postModal) {
            postModal.style.display = 'none';
        }
    });

    // Edit Profile Modal
    const editModal = document.getElementById('editProfileModal');
    const editBtn = document.getElementById('editProfileBtn');
    const editCloseBtn = document.querySelector('.profile-edit-modal-close');

    // Show edit profile modal when button is clicked
    if (editBtn) {
        editBtn.addEventListener('click', function() {
            if (editModal) {
                editModal.style.display = 'flex';
            }
        });
    }

    // Hide edit profile modal when close button is clicked
    if (editCloseBtn) {
        editCloseBtn.addEventListener('click', function() {
            if (editModal) {
                editModal.style.display = 'none';
            }
        });
    }

    // Hide edit profile modal when clicking outside
    window.addEventListener('click', function(event) {
        if (editModal && event.target === editModal) {
            editModal.style.display = 'none';
        }
    });

    // Handle edit profile form submission via AJAX with bio length check
    const editForm = document.getElementById('editProfileForm');
    const bioInput = document.getElementById('id_description'); // Bio input field
    if (editForm) {
        editForm.addEventListener('submit', function(e) {
            e.preventDefault();
            if (bioInput && bioInput.value.length > 160) {
                alert('Bio cannot exceed 160 characters.');
                return;
            }
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
                    if (editModal) {
                        editModal.style.display = 'none';
                    }
                    location.reload(); // Reload to update profile data on the page
                } else {
                    alert('Error updating profile: ' + data.error);
                }
            })
            .catch(error => {
                alert('An error occurred: ' + error);
            });
        });
    }

    // Banner and Avatar Upload/Deletion (with preview in modal and profile update)
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

    // Add banner
    const addBannerBtn = document.querySelector('.profile-edit-action-btn[data-action="add-banner"]');
    if (addBannerBtn) {
        addBannerBtn.addEventListener('click', function() {
            bannerInput.click();
        });
    }

    // Delete banner (set flag and update preview, but don't submit immediately)
    const deleteBannerBtn = document.querySelector('.profile-edit-action-btn[data-action="delete-banner"]');
    if (deleteBannerBtn) {
        deleteBannerBtn.addEventListener('click', function() {
            if (confirm('Are you sure you want to delete your banner?')) {
                const form = document.getElementById('editProfileForm');
                let input = form.querySelector('input[name="banner-clear"]');
                if (!input) {
                    input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = 'banner-clear';
                    input.value = '1';
                    form.appendChild(input);
                }
                document.querySelector('.profile-edit-banner-img').src = 'https://via.placeholder.com/598x200';
                document.querySelector('.profile-banner').src = 'https://via.placeholder.com/598x200';
                // Form is not submitted here; user must submit manually
            }
        });
    }

    // Add avatar
    const addAvatarBtn = document.querySelector('.profile-edit-action-btn[data-action="add-avatar"]');
    if (addAvatarBtn) {
        addAvatarBtn.addEventListener('click', function() {
            avatarInput.click();
        });
    }

    // Handle banner upload (preview in modal and update profile)
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
                    const bannerUrl = URL.createObjectURL(e.target.files[0]);
                    document.querySelector('.profile-edit-banner-img').src = bannerUrl; // Update modal preview
                    document.querySelector('.profile-banner').src = bannerUrl; // Update profile page banner
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

    // Handle avatar upload (preview in modal and update profile)
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
                    const avatarUrl = URL.createObjectURL(e.target.files[0]);
                    document.querySelector('.profile-edit-avatar-img').src = avatarUrl; // Update modal preview
                    document.querySelector('.profile-avatar').src = avatarUrl; // Update profile page avatar
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
    const charCount = document.querySelector('.char-count');
    if (bioInput && charCount) {
        bioInput.addEventListener('input', function() {
            const length = this.value.length;
            charCount.textContent = length + ' / 160 characters';
            if (length > 160) {
                charCount.style.color = '#ff4136';
            } else {
                charCount.style.color = '#666666';
            }
        });
    }

    // Function to get CSRF token (for Django security)
    function getCSRFToken() {
        return document.querySelector('input[name="csrfmiddlewaretoken"]').value;
    }
});