// static/js/pages/nav.js
import { getCSRFToken } from './utils.js';

export function setupNavigation() {
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

        document.addEventListener('click', function(e) {
            if (isDropdownOpen && !navUserContent.contains(e.target)) {
                navUserDropdown.style.display = 'none';
                isDropdownOpen = false;
            }
        });

        const dropdownItems = navUserDropdown.querySelectorAll('.nav-dropdown-item');
        dropdownItems.forEach(item => {
            item.addEventListener('click', function(e) {
                navUserDropdown.style.display = 'none';
                isDropdownOpen = false;
            });
        });
    }

    const logoutBtn = document.querySelector('.nav-logout-btn[data-logout]');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Logout button clicked, fetching:', window.logout_url);
            fetch(window.logout_url, { // Use lowercase window.logout_url
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken(),
                },
            })
            .then(response => {
                if (response.ok) {
                    console.log('Logout successful, redirecting to:', window.landing_url);
                    window.location.href = window.landing_url; // Use lowercase window.landing_url
                } else {
                    console.error('Logout failed, response status:', response.status);
                    alert('Error logging out');
                }
            })
            .catch(error => {
                console.error('Logout error:', error);
                alert('An error occurred while logging out');
            });
        });
    }

    // More Sports popup logic
    const moreSportsBtn = document.getElementById('more-sports-btn');
    const moreSportsPopup = document.getElementById('more-sports-popup');
    const moreSportsClose = document.getElementById('more-sports-close');

    if (moreSportsBtn && moreSportsPopup && moreSportsClose) {
        moreSportsBtn.addEventListener('click', function(e) {
            e.preventDefault();
            moreSportsPopup.style.display = 'flex';
        });
        moreSportsClose.addEventListener('click', function() {
            moreSportsPopup.style.display = 'none';
        });
        // Optional: close popup when clicking outside the content
        moreSportsPopup.addEventListener('click', function(e) {
            if (e.target === moreSportsPopup) {
                moreSportsPopup.style.display = 'none';
            }
        });
    }
}