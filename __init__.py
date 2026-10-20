"""Active Review Timer: a simple always-on Pomodoro that only counts real review time.

- Counts while you're reviewing; any key, click, scroll or new card is activity.
- Pauses after `idle_seconds` of no activity.
- Resets after `reset_after_minutes` without review activity.
- Reminds you to break at `pomodoro_minutes`.
- "Break" button switches to a break timer; "Resume" (or revealing a card) ends it
  and starts a fresh review session.
"""
import time

from aqt import mw, gui_hooks
from aqt.qt import QEvent, QObject, QTimer
from aqt.utils import tooltip

_cfg = mw.addonManager.getConfig(__name__) or {}
IDLE = float(_cfg.get("idle_seconds", 45))
RESET = float(_cfg.get("reset_after_minutes", 5)) * 60
POMO = float(_cfg.get("pomodoro_minutes", 25)) * 60
BREAK = float(_cfg.get("break_minutes", 5)) * 60

_s = {
    "active": 0.0,
    "last": 0.0,
    "tick": time.time(),
    "alerted": False,
    "break_start": None,  # wall time when break began, None if not on break
    "break_alerted": False,
}


def _new_session():
    _s["active"] = 0.0
    _s["alerted"] = False


def _touch(*_args):
    if mw.state != "review" or _s["break_start"] is not None:
        return
    now = time.time()
    if now - _s["last"] > RESET:
        _new_session()
    _s["last"] = now


def _start_break():
    _s["break_start"] = time.time()
    _s["break_alerted"] = False
    _render()


def _end_break():
    if _s["break_start"] is None:
        return
    _s["break_start"] = None
    _new_session()
    _s["last"] = time.time()
    _render()


def _fmt(sec):
    sec = int(max(sec, 0))
    return f"{sec // 60}:{sec % 60:02d}"


_BTN = (
    "margin-left:8px;font:600 12px -apple-system,Helvetica,sans-serif;"
    "padding:2px 8px;border-radius:8px;border:1px solid rgba(128,128,128,.4);"
    "background:rgba(128,128,128,.15);color:inherit;cursor:pointer"
)


def _render(idle=None):
    web = getattr(mw.reviewer, "web", None)
    if not web or mw.state != "review":
        return
    now = time.time()
    if _s["break_start"] is not None:
        b = now - _s["break_start"]
        label = f"\u2615 Break {_fmt(b)}"
        color = "#2e9e44" if b >= BREAK > 0 else "#e0a030"
        btn = ("Resume", "art_resume")
    else:
        if idle is None:
            idle = (now - _s["last"]) > IDLE
        label = f"\u23f1 {_fmt(_s['active'])}" + (" \u00b7 paused" if idle else "")
        color = "#2e9e44" if _s["alerted"] else ("#999" if idle else "inherit")
        btn = ("Break", "art_break")
    js = (
        "(function(){var e=document.getElementById('art-timer');"
        "if(!e){e=document.createElement('div');e.id='art-timer';"
        "e.style.cssText='position:fixed;z-index:99999;white-space:nowrap;"
        "left:50%;bottom:8px;transform:translateX(-50%);display:flex;align-items:center;"
        "font:600 14px -apple-system,Helvetica,sans-serif;padding:4px 6px 4px 10px;"
        "border-radius:10px;background:rgba(128,128,128,.18)';"
        "var t=document.createElement('span');t.id='art-timer-t';e.appendChild(t);"
        f"var b=document.createElement('button');b.id='art-timer-b';b.style.cssText={_BTN!r};"
        "b.onclick=function(ev){ev.stopPropagation();pycmd(b.dataset.cmd);b.blur();};"
        "e.appendChild(b);document.body.appendChild(e);}"
        f"var t=document.getElementById('art-timer-t');t.textContent={label!r};t.style.color={color!r};"
        f"var b=document.getElementById('art-timer-b');b.textContent={btn[0]!r};b.dataset.cmd={btn[1]!r};"
        "})();"
    )
    web.eval(js)


def _rerender_soon(*_args):
    QTimer.singleShot(60, _render)


def _on_tick():
    now = time.time()
    dt = now - _s["tick"]
    _s["tick"] = now
    if _s["break_start"] is not None:
        if BREAK > 0 and not _s["break_alerted"] and now - _s["break_start"] >= BREAK:
            _s["break_alerted"] = True
            tooltip(f"\u2615 {int(BREAK // 60)} min break done - back to it!", period=8000)
        _render()
        return
    if mw.state != "review":
        return
    idle = (now - _s["last"]) > IDLE
    if not idle:
        _s["active"] += dt
        if POMO > 0 and not _s["alerted"] and _s["active"] >= POMO:
            _s["alerted"] = True
            tooltip(f"\U0001f345 {int(POMO // 60)} min of real review done - take a break!", period=8000)
    _render(idle)


def _on_js(handled, message, context):
    if message == "art_break":
        _start_break()
        return (True, None)
    if message == "art_resume":
        _end_break()
        return (True, None)
    return handled


def _on_card_shown(*_args):
    # Revealing a card while on break means you're back: end the break.
    if _s["break_start"] is not None and mw.state == "review":
        _end_break()
    _touch()
    _rerender_soon()


class _ActivityFilter(QObject):
    _types = (QEvent.Type.KeyPress, QEvent.Type.MouseButtonPress, QEvent.Type.Wheel)

    def eventFilter(self, obj, event):
        if event.type() in self._types:
            _touch()
        return False


def _on_state(new_state, _old_state):
    if new_state == "review":
        _touch()


_filter = _ActivityFilter(mw)
mw.app.installEventFilter(_filter)
_timer = QTimer(mw)
_timer.timeout.connect(_on_tick)
_timer.start(1000)

gui_hooks.state_did_change.append(_on_state)
gui_hooks.webview_did_receive_js_message.append(_on_js)
gui_hooks.reviewer_did_show_answer.append(_on_card_shown)
gui_hooks.reviewer_did_show_question.append(_on_card_shown)
