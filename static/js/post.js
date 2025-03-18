import { getCSRFToken } from './utils.js';

// Function to show the success popup
function showSuccessPopup() {
    const popup = document.getElementById('success-popup');
    if (popup) {
        popup.style.display = 'block';
        
        const closeBtn = popup.querySelector('.success-popup-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                popup.style.display = 'none';
            });
        }
        
        popup.addEventListener('click', (event) => {
            if (event.target === popup) {
                popup.style.display = 'none';
            }
        });
        
        setTimeout(() => {
            popup.style.display = 'none';
        }, 3000);
    }
}

// Helper function to apply formatting (bold or italic) to the selected text in a textarea
function applyFormatting(textarea, tag) {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = textarea.value.substring(start, end);
    const beforeText = textarea.value.substring(0, start);
    const afterText = textarea.value.substring(end);

    let newText, newSelectionStart, newSelectionEnd;

    if (selectedText.length > 0) {
        // If text is selected, wrap it with the tag
        newText = `${beforeText}<${tag}>${selectedText}</${tag}>${afterText}`;
        newSelectionStart = start;
        newSelectionEnd = end + tag.length * 2 + 5; // Adjust for the length of the tags
    } else {
        // If no text is selected, insert the tag with a placeholder
        const placeholder = tag === 'b' ? 'bold text' : 'italic text';
        newText = `${beforeText}<${tag}>${placeholder}</${tag}>${afterText}`;
        newSelectionStart = start + tag.length + 2; // Position cursor after the opening tag
        newSelectionEnd = newSelectionStart + placeholder.length; // Select the placeholder text
    }

    textarea.value = newText;
    textarea.setSelectionRange(newSelectionStart, newSelectionEnd);
    textarea.focus();
}

export function setupCentralFeedPost() {
    const postSubmitBtn = document.querySelector('.post-submit');
    const postInput = document.querySelector('.post-input');
    const postAudience = document.querySelector('.post-audience');
    const emojiBtn = document.querySelector('.post-action-btn.emoji');
    const gifBtn = document.querySelector('.post-action-btn.gif');
    const imageBtn = document.querySelector('.post-action-btn.image');
    const locationBtn = document.querySelector('.post-action-btn.location');
    const boldBtn = document.querySelector('.post-action-btn.bold');
    const italicBtn = document.querySelector('.post-action-btn.italic');
    const pollBtn = document.querySelector('.post-action-btn.poll');
    const scheduleBtn = document.querySelector('.post-action-btn.schedule');

    if (!postSubmitBtn || !postInput || !postAudience || !emojiBtn || !gifBtn || !imageBtn || !locationBtn || !boldBtn || !italicBtn || !pollBtn || !scheduleBtn) {
        console.warn('setupCentralFeedPost: One or more required DOM elements are missing.');
        console.log({
            postSubmitBtn: !!postSubmitBtn,
            postInput: !!postInput,
            postAudience: !!postAudience,
            emojiBtn: !!emojiBtn,
            gifBtn: !!gifBtn,
            imageBtn: !!imageBtn,
            locationBtn: !!locationBtn,
            boldBtn: !!boldBtn,
            italicBtn: !!italicBtn,
            pollBtn: !!pollBtn,
            scheduleBtn: !!scheduleBtn
        });
        return;
    }

    // Track location separately for form submission
    let locationData = '';

    // Bold button functionality
    boldBtn.addEventListener('click', (e) => {
        e.preventDefault();
        applyFormatting(postInput, 'b');
    });

    // Italic button functionality
    italicBtn.addEventListener('click', (e) => {
        e.preventDefault();
        applyFormatting(postInput, 'i');
    });

    // Location functionality
    locationBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const { latitude, longitude } = position.coords;
                    locationData = `${latitude.toFixed(2)},${longitude.toFixed(2)}`;
                    postInput.value += ` [Location: ${locationData}]`;
                },
                (error) => {
                    alert('Unable to retrieve location: ' + error.message);
                }
            );
        } else {
            alert('Geolocation is not supported by your browser.');
        }
    });

    // Image functionality
    const imageInput = document.createElement('input');
    imageInput.type = 'file';
    imageInput.accept = 'image/*';
    imageInput.style.display = 'none';
    document.body.appendChild(imageInput);

    imageBtn.addEventListener('click', (e) => {
        e.preventDefault();
        imageInput.click();
    });

    imageInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            console.log('Image selected:', file.name);
        }
    });

    // GIF functionality
    const gifInput = document.createElement('input');
    gifInput.type = 'file';
    gifInput.accept = 'image/gif';
    gifInput.style.display = 'none';
    document.body.appendChild(gifInput);

    gifBtn.addEventListener('click', (e) => {
        e.preventDefault();
        gifInput.click();
    });

    gifInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            console.log('GIF selected:', file.name);
        }
    });

    // Poll functionality (placeholder for now)
    pollBtn.addEventListener('click', (e) => {
        e.preventDefault();
        alert('Poll functionality coming soon!');
        // Future: Show a modal to input poll options
    });

    // Schedule functionality (placeholder for now)
    scheduleBtn.addEventListener('click', (e) => {
        e.preventDefault();
        alert('Schedule functionality coming soon!');
        // Future: Show a date/time picker
    });

    // Submit logic
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

        // Append optional fields if they exist
        if (imageInput.files[0]) {
            formData.append('image', imageInput.files[0]);
        }
        if (gifInput.files[0]) {
            formData.append('gif', gifInput.files[0]);
        }
        if (locationData) {
            formData.append('location', locationData);
        }
        formData.append('poll', '{}'); // Default empty JSON string
        formData.append('emojis', '{}'); // Default empty JSON string

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
                showSuccessPopup();
                postInput.value = '';
                imageInput.value = '';
                gifInput.value = '';
                locationData = '';
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
            const modalBoldBtn = postModal.querySelector('.post-action-btn.bold');
            const modalItalicBtn = postModal.querySelector('.post-action-btn.italic');
            const modalImageBtn = postModal.querySelector('.post-action-btn.image');
            const modalGifBtn = postModal.querySelector('.post-action-btn.gif');
            const modalLocationBtn = postModal.querySelector('.post-action-btn.location');

            if (modalSubmitBtn && modalInput && modalAudience && modalBoldBtn && modalItalicBtn && modalImageBtn && modalGifBtn && modalLocationBtn) {
                // Bold button functionality for modal
                modalBoldBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    applyFormatting(modalInput, 'b');
                });

                // Italic button functionality for modal
                modalItalicBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    applyFormatting(modalInput, 'i');
                });

                // Image functionality for modal
                const modalImageInput = document.createElement('input');
                modalImageInput.type = 'file';
                modalImageInput.accept = 'image/*';
                modalImageInput.style.display = 'none';
                document.body.appendChild(modalImageInput);

                modalImageBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    modalImageInput.click();
                });

                modalImageInput.addEventListener('change', (e) => {
                    const file = e.target.files[0];
                    if (file) {
                        console.log('Modal Image selected:', file.name);
                    }
                });

                // GIF functionality for modal
                const modalGifInput = document.createElement('input');
                modalGifInput.type = 'file';
                modalGifInput.accept = 'image/gif';
                modalGifInput.style.display = 'none';
                document.body.appendChild(modalGifInput);

                modalGifBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    modalGifInput.click();
                });

                modalGifInput.addEventListener('change', (e) => {
                    const file = e.target.files[0];
                    if (file) {
                        console.log('Modal GIF selected:', file.name);
                    }
                });

                // Location functionality for modal
                let modalLocationData = '';
                modalLocationBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    if (navigator.geolocation) {
                        navigator.geolocation.getCurrentPosition(
                            (position) => {
                                const { latitude, longitude } = position.coords;
                                modalLocationData = `${latitude.toFixed(2)},${longitude.toFixed(2)}`;
                                modalInput.value += ` [Location: ${modalLocationData}]`;
                            },
                            (error) => {
                                alert('Unable to retrieve location: ' + error.message);
                            }
                        );
                    } else {
                        alert('Geolocation is not supported by your browser.');
                    }
                });

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

    // Append optional fields if they exist
    const modalImageInput = document.querySelectorAll('input[type="file"]')[1]; // Assuming second file input is modal's
    const modalGifInput = document.querySelectorAll('input[type="file"]')[2];   // Assuming third file input is modal's
    if (modalImageInput && modalImageInput.files[0]) {
        formData.append('image', modalImageInput.files[0]);
    }
    if (modalGifInput && modalGifInput.files[0]) {
        formData.append('gif', modalGifInput.files[0]);
    }
    const modalLocationBtn = document.querySelector('.post-modal .post-action-btn.location');
    let modalLocationData = '';
    if (modalLocationBtn) {
        modalLocationData = modalInput.value.match(/\[Location: ([\d.,]+)\]/)?.[1] || '';
    }
    if (modalLocationData) {
        formData.append('location', modalLocationData);
    }
    formData.append('poll', '{}'); // Default empty JSON string
    formData.append('emojis', '{}'); // Default empty JSON string

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
            showSuccessPopup();
            modalInput.value = '';
            if (modalImageInput) modalImageInput.value = '';
            if (modalGifInput) modalGifInput.value = '';
            modalLocationData = '';
            document.getElementById('post-modal').style.display = 'none';
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