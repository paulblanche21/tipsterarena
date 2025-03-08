document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded');

    // Function to get CSRF token
    function getCSRFToken() {
        const tokenElement = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (!tokenElement) {
            console.warn("CSRF token not found on page");
            return null;
        }
        return tokenElement.value;
    }

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

    // Upcoming Events Carousel Logic
    const carouselSlides = document.querySelectorAll('.carousel-slide');
    const dots = document.querySelectorAll('.dot');
    const showMoreButtons = document.querySelectorAll('.show-more');

    let currentSlide = 0;

    function showSlide(index) {
        if (index >= carouselSlides.length) currentSlide = 0;
        if (index < 0) currentSlide = carouselSlides.length - 1;

        carouselSlides.forEach(slide => slide.classList.remove('active'));
        dots.forEach(dot => dot.classList.remove('active'));

        carouselSlides[currentSlide].classList.add('active');
        dots[currentSlide].classList.add('active');
    }

    function nextSlide() {
        currentSlide++;
        showSlide(currentSlide);
    }

    if (carouselSlides.length > 0) {
        dots.forEach((dot, index) => {
            dot.addEventListener('click', () => {
                currentSlide = index;
                showSlide(currentSlide);
            });
        });

        // Auto-slide every 5 seconds
        setInterval(nextSlide, 5000);

        // Show the first slide initially
        showSlide(currentSlide);
    }

    // Show More Button Logic (Sport-Specific Central Feed)
    showMoreButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const target = this.getAttribute('data-target');
            const content = document.querySelector('.content');
            let previousUrl = window.location.pathname;

            content.innerHTML = '';

            switch (target) {
                case 'upcoming-events':
                    // Detect current page and display sport-specific fixtures
                    const currentPath = window.location.pathname.toLowerCase(); // Case-insensitive match
                    if (currentPath.includes('/sports/football/')) {
                        // Football fixtures only
                        content.innerHTML = `
                            <div class="follow-card">
                                <h2>Upcoming Football Fixtures</h2>
                                <p>Here are the latest football fixtures in Tipster Arena:</p>
                                <div class="event-list">
                                    <div class="event-item"><p><span class="sport-icon">⚽</span> Premier League: Manchester United vs. Tottenham, Mar 12, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⚽</span> La Liga: Real Madrid vs. Barcelona, Mar 15, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⚽</span> Champions League: Bayern Munich vs. PSG, Mar 16, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⚽</span> FA Cup: Chelsea vs. Arsenal, Mar 17, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⚽</span> Serie A: Juventus vs. Inter Milan, Mar 18, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⚽</span> Bundesliga: Dortmund vs. Leipzig, Mar 19, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⚽</span> Europa League: Ajax vs. Roma, Mar 20, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⚽</span> Premier League: Liverpool vs. Manchester City, Mar 21, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⚽</span> La Liga: Atletico Madrid vs. Sevilla, Mar 22, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⚽</span> Serie A: AC Milan vs. Napoli, Mar 23, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⚽</span> Premier League: Arsenal vs. Chelsea, Mar 25, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⚽</span> La Liga: Barcelona vs. Real Madrid, Mar 26, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⚽</span> Champions League: PSG vs. Bayern Munich, Mar 27, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⚽</span> FA Cup: Tottenham vs. Manchester United, Mar 28, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⚽</span> Serie A: Inter Milan vs. Juventus, Mar 29, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⚽</span> Bundesliga: Leipzig vs. Dortmund, Mar 30, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⚽</span> Europa League: Roma vs. Ajax, Mar 31, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⚽</span> Premier League: Manchester City vs. Liverpool, Apr 1, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⚽</span> La Liga: Sevilla vs. Atletico Madrid, Apr 2, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⚽</span> Serie A: Napoli vs. AC Milan, Apr 3, 2025</p></div>
                                </div>
                                <a href="#" class="show-less" data-target="${target}">Show less</a>
                            </div>
                        `;
                    } else if (currentPath.includes('/sports/golf/')) {
                        // Golf fixtures only
                        content.innerHTML = `
                            <div class="follow-card">
                                <h2>Upcoming Golf Events</h2>
                                <p>Here are the latest golf events in Tipster Arena:</p>
                                <div class="event-list">
                                    <div class="event-item"><p><span class="sport-icon">⛳</span> US PGA Tour: The Players Championship, Mar 13-16, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⛳</span> US PGA Tour: Valspar Championship, Mar 20-23, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⛳</span> US PGA Tour: WGC-Dell Technologies Match Play, Mar 26-30, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⛳</span> US PGA Tour: Houston Open, Apr 3-6, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⛳</span> US PGA Tour: Masters Tournament, Apr 10-13, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⛳</span> DP World Tour: Magical Kenya Open, Mar 13-16, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⛳</span> DP World Tour: Qatar Masters, Mar 20-23, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⛳</span> DP World Tour: Hero Indian Open, Mar 27-30, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⛳</span> DP World Tour: Volvo China Open, Apr 3-6, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⛳</span> DP World Tour: Open de Espana, Apr 10-13, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⛳</span> LIV Golf Tour: Jeddah, Mar 14-16, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⛳</span> LIV Golf Tour: Hong Kong, Mar 21-23, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⛳</span> LIV Golf Tour: Tucson, Mar 28-30, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⛳</span> LIV Golf Tour: Miami, Apr 4-6, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⛳</span> LIV Golf Tour: Adelaide, Apr 11-13, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⛳</span> LPGA: Honda LPGA Thailand, Feb 20-23, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⛳</span> LPGA: HSBC Women’s World Championship, Mar 6-9, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⛳</span> LPGA: Blue Bay LPGA, Mar 13-16, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⛳</span> LPGA: Kia Classic, Mar 20-23, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⛳</span> LPGA: ANA Inspiration, Apr 3-6, 2025</p></div>
                                </div>
                                <a href="#" class="show-less" data-target="${target}">Show less</a>
                            </div>
                        `;
                    } else {
                        // Default case for home page or other pages
                        content.innerHTML = `
                            <div class="follow-card">
                                <h2>Upcoming Events</h2>
                                <p>Here are the latest upcoming events in Tipster Arena:</p>
                                <div class="event-list">
                                    <div class="event-item"><p><span class="sport-icon">⚽</span> Premier League: Manchester United vs. Tottenham, Mar 12, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">⛳</span> US PGA Tour: The Players Championship, Mar 13-16, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">🎾</span> Tennis: Australian Open Qualifiers, Mar 10-12, 2025</p></div>
                                    <div class="event-item"><p><span class="sport-icon">🏇</span> Horse Racing: Grand National Trials, Mar 14, 2025</p></div>
                                    <!-- Add more events as needed for default view -->
                                </div>
                                <a href="#" class="show-less" data-target="${target}">Show less</a>
                            </div>
                        `;
                    }
                    break;
                case 'trending-tips':
                    content.innerHTML = `
                        <div class="follow-card">
                            <h2>Trending Tips</h2>
                            <p>Hot tips for today’s big tournaments in Tipster Arena:</p>
                            <div class="tip-list">
                                <div class="tip-item">
                                    <img src="${DEFAULT_AVATAR_URL}" alt="User Avatar" class="tip-avatar">
                                    <div class="tip-details">
                                        <strong>User 1</strong> - Rory McIlroy to win The Players Championship (Odds: 10.0) - Likes: 150
                                    </div>
                                </div>
                                <div class="tip-item">
                                    <img src="${DEFAULT_AVATAR_URL}" alt="User Avatar" class="tip-avatar">
                                    <div class="tip-details">
                                        <strong>User 2</strong> - Scottie Scheffler top 10 at Masters (Odds: 2.5) - Likes: 120
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
                            <h2>Who to Follow</h2>
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
                    window.location.href = previousUrl; // Return to previous state
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
            formData.append('sport', 'golf'); // Add sport context for golf page (to be adjusted dynamically)

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

    // Toggle User Dropdown Menu
    const navUserContent = document.querySelector('.nav-user-content');
    const navUserDropdown = document.querySelector('.nav-user-dropdown');
    const navMenuIcon = document.querySelector('.nav-menu-icon');

    if (navUserContent && navUserDropdown && navMenuIcon) {
        let isDropdownOpen = false;

        navMenuIcon.addEventListener('click', function(e) {
            e.preventDefault();
            isDropdownOpen = !isDropdownOpen;
            navUserDropdown.style.display = isDropdownOpen ? 'block' : 'none';
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (isDropdownOpen && !navUserContent.contains(e.target)) {
                navUserDropdown.style.display = 'none';
                isDropdownOpen = false;
            }
        });

        // Close dropdown when a dropdown item is clicked (e.g., logout)
        const dropdownItems = navUserDropdown.querySelectorAll('.nav-dropdown-item');
        dropdownItems.forEach(item => {
            item.addEventListener('click', function() {
                navUserDropdown.style.display = 'none';
                isDropdownOpen = false;
            });
        });
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

    console.log('Post Tip Button:', postTipBtn); // Debug log
    console.log('Post Modal:', postModal); // Debug log

    if (postTipBtn && postModal) {
        postTipBtn.addEventListener('click', function() {
            console.log('Toggling post modal'); // Debug log
            postModal.style.display = postModal.style.display === 'block' ? 'none' : 'block';
        });

        // Close modal when clicking outside
        window.addEventListener('click', function(event) {
            if (event.target === postModal) {
                console.log('Closing modal by clicking outside'); // Debug log
                postModal.style.display = 'none';
            }
        });

        // Ensure the close button works
        const postModalClose = document.querySelector('.post-modal-close');
        console.log('Post Modal Close Button:', postModalClose); // Debug log
        if (postModalClose) {
            postModalClose.addEventListener('click', function() {
                console.log('Closing modal with close button'); // Debug log
                postModal.style.display = 'none';
            });
        }
    } else {
        console.warn('Post modal elements not found:', { postTipBtn, postModal });
    }
});