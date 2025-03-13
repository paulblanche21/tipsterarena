// carousel.js
export function initCarousel() {
    const carouselSlides = document.querySelectorAll('.carousel-slide');
    const dots = document.querySelectorAll('.dot');
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

        // Auto-slide every 10 seconds
        setInterval(nextSlide, 10000);

        // Show the first slide initially
        showSlide(currentSlide);
    }
}

// If you want to auto-initialize (optional, but we'll move this to main.js)
document.addEventListener('DOMContentLoaded', initCarousel);