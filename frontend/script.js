const header = document.querySelector('.header');

let lastScroll = 0;

window.addEventListener('scroll', function () {
    const currentScroll = window.scrollY;

    if (currentScroll > lastScroll) {
        header.style.backgroundColor = 'rgba(10, 10, 10, 0.7)';
        header.style.border = '1px solid rgba(50, 50, 50, 0.3)';
    } else {
        header.style.backgroundColor = 'rgba(10, 10, 10, 0)';
        header.style.border = '1px solid rgba(50, 50, 50, 0)';
    }
});