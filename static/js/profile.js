import { getCSRFToken } from './utils.js';

export function setupProfileEditing() {
    const editProfileModal = document.getElementById("editProfileModal");
    const editProfileBtn = document.getElementById("editProfileBtn");
    const editCloseBtn = editProfileModal?.getElementsByClassName("profile-edit-modal-close")[0];

    if (editProfileBtn) {
        editProfileBtn.onclick = function() {
            if (editProfileModal) editProfileModal.style.display = "block";
        };
    }

    if (editCloseBtn) {
        editCloseBtn.onclick = function() {
            if (editProfileModal) editProfileModal.style.display = "none";
        };
    }

    window.addEventListener('click', function(event) {
        if (editProfileModal && event.target === editProfileModal) {
            editProfileModal.style.display = "none";
        }
    });

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
                    if (editProfileModal) editProfileModal.style.display = "none";
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

    if (addBannerBtn) addBannerBtn.addEventListener('click', () => bannerInput.click());
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
    if (addAvatarBtn) addAvatarBtn.addEventListener('click', () => avatarInput.click());

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

    const bioInput = document.getElementById('id_bio');
    const charCount = document.querySelector('.char-count');
    if (bioInput && charCount) {
        bioInput.addEventListener('input', function() {
            const length = this.value.length;
            charCount.textContent = length + ' / 160 characters';
            charCount.style.color = length > 160 ? '#ff4136' : '#666666';
        });
    }
}