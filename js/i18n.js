/* Three locales, no dependencies, same shape as the other modules.

   Every visible string lives in STRINGS below rather than in the markup or
   in game.js/form.js, so adding a fourth language is one more object and
   nothing else. Nodes opt in with data-i18n="key"; attributes with
   data-i18n-attr="attr:key" (semicolon-separated for more than one).

   Ukrainian is the default and the fallback, so its table is the one that has
   to be complete: t() falls through to it for anything a locale is missing,
   and a key missing from the fallback too renders as the key itself. */
(function () {
  'use strict';

  var LANGS = ['ua', 'ru', 'en'];
  var FALLBACK = 'ua';
  var STORE_KEY = 'tw-lang';

  /* "ua" is the code the design, the menu and this file use, and it is not a
     language tag: ua is the REGION subtag for Ukraine, and the language is
     uk. The distinction only matters where a real tag is required, so the
     internal code is mapped rather than renamed -- documentElement.lang is
     what a screen reader picks a voice and a pronunciation from, and lang="ua"
     asks it to read Ukrainian as something that does not exist.

     detect() reads through the same map, so a browser reporting uk-UA matches
     the Ukrainian locale rather than falling through to the default by luck. */
  var LOCALE = { ua: 'uk', ru: 'ru', en: 'en' };

  /* \n means a real line break in the rendered text -- only the tagline uses
     it, and it is the reason the markup no longer carries a <br>. */
  var STRINGS = {
    en: {
      'title':          'Top Win — Score the penalty and win!',
      'hdr.sound':      'Toggle sound',
      'hdr.lang':       'Language',
      'tagline':        'Score the penalty\nand win!',
      'goal.aim':       'Choose where to shoot',
      /* The six targets carry only a multiplier, and three of those repeat.
         The position is what tells them apart; game.js joins it to the
         multiplier, which stays in the markup. */
      'cell.tl':        'Top left',
      'cell.tc':        'Top centre',
      'cell.tr':        'Top right',
      'cell.bl':        'Bottom left',
      'cell.bc':        'Bottom centre',
      'cell.br':        'Bottom right',
      'ball.shoot':     'Shoot at a random spot',
      'msg.miss':       'So close! One more try',
      'msg.goal':       'GOAL!',
      /* The offer figures are final copy and identical in every language, so
         they are strings here rather than markup: a locale that wanted to
         write the amount differently can, without touching index.html. */
      'promo.title':    'Welcome sports bonus',
      'promo.pct':      '225%',
      'promo.amount':   'up to 15000 UAH',
      'tabs.label':     'Sign up with',
      'tab.phone':      'PHONE',
      'tab.email':      'EMAIL',
      /* The placeholders are the design's own. The email field has no label
         above it, which is why the word sits inside the box; the phone field
         shows the shape of the number behind the fixed +380. */
      'field.email':    'Email',
      'field.phone':    '00 000 0000',
      'field.phoneLabel': 'Phone number',
      'field.password': 'Password',
      'field.passwordHint': 'Enter password',
      'field.reveal':   'Show password',
      'err.phone':      'Invalid phone number',
      'err.email':      'Invalid email address',
      'err.password':   'Password is too short',
      'dialog.close':   'Close',
      /* Five pieces rather than one sentence with markup in it: the two links
         are their own nodes, so a locale can move them within the sentence
         and none of the strings carries a tag. */
      'agree.aria':     'I am 18 and I accept the terms',
      'agree.pre':      'I am 18 years old and I accept the ',
      'agree.terms':    'Terms of Use',
      'agree.mid':      ' and the ',
      'agree.privacy':  'Privacy Policy',
      'agree.post':     '.',
      'cta.register':   'REGISTER',
      'foot.have':      'Already have an account?',
      'foot.login':     'Log in',
      'done.title':     'Registration successful!',
      'done.login':     'Login:',
      'done.password':  'Password:',
      'done.copy':      'Copy',
      'done.note':      'Save your login details',
      'cta.website':    'GO TO WEBSITE',
      'footer.pay':     'Payment methods',
      'footer.copy':    '© 2026 All rights reserved'
    },

    /* The default, the fallback, and the only table read straight off the
       design. Every string from 'promo.title' down is the card's own copy,
       transcribed from the Figma nodes rather than translated -- these are the
       words the client signed off, apostrophes and casing included. The game
       strings above them are ours: the pitch is not in the design. */
    ua: {
      'title':          'Top Win — Заб’єш пенальті та виграєш!',
      'hdr.sound':      'Увімкнути або вимкнути звук',
      'hdr.lang':       'Мова',
      'tagline':        'Заб’єш пенальті\nта виграєш!',
      'goal.aim':       'Оберіть, куди бити',
      'cell.tl':        'Угорі ліворуч',
      'cell.tc':        'Угорі по центру',
      'cell.tr':        'Угорі праворуч',
      'cell.bl':        'Унизу ліворуч',
      'cell.bc':        'Унизу по центру',
      'cell.br':        'Унизу праворуч',
      'ball.shoot':     'Удар у випадкову точку',
      'msg.miss':       'Так близько! Ще спроба',
      'msg.goal':       'ГОЛ!',
      'promo.title':    'Вітальний спортивний бонус',
      'promo.pct':      '225%',
      'promo.amount':   'до 15000 UAH',
      'tabs.label':     'Спосіб реєстрації',
      'tab.phone':      'ТЕЛЕФОН',
      'tab.email':      'EMAIL',
      'field.email':    'Email',
      'field.phone':    '00 000 0000',
      'field.phoneLabel': 'Номер телефону',
      'field.password': 'Пароль',
      'field.passwordHint': 'Введіть пароль',
      'field.reveal':   'Показати пароль',
      'err.phone':      'Невірний номер телефону',
      'err.email':      'Невірна адреса електронної пошти',
      'err.password':   'Пароль занадто короткий',
      'dialog.close':   'Закрити',
      'agree.aria':     'Мені 18 років, і я приймаю умови',
      'agree.pre':      'Мені 18 років, і я приймаю ',
      'agree.terms':    'Умови Використання',
      'agree.mid':      ' та ',
      'agree.privacy':  'Політику конфіденційності',
      'agree.post':     '.',
      'cta.register':   'ЗАРЕЄСТРУВАТИСЬ',
      'foot.have':      'Вже є акаунт?',
      'foot.login':     'Увійти',
      'done.title':     'Реєстрація успішна!',
      'done.login':     'Логін:',
      'done.password':  'Пароль:',
      'done.copy':      'Копіювати',
      'done.note':      'Збережіть ваші дані для входу',
      'cta.website':    'ПЕРЕЙТИ НА САЙТ',
      /* The year is the design's, not the clock's: it is copy the client set,
         so it changes when they change it rather than on 1 January. */
      'footer.pay':     'Способи оплати',
      'footer.copy':    '© 2026 Усі права захищені'
    },

    ru: {
      'title':          'Top Win — Забей пенальти и выиграй!',
      'hdr.sound':      'Включить или выключить звук',
      'hdr.lang':       'Язык',
      'tagline':        'Забей пенальти\nи выиграй!',
      'goal.aim':       'Выберите, куда бить',
      'cell.tl':        'Вверху слева',
      'cell.tc':        'Вверху по центру',
      'cell.tr':        'Вверху справа',
      'cell.bl':        'Внизу слева',
      'cell.bc':        'Внизу по центру',
      'cell.br':        'Внизу справа',
      'ball.shoot':     'Удар в случайную точку',
      'msg.miss':       'Так близко! Ещё попытка',
      'msg.goal':       'ГОЛ!',
      /* Written, not transcribed. The Figma page carries the card in
         Ukrainian only -- fourteen variants, all UA -- so unlike the block
         above, this half of the Russian table has never been read by the
         designer or by a native speaker. The offer figures are the exception:
         225% and the amount are the same string in every locale. */
      'promo.title':    'Приветственный спортивный бонус',
      'promo.pct':      '225%',
      'promo.amount':   'до 15000 UAH',
      'tabs.label':     'Способ регистрации',
      'tab.phone':      'ТЕЛЕФОН',
      'tab.email':      'EMAIL',
      'field.email':    'Email',
      'field.phone':    '00 000 0000',
      'field.phoneLabel': 'Номер телефона',
      'field.password': 'Пароль',
      'field.passwordHint': 'Введите пароль',
      'field.reveal':   'Показать пароль',
      'err.phone':      'Неверный номер телефона',
      'err.email':      'Неверный адрес почты',
      'err.password':   'Пароль слишком короткий',
      'dialog.close':   'Закрыть',
      'agree.aria':     'Мне 18 лет, и я принимаю условия',
      'agree.pre':      'Мне 18 лет, и я принимаю ',
      'agree.terms':    'Условия использования',
      'agree.mid':      ' и ',
      'agree.privacy':  'Политику конфиденциальности',
      'agree.post':     '.',
      'cta.register':   'ЗАРЕГИСТРИРОВАТЬСЯ',
      'foot.have':      'Уже есть аккаунт?',
      'foot.login':     'Войти',
      'done.title':     'Регистрация успешна!',
      'done.login':     'Логин:',
      'done.password':  'Пароль:',
      'done.copy':      'Копировать',
      'done.note':      'Сохраните свои данные для входа',
      'cta.website':    'ПЕРЕЙТИ НА САЙТ',
      'footer.pay':     'Способы оплаты',
      'footer.copy':    '© 2026 Все права защищены'
    }
  };

  /* Shown inside the menu, so each language names itself. Never translated. */
  var ENDONYM = { ua: 'Українська', ru: 'Русский', en: 'English' };

  var lang = FALLBACK;
  var watchers = [];
  var btn, menu, options;
  var hideTimer = 0;

  /* Must match the exit transition on .lang-menu in css/game.css. */
  var EXIT_MS = 120;

  /* ── strings ──────────────────────────────────────────────── */

  function t(key) {
    var table = STRINGS[lang];
    var value = table && table[key];
    if (value == null) value = STRINGS[FALLBACK][key];
    return value == null ? key : value;
  }

  function setText(el, value) {
    if (value.indexOf('\n') < 0) { el.textContent = value; return; }
    el.textContent = '';
    value.split('\n').forEach(function (line, i) {
      if (i) el.appendChild(document.createElement('br'));
      el.appendChild(document.createTextNode(line));
    });
  }

  /* Re-render one subtree. form.js calls it with the done step after it
     swaps the account label between phone and email. */
  function apply(root) {
    root = root || document;

    Array.prototype.forEach.call(root.querySelectorAll('[data-i18n]'), function (el) {
      setText(el, t(el.getAttribute('data-i18n')));
    });

    Array.prototype.forEach.call(root.querySelectorAll('[data-i18n-attr]'), function (el) {
      el.getAttribute('data-i18n-attr').split(';').forEach(function (pair) {
        var bits = pair.split(':');
        if (bits.length === 2) el.setAttribute(bits[0].trim(), t(bits[1].trim()));
      });
    });

    // The tag, not our internal code -- see LOCALE at the top of the file.
    document.documentElement.lang = LOCALE[lang] || lang;
  }

  function set(next) {
    if (LANGS.indexOf(next) < 0 || next === lang) return;
    lang = next;
    try { localStorage.setItem(STORE_KEY, next); } catch (e) { /* private mode */ }
    apply();
    syncSelector();
    watchers.forEach(function (fn) { fn(next); });
  }

  /* Saved choice wins, then the browser's own language, then English. */
  function detect() {
    var saved = null;
    try { saved = localStorage.getItem(STORE_KEY); } catch (e) { /* private mode */ }
    if (LANGS.indexOf(saved) >= 0) return saved;

    /* Matched against the real language tags, not against our own codes: a
       Ukrainian browser reports uk-UA, which never equals "ua". Comparing the
       two directly landed every Ukrainian visitor on the fallback and only
       looked correct because the fallback is Ukrainian. */
    var nav = (navigator.language || '').slice(0, 2).toLowerCase();
    for (var i = 0; i < LANGS.length; i++) {
      if (LOCALE[LANGS[i]] === nav) return LANGS[i];
    }
    return FALLBACK;
  }

  /* ── selector ─────────────────────────────────────────────── */

  /* A listbox, not a dialog: focus moves along the options with the arrow
     keys instead of being trapped, so this deliberately does not reuse the
     Tab trap in form.js -- that pattern is for modals. */

  function isOpen() {
    return btn.getAttribute('aria-expanded') === 'true';
  }

  /* reset.css forces [hidden] to display:none !important, so the menu cannot
     transition its own display. Unhide first, let one frame pass, then add
     the class the transition runs on -- the same two-step as form.js. */
  function openMenu(focusIndex) {
    clearTimeout(hideTimer);
    menu.hidden = false;
    btn.setAttribute('aria-expanded', 'true');
    TWFx.next(function () { menu.classList.add('is-open'); });

    document.addEventListener('keydown', onKeydown, true);
    document.addEventListener('pointerdown', onPointerDown, true);

    var i = typeof focusIndex === 'number' ? focusIndex : LANGS.indexOf(lang);
    options[Math.max(0, i)].focus({ preventScroll: true });
  }

  function closeMenu(restoreFocus) {
    if (!isOpen()) return;
    menu.classList.remove('is-open');
    btn.setAttribute('aria-expanded', 'false');

    document.removeEventListener('keydown', onKeydown, true);
    document.removeEventListener('pointerdown', onPointerDown, true);

    // Focus has to leave before the menu is taken out of the layout, or the
    // browser drops it on <body> and the next Tab starts from the top.
    if (restoreFocus !== false) btn.focus({ preventScroll: true });
    else if (menu.contains(document.activeElement)) document.activeElement.blur();

    clearTimeout(hideTimer);
    hideTimer = setTimeout(function () { menu.hidden = true; }, EXIT_MS);
  }

  function move(step) {
    var here = options.indexOf(document.activeElement);
    var next = (here + step + options.length) % options.length;
    options[next].focus({ preventScroll: true });
  }

  function onKeydown(ev) {
    switch (ev.key) {
      case 'Escape':    ev.preventDefault(); closeMenu(); break;
      case 'ArrowDown': ev.preventDefault(); move(1); break;
      case 'ArrowUp':   ev.preventDefault(); move(-1); break;
      case 'Home':      ev.preventDefault(); options[0].focus({ preventScroll: true }); break;
      case 'End':       ev.preventDefault(); options[options.length - 1].focus({ preventScroll: true }); break;
      case 'Enter':
      case ' ':
        if (options.indexOf(document.activeElement) >= 0) {
          ev.preventDefault();
          choose(document.activeElement);
        }
        break;
      case 'Tab':
        /* Hand focus back to the trigger and let the Tab carry on from there,
           forwards or backwards. Closing with `false` blurred instead, which
           is the exact failure the comment in closeMenu warns about: the next
           Tab restarted from the top of the page. */
        closeMenu();
        break;
    }
  }

  function onPointerDown(ev) {
    if (!menu.contains(ev.target) && ev.target !== btn) closeMenu(false);
  }

  function choose(option) {
    set(option.getAttribute('data-lang'));
    closeMenu();
  }

  function syncSelector() {
    if (!btn) return;
    btn.querySelector('.lang__code').textContent = lang.toUpperCase();

    // The trigger carries a globe now, the way the design draws it, so there
    // is no flag on it to keep in step with the choice -- only the code and
    // which row shows its tick.
    options.forEach(function (o) {
      o.setAttribute('aria-selected',
                     String(o.getAttribute('data-lang') === lang));
    });
  }

  function wireSelector() {
    btn = document.querySelector('.lang');
    menu = document.querySelector('.lang-menu');
    if (!btn || !menu) return;

    options = Array.prototype.slice.call(menu.querySelectorAll('[data-lang]'));
    options.forEach(function (o) {
      var code = o.getAttribute('data-lang');
      o.querySelector('.lang-opt__name').textContent = ENDONYM[code] || code;
      o.addEventListener('click', function () { choose(o); });
    });

    btn.addEventListener('click', function () {
      if (isOpen()) closeMenu(); else openMenu();
    });

    // Opening straight onto an end of the list is the expected shortcut.
    btn.addEventListener('keydown', function (ev) {
      if (ev.key === 'ArrowDown') { ev.preventDefault(); openMenu(0); }
      else if (ev.key === 'ArrowUp') { ev.preventDefault(); openMenu(options.length - 1); }
    });

    syncSelector();
  }

  /* ── boot ─────────────────────────────────────────────────── */

  function init() {
    lang = detect();
    apply();
    wireSelector();
  }

  window.TWI18n = {
    init: init,
    t: t,
    set: set,
    apply: apply,
    langs: LANGS,
    current: function () { return lang; },
    onChange: function (fn) { watchers.push(fn); }
  };
})();
