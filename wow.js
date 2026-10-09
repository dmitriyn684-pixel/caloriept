/* CaloriePT — премиальный слой: заставка, курсор, 3D-карточки, сцены на прокрутке. GSAP + ScrollTrigger + Lenis. */
(function () {
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var fine = matchMedia('(pointer: fine)').matches;
  var wide = matchMedia('(min-width: 1025px)').matches;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  var nav = $('nav'), bar = $('.scroll-progress');
  function onScroll(y) {
    nav.classList.toggle('scrolled', y > 40);
    var h = document.documentElement.scrollHeight - innerHeight;
    if (bar) bar.style.transform = 'scaleX(' + (h > 0 ? y / h : 0) + ')';
  }
  addEventListener('scroll', function () { onScroll(scrollY); }, { passive: true });
  onScroll(scrollY);

  // стеклянные карточки с золотой рамкой
  $$('.feature, .stat, .step, .eco-card, .partner-card, .art-card, .faq-item, .nf-card').forEach(function (el) { el.classList.add('glow-border'); });

  // переключатель режимов нутрициолога Анны
  $$('.anna-modes button').forEach(function (b) {
    b.addEventListener('click', function () {
      var mode = b.dataset.mode;
      $$('.anna-modes button').forEach(function (x) { x.setAttribute('aria-selected', x === b ? 'true' : 'false'); });
      $$('.anna-a').forEach(function (a) {
        var on = a.dataset.mode === mode;
        a.hidden = !on;
        if (on && window.gsap) gsap.fromTo(a, { y: 14, opacity: 0 }, { y: 0, opacity: 1, duration: .5, ease: 'power3.out' });
      });
    });
  });

  // огромное название студии в подвале: подгоняем под ширину
  var sname = $('.sfoot-name');
  if (sname) {
    var txt = sname.textContent.trim();
    sname.innerHTML = txt.split('').map(function (c) { return '<span class="ch">' + c + '</span>'; }).join('');
    var fit = function () {
      sname.style.fontSize = '100px';
      var cs = sname.querySelectorAll('.ch'), w = cs[cs.length - 1].getBoundingClientRect().right - cs[0].getBoundingClientRect().left;
      if (w > 0) sname.style.fontSize = (100 * sname.clientWidth / w * .98).toFixed(2) + 'px';
    };
    fit(); addEventListener('resize', fit);
    if (document.fonts) document.fonts.ready.then(fit);
  }

  if (reduce || !window.gsap || !window.ScrollTrigger) return;
  gsap.registerPlugin(ScrollTrigger);

  // ── разбиение заголовка на буквы ──
  function splitChars(root) {
    $$('.line > span', root).forEach(function (wrap) {
      (function walk(node) {
        Array.prototype.slice.call(node.childNodes).forEach(function (n) {
          if (n.nodeType === 3) {
            var frag = document.createDocumentFragment();
            n.textContent.split('').forEach(function (c) {
              var s = document.createElement('span');
              s.className = 'ch'; s.textContent = c === ' ' ? ' ' : c;
              frag.appendChild(s);
            });
            node.replaceChild(frag, n);
          } else if (n.nodeType === 1 && n.tagName === 'EM') {
            n.classList.add('ch');            // золотой перелив держится на целом слове
          } else if (n.nodeType === 1) walk(n);
        });
      })(wrap);
    });
  }
  splitChars($('.hero-title'));

  // прокрутка — нативная браузерная: ничего не перехватываем
  var lenis = null;

  // ── заставка (один раз за сессию) ──
  var seen = false;
  try { seen = sessionStorage.getItem('cpt_intro') === '1'; sessionStorage.setItem('cpt_intro', '1'); } catch (e) {}
  var intro = gsap.timeline({ paused: true });
  if (!seen) {
    var pl = document.createElement('div');
    pl.className = 'preloader';
    pl.innerHTML = '<div class="pl-logo"><span>Calorie<em>PT</em></span></div><div class="pl-line"><i></i></div><div class="pl-count">0%</div>';
    document.body.appendChild(pl);
    var c = { v: 0 }, done = false;
    var finish = function () { if (done) return; done = true; pl.remove(); intro.play(); };
    setTimeout(finish, 2500);             // страховка: прокрутка не останется заблокированной
    gsap.timeline({ onComplete: finish })
      .from('.pl-logo span', { yPercent: 110, duration: .6, ease: 'expo.out' })
      .to('.pl-line i', { scaleX: 1, duration: .7, ease: 'power2.inOut' }, '<.05')
      .to(c, { v: 100, duration: .7, ease: 'power2.inOut', onUpdate: function () { $('.pl-count').textContent = Math.round(c.v) + '%'; } }, '<')
      .to('.pl-logo span', { yPercent: -110, duration: .4, ease: 'power3.in' })
      .to(pl, { clipPath: 'inset(0 0 100% 0)', duration: .7, ease: 'expo.inOut' }, '-=.1')
      .add(function () { intro.play(); }, '-=.45');
  } else {
    gsap.delayedCall(.1, function () { intro.play(); });
  }

  // ── первый экран ──
  intro
    .fromTo('.hero-bg', { scale: 1.25 }, { scale: 1.05, duration: 2.6, ease: 'expo.out' }, 0)
    .from('.hero-title .ch', { yPercent: 120, rotateX: -90, opacity: 0, filter: 'blur(10px)', duration: 1.3, ease: 'expo.out', stagger: .028 }, .1)
    .from('.hero-eyebrow', { y: 20, opacity: 0, letterSpacing: '.6em', duration: 1.4, ease: 'expo.out' }, .2)
    .from('.hero-sub, .hero-actions > *, .scroll-hint', { y: 30, opacity: 0, duration: 1, ease: 'power3.out', stagger: .08 }, .6)
    .from('.chip', { y: 80, opacity: 0, scale: .85, rotateX: 25, duration: 1.4, ease: 'expo.out', stagger: .15 }, .5)
    .to('.chip-bar i', { width: '90%', duration: 1.6, ease: 'power3.out' }, 1.2);
  $('.hero-content').style.animation = 'none';

  // парящие карточки: «плавание»
  $$('.chip').forEach(function (ch, i) {
    gsap.to(ch, { y: '+=' + (10 + i * 4), duration: 3 + i * .6, ease: 'sine.inOut', yoyo: true, repeat: -1, delay: 2 + i * .3 });
  });

  // параллакс от мышки
  if (fine) {
    var bgX = gsap.quickTo('.hero-bg', 'x', { duration: 1.2, ease: 'power3' }), bgY = gsap.quickTo('.hero-bg', 'y', { duration: 1.2, ease: 'power3' });
    var chX = gsap.quickTo('.hero-chips', 'x', { duration: 1, ease: 'power3' }), chY = gsap.quickTo('.hero-chips', 'y', { duration: 1, ease: 'power3' });
    $('.hero').addEventListener('pointermove', function (e) {
      var nx = e.clientX / innerWidth - .5, ny = e.clientY / innerHeight - .5;
      bgX(nx * -30); bgY(ny * -20); chX(nx * 40); chY(ny * 30);
    });
  }
  gsap.to('.hero-bg', { yPercent: 18, ease: 'none', scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: true } });
  gsap.to('.hero-content', { yPercent: -25, opacity: .2, ease: 'none', scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: true } });
  gsap.to('.hero-chips', { yPercent: -40, ease: 'none', scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: true } });

  // ── бегущие строки: наклон от скорости прокрутки ──
  $$('.marquee').forEach(function (m) {
    var sk = gsap.quickTo(m.querySelector('.marquee-skew'), 'skewX', { duration: .5, ease: 'power3' });
    ScrollTrigger.create({ trigger: m, start: 'top bottom', end: 'bottom top',
      onUpdate: function (self) { sk(gsap.utils.clamp(-12, 12, self.getVelocity() / -250)); } });
  });

  // ── заголовки секций: слова выезжают из-под маски ──
  $$('.section-title').forEach(function (t) {
    var html = t.innerHTML.split(/(<em>.*?<\/em>|\s+)/).filter(Boolean).map(function (w) {
      return /^\s+$/.test(w) ? ' ' : '<span style="display:inline-block;overflow:hidden;vertical-align:top;padding-bottom:.08em"><span class="w" style="display:inline-block">' + w + '</span></span>';
    }).join('');
    t.innerHTML = html;
    gsap.from(t.querySelectorAll('.w'), { yPercent: 110, rotate: 4, duration: 1.1, ease: 'expo.out', stagger: .06,
      scrollTrigger: { trigger: t, start: 'top 95%' } });
  });
  $$('.section-eyebrow').forEach(function (e) {
    gsap.from(e, { opacity: 0, letterSpacing: '.6em', duration: 1.2, ease: 'expo.out', scrollTrigger: { trigger: e, start: 'top 90%' } });
  });

  // ── карточки: появление из глубины ──
  ['.stats', '.features-grid', '#partners > div', 'section[style*="padding-top:100px"] > div[style*="grid"]', '.art-grid', '.faq-list'].forEach(function (sel) {
    var box = $(sel); if (!box) return;
    var items = gsap.utils.toArray(box.children);
    gsap.set(items, { y: 40, opacity: 0, rotateX: 10, transformPerspective: 900, transformOrigin: '50% 100%' });
    ScrollTrigger.batch(items, { start: 'top bottom', once: true,
      onEnter: function (b) { gsap.to(b, { y: 0, opacity: 1, rotateX: 0, duration: .8, ease: 'power3.out', stagger: .06, overwrite: true }); } });
  });

  // ── 3D-наклон с бликом ──
  if (fine) {
    $$('.feature, .eco-card, .partner-card, .art-card, .stat').forEach(function (card) {
      var g = document.createElement('span'); g.className = 'tilt-glare'; card.appendChild(g);
      var rx = gsap.quickTo(card, 'rotationX', { duration: .6, ease: 'power3' }), ry = gsap.quickTo(card, 'rotationY', { duration: .6, ease: 'power3' });
      gsap.set(card, { transformPerspective: 1000 });
      card.addEventListener('pointermove', function (e) {
        var r = card.getBoundingClientRect(), px = (e.clientX - r.left) / r.width, py = (e.clientY - r.top) / r.height;
        rx((.5 - py) * 10); ry((px - .5) * 12);
        card.style.setProperty('--gx', px * 100 + '%'); card.style.setProperty('--gy', py * 100 + '%');
        card.classList.add('tilting');
      });
      card.addEventListener('pointerleave', function () { rx(0); ry(0); card.classList.remove('tilting'); });
    });
  }

  // ── фото спортзала: раскрытие кругом ──
  var tech = $('#tech-section');
  if (tech) {
    var photo = tech.firstElementChild;
    photo.classList.add('tech-photo');
    gsap.fromTo(photo, { clipPath: 'circle(12% at 25% 50%)', scale: 1.25 },
      { clipPath: 'circle(150% at 25% 50%)', scale: 1, ease: 'none',
        scrollTrigger: { trigger: tech, start: 'top 85%', end: 'center 45%', scrub: 1 } });
    var txt = $('#tech-section > div[style*="grid"] > div:last-child > div');
    if (txt) gsap.from(txt.children, { x: 80, opacity: 0, duration: 1.2, ease: 'expo.out', stagger: .12,
      scrollTrigger: { trigger: tech, start: 'top 75%' } });
  }

  // ── «Как это работает»: карточки и линия прогресса ──
  var how = $('#how'), steps = $('#how .steps');
  if (how && steps) {
    var hb = document.createElement('div'); hb.className = 'how-bar'; hb.innerHTML = '<i></i>'; how.appendChild(hb);
    gsap.set(steps.children, { y: 40, opacity: 0 });
    ScrollTrigger.batch(steps.children, { start: 'top bottom', once: true,
      onEnter: function (b) { gsap.to(b, { y: 0, opacity: 1, duration: .8, ease: 'power3.out', stagger: .06 }); } });
    gsap.to(hb.querySelector('i'), { scaleX: 1, ease: 'none', scrollTrigger: { trigger: steps, start: 'top 80%', end: 'bottom 50%', scrub: true } });
  }

  // ── финальный призыв ──
  var cta = $('.cta-section');
  if (cta) {
    var beams = document.createElement('div'); beams.className = 'cta-beams'; cta.prepend(beams);
    gsap.fromTo('.cta-title', { scale: .78, opacity: .2 }, { scale: 1, opacity: 1, ease: 'none',
      scrollTrigger: { trigger: cta, start: 'top 95%', end: 'center 60%', scrub: 1 } });
    gsap.from('.cta-sub, .cta-buttons > *', { y: 40, opacity: 0, duration: 1, ease: 'expo.out', stagger: .08,
      scrollTrigger: { trigger: cta, start: 'top 55%' } });
    if (fine) cta.addEventListener('pointermove', function (e) {
      var r = cta.getBoundingClientRect();
      cta.style.setProperty('--cx', (e.clientX - r.left) + 'px'); cta.style.setProperty('--cy', (e.clientY - r.top) + 'px');
    });
  }

  // ── курсор и магнитные кнопки ──
  if (fine) {
    document.documentElement.classList.add('has-cursor');
    var dot = document.createElement('div'); dot.className = 'cur-dot';
    var ring = document.createElement('div'); ring.className = 'cur-ring'; ring.innerHTML = '<b></b>';
    document.body.appendChild(ring); document.body.appendChild(dot);
    var dX = gsap.quickTo(dot, 'x', { duration: .08 }), dY = gsap.quickTo(dot, 'y', { duration: .08 });
    var rX = gsap.quickTo(ring, 'x', { duration: .45, ease: 'power3' }), rY = gsap.quickTo(ring, 'y', { duration: .45, ease: 'power3' });
    addEventListener('pointermove', function (e) { dX(e.clientX); dY(e.clientY); rX(e.clientX); rY(e.clientY); }, { passive: true });
    document.addEventListener('pointerover', function (e) {
      var a = e.target.closest && e.target.closest('a, summary, button');
      ring.classList.toggle('hover', !!a);
      ring.firstChild.textContent = a ? (a.matches('a[href*="t.me"]') ? 'Открыть' : a.matches('summary') ? 'Ответ' : 'Смотреть') : '';
    });
    $$('.btn-primary, .btn-ghost, .nav-cta').forEach(function (b) {
      b.classList.add('magnetic');
      b.addEventListener('pointermove', function (e) {
        var r = b.getBoundingClientRect();
        b.style.transform = 'translate(' + (e.clientX - r.left - r.width / 2) * .3 + 'px,' + (e.clientY - r.top - r.height / 2) * .4 + 'px)';
      });
      b.addEventListener('pointerleave', function () { b.style.transform = ''; });
    });
  }

  // ── «Новое в боте» ──
  var nfItems = $$('.nf-card');
  if (nfItems.length) {
    gsap.set(nfItems, { y: 40, opacity: 0 });
    ScrollTrigger.batch(nfItems, { start: 'top bottom', once: true,
      onEnter: function (b) { gsap.to(b, { y: 0, opacity: 1, duration: .8, ease: 'power3.out', stagger: .08, overwrite: true }); } });
  }
  var ring = $('.cycle-ring');
  if (ring) {
    gsap.from('.cr-seg', { strokeDasharray: '0 28', duration: 1.4, ease: 'power3.out', stagger: .2, scrollTrigger: { trigger: ring, start: 'top 90%' } });
    gsap.from('.cr-dot', { opacity: 0, duration: .6, delay: 1.2, scrollTrigger: { trigger: ring, start: 'top 90%' } });
  }
  if ($('.wg-fill')) gsap.from('.wg-fill', { height: '0%', duration: 2, ease: 'power2.out', scrollTrigger: { trigger: '.water-glass', start: 'top 90%' } });
  var qs = $('.q-score b');
  if (qs) {
    $$('.q-bars i').forEach(function (i) { i.style.setProperty('--s', 0); });
    ScrollTrigger.create({ trigger: '.nf-quality', start: 'top 85%', once: true, onEnter: function () {
      var o = { v: 0 }; gsap.to(o, { v: +qs.dataset.count, duration: 1.6, ease: 'power2.out', onUpdate: function () { qs.textContent = Math.round(o.v); } });
      $$('.q-bars i').forEach(function (i, k) { setTimeout(function () { i.style.setProperty('--s', 1); }, 120 * k); });
    } });
  }
  if (fine) $$('.nf-card').forEach(function (card) {
    var rx = gsap.quickTo(card, 'rotationX', { duration: .6, ease: 'power3' }), ry = gsap.quickTo(card, 'rotationY', { duration: .6, ease: 'power3' });
    gsap.set(card, { transformPerspective: 1400 });
    card.addEventListener('pointermove', function (e) {
      var r = card.getBoundingClientRect();
      rx((.5 - (e.clientY - r.top) / r.height) * 5); ry(((e.clientX - r.left) / r.width - .5) * 6);
    });
    card.addEventListener('pointerleave', function () { rx(0); ry(0); });
  });

  // ── подвал: буквы названия падают сверху ──
  if (sname) {
    var chs = sname.querySelectorAll('.ch');
    gsap.set(chs, { yPercent: -110 });
    ScrollTrigger.create({ trigger: sname, start: 'top bottom', once: true,
      onEnter: function () { gsap.to(chs, { yPercent: 0, duration: 1.1, ease: 'power3.out', stagger: { amount: .45, ease: 'power2.inOut' } }); } });
    gsap.from('.sfoot-col, .sfoot-brand', { y: 30, opacity: 0, duration: .8, ease: 'power3.out', stagger: .08,
      scrollTrigger: { trigger: '.sfoot', start: 'top 90%' } });
  }

  addEventListener('load', function () { ScrollTrigger.refresh(); });
})();
