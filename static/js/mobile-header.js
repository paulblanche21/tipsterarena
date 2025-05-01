document.addEventListener('DOMContentLoaded', function() {
  const mobileAvatar = document.getElementById('mobile-avatar');
  const navbar = document.querySelector('.navbar');
  const overlay = document.getElementById('navbar-overlay');
  const mainContainer = document.getElementById('main-container');
  const mobileHeader = document.querySelector('.mobile-header');
  const navAccordionBtn = document.getElementById('nav-accordion-btn');

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

  if (navAccordionBtn) {
    navAccordionBtn.addEventListener('click', function() {
      navbar.classList.toggle('active');
      overlay.classList.toggle('active');
      mainContainer.classList.toggle('nav-active');
    });
  }
}); 