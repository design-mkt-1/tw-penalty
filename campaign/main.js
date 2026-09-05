/* ═══════════════════════════════════════════════════════════════
   TW-PENALTY — the mechanic

   Scripted penalty: the first attempt is always saved, the second always
   scores. The panel the visitor picks never changes the outcome — it only
   selects which dive and which ball trajectory play.

   This file is the controller. Three siblings carry the rest, and index.html
   loads them BEFORE this one, because TW.ready() fires the moment the shell
   has booted and this file uses all three inside it:

     campaign/fx.js        CMPFx        the canvas: ball in flight, its
                                        travelling shadow, the net, confetti
     campaign/animator.js  CMPAnimator  the keeper's ten sprites and the dives
     campaign/audio.js     CMPAudio     the seven clips and the mute state

   ── What the shell owns, and this file must not touch ────────
   The header, the footer and the whole registration card. The mechanic
   reaches them only through window.TW:

     TW.ready(fn)       run once the chrome is mounted and a language applied
     TW.openForm()      open the registration dialog — the point of the page
     TW.t(key)          a translated string
     TW.on('lang')      re-label the six panels when the language changes
     TW.on('formclose') put the pitch back when the card closes
     TW.track(event)    analytics; a no-op unless an id is configured

   Do not call showModal(), do not reach into the dialog, do not re-implement
   the focus trap. This landing's old js/main.js and js/form.js did all three;
   css/form.css and js/form.js do it for every campaign now.
   ═══════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  /* ── the stage's own geometry ──────────────────────────────
     Was js/stage.js. Two thirds of that file is css/stage.css now; what is
     left is the canvas backing store, which cannot be set from CSS, and the
     unit the hand-tuned distances in campaign/fx.js are scaled by. Both
     belong to the mechanic, which is why they live here. */

  /* The reference composition: every distance in campaign/fx.js was written
     against a 360px goal and is multiplied by unit() at run time. */
  var GOAL_REF = 360;

  /* Cap the buffer at 2x: past that the scene costs more to draw than it
     gains, and a 3x phone would allocate four times the pixels for nothing. */
  function ratio() {
    return Math.min(window.devicePixelRatio || 1, 2);
  }

  function fit() {
    var main = document.getElementById('tw-main');
    var canvas = document.querySelector('.cmp-fx');
    if (!main || !canvas) return;

    var r = main.getBoundingClientRect();
    if (!r.width || !r.height) return;

    var k = ratio();
    var w = Math.round(r.width * k);
    var h = Math.round(r.height * k);
    if (canvas.width === w && canvas.height === h) return;

    canvas.width = w;
    canvas.height = h;
    // Draw in CSS pixels; the buffer scale is handled once, here.
    canvas.getContext('2d').setTransform(k, 0, 0, k, 0, 0);
  }

  /* The width of the goal as rendered, over the width it was designed at. */
  function unit() {
    var g = document.querySelector('.cmp-goal');
    if (!g) return 1;
    var w = g.getBoundingClientRect().width;
    return w ? w / GOAL_REF : 1;
  }

  var raf = 0;
  function schedule() {
    if (raf) cancelAnimationFrame(raf);
    raf = requestAnimationFrame(function () { raf = 0; fit(); });
  }

  window.CMPStage = { fit: fit, unit: unit, ratio: ratio };


  /* ── the game ──────────────────────────────────────────────── */

  var stage, ball, keeper, msg, panels, anim, goal, dust, hit;
  var attempt = 0;
  var busy = false;
  var msgTimer = 0;
  var msgHideTimer = 0;

  /* Every timer shoot() starts, so reset() can cancel them. `busy` makes them
     unreachable along the normal path, but reset() is also called when the
     visitor closes the card — that is, from outside this state machine, in
     the middle of a sequence. */
  var timers = [];

  function later(fn, ms) {
    var id = setTimeout(function () {
      var i = timers.indexOf(id);
      if (i >= 0) timers.splice(i, 1);
      fn();
    }, ms);
    timers.push(id);
    return id;
  }

  function clearTimers() {
    timers.forEach(clearTimeout);
    timers.length = 0;
  }

  /* ── geometry helpers ─────────────────────────────────────── */

  function centre(el) {
    var r = el.getBoundingClientRect();
    return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
  }

  /* Which way the ball comes off the glove. A keeper diving to his left
     pushes it further left; a save down the middle is parried back at the
     taker, so it barely travels sideways. */
  var SAVE_SIDE = { tl: -1, bl: -1, tc: 0.45, bc: -0.45, tr: 1, br: 1 };

  /* How far along the flight the ball meets the glove. It stops in front of
     the line, not on it, because the keeper's hands are in front of the net. */
  var SAVE_AT = 0.88;

  /* The keeper commits before the ball arrives, as he would in a real
     penalty: he is reading the run-up, not the flight. */
  var DIVE_DELAY = 90;

  /* ── impact ─────────────────────────────────────── */

  /* Restart a one-shot CSS animation. Removing the class is not enough on its
     own -- the style has to be recomputed in between, which reading a layout
     property forces. Cheap enough here: a visitor fires it twice a visit. */
  function fx(el, vars) {
    el.classList.remove('is-live');
    void el.offsetWidth;
    if (vars) Object.keys(vars).forEach(function (k) { el.style.setProperty(k, vars[k]); });
    el.classList.add('is-live');
  }

  /* The strike point, as a share of the goal box, so the ring lands on the
     panel whatever size the goal renders at. */
  function mark(panel) {
    var g = goal.getBoundingClientRect();
    var r = panel.getBoundingClientRect();
    fx(hit, {
      '--hit-x': ((r.left + r.width / 2 - g.left) / g.width * 100).toFixed(1) + '%',
      '--hit-y': ((r.top + r.height / 2 - g.top) / g.height * 100).toFixed(1) + '%'
    });
  }

  /* ── messages ─────────────────────────────────────────────── */

  function say(text, ms) {
    clearTimeout(msgTimer);
    clearTimeout(msgHideTimer);
    /* Unhide before writing, not after. .cmp-msg is role="status": a hidden
       element is not in the accessibility tree, so a text change made while it
       is still hidden can go unannounced entirely. */
    msg.hidden = false;
    msg.textContent = text;
    CMPFx.next(function () { msg.classList.add('is-visible'); });
    msgTimer = setTimeout(function () {
      msg.classList.remove('is-visible');
      /* Held as well: clearTimeout(msgTimer) cannot reach a timer that timer
         started, so a second message inside the 260ms exit would be unhidden
         and then hidden again by the first message's tail. */
      msgHideTimer = setTimeout(function () { msg.hidden = true; }, 260);
    }, ms || 1600);
  }

  /* ── the two scripted shots ───────────────────────────────── */

  function shoot(panel) {
    if (busy) return;
    busy = true;
    attempt += 1;

    var cell = panel.dataset.cell;
    var scores = attempt >= 2;
    var T = CMPAnimator.TIMING;

    stage.dataset.state = 'shooting';
    panel.classList.add('is-armed');
    CMPAudio.play('kick', 0.9);
    TW.track('shot', { attempt: attempt, cell: cell, mult: panel.dataset.mult });

    var dive = scores ? CMPAnimator.WRONG_WAY[cell] : CMPAnimator.COVERS[cell];
    later(function () { anim.play(dive); }, DIVE_DELAY);

    // The plume and the jolt are the impact a still sprite cannot show. Which
    // frame carries that impact depends on the dive, so the animator is asked
    // rather than told: a high dive never lands, and its only contact with the
    // grass is the push-off. Nothing here is restated -- these numbers used to
    // be spelled out as `90 + 540 * 0.84`, so retuning the dive desynced the
    // dust.
    var impact = anim.impact(dive);
    later(function () {
      fx(dust, { '--dust-x': impact.x });
      CMPFx.shake(220, impact.force);
    }, DIVE_DELAY + T.duration * impact.at);

    if (scores) {
      CMPFx.shoot(ball, panel, { duration: 640 })
        .then(function (state) {
          mark(panel);
          CMPAudio.play('net', 0.8);
          CMPAudio.play('cheer', 0.7);
          CMPFx.netBulge(state.x, state.y, state.r * state.s);
          CMPFx.shake(320, 5);
          CMPFx.intoNet(state);
          stage.dataset.state = 'celebrate';
          // A beat, then the confetti. 110 bits out of the strike point cover
          // the net bulge completely, and the bulge is over inside 520ms --
          // fired together, the net was never seen at all. The gap also reads
          // as a crowd taking a moment to realise.
          later(function () {
            CMPFx.burst(centre(panel));
            // With the burst, not with the goal: the 180ms gap is the whole
            // point of the delay, and a pop on the goal would close it.
            CMPAudio.play('confetti', 0.55);
          }, 180);
          // He is still in the air when the ball crosses the line -- the dive
          // runs to DIVE_DELAY + T.duration = 650ms and the ball arrives at
          // 640. Let him land before he reacts to it.
          later(function () {
            anim.react('beaten', { hold: 1200 });
            // Quiet: this one plays under net, cheer and the confetti, and is
            // meant to be felt rather than picked out. See tools/sfx.py.
            CMPAudio.play('slump', 0.5);
          }, 320);
          say(TW.t('msg.goal'), 1400);
          return wait(1500);
        })
        .then(function () {
          panel.classList.remove('is-armed');
          stage.dataset.state = 'form';
          busy = false;
          /* The two lines the whole integration comes down to. */
          TW.track('game_win', { mechanic: 'penalty', cell: cell });
          TW.openForm();
        })
        .catch(recover);
      return;
    }

    CMPFx.shoot(ball, panel, { duration: 620, stopAt: SAVE_AT })
      .then(function (state) {
        mark(panel);
        CMPAudio.play('save', 0.9);
        CMPFx.shake(260, 4);
        return CMPFx.deflect(state, SAVE_SIDE[cell]);
      })
      .then(function () {
        say(TW.t('msg.miss'), 1800);
        panel.classList.remove('is-armed');
        // He gets to enjoy it. react() stands him back up on its own once the
        // hold is over, so nothing else has to call reset here.
        anim.react('cheer', { hold: 900 });
        return CMPFx.home(ball);
      })
      .then(function () {
        stage.dataset.state = 'idle';
        busy = false;
      })
      .catch(recover);
  }

  /* Nothing above is allowed to leave the page locked. `busy` is the only
     latch, so an exception inside a .then would strand it at true with no
     trace at all: every panel dead, nothing in the console to say why. */
  function recover(err) {
    if (window.console && console.error) {
      console.error('[tw-penalty] the shot sequence failed', err);
    }
    panels.forEach(function (p) { p.classList.remove('is-armed'); });
    busy = false;
    stage.dataset.state = 'idle';
  }

  function wait(ms) {
    return new Promise(function (r) { later(r, ms); });
  }

  /* ── back to the start ────────────────────────────────────── */

  /* Runs when the registration card closes — TW.on('formclose') in init().
     #tw-main is still carrying data-state="form", which holds .cmp-panel and
     .cmp-ball at pointer-events:none, and `attempt` is still past the end of
     the scripted sequence — so without this the page is dead, and clearing
     only the state would make the next shot score instantly. Both have to be
     undone together. */
  function reset() {
    clearTimers();
    clearTimeout(msgTimer);
    clearTimeout(msgHideTimer);
    msg.classList.remove('is-visible');
    msg.hidden = true;

    panels.forEach(function (p) { p.classList.remove('is-armed'); });
    dust.classList.remove('is-live');
    hit.classList.remove('is-live');

    attempt = 0;
    busy = false;

    anim.reset();
    stage.dataset.state = 'idle';
    return CMPFx.home(ball);
  }

  /* ── boot ─────────────────────────────────────────────────── */

  /* Six buttons whose whole text is a multiplier, and three of those repeat:
     "×12" twice, "×3" twice, "×2" twice. A pointer user tells them apart by
     where they are; a screen reader user had six buttons and three names. The
     position comes from the campaign's string table, the multiplier from
     data-mult, so the numbers are still written once. Re-runs on a language
     change. */
  function labelPanels() {
    panels.forEach(function (p) {
      p.setAttribute('aria-label',
        TW.t('cell.' + p.dataset.cell) + ', ×' + p.dataset.mult);
    });
  }

  function init() {
    stage  = document.getElementById('tw-main');
    ball   = document.querySelector('.cmp-ball');
    keeper = document.querySelector('.cmp-keeper');
    goal   = document.querySelector('.cmp-goal');
    dust   = document.querySelector('.cmp-dust');
    hit    = document.querySelector('.cmp-hit');
    msg    = document.querySelector('.cmp-msg');
    panels = Array.prototype.slice.call(document.querySelectorAll('.cmp-panel'));

    fit();
    CMPFx.init();
    anim = new CMPAnimator.PoseAnimator(keeper,
                                        document.querySelector('.cmp-keeper-shadow'));
    /* 283 kB of dive sprites that nothing needs until the first shot. The one
       pose on screen, keeper-idle, comes from campaign/main.css and is already
       loading. Warm the rest when the browser is idle, or on the first
       gesture, whichever comes first — a shot cannot start before that
       gesture, so the sprites are never late. */
    var warmed = false;
    var warm = function () {
      if (warmed) return;
      warmed = true;
      anim.preload();
    };
    if (window.requestIdleCallback) window.requestIdleCallback(warm, { timeout: 3000 });
    else setTimeout(warm, 1200);
    window.addEventListener('pointerdown', warm, { once: true });

    keeper.classList.add('is-idling');
    ball.classList.add('is-bobbing');
    stage.dataset.state = 'idle';

    labelPanels();
    TW.on('lang', labelPanels);

    panels.forEach(function (p) {
      p.addEventListener('click', function () { shoot(p); });
    });

    // Tapping the ball shoots at a panel picked at random. The outcome is
    // still decided by the attempt index, exactly as for a deliberate aim —
    // the random pick only chooses which dive and trajectory play.
    ball.addEventListener('click', function () {
      shoot(panels[Math.floor(Math.random() * panels.length)]);
    });

    /* The card closing is the only way back to a live pitch. */
    TW.on('formclose', reset);

    /* The shell renders the mute button because campaign.js sets header.mute,
       and deliberately does not wire it: the audio belongs to the mechanic,
       so the handler does too. */
    var muteBtn = document.querySelector('.tw-mute');
    if (muteBtn) {
      muteBtn.setAttribute('aria-pressed', String(CMPAudio.isMuted()));
      muteBtn.addEventListener('click', function () { CMPAudio.toggle(); });
    }

    // Audio can only start inside a user gesture.
    var unlock = function () {
      CMPAudio.unlock();
      window.removeEventListener('pointerdown', unlock);
      window.removeEventListener('keydown', unlock);
    };
    window.addEventListener('pointerdown', unlock);
    window.addEventListener('keydown', unlock);

    /* The canvas is sized against #tw-main, whose height changes when the two
       bars do: a soft keyboard, a rotation, or the landscape rule in
       css/stage.css that drops the footer. */
    window.addEventListener('resize', schedule);
    window.addEventListener('orientationchange', schedule);
    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', schedule);
      window.visualViewport.addEventListener('scroll', schedule);
    }
  }

  window.CMPGame = {
    reset: reset,
    attempt: function () { return attempt; }
  };

  TW.ready(init);
}());
