/* Согласие на cookie: Яндекс Метрика загружается только после «Принять». Выбор хранится в localStorage. */
(function () {
  var KEY = 'cpt_cookie_consent';
  var COUNTER = 110221375;

  function read() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function save(v) { try { localStorage.setItem(KEY, v); } catch (e) {} }

  function loadMetrika() {
    if (window.ym) return;
    (function (m, e, t, r, i, k, a) {
      m[i] = m[i] || function () { (m[i].a = m[i].a || []).push(arguments); };
      m[i].l = 1 * new Date();
      k = e.createElement(t); a = e.getElementsByTagName(t)[0]; k.async = 1; k.src = r; a.parentNode.insertBefore(k, a);
    })(window, document, 'script', 'https://mc.yandex.ru/metrika/tag.js?id=' + COUNTER, 'ym');
    ym(COUNTER, 'init', { clickmap: true, trackLinks: true, accurateTrackBounce: true, webvisor: true });
  }

  function banner() {
    var css = document.createElement('style');
    css.textContent =
      '.cc{position:fixed;left:24px;bottom:24px;z-index:400;max-width:420px;padding:22px 24px;background:rgba(17,22,32,.96);' +
      'border:1px solid rgba(201,169,110,.35);box-shadow:0 20px 60px rgba(0,0,0,.5);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);' +
      'font-family:Inter,system-ui,sans-serif;font-weight:300;color:#B9C1CF;font-size:13px;line-height:1.65;opacity:0;transform:translateY(16px);transition:opacity .5s,transform .5s}' +
      '.cc.show{opacity:1;transform:none}.cc a{color:#C9A96E}.cc-row{display:flex;gap:10px;margin-top:16px;flex-wrap:wrap}' +
      '.cc button{font:inherit;font-size:11px;letter-spacing:.14em;text-transform:uppercase;padding:11px 20px;cursor:pointer;transition:all .25s}' +
      '.cc-yes{background:#C9A96E;color:#0C1018;border:1px solid #C9A96E;font-weight:500}.cc-yes:hover{background:#E2C99A}' +
      '.cc-no{background:transparent;color:#F0EDE8;border:1px solid rgba(240,237,232,.25)}.cc-no:hover{border-color:#F0EDE8}' +
      '@media(max-width:520px){.cc{left:16px;right:16px;bottom:16px;max-width:none}}';
    document.head.appendChild(css);
    var box = document.createElement('div');
    box.className = 'cc';
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-label', 'Согласие на cookie');
    box.innerHTML = 'Мы используем cookie и Яндекс Метрику, чтобы понимать, как улучшить сайт. ' +
      'Метрика включится только с вашего согласия. <a href="/cookies/">Подробнее о cookie</a>' +
      '<div class="cc-row"><button class="cc-yes" type="button">Принять</button><button class="cc-no" type="button">Отклонить</button></div>';
    document.body.appendChild(box);
    requestAnimationFrame(function () { box.classList.add('show'); });
    function close(v) {
      save(v);
      box.classList.remove('show');
      setTimeout(function () { box.remove(); }, 500);
      if (v === 'yes') loadMetrika();
    }
    box.querySelector('.cc-yes').onclick = function () { close('yes'); };
    box.querySelector('.cc-no').onclick = function () { close('no'); };
  }

  // кнопка «Настройки cookie» на странице /cookies/ сбрасывает выбор
  window.cptResetConsent = function () { save(''); location.reload(); };

  var v = read();
  if (v === 'yes') loadMetrika();
  else if (v !== 'no') {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', banner);
    else banner();
  }
})();
