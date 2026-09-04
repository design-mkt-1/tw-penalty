/* Boot. Wires the mute button, unlocks audio on the first gesture,
   and hands control to the game. */
(function () {
  'use strict';

  /* The four outbound links the client has not supplied yet. No anchor
     carries an href in the markup, so until a seam is filled it is not a link
     at all: no tab stop, nothing announced as a link, and no click. That is
     the point. They used to be href="#", which offers a link that goes
     nowhere and drops a bare fragment into the address bar of a page that is
     not allowed to scroll.

     Filling any of them is a one-line change and needs nothing else. The
     fifth URL, behind GO TO WEBSITE, is DESTINATION at the top of
     js/form.js. */
  var HOME_URL    = null;   // e.g. 'https://topwin.example/'
  var LOGIN_URL   = null;   // e.g. 'https://topwin.example/login'
  var TERMS_URL   = null;   // e.g. 'https://topwin.example/terms'
  var PRIVACY_URL = null;   // e.g. 'https://topwin.example/privacy'

  function link(sel, url) {
    if (!url) return;
    var a = document.querySelector(sel);
    if (a) a.setAttribute('href', url);
  }

  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  ready(function () {
    /* All four init() calls share this callback, so anything that throws up
       here takes the whole page down with it. The mute button is a convenience;
       the game is not. */
    var muteBtn = document.querySelector('.mute');
    if (muteBtn) {
      muteBtn.setAttribute('aria-pressed', String(TWAudio.isMuted()));
      muteBtn.addEventListener('click', function () { TWAudio.toggle(); });
    }

    // Audio can only start inside a user gesture.
    var unlock = function () {
      TWAudio.unlock();
      window.removeEventListener('pointerdown', unlock);
      window.removeEventListener('keydown', unlock);
    };
    window.addEventListener('pointerdown', unlock, { once: false });
    window.addEventListener('keydown', unlock, { once: false });

    // The card is in the DOM from the start, only hidden, so all four resolve
    // here. The two consent links are addressed by position within the
    // sentence, which is the only thing that distinguishes them -- js/i18n.js
    // may reorder the words around them but not the anchors themselves.
    link('.hdr__logo', HOME_URL);
    link('.card .foot a', LOGIN_URL);
    link('.card .agree__text a:nth-of-type(1)', TERMS_URL);
    link('.card .agree__text a:nth-of-type(2)', PRIVACY_URL);

    TWI18n.init();
    TWForm.init();
    TWGame.init();
    TWStage.fit();
  });
})();
