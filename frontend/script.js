const header = document.querySelector('.header');

let lastScroll = 0;

window.addEventListener('scroll', function () {
    const currentScroll = window.scrollY;

    if (currentScroll > lastScroll) {
        header.style.backgroundColor = 'rgba(10, 10, 10, 0.7)';
    }
    else {
        header.style.backgroundColor = 'rgba(10, 10, 10, 0)';
    }
});