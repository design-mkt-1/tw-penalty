/* tw-penalty — the campaign's own configuration.

   This landing is a tw-lp-template clone: the header, the footer and the
   registration card are that repo's files, unmodified, and this file is where
   the campaign speaks to them. The mechanic — the goal, the keeper, the ball,
   the effects canvas — is js/game.js, js/animator.js, js/fx.js, js/stage.js
   and css/game.css, and it is the only part of this repo that is this
   landing's own.

   Never edit the shared files. `python tools/drift.py` fails if one moves. A
   change one of them genuinely needs is made in tw-lp-template, SHARED.lock
   is bumped there, and the change is pulled down.

   The template was distilled OUT of this landing in the first place, which is
   why adopting it back changed no copy: 35 of its 35 shared strings were
   already word for word what this page said. The two that were not were
   `promo.pct` and `promo.amount`, which hardcoded 225% and 15000 UAH — those
   figures now live once, in `offer` below.
   ─────────────────────────────────────────────────────────────────────── */

window.TW_CAMPAIGN = {

  id: 'tw-penalty',

  /* ── The offer ────────────────────────────────────────────────
     NUMBERS ONLY; every locale writes the sentence around them and
     interpolates {percent} {amount} {currency} {spins}.

     No `hero` key: with a percent present the shell leads with it, which is
     what this landing has always done. */
  offer: {
    percent:  '225%',
    amount:   '15000',
    currency: 'UAH',
    spins:    '',
    code:     'PENALTY225'   // what the platform is told; payload field `bonus`
  },

  /* ── Where the buttons go ─────────────────────────────────────
     '' leaves the anchor with NO href, so it is not a link at all: no tab
     stop, nothing announced, nothing to click. Never write '#'.

     terms and privacy BLOCK GO-LIVE — the card collects an 18+ consent, and
     consent text with no documents behind it is a compliance problem. These
     five were HOME_URL / LOGIN_URL / TERMS_URL / PRIVACY_URL in js/main.js
     and DESTINATION in js/form.js until the shell became shared code; the
     fifth being in a different file from the other four is exactly the kind
     of thing that gets forgotten at handover. */
  links: {
    home:    '',
    login:   '',
    terms:   '',
    privacy: '',
    cta:     ''
  },

  /* Appended to every outbound link and copied onto the form payload. */
  params: {
    // utm_source:   'facebook',
    // utm_medium:   'cpc',
    // utm_campaign: 'penalty'
  },

  /* Query parameters on THIS page's URL that ride through to the outbound
     click — how an affiliate click id survives the landing. This landing had
     no passthrough at all before the port: an id on the landing URL was lost
     here and nowhere else. */
  passthrough: ['click_id', 'sub1', 'sub2', 'gclid', 'fbclid', 'ttclid'],

  /* Both empty means not one third-party request. Setting either also needs
     the CSP <meta> in index.html swapped for the analytics one. */
  analytics: {
    gtmId:       '',
    metaPixelId: '',
    debug:       false
  },

  /* ── The registration form ────────────────────────────────────
     endpoint '' means nothing is sent: the validated payload goes to
     console.info and, with demoDone true, the confirmation screen is walked
     anyway. The payload carries the password, so `endpoint` must be the
     operator's own TLS endpoint and nowhere else. */
  form: {
    endpoint:     '',
    onRegister:   null,
    hiddenFields: { landing_id: 'tw-penalty' },
    demoDone:     true,
    dialCode:     '+380',
    dialFlag:     'assets/img/icons/flag-ua.svg',
    phoneDigits:  9,
    passwordMin:  8
  },

  /* ── Languages ────────────────────────────────────────────────
     One HTML file, all three languages, switched from the header menu and
     persisted in localStorage under 'tw-lang'. languageUrls stays empty:
     that mode is for a landing served as three separate files, which this
     one is not. */
  languages: ['ua', 'ru', 'en'],
  languageUrls: {},

  /* ── Brand and chrome ─────────────────────────────────────────
     The bar and the footer are the shell's now. Until the port this landing
     carried its own: a 63px bar with a 172px logo welded into css/game.css,
     and a footer in css/footer.css — against the template's 52/64px bar and
     a footer 6px shorter. Three Top Win pages, three sets of numbers. */
  brand: {
    logo:       'assets/img/logo-topwin.svg',
    logoAlt:    'Top Win',
    themeColor: '#040412',
    payments:   ['visa', 'mastercard', 'tether', 'bitcoin']
  },
  header: { show: true, mute: true, lang: true },
  footer: { show: true },

  /* ── Sound ────────────────────────────────────────────────────
     The seven clips the mechanic plays, by name. js/audio.js owns everything
     else: nothing loads until the visitor's first gesture, the mute state
     persists, and a clip that fails to load simply never plays. The speaker
     in the bar needs both header.mute above and a non-empty map here.

     tools/sfx.py regenerates save.mp3 and slump.mp3; the rest are the
     originals. */
  sounds: {
    kick:     'assets/audio/kick.mp3',
    save:     'assets/audio/save.mp3',
    net:      'assets/audio/net.mp3',
    cheer:    'assets/audio/cheer.mp3',
    whistle:  'assets/audio/whistle.mp3',
    confetti: 'assets/audio/confetti.mp3',
    slump:    'assets/audio/slump.mp3'
  },

  /* ── Campaign copy ────────────────────────────────────────────
     ONLY what this campaign owns: the page title, the tagline over the goal,
     the six panel labels, the ball's accessible name and the two messages the
     game shows between shots. Everything the header, the footer and the card
     say is in js/strings.js and is the same in every Top Win landing.

     \n is a real line break — js/i18n.js splits on it, and the markup carries
     no <br>. */
  strings: {
    ua: {
      'title':      'Top Win — Заб’єш пенальті та виграєш!',
      'tagline':    'Заб’єш пенальті\nта виграєш!',
      'goal.aim':   'Оберіть, куди бити',
      'ball.shoot': 'Удар у випадкову точку',
      'cell.tl':    'Угорі ліворуч',
      'cell.tc':    'Угорі по центру',
      'cell.tr':    'Угорі праворуч',
      'cell.bl':    'Унизу ліворуч',
      'cell.bc':    'Унизу по центру',
      'cell.br':    'Унизу праворуч',
      'msg.miss':   'Так близько! Ще спроба',
      'msg.goal':   'ГОЛ!'
    },
    ru: {
      'title':      'Top Win — Забей пенальти и выиграй!',
      'tagline':    'Забей пенальти\nи выиграй!',
      'goal.aim':   'Выберите, куда бить',
      'ball.shoot': 'Удар в случайную точку',
      'cell.tl':    'Вверху слева',
      'cell.tc':    'Вверху по центру',
      'cell.tr':    'Вверху справа',
      'cell.bl':    'Внизу слева',
      'cell.bc':    'Внизу по центру',
      'cell.br':    'Внизу справа',
      'msg.miss':   'Так близко! Ещё попытка',
      'msg.goal':   'ГОЛ!'
    },
    en: {
      'title':      'Top Win — Score the penalty and win!',
      'tagline':    'Score the penalty\nand win!',
      'goal.aim':   'Choose where to shoot',
      'ball.shoot': 'Shoot at a random spot',
      'cell.tl':    'Top left',
      'cell.tc':    'Top centre',
      'cell.tr':    'Top right',
      'cell.bl':    'Bottom left',
      'cell.bc':    'Bottom centre',
      'cell.br':    'Bottom right',
      'msg.miss':   'So close! One more try',
      'msg.goal':   'GOAL!'
    }
  }
};
