document.addEventListener('DOMContentLoaded', function() {
  const mobileAvatar = document.getElementById('mobile-avatar');
  const navbar = document.querySelector('.navbar');
  const overlay = document.getElementById('navbar-overlay');
  const mainContainer = document.getElementById('main-container');
  let lastScrollTop = 0;

  if (mobileAvatar) {
    mobileAvatar.addEventListener('click', function(e) {
      e.preventDefault();
      navbar.classList.toggle('active');
      overlay.classList.toggle('active');
      mainContainer.classList.toggle('nav-active');
    });
  }

  overlay.addEventListener('click', function() {
    navbar.classList.remove('active');
    overlay.classList.remove('active');
    mainContainer.classList.remove('nav-active');
  });

  // Handle scroll behavior
  window.addEventListener('scroll', function() {
    const st = window.pageYOffset || document.documentElement.scrollTop;
    const mobileHeader = document.querySelector('.mobile-header');
    
    if (st > lastScrollTop) {
      // Scrolling down
      mobileHeader.classList.add('hidden');
      mainContainer.classList.add('header-hidden');
    } else {
      // Scrolling up
      mobileHeader.classList.remove('hidden');
      mainContainer.classList.remove('header-hidden');
    }
    
    lastScrollTop = st <= 0 ? 0 : st;
  });
}); 