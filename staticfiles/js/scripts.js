// scripts.js
document.addEventListener('DOMContentLoaded', function() {
    // Get the modal and button
    const modal = document.getElementById('post-modal');
    const btn = document.querySelector('.post-btn');
    const closeBtn = document.querySelector('.post-modal-close');

    // Show modal when Post Tip button is clicked
    btn.addEventListener('click', function() {
        modal.style.display = 'flex';
    });

    // Hide modal when close button is clicked
    closeBtn.addEventListener('click', function() {
        modal.style.display = 'none';
    });

    // Hide modal when clicking outside the modal content
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
});


document.addEventListener('DOMContentLoaded', function() {
    // Edit Profile Modal
    var modal = document.getElementById("editProfileModal");
    var btn = document.getElementById("editProfileBtn");
    var span = document.getElementById("editProfileModal").getElementsByClassName("profile-edit-modal-close")[0];

    // Show modal when button is clicked
    if (btn) {
        btn.onclick = function() {
            if (modal) {
                modal.style.display = "block";
            }
        }
    }

    // Close modal when close button (×) is clicked
    if (span) {
        span.onclick = function() {
            if (modal) {
                modal.style.display = "none";
            }
        }
    }

    // Close modal when clicking outside
    window.onclick = function(event) {
        if (modal && event.target == modal) {
            modal.style.display = "none";
        }
    }

    // Handle form submission via AJAX to prevent page reload
    var form = document.getElementById('editProfileForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            var formData = new FormData(this);
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
                    if (modal) {
                        modal.style.display = "none";
                    }
                    location.reload(); // Reload to update profile data
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
    var bannerInput = document.createElement('input');
    bannerInput.type = 'file';
    bannerInput.accept = 'image/*';
    bannerInput.style.display = 'none';
    document.body.appendChild(bannerInput);

    var avatarInput = document.createElement('input');
    avatarInput.type = 'file';
    avatarInput.accept = 'image/*';
    avatarInput.style.display = 'none';
    document.body.appendChild(avatarInput);

    document.querySelector('.profile-edit-action-btn[data-action="add-banner"]').addEventListener('click', function() {
        bannerInput.click();
    });

    document.querySelector('.profile-edit-action-btn[data-action="delete-banner"]').addEventListener('click', function() {
        if (confirm('Are you sure you want to delete your banner?')) {
            var form = document.getElementById('editProfileForm');
            var input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'banner-clear';
            input.value = '1';
            form.appendChild(input);
            document.querySelector('.profile-edit-banner img').src = 'https://via.placeholder.com/650x200';
            form.submit();
        }
    });

    document.querySelector('.profile-edit-action-btn[data-action="add-avatar"]').addEventListener('click', function() {
        avatarInput.click();
    });

    bannerInput.addEventListener('change', function(e) {
        if (e.target.files && e.target.files[0]) {
            var form = document.getElementById('editProfileForm');
            var formData = new FormData(form);
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
            var form = document.getElementById('editProfileForm');
            var formData = new FormData(form);
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
    var bioInput = document.getElementById('id_bio');
    var charCount = document.querySelector('.char-count');

    if (bioInput && charCount) {
        bioInput.addEventListener('input', function() {
            var length = this.value.length;
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