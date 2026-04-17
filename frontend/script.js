let h = document.querySelector('.header');
let t = document.getElementById('scrolltext');
let x = "प्रकृतिः रक्षति रक्षिता";
let e = document.querySelector('.earth');

window.addEventListener('scroll', function () {
    let y = window.scrollY;
    h.style.backgroundColor = y > 50 ? 'rgba(10, 10, 10, 0.9)' : 'transparent';

    let b = document.getElementById('scrollbox');
    let r = b.getBoundingClientRect();
    let w = window.innerHeight;

    if (r.top < w && r.bottom > 0) {
        let v = w - r.top;
        let c = w + r.height;
        let p = v / c;
        let l = Math.floor(p * x.length * 1.5);
        if (l > x.length) l = x.length;
        if (l < 0) l = 0;
        t.innerText = x.substring(0, l);
    }

    e.style.transform = `translate(-50%, -50%) rotate(${y * 0.1}deg)`;
});
