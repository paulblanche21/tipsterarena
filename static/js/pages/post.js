import { getCSRFToken } from './utils.js';

// Giphy API Key
const GIPHY_API_KEY = 'Lpfo7GvcccncunU2gvf0Cy9N3NCzrg35';

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
        newText = `${beforeText}<${tag}>${selectedText}</${tag}>${afterText}`;
        newSelectionStart = start;
        newSelectionEnd = end + tag.length * 2 + 5;
    } else {
        const placeholder = tag === 'b' ? 'bold text' : 'italic text';
        newText = `${beforeText}<${tag}>${placeholder}</${tag}>${afterText}`;
        newSelectionStart = start + tag.length + 2;
        newSelectionEnd = newSelectionStart + placeholder.length;
    }

    textarea.value = newText;
    textarea.setSelectionRange(newSelectionStart, newSelectionEnd);
    textarea.focus();
}

// Debounce function to limit API calls
function debounce(func, wait) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// Function to show the GIF search modal
function showGifModal(textarea, previewDiv) {
    let gifModal = document.getElementById('gif-modal');
    if (!gifModal) {
        gifModal = document.createElement('div');
        gifModal.id = 'gif-modal';
        gifModal.className = 'gif-modal';
        gifModal.innerHTML = `
            <div class="gif-modal-content">
                <span class="gif-modal-close">×</span>
                <input type="text" class="gif-search-input" placeholder="Search GIFs...">
                <div class="gif-results"></div>
            </div>
        `;
        document.body.appendChild(gifModal);
    }

    gifModal.style.display = 'block';

    const closeBtn = gifModal.querySelector('.gif-modal-close');
    const searchInput = gifModal.querySelector('.gif-search-input');
    const resultsDiv = gifModal.querySelector('.gif-results');

    closeBtn.onclick = () => gifModal.style.display = 'none';
    window.onclick = (event) => {
        if (event.target === gifModal) gifModal.style.display = 'none';
    };

    searchInput.oninput = debounce((e) => {
        const query = e.target.value.trim();
        if (query) {
            fetch(`https://api.giphy.com/v1/gifs/search?api_key=${GIPHY_API_KEY}&q=${encodeURIComponent(query)}&limit=10`)
                .then(response => response.json())
                .then(data => {
                    resultsDiv.innerHTML = '';
                    if (data.data.length === 0) {
                        resultsDiv.innerHTML = '<p>No GIFs found.</p>';
                        return;
                    }
                    data.data.forEach(gif => {
                        const img = document.createElement('img');
                        img.src = gif.images.fixed_height.url;
                        img.alt = gif.title;
                        img.className = 'gif-result';
                        img.onclick = () => {
                            textarea.dataset.gifUrl = gif.images.original.url;
                            const previewImg = previewDiv.querySelector('.preview-media');
                            previewImg.src = gif.images.original.url;
                            previewDiv.style.display = 'block';
                            gifModal.style.display = 'none';
                        };
                        resultsDiv.appendChild(img);
                    });
                })
                .catch(error => {
                    console.error('Error fetching GIFs:', error);
                    resultsDiv.innerHTML = '<p>Error fetching GIFs. Please try again.</p>';
                });
        } else {
            resultsDiv.innerHTML = '';
        }
    }, 300);
}

// Function to fetch and show the emoji picker with all emojis, X-style
export async function showEmojiPicker(textarea, triggerButton) {
    let emojiPicker = document.getElementById('emoji-picker');
    if (!emojiPicker) {
        emojiPicker = document.createElement('div');
        emojiPicker.id = 'emoji-picker';
        emojiPicker.className = 'emoji-picker';
        emojiPicker.innerHTML = `
            <div class="emoji-picker-content">
                <span class="emoji-picker-close">×</span>
                <input type="text" class="emoji-search" placeholder="Search emojis...">
                <div class="emoji-tabs">
                    <button class="emoji-tab active" data-category="recent" title="Recent">🕒</button>
                    <button class="emoji-tab" data-category="Smileys & Emotion" title="Smileys & People">😊</button>
                    <button class="emoji-tab" data-category="Animals & Nature" title="Animals & Nature">🐾</button>
                    <button class="emoji-tab" data-category="Food & Drink" title="Food & Drink">🍔</button>
                    <button class="emoji-tab" data-category="Activities" title="Activities">⚽</button>
                    <button class="emoji-tab" data-category="Travel & Places" title="Travel & Places">✈️</button>
                    <button class="emoji-tab" data-category="Objects" title="Objects">💡</button>
                    <button class="emoji-tab" data-category="Symbols" title="Symbols">❤️</button>
                    <button class="emoji-tab" data-category="Flags" title="Flags">🏳️</button>
                </div>
                <div class="emoji-category-title"></div>
                <div class="emoji-grid"></div>
            </div>
        `;
        document.body.appendChild(emojiPicker);
    }

    const emojiGrid = emojiPicker.querySelector('.emoji-grid');
    const categoryTitle = emojiPicker.querySelector('.emoji-category-title');
    const searchInput = emojiPicker.querySelector('.emoji-search');
    const tabs = emojiPicker.querySelectorAll('.emoji-tab');
    let allEmojis = [];
    let recentEmojis = JSON.parse(localStorage.getItem('recentEmojis')) || [];

    // Fetch emoji data only when the function runs
    const loadEmojis = async () => {
        try {
            const response = await fetch('https://unpkg.com/emoji.json@14.0.0/emoji.json');
            const emojiData = await response.json();
            console.log(`Loaded ${emojiData.length} emojis`);
            const uniqueCategories = [...new Set(emojiData.map(emoji => emoji.category))];
            console.log('Unique categories in emoji.json:', uniqueCategories);
            return emojiData;
        } catch (error) {
            console.error('Error fetching emoji data:', error);
            return [
                { char: '😀', category: 'Smileys & Emotion', name: 'grinning face' },
                { char: '😂', category: 'Smileys & Emotion', name: 'face with tears of joy' },
                { char: '😍', category: 'Smileys & Emotion', name: 'smiling face with heart-eyes' },
                { char: '😢', category: 'Smileys & Emotion', name: 'crying face' },
                { char: '😡', category: 'Smileys & Emotion', name: 'pouting face' },
                { char: '👍', category: 'Smileys & Emotion', name: 'thumbs up' },
                { char: '👎', category: 'Smileys & Emotion', name: 'thumbs down' },
                { char: '❤️', category: 'Symbols', name: 'red heart' },
                { char: '🔥', category: 'Symbols', name: 'fire' },
                { char: '✨', category: 'Symbols', name: 'sparkles' },
                { char: '🎉', category: 'Activities', name: 'party popper' },
                { char: '💪', category: 'Smileys & Emotion', name: 'flexed biceps' },
                { char: '🙌', category: 'Smileys & Emotion', name: 'raising hands' },
                { char: '👏', category: 'Smileys & Emotion', name: 'clapping hands' },
                { char: '🤓', category: 'Smileys & Emotion', name: 'nerd face' },
                { char: '😎', category: 'Smileys & Emotion', name: 'smiling face with sunglasses' },
                { char: '🤔', category: 'Smileys & Emotion', name: 'thinking face' },
                { char: '🙏', category: 'Smileys & Emotion', name: 'folded hands' },
                { char: '🚀', category: 'Travel & Places', name: 'rocket' },
                { char: '🌟', category: 'Symbols', name: 'glowing star' },
                { char: '⚽', category: 'Activities', name: 'soccer ball' },
                { char: '⛳', category: 'Activities', name: 'flag in hole' },
                { char: '🎾', category: 'Activities', name: 'tennis' },
                { char: '🏇', category: 'Animals & Nature', name: 'horse racing' },
                { char: '🏀', category: 'Activities', name: 'basketball' },
                { char: '🏈', category: 'Activities', name: 'american football' },
                { char: '🎲', category: 'Objects', name: 'game die' },
                { char: '🎯', category: 'Activities', name: 'bullseye' },
                { char: '🎸', category: 'Objects', name: 'guitar' },
                { char: '🎮', category: 'Objects', name: 'video game' }
            ];
        }
    };

    allEmojis = await loadEmojis();

    function renderEmojis(emojis) {
        emojiGrid.innerHTML = '';
        if (emojis.length === 0) {
            emojiGrid.innerHTML = '<p>No emojis found.</p>';
            return;
        }
        emojis.forEach(emoji => {
            const span = document.createElement('span');
            span.textContent = emoji.char;
            span.className = 'emoji-item';
            span.title = emoji.name; // Add tooltip with emoji name
            span.addEventListener('click', () => {
                const cursorPos = textarea.selectionStart;
                const textBefore = textarea.value.substring(0, cursorPos);
                const textAfter = textarea.value.substring(cursorPos);
                textarea.value = textBefore + emoji.char + textAfter;
                textarea.focus();
                textarea.selectionStart = textarea.selectionEnd = cursorPos + emoji.char.length;

                // Add to recent emojis
                recentEmojis = recentEmojis.filter(e => e !== emoji.char);
                recentEmojis.unshift(emoji.char);
                if (recentEmojis.length > 20) recentEmojis.pop();
                localStorage.setItem('recentEmojis', JSON.stringify(recentEmojis));

                emojiPicker.style.display = 'none';
            });
            emojiGrid.appendChild(span);
        });
    }

    // Update category title
    function updateCategoryTitle(category) {
        const titles = {
            recent: 'Recent',
            'Smileys & Emotion': 'Smileys & People',
            'People & Body': 'People & Body',
            'Animals & Nature': 'Animals & Nature',
            'Food & Drink': 'Food & Drink',
            'Activities': 'Activities',
            'Travel & Places': 'Travel & Places',
            'Objects': 'Objects',
            'Symbols': 'Symbols',
            'Flags': 'Flags'
        };
        categoryTitle.textContent = titles[category] || '';
    }

    // Initial render (default to recent emojis)
    const activeTab = emojiPicker.querySelector('.emoji-tab.active');
    const initialCategory = activeTab ? activeTab.dataset.category : 'recent';
    if (initialCategory === 'recent') {
        renderEmojis(recentEmojis.map(char => ({ char })));
        updateCategoryTitle('recent');
    } else {
        const filteredEmojis = allEmojis.filter(emoji => {
            const topLevelCategory = emoji.category.split(' (')[0]; // Extract top-level category
            return topLevelCategory === initialCategory;
        });
        console.log(`Initial category: ${initialCategory}, Filtered emojis: ${filteredEmojis.length}`);
        renderEmojis(filteredEmojis);
        updateCategoryTitle(initialCategory);
    }

    // Tab switching
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            const category = tab.dataset.category;
            let filteredEmojis;
            if (category === 'recent') {
                filteredEmojis = recentEmojis.map(char => ({ char }));
            } else {
                filteredEmojis = allEmojis.filter(emoji => {
                    const topLevelCategory = emoji.category.split(' (')[0]; // Extract top-level category
                    return topLevelCategory === category;
                });
            }
            console.log(`Switching to category: ${category}, Filtered emojis: ${filteredEmojis.length}`);
            renderEmojis(filteredEmojis);
            updateCategoryTitle(category);
            searchInput.value = ''; // Clear search on tab switch
        });
    });

    // Search functionality
    searchInput.addEventListener('input', debounce((e) => {
        const query = e.target.value.toLowerCase().trim();
        const activeTab = emojiPicker.querySelector('.emoji-tab.active');
        const category = activeTab.dataset.category;
        let emojisToSearch = category === 'recent' 
            ? recentEmojis.map(char => ({ char, name: char }))
            : allEmojis.filter(emoji => {
                const topLevelCategory = emoji.category.split(' (')[0];
                return topLevelCategory === category;
            });
        
        if (query) {
            emojisToSearch = allEmojis.filter(emoji => 
                emoji.name.toLowerCase().includes(query) || // Search by name
                emoji.char.toLowerCase().includes(query) || // Search by char
                emoji.char.charCodeAt(0).toString(16).includes(query) // Fallback to Unicode
            );
            updateCategoryTitle(''); // Clear category title during search
        } else {
            emojisToSearch = category === 'recent' 
                ? recentEmojis.map(char => ({ char, name: char }))
                : allEmojis.filter(emoji => {
                    const topLevelCategory = emoji.category.split(' (')[0];
                    return topLevelCategory === category;
                });
            updateCategoryTitle(category);
        }
        console.log(`Search query: ${query}, Filtered emojis: ${emojisToSearch.length}`);
        renderEmojis(emojisToSearch);
    }, 300));

    emojiPicker.style.display = 'block';
    const rect = triggerButton.getBoundingClientRect();
    emojiPicker.style.position = 'absolute';
    emojiPicker.style.top = `${rect.bottom + window.scrollY}px`;
    emojiPicker.style.left = `${rect.left + window.scrollX}px`;

    const closeBtn = emojiPicker.querySelector('.emoji-picker-close');
    closeBtn.onclick = () => emojiPicker.style.display = 'none';
    window.onclick = (event) => {
        if (event.target === emojiPicker) emojiPicker.style.display = 'none';
    };
}

