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
            fetch(window.LOGOUT_URL, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken(),
                },
            })
            .then(response => {
                if (response.ok) {
                    window.location.href = window.LANDING_URL;
                } else {
                    alert('Error logging out');
                }
            })
            .catch(error => {
                console.error('Logout error:', error);
                alert('An error occurred while logging out');
            });
        });
    }
}