import { getCSRFToken } from './utils.js';

export function setupCentralFeedPost() {
    const postSubmitBtn = document.querySelector('.post-submit');
    const postInput = document.querySelector('.post-input');
    const postAudience = document.querySelector('.post-audience');

    if (postSubmitBtn && postInput && postAudience) {
        postSubmitBtn.addEventListener('click', function() {
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
    }
}

export function setupPostModal() {
    const postTipBtn = document.querySelector('.nav-post-btn[data-toggle="post-modal"]');
    const postModal = document.getElementById('post-modal');

    if (postTipBtn && postModal) {
        postTipBtn.addEventListener('click', function(e) {
            e.preventDefault();
            postModal.style.display = postModal.style.display === 'block' ? 'none' : 'block';

            const modalSubmitBtn = postModal.querySelector('.post-submit');
            const modalInput = postModal.querySelector('.post-input');
            const modalAudience = postModal.querySelector('.post-audience');

            if (modalSubmitBtn && modalInput && modalAudience) {
                modalSubmitBtn.removeEventListener('click', handleModalPostSubmit);
                modalSubmitBtn.addEventListener('click', handleModalPostSubmit);
            }
        });

        window.addEventListener('click', function(event) {
            if (event.target === postModal) {
                postModal.style.display = 'none';
            }
        });

        const postModalClose = postModal.querySelector('.post-modal-close');
        if (postModalClose) {
            postModalClose.addEventListener('click', function() {
                postModal.style.display = 'none';
            });
        }
    }
}

function handleModalPostSubmit() {
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