let hd = document.getElementById('mainHeader');
let az = document.getElementById('animationZone');
let st = document.getElementById('scrolltext');
let er = document.querySelector('.earth');
let sa = document.querySelector('.satellite');
let cu = document.getElementById('cursor');
let sk = document.querySelector('.stickytext');
let ini = document.getElementById('initText');
let bg = document.getElementById('endBg');
let ph = "प्रकृति का प्रकोप अजेय है, पूर्वानुमान ही बचाव है।";

let mx = 0;
let my = 0;
let sy = 0;
let ma = 0;
let la = 0;
let ml = false;
let bt = 0;

hd.style.transition = 'transform 0.5s cubic-bezier(0.4, 0, 0.2, 1), background-color 0.5s ease, opacity 0.5s ease';

document.addEventListener('mousemove', function(e) {
    cu.style.left = e.clientX + 'px';
    cu.style.top = e.clientY + 'px';
    mx = (window.innerWidth / 2 - e.clientX) / 40;
    my = (window.innerHeight / 2 - e.clientY) / 40;
});

document.addEventListener('mousedown', function() { cu.classList.add('cclick'); });
document.addEventListener('mouseup', function() { cu.classList.remove('cclick'); });

window.addEventListener('scroll', function() {
    sy = window.scrollY;
});

function loop() {
    let wh = window.innerHeight;
    let ww = window.innerWidth;

    if (sy > wh * 0.2 && sy < wh * 3) {
        hd.style.transform = 'translateY(-100%)';
        hd.style.opacity = '0';
    } else {
        hd.style.transform = 'translateY(0)';
        hd.style.opacity = '1';
        hd.style.backgroundColor = sy > 50 ? 'rgba(10, 10, 10, 0.9)' : 'transparent';
    }

    let rt = az.getBoundingClientRect();
    let ms = rt.height - wh;
    let p = 0;

    if (rt.top > 0) {
        p = 0;
    } else if (rt.bottom < wh) {
        p = 1;
    } else {
        p = Math.abs(rt.top) / ms;
    }

    if (p === 0) {
        bt += 0.01;
        ma += 0.015;
        ml = false;

        er.style.transform = `translate(calc(-50% + ${mx}px), calc(-50% + ${my}px)) scale(1) rotate(${bt*5}deg)`;
        er.style.opacity = 1;
        er.style.background = `radial-gradient(circle at 30% 30%, #00acee, #001133)`;

        let ox = Math.cos(ma) * 250;
        let oy = Math.sin(ma) * 250;
        sa.style.transform = `translate(calc(-50% + ${mx*2 + ox}px), calc(-50% + ${my*2 + oy}px)) scale(1)`;
        sa.style.opacity = 1;

        st.innerText = "";
        sk.style.opacity = 0;
        ini.style.opacity = 0;
        bg.style.opacity = 0;
    } else {
        if (!ml) {
            la = ma;
            ml = true;
        }

        let tp = p / 0.4;
        if (tp > 1) tp = 1;
        let r = Math.floor(tp * ph.length);
        st.innerText = ph.substring(0, r);

        let fop = 1;
        if (p > 0.4 && p <= 0.6) {
            fop = 1 - ((p - 0.4) / 0.2);
        } else if (p > 0.6) {
            fop = 0;
        }

        sk.style.opacity = fop;
        er.style.opacity = fop;
        sa.style.opacity = fop;

        let es = 1 + (p * 35);
        let erot = bt*5 + (p * 45);
        let sxn = 30 + (p * 60);
        let syn = 30 + (p * 40);

        er.style.background = `radial-gradient(circle at ${sxn}% ${syn}%, #00acee, #001133)`;
        er.style.transform = `translate(calc(-50% + ${mx}px), calc(-50% + ${my}px)) scale(${es}) rotate(${erot}deg)`;

        let sxx = Math.cos(la) * 250;
        let syy = Math.sin(la) * 250;
        let vxx = Math.cos(la + Math.PI) * ww * 1.5;
        let vyy = Math.sin(la + Math.PI) * wh * 1.5;

        sa.style.transform = `translate(calc(-50% + ${mx*2 + sxx + p*vxx}px), calc(-50% + ${my*2 + syy + p*vyy}px)) scale(${1 + p*5})`;

        let iop = 0;
        if (p > 0.6 && p <= 0.7) {
            iop = (p - 0.6) / 0.1;
        } else if (p > 0.7 && p <= 0.8) {
            iop = 1 - ((p - 0.7) / 0.1);
        }
        ini.style.opacity = iop;

        let bop = 0;
        if (p > 0.8) {
            bop = (p - 0.8) / 0.2;
        }
        bg.style.opacity = bop * 0.4;
    }

    requestAnimationFrame(loop);
}
loop();
