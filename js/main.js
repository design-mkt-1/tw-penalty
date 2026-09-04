/* Boot. Wires the mute button, unlocks audio on the first gesture,
   and hands control to the game. */
(function () {
  'use strict';

  /* The two outbound links the client has not supplied yet. Neither anchor
     carries an href in the markup, so until a seam is filled it is not a link
     at all: no tab stop, nothing announced as a link, and no click. That is
     the point. Both used to be href="#", which offers a link that goes
     nowhere and drops a bare fragment into the address bar of a page that is
     not allowed to scroll.

     Filling either is a one-line change and needs nothing else. The third URL,
     behind GO TO WEBSITE, is DESTINATION at the top of js/form.js. */
  var HOME_URL  = null;   // e.g. 'https://topwin.example/'
  var LOGIN_URL = null;   // e.g. 'https://topwin.example/login'

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

    // The card is in the DOM from the start, only hidden, so both resolve here.
    link('.hdr__logo', HOME_URL);
    link('.card .foot a', LOGIN_URL);

    TWI18n.init();
    TWForm.init();
    TWGame.init();
    TWStage.fit();
  });
})();
