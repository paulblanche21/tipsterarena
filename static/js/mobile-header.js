// Wait for DOM to be loaded
function initializeMobileMenu() {
  const mobileAvatar = document.getElementById('mobile-avatar');
  const menuTrigger = document.getElementById('mobile-menu-trigger');
  const navbar = document.querySelector('.navbar');
  const overlay = document.getElementById('navbar-overlay');
  const mainContainer = document.getElementById('main-container');
  const mobileHeader = document.querySelector('.mobile-header');
  const navAccordionBtn = document.getElementById('nav-accordion-btn');

  // Handle menu trigger click
  if (menuTrigger) {
    menuTrigger.addEventListener('click', function() {
      navbar.classList.toggle('active');
      overlay.classList.toggle('active');
      mainContainer.classList.toggle('nav-active');
    });
  }

  // Handle avatar click to show navbar
  if (mobileAvatar) {
    mobileAvatar.addEventListener('click', function() {
      navbar.classList.add('active');
      overlay.classList.add('active');
      mainContainer.classList.add('nav-active');
    });
  }

  // Handle overlay click to hide navbar
  if (overlay) {
    overlay.addEventListener('click', function() {
      navbar.classList.remove('active');
      overlay.classList.remove('active');
      mainContainer.classList.remove('nav-active');
    });
  }

  // Handle scroll behavior
  let lastScrollTop = 0;
  if (mobileHeader) {
    window.addEventListener('scroll', function() {
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      
      if (scrollTop > lastScrollTop) {
        // Scrolling down
        mobileHeader.classList.add('hidden');
      } else {
        // Scrolling up
        mobileHeader.classList.remove('hidden');
      }
      
      lastScrollTop = scrollTop;
    });
  }

  // Handle nav accordion button
  if (navAccordionBtn) {
    navAccordionBtn.addEventListener('click', function() {
      navbar.classList.toggle('active');
      overlay.classList.toggle('active');
      mainContainer.classList.toggle('nav-active');
    });
  }
}

// Try to initialize immediately if DOM is already loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeMobileMenu);
} else {
  initializeMobileMenu();
} 