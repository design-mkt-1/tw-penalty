"""The mechanic's own browser check, run by tools/smoke.py after its nine.

tools/smoke.py proves the SHELL works: the bars mounted, the dialog opens from
TW.openForm(), no dead link, no untranslated key. It cannot know what a
campaign's win condition is, so it calls this file's check() once per viewport
and language and lets it assert the rest.

What is asserted here is the whole point of the page, and the one sequence that
has broken twice in this landing's history:

  1. the first shot is saved and the page comes back to `idle` on its own --
     the failure mode is `busy` left latched, which kills every panel silently;
  2. the second shot scores and opens the registration card WITHOUT this file
     touching the dialog;
  3. the speaker in the header actually mutes, and the choice survives a
     reload -- js/shell.js renders that button and campaigns used to wire it,
     so a landing could ship one that did nothing;
  4. closing the card resets the pitch -- attempt back to 0 and the state off
     `form`, which is what re-enables the panels. Clearing one without the
     other is the exact bug the old js/form.js -> TWGame.reset() seam existed
     to prevent.

An assertion here fails the run with a traceback naming the viewport and the
language, which is enough to find it.
"""


def check(page, viewport, lang):
    tag = f"[{viewport} {lang}]"

    # The mechanic booted and the pitch is live.
    assert page.eval_on_selector("#tw-main", "el => el.dataset.state") == "idle", \
        f"{tag} the pitch did not start idle"
    assert page.locator(".cmp-panel").count() == 6, f"{tag} the goal has no six panels"

    # 1. First shot: always saved, and the page has to come back on its own.
    page.click(".cmp-panel[data-cell='bl']")
    page.wait_for_function(
        "() => document.getElementById('tw-main').dataset.state === 'idle'",
        timeout=8000)
    assert page.evaluate("CMPGame.attempt()") == 1, f"{tag} the first shot did not count"
    assert not page.eval_on_selector("#tw-signup", "el => el.open"), \
        f"{tag} the saved shot opened the card"

    # The speaker. It only renders when campaign.js sets header.mute AND has
    # clips, so its presence is also the proof that the sounds map arrived.
    mute = page.locator(".tw-mute")
    assert mute.count() == 1, f"{tag} the header has no mute button"
    assert page.evaluate("TW.muted()") is False, f"{tag} the page starts muted"
    mute.click()
    assert page.evaluate("TW.muted()") is True, f"{tag} the speaker did not mute"
    assert mute.get_attribute("aria-pressed") == "true", f"{tag} aria-pressed did not follow"
    page.reload()
    page.wait_for_timeout(400)
    assert page.evaluate("TW.muted()") is True, f"{tag} mute did not survive a reload"
    # Leave the page as it was found: the next viewport gets a fresh context,
    # but the mute flag lives in localStorage, which is per origin.
    page.evaluate("TWAudio.setMuted(false)")
    page.reload()
    page.wait_for_timeout(400)

    # The reload put the board back, so the two shots start again from zero.
    page.click(".cmp-panel[data-cell='bl']")
    page.wait_for_function(
        "() => document.getElementById('tw-main').dataset.state === 'idle'",
        timeout=8000)

    # 2. Second shot: scores, and the card opens by itself.
    page.click(".cmp-panel[data-cell='tr']")
    page.wait_for_function("() => document.getElementById('tw-signup').open",
                           timeout=10000)
    assert page.eval_on_selector("#tw-main", "el => el.dataset.state") == "form", \
        f"{tag} the stage did not go to the form state"

    # 3. Closing the card puts the pitch back. Escape, because that is the path
    #    that skips every button this file could have clicked instead.
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)
    assert page.evaluate("CMPGame.attempt()") == 0, f"{tag} the attempt count did not reset"
    assert page.eval_on_selector("#tw-main", "el => el.dataset.state") == "idle", \
        f"{tag} the pitch stayed locked after the card closed"