function setupCentralFeedPost() {
    const postBox = document.querySelector('.post-box');
    const postSubmitBtn = document.querySelector('.post-box .post-submit');
    const postInput = document.querySelector('.post-box .post-input');
    const postAudience = document.querySelector('.post-box .post-audience');
    const postSport = document.querySelector('.post-box .post-sport'); // May be null on sport pages
    const emojiBtn = document.querySelector('.post-box .post-action-btn.emoji');
    const gifBtn = document.querySelector('.post-box .post-action-btn.gif');
    const imageBtn = document.querySelector('.post-box .post-action-btn.image');
    const locationBtn = document.querySelector('.post-box .post-action-btn.location');
    const boldBtn = document.querySelector('.post-box .post-action-btn.bold');
    const italicBtn = document.querySelector('.post-box .post-action-btn.italic');
    const pollBtn = document.querySelector('.post-box .post-action-btn.poll');
    const scheduleBtn = document.querySelector('.post-box .post-action-btn.schedule');
    const previewDiv = document.querySelector('.post-box .post-preview');

    if (!postBox || !postSubmitBtn || !postInput || !postAudience || !emojiBtn || !gifBtn || !imageBtn || !locationBtn || !boldBtn || !italicBtn || !pollBtn || !scheduleBtn || !previewDiv) {
        console.warn('setupCentralFeedPost: One or more required DOM elements are missing.');
        console.log({
            postBox: !!postBox,
            postSubmitBtn: !!postSubmitBtn,
            postInput: !!postInput,
            postAudience: !!postAudience,
            postSport: !!postSport,
            emojiBtn: !!emojiBtn,
            gifBtn: !!gifBtn,
            imageBtn: !!imageBtn,
            locationBtn: !!locationBtn,
            boldBtn: !!boldBtn,
            italicBtn: !!italicBtn,
            pollBtn: !!pollBtn,
            scheduleBtn: !!scheduleBtn,
            previewDiv: !!previewDiv
        });
        return;
    }

    // Enable/disable button and update character count based on input
    postInput.addEventListener('input', function() {
        postSubmitBtn.disabled = !postInput.value.trim();
        const charCount = document.querySelector('.post-box .char-count');
        if (charCount) {
            charCount.textContent = `${postInput.value.length}/280`;
        }
    });

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

    // Emoji button functionality
    emojiBtn.addEventListener('click', (e) => {
        e.preventDefault();
        showEmojiPicker(postInput, emojiBtn);
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
            const reader = new FileReader();
            reader.onload = (event) => {
                const previewImg = previewDiv.querySelector('.preview-media');
                previewImg.src = event.target.result;
                previewDiv.style.display = 'block';
                postInput.dataset.imageFile = 'true';
            };
            reader.readAsDataURL(file);
        }
    });

    // GIF functionality
    gifBtn.addEventListener('click', (e) => {
        e.preventDefault();
        showGifModal(postInput, previewDiv);
    });

    // Remove preview functionality
    const removePreviewBtn = previewDiv.querySelector('.remove-preview');
    removePreviewBtn.addEventListener('click', () => {
        previewDiv.style.display = 'none';
        postInput.dataset.gifUrl = '';
        postInput.dataset.imageFile = '';
        imageInput.value = '';
    });

    // Poll functionality (placeholder for now)
    pollBtn.addEventListener('click', (e) => {
        e.preventDefault();
        alert('Poll functionality coming soon!');
    });

    // Schedule functionality (placeholder for now)
    scheduleBtn.addEventListener('click', (e) => {
        e.preventDefault();
        alert('Schedule functionality coming soon!');
    });

    // Submit logic
    postSubmitBtn.addEventListener('click', function() {
        const text = postInput.value.trim();
        const audience = postAudience.value;
        const sport = postSport ? postSport.value : postBox.dataset.sport;
        console.log('Sport for posting:', sport);

        if (!text) {
            alert('Please enter a tip before posting.');
            return;
        }

        if (!sport) {
            alert('Sport is not defined. Please select a sport or ensure the page is configured correctly.');
            return;
        }

        const formData = new FormData();
        formData.append('text', text);
        formData.append('audience', audience);
        formData.append('sport', sport);

        if (postInput.dataset.imageFile && imageInput.files[0]) {
            formData.append('image', imageInput.files[0]);
        }
        if (postInput.dataset.gifUrl) {
            formData.append('gif', postInput.dataset.gifUrl);
        }
        if (locationData) {
            formData.append('location', locationData);
        }
        formData.append('poll', '{}');
        formData.append('emojis', '{}');

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
                postInput.dataset.gifUrl = '';
                postInput.dataset.imageFile = '';
                imageInput.value = '';
                locationData = '';
                previewDiv.style.display = 'none';
                location.reload();
                
                const tipFeed = document.querySelector('.tip-feed');
                const newTip = document.createElement('div');
                newTip.className = 'tip';
                newTip.dataset.tipId = data.tip.id;
                newTip.innerHTML = `
                    <img src="${data.tip.avatar}" alt="${data.tip.username} Avatar" class="tip-avatar">
                    <div class="tip-content">
                        <div class="tip-header">
                            <a href="/profile/${data.tip.username}/" class="tip-username">
                                <strong>${data.tip.username}</strong>
                                <span class="user-handle">${data.tip.handle}</span>
                            </a>
                            ${data.tip.sport === 'football' ? '⚽' : data.tip.sport === 'golf' ? '⛳' : data.tip.sport === 'tennis' ? '🎾' : data.tip.sport === 'horse_racing' ? '🏇' : ''}
                        </div>
                        <div class="tip-body">
                            <p>${data.tip.text}</p>
                            ${data.tip.image ? `<img src="${data.tip.image}" alt="Tip Image" class="tip-image">` : ''}
                            ${data.tip.gif ? `<img src="${data.tip.gif}" alt="Tip GIF" class="tip-image">` : ''}
                        </div>
                        <small class="tip-timestamp">${new Date(data.tip.created_at).toLocaleString()}</small>
                    </div>
                `;
                tipFeed.insertBefore(newTip, tipFeed.firstChild);
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

function setupPostModal() {
    const postTipBtn = document.querySelector('.nav-post-btn[data-toggle="post-modal"]');
    const postModal = document.getElementById('post-modal');

    if (postTipBtn && postModal) {
        postTipBtn.addEventListener('click', function(e) {
            e.preventDefault();
            postModal.style.display = postModal.style.display === 'block' ? 'none' : 'block';

            const modalSubmitBtn = postModal.querySelector('.post-submit');
            const modalInput = postModal.querySelector('.post-input');
            const modalAudience = postModal.querySelector('.post-audience');
            const modalSport = postModal.querySelector('.post-sport');
            const modalBoldBtn = postModal.querySelector('.post-action-btn.bold');
            const modalItalicBtn = postModal.querySelector('.post-action-btn.italic');
            const modalImageBtn = postModal.querySelector('.post-action-btn.image');
            const modalGifBtn = postModal.querySelector('.post-action-btn.gif');
            const modalLocationBtn = postModal.querySelector('.post-action-btn.location');
            const modalPreviewDiv = postModal.querySelector('.post-preview');
            const modalEmojiBtn = postModal.querySelector('.post-action-btn.emoji'); // Add emoji button for modal

            if (!modalSubmitBtn || !modalInput || !modalAudience || !modalBoldBtn || !modalItalicBtn || !modalImageBtn || !modalGifBtn || !modalLocationBtn || !modalPreviewDiv || !modalEmojiBtn) {
                console.warn('setupPostModal: One or more required DOM elements are missing.');
                console.log({
                    modalSubmitBtn: !!modalSubmitBtn,
                    modalInput: !!modalInput,
                    modalAudience: !!modalAudience,
                    modalSport: !!modalSport,
                    modalBoldBtn: !!modalBoldBtn,
                    modalItalicBtn: !!modalItalicBtn,
                    modalImageBtn: !!modalImageBtn,
                    modalGifBtn: !!modalGifBtn,
                    modalLocationBtn: !!modalLocationBtn,
                    modalPreviewDiv: !!modalPreviewDiv,
                    modalEmojiBtn: !!modalEmojiBtn
                });
                return;
            }

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

            // Emoji button functionality for modal
            modalEmojiBtn.addEventListener('click', (e) => {
                e.preventDefault();
                showEmojiPicker(modalInput, modalEmojiBtn);
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
                    const reader = new FileReader();
                    reader.onload = (event) => {
                        const previewImg = modalPreviewDiv.querySelector('.preview-media');
                        previewImg.src = event.target.result;
                        modalPreviewDiv.style.display = 'block';
                        modalInput.dataset.imageFile = 'true';
                    };
                    reader.readAsDataURL(file);
                }
            });

            // GIF functionality for modal
            modalGifBtn.addEventListener('click', (e) => {
                e.preventDefault();
                showGifModal(modalInput, modalPreviewDiv);
            });

            // Remove preview functionality for modal
            const modalRemovePreviewBtn = modalPreviewDiv.querySelector('.remove-preview');
            modalRemovePreviewBtn.addEventListener('click', () => {
                modalPreviewDiv.style.display = 'none';
                modalInput.dataset.gifUrl = '';
                modalInput.dataset.imageFile = '';
                modalImageInput.value = '';
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
    const modal = this.closest('.post-modal');
    const modalInput = this.closest('.post-modal-content').querySelector('.post-input');
    const modalAudience = this.closest('.post-modal-content').querySelector('.post-audience');
    const modalSport = this.closest('.post-modal-content').querySelector('.post-sport');
    const modalPreviewDiv = this.closest('.post-modal-content').querySelector('.post-preview');
    const text = modalInput.value.trim();
    const audience = modalAudience.value;
    const sport = modalSport ? modalSport.value : modal.dataset.sport;
    console.log('Modal sport for posting:', sport);

    if (!text) {
        alert('Please enter a tip before posting.');
        return;
    }

    if (!sport) {
        alert('Sport is not defined. Please select a sport or ensure the page is configured correctly.');
        return;
    }

    const formData = new FormData();
    formData.append('text', text);
    formData.append('audience', audience);
    formData.append('sport', sport);

    const modalImageInput = document.querySelectorAll('input[type="file"]')[1];
    if (modalInput.dataset.imageFile && modalImageInput && modalImageInput.files[0]) {
        formData.append('image', modalImageInput.files[0]);
    }
    if (modalInput.dataset.gifUrl) {
        formData.append('gif', modalInput.dataset.gifUrl);
    }
    const modalLocationBtn = document.querySelector('.post-modal .post-action-btn.location');
    let modalLocationData = '';
    if (modalLocationBtn) {
        modalLocationData = modalInput.value.match(/\[Location: ([\d.,]+)\]/)?.[1] || '';
    }
    if (modalLocationData) {
        formData.append('location', modalLocationData);
    }
    formData.append('poll', '{}');
    formData.append('emojis', '{}');

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
            modalInput.dataset.gifUrl = '';
            modalInput.dataset.imageFile = '';
            if (modalImageInput) modalImageInput.value = '';
            modalLocationData = '';
            modalPreviewDiv.style.display = 'none';
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

export { 
    applyFormatting, 
    showGifModal, 
    setupCentralFeedPost, 
    setupPostModal,
    /*showEmojiPicker*/
};