// profile-edit.js
import { getCSRFToken } from './utils.js';

export function setupProfileEditing() {
    const editProfileModal = document.getElementById("editProfileModal");
    const editProfileBtn = document.getElementById("editProfileBtn");
    const editCloseBtn = editProfileModal?.getElementsByClassName("profile-edit-modal-close")[0];

    // Modal open/close logic
    if (editProfileBtn) {
        editProfileBtn.onclick = () => {
            editProfileModal.style.display = "block";
        };
    }

    if (editCloseBtn) {
        editCloseBtn.onclick = () => {
            editProfileModal.style.display = "none";
        };
        editCloseBtn.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === 'Space') {
                editProfileModal.style.display = "none";
            }
        });
    }

    window.addEventListener('click', (event) => {
        if (event.target === editProfileModal) {
            editProfileModal.style.display = "none";
        }
    });

    // Form submission with loading state
    const editProfileForm = document.getElementById('editProfileForm');
    if (editProfileForm) {
        editProfileForm.addEventListener('submit', (e) => {
            e.preventDefault();
            // Clear previous errors
            editProfileForm.querySelectorAll('.error').forEach(el => el.remove());
            const submitBtn = editProfileForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Saving...';
            const formData = new FormData(editProfileForm);
            fetch('/profile/' + encodeURIComponent(window.profileUsername) + '/edit/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCSRFToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    editProfileModal.style.display = "none";
                    location.reload();
                } else {
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'error';
                    errorDiv.textContent = 'Error updating profile: ' + data.error;
                    editProfileForm.prepend(errorDiv);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                const errorDiv = document.createElement('div');
                errorDiv.className = 'error';
                errorDiv.textContent = 'An error occurred. Please try again.';
                editProfileForm.prepend(errorDiv);
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Save Changes';
            });
        });
    }

    // File input triggers
    const addBannerBtn = document.querySelector('.profile-edit-action-btn[data-action="add-banner"]');
    const deleteBannerBtn = document.querySelector('.profile-edit-action-btn[data-action="delete-banner"]');
    const addAvatarBtn = document.querySelector('.profile-edit-action-btn[data-action="add-avatar"]');

    if (addBannerBtn) {
        addBannerBtn.addEventListener('click', () => {
            document.getElementById('id_banner').click();
        });
    }

    if (deleteBannerBtn) {
        deleteBannerBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to delete your banner?')) {
                const bannerInput = document.getElementById('id_banner');
                bannerInput.value = '';
                const bannerPreview = document.getElementById('banner-preview');
                bannerPreview.src = bannerPreview.dataset.defaultSrc;
            }
        });
    }

    if (addAvatarBtn) {
        addAvatarBtn.addEventListener('click', () => {
            document.getElementById('id_avatar').click();
        });
    }

    // Image preview and validation
    function previewImage(input, previewId) {
        const preview = document.getElementById(previewId);
        const file = input.files[0];
        if (file) {
            if (file.size > 5 * 1024 * 1024) {
                alert('File size exceeds 5MB.');
                input.value = '';
                return;
            }
            if (!file.type.startsWith('image/')) {
                alert('Please upload an image file.');
                input.value = '';
                return;
            }
            const reader = new FileReader();
            reader.onload = (e) => {
                preview.src = e.target.result;
            };
            reader.readAsDataURL(file);
        }
    }

    const bannerInput = document.getElementById('id_banner');
    const avatarInput = document.getElementById('id_avatar');
    if (bannerInput) {
        bannerInput.addEventListener('change', (e) => previewImage(e.target, 'banner-preview'));
    }
    if (avatarInput) {
        avatarInput.addEventListener('change', (e) => previewImage(e.target, 'avatar-preview'));
    }

    // Bio character counting
    const descriptionInput = document.getElementById('id_description');
    const charCount = document.querySelector('.char-count');
    if (descriptionInput && charCount) {
        descriptionInput.addEventListener('input', () => {
            const length = descriptionInput.value.length;
            charCount.textContent = length + ' / 160 characters';
            charCount.style.color = length > 160 ? '#ff4136' : '#666666';
        });
    }
}