const header = document.getElementById('main-header');
const animZone = document.getElementById('animation-zone');
const scrollText = document.getElementById('scrolltext');
const earth = document.querySelector('.earth');

// The new Hindi phrase requested
const phrase = "प्रकृति का प्रकोप अजेय है, पूर्वानुमान ही बचाव है।";

window.addEventListener('scroll', function () {
    let scrollY = window.scrollY;
    let windowHeight = window.innerHeight;

    // 1. Rotate the Earth based on scroll
    earth.style.transform = `translate(-50%, -50%) rotate(${scrollY * 0.05}deg)`;

    // 2. Hide Header when scrolling down past the landing zone
    if (scrollY > windowHeight * 0.3) {
        header.style.opacity = '0';
        header.style.pointerEvents = 'none';
        header.style.transition = 'opacity 0.4s ease';
    } else {
        header.style.opacity = '1';
        header.style.pointerEvents = 'auto';
    }

    // 3. Typing Animation Logic
    let rect = animZone.getBoundingClientRect();

    // Check if the animation zone is currently in the viewport
    if (rect.top <= windowHeight && rect.bottom >= 0) {
        // Calculate how far we have scrolled through the animation zone (0 to 1)
        let scrollProgress = (windowHeight - rect.top) / (rect.height);

        // Map the progress to the length of the string
        let charCount = Math.floor(scrollProgress * phrase.length * 1.5); // 1.5 speeds up the typing slightly

        // Constrain the character count bounds
        if (charCount < 0) charCount = 0;
        if (charCount > phrase.length) charCount = phrase.length;

        scrollText.innerText = phrase.substring(0, charCount);
    }
});
