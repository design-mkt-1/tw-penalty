/* Registration card behaviour. Client-side only: no request is ever sent.
   Tab switch, per-field validation, then the "Registration complete" state
   from the design.

   The card claims role="dialog" aria-modal="true" in the markup, so it has to
   behave like one: focus moves in on open, Tab stays inside, Escape closes,
   and focus goes back where it came from. */
(function () {
  'use strict';

  /* IT will replace this with the real signup URL. While it is null the
     "GO TO WEBSITE" button reloads the page, which is the safe stand-in.
     Pointing it at the real destination is a one-line change. */
  var DESTINATION = null;   // e.g. 'https://topwin.example/signup?utm=penalty'

  /* The card has never sent anything anywhere, and this is where it would.
     SUBMIT receives what the visitor actually filled in -- the contact, which
     tab it came from, and the password they chose -- and null leaves the
     behaviour exactly as it was. IT replaces the body; nothing else in this
     file has to change.

     The password is in the payload because a registration hook without one is
     useless, which also means this seam must point at the client's own
     endpoint over TLS and nowhere else.

     It is called after the done screen is already up, and inside a try, so a
     hook that throws cannot strand the visitor on a form that has stopped
     responding. Same reason game.js catches around the shot sequence. */
  var SUBMIT = null;   // e.g. function (data) { fetch('/signup', {method:'POST', body: JSON.stringify(data)}); }

  /* Ukrainian mobile numbers are nine digits behind +380, and the design
     writes the prefix into the field as fixed text rather than offering a
     country picker. */
  var PHONE_DIGITS = 9;
  var PHONE_PREFIX = '+380';

  /* The design shows a twelve-character password and an error that reads
     "too short" without saying what short is. Eight is the rule this file
     applies; it is stated here rather than buried in the test below. */
  var PASSWORD_MIN = 8;

  var FOCUSABLE = 'a[href],button:not([disabled]),input:not([disabled]),' +
                  'select:not([disabled]),textarea:not([disabled]),' +
                  '[tabindex]:not([tabindex="-1"])';

  var sheet, card, stepForm, stepDone, tabs, phoneInput, emailInput,
      passInput, agreeBox, eyeBtn;
  var mode = 'email';
  var lastFocus = null;
  var closing = false;

  function field(name) {
    return card.querySelector('.field[data-for="' + name + '"]');
  }

  function setTab(next) {
    mode = next;
    tabs.forEach(function (t) {
      var on = t.dataset.tab === next;
      t.classList.toggle('is-active', on);
      t.setAttribute('aria-selected', String(on));
    });
    ['email', 'phone'].forEach(function (name) {
      var f = field(name);
      f.hidden = name !== next;
      clearError(f);
      f.classList.remove('is-valid');
    });
  }

  /* The error line fades rather than appearing. It used to be a plain
     `hidden` toggle, so a failed submit snapped 22px of card into existence
     with nothing to explain the movement.

     Two steps, because reset.css forces [hidden] to display:none !important
     and display cannot be transitioned: unhide one frame ahead of the class
     going on, and take the class off one transition ahead of hiding. The
     language menu and the registration card itself both do this already. */
  var ERR_OUT = 160;
  var errTimers = {};

  function clearError(f) {
    f.classList.remove('is-invalid');
    var input = f.querySelector('input');
    if (input) input.removeAttribute('aria-invalid');
    var e = f.querySelector('.err');
    if (!e || e.hidden) return;
    e.classList.remove('is-shown');
    clearTimeout(errTimers[e.id]);
    errTimers[e.id] = setTimeout(function () { e.hidden = true; }, ERR_OUT);
  }

  /* `focus` is false for every field after the first: showing three errors
     and focusing the last one would put the cursor at the bottom of the form
     and read the wrong message out. */
  function showError(f, focus) {
    f.classList.add('is-invalid');
    f.classList.remove('is-valid');
    /* The red ring is only half the message. aria-invalid states it, and the
       focus move is what makes aria-describedby read the error out: nothing
       announces a message that arrives while focus sits on the dialog. */
    var input = f.querySelector('input');
    if (input) {
      input.setAttribute('aria-invalid', 'true');
      if (focus) input.focus({ preventScroll: true });
    }
    var e = f.querySelector('.err');
    if (!e) return;
    clearTimeout(errTimers[e.id]);
    e.hidden = false;
    TWFx.next(function () { e.classList.add('is-shown'); });
  }

  /* ── validation ───────────────────────────────────────────── */

  /* Each of these returns the value to keep, or null. They do not touch the
     DOM: the caller decides whether a failure is worth showing yet, which is
     what lets the same tests drive both the submit path and the live green
     border the success state (19:4635) asks for. */

  function readContact() {
    var value = (mode === 'phone' ? phoneInput : emailInput).value.trim();

    if (mode === 'phone') {
      var digits = value.replace(/[^\d]/g, '');

      /* Three forms reach this field and all three are the same number:
         931234567 as the design's placeholder asks for it, 0931234567 with
         the trunk zero people type out of habit, and 380931234567 pasted
         with the country code -- which has to lose it or the done screen
         reads "+380 +380931234567".

         Keyed on the total length rather than on the prefix, so a national
         number that itself begins 380 is never mistaken for a country code:
         at nine digits it is already the right length and nothing is cut. */
      if (digits.length === 12 && digits.indexOf('380') === 0) digits = digits.slice(3);
      else if (digits.length === 10 && digits.charAt(0) === '0') digits = digits.slice(1);

      if (digits.length !== PHONE_DIGITS || /[a-z]/i.test(value)) return null;
      // E.164, unspaced: this value is what the SUBMIT hook receives, and a
      // hook wants the canonical number. The spacing is a display concern and
      // lives in shown() below.
      return PHONE_PREFIX + digits;
    }

    return /^[^\s@]+@[^\s@]+\.[a-z]{2,}$/i.test(value) ? value : null;
  }

  /* The complete screen groups the number the way the design writes it,
     "+380 93 123 4567", which is also how the placeholder groups it. */
  function shown(contact) {
    if (mode !== 'phone') return contact;
    var d = contact.slice(PHONE_PREFIX.length);
    return PHONE_PREFIX + ' ' + d.slice(0, 2) + ' ' + d.slice(2, 5) + ' ' + d.slice(5);
  }

  function readPassword() {
    var value = passInput.value;
    return value.length >= PASSWORD_MIN ? value : null;
  }

  /* The green border and tick of the success state, applied as the visitor
     types. Only ever adds the valid mark -- turning a field red while
     somebody is still halfway through typing into it is the one thing a live
     check must not do. */
  function mark(f, ok) {
    f.classList.toggle('is-valid', !!ok);
    if (ok) clearError(f);
  }

  function submit(ev) {
    ev.preventDefault();

    var contactField = field(mode);
    var passField = field('password');
    var contact = readContact();
    var password = readPassword();
    var first = true;

    if (!contact) { showError(contactField, first); first = false; }
    if (!password) { showError(passField, first); first = false; }

    /* The design has no error state for the 18+ box -- it is drawn checked in
       every screen -- so an unchecked one is marked and focused rather than
       given a message this card has no words for. */
    agreeBox.setAttribute('aria-invalid', String(!agreeBox.checked));
    if (!agreeBox.checked) {
      if (first) agreeBox.focus({ preventScroll: true });
      return;
    }

    if (!contact || !password) return;

    /* The design labels the row "Login" whichever tab was used, so unlike the
       card this replaces there is no label to swap between phone and email. */
    stepDone.querySelector('.done__id').textContent = shown(contact);
    stepDone.querySelector('.done__pw').textContent = password;

    stepForm.hidden = true;
    stepDone.hidden = false;
    // #promo-title survives the step swap now -- the promo header sits outside
    // both steps -- but the dialog should still be named by what it shows.
    card.setAttribute('aria-labelledby', 'done-title');
    card.scrollTop = 0;
    TWAudio.play('whistle', 0.5);

    /* Last, and guarded: the visitor is already on the done screen, so a hook
       that throws costs a delivery rather than the card. */
    if (SUBMIT) {
      try {
        SUBMIT({
          via: mode,
          contact: contact,
          password: password,
          lang: document.documentElement.lang || null
        });
      } catch (err) {
        console.error('[tw-penalty] the submit hook failed', err);
      }
    }
  }

  /* ── password reveal ──────────────────────────────────────── */

  function toggleEye() {
    var shown = passInput.type === 'text';
    passInput.type = shown ? 'password' : 'text';
    eyeBtn.setAttribute('aria-pressed', String(!shown));
    // Keep the caret where it was: changing type moves focus off the input in
    // some browsers, and the visitor is mid-password.
    passInput.focus({ preventScroll: true });
  }

  /* ── copy buttons ─────────────────────────────────────────── */

  var copyTimer = 0;

  function copy(btn) {
    var target = stepDone.querySelector(btn.getAttribute('data-copy'));
    if (!target) return;
    var text = target.textContent;

    /* clipboard.writeText needs a secure context and permission, and the
       whole point of this button is that the visitor keeps their details --
       so a refusal selects the text instead of failing silently. */
    var done = function () {
      btn.classList.add('is-copied');
      clearTimeout(copyTimer);
      copyTimer = setTimeout(function () {
        btn.classList.remove('is-copied');
      }, 1200);
    };

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, function () { select(target); });
    } else {
      select(target);
    }
  }

  function select(el) {
    var range = document.createRange();
    range.selectNodeContents(el);
    var sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
  }

  /* ── focus containment ────────────────────────────────────── */

  /* Only what is genuinely on screen: the phone field is hidden while the
     email tab is active, and one of the two steps is always hidden. */
  function focusables() {
    return Array.prototype.filter.call(
      card.querySelectorAll(FOCUSABLE),
      function (el) { return el.getClientRects().length > 0; }
    );
  }

  /* Every focus() call passes preventScroll: the page must never scroll, and
     the browser's default scroll-into-view would break that on its own. */
  function onKeydown(ev) {
    if (ev.key === 'Escape') {
      ev.preventDefault();
      close();
      return;
    }
    if (ev.key !== 'Tab') return;

    var list = focusables();
    if (!list.length) return;

    var first = list[0];
    var last = list[list.length - 1];

    if (!card.contains(document.activeElement)) {
      ev.preventDefault();
      (ev.shiftKey ? last : first).focus({ preventScroll: true });
    } else if (ev.shiftKey && document.activeElement === first) {
      ev.preventDefault();
      last.focus({ preventScroll: true });
    } else if (!ev.shiftKey && document.activeElement === last) {
      ev.preventDefault();
      first.focus({ preventScroll: true });
    }
  }

  /* ── open / close ─────────────────────────────────────────── */

  /* Tab is trapped, but a screen reader's virtual cursor is not: without this
     it browses the header, the six targets and the ball behind a dialog that
     claims aria-modal. inert takes them out of the accessibility tree and out
     of hit-testing in one attribute. Everything under #stage except the sheet
     itself, which is where the card lives. */
  function background(off) {
    Array.prototype.forEach.call(sheet.parentNode.children, function (el) {
      if (el === sheet) return;
      if (off) el.setAttribute('inert', '');
      else el.removeAttribute('inert');
    });
  }

  function open() {
    if (!sheet.hidden) return;
    lastFocus = document.activeElement;
    closing = false;

    sheet.hidden = false;
    sheet.setAttribute('aria-hidden', 'false');
    background(true);
    document.addEventListener('keydown', onKeydown, true);

    TWFx.next(function () {
      sheet.classList.add('is-open');
      // The card itself, not the first field: on a phone, focusing a text
      // input pops the soft keyboard the instant the goal is scored.
      card.focus({ preventScroll: true });
    });
  }

  /* onDone runs once the card is fully gone. "GO TO WEBSITE" passes the
     navigation; Escape passes nothing and simply hands the pitch back. */
  function close(onDone) {
    if (closing || sheet.hidden) return;
    closing = true;

    sheet.classList.remove('is-open');
    document.removeEventListener('keydown', onKeydown, true);

    setTimeout(function () {
      sheet.hidden = true;
      sheet.setAttribute('aria-hidden', 'true');
      closing = false;
      restore();

      // Before the focus restore below: focus() cannot land inside inert.
      background(false);

      if (lastFocus && lastFocus.focus) lastFocus.focus({ preventScroll: true });
      lastFocus = null;

      // The stage still carries data-state="form", which holds .panel and
      // .ball at pointer-events:none, and the attempt counter is still past
      // the end of the scripted sequence. Hand both back to the game, or the
      // page stays dead behind a card nobody can see.
      if (window.TWGame && TWGame.reset) TWGame.reset();

      if (typeof onDone === 'function') onDone();
    }, 280);
  }

  /* Back to the opening state, so a second visit does not start on the
     complete screen with the previous answers still sitting in the fields.
     Every control the card owns is listed here: the one the card this
     replaces forgot was the only one it had that this function did not
     name. */
  function restore() {
    stepDone.hidden = true;
    stepForm.hidden = false;
    card.setAttribute('aria-labelledby', 'promo-title');
    emailInput.value = '';
    phoneInput.value = '';
    passInput.value = '';
    passInput.type = 'password';
    eyeBtn.setAttribute('aria-pressed', 'false');
    // Checked is the design's default state, not merely the initial one.
    agreeBox.checked = true;
    agreeBox.removeAttribute('aria-invalid');
    clearError(field('password'));
    field('password').classList.remove('is-valid');
    setTab('email');
    card.scrollTop = 0;
  }

  function go() {
    if (DESTINATION) window.location.assign(DESTINATION);
    else window.location.reload();
  }

  /* ── boot ─────────────────────────────────────────────────── */

  function init() {
    sheet    = document.querySelector('.sheet');
    card     = sheet.querySelector('.card');
    stepForm = card.querySelector('[data-step="form"]');
    stepDone = card.querySelector('[data-step="done"]');
    tabs     = Array.prototype.slice.call(card.querySelectorAll('.tab'));
    emailInput = card.querySelector('#tw-email');
    phoneInput = card.querySelector('#tw-phone');
    passInput  = card.querySelector('#tw-pass');
    agreeBox   = card.querySelector('#tw-agree');
    eyeBtn     = card.querySelector('.eye');

    tabs.forEach(function (t) {
      t.addEventListener('click', function () { setTab(t.dataset.tab); });
    });

    [emailInput, phoneInput].forEach(function (input) {
      input.addEventListener('input', function () {
        var f = input.closest('.field');
        clearError(f);
        mark(f, readContact());
      });
    });

    passInput.addEventListener('input', function () {
      var f = passInput.closest('.field');
      clearError(f);
      mark(f, readPassword());
    });

    agreeBox.addEventListener('change', function () {
      if (agreeBox.checked) agreeBox.removeAttribute('aria-invalid');
    });

    eyeBtn.addEventListener('click', toggleEye);

    Array.prototype.forEach.call(card.querySelectorAll('.copy'), function (btn) {
      btn.addEventListener('click', function () { copy(btn); });
    });

    card.addEventListener('submit', submit);

    card.querySelector('[data-action="close"]')
        .addEventListener('click', function () { close(go); });

    // The soft keyboard changes the usable height; re-fit the stage around it.
    card.addEventListener('focusin', function () { TWStage.fit(); });
    card.addEventListener('focusout', function () { TWStage.fit(); });
  }

  window.TWForm = { init: init, open: open, close: close };
})();
