# Active Review Timer for Anki

An always-on Pomodoro timer for Anki that only counts time you're **actually reviewing**.

- Counts while you review; any key press, click, scroll or new card counts as activity.
- Pauses automatically after 45 s of inactivity, so zoning out on a card doesn't inflate your time.
- Resets after 5 min away from reviews, so every session starts fresh.
- Reminds you to take a break after 25 min of real review.
- **Break** button switches to a break timer; **Resume** (or revealing a card) starts a new session.

The timer sits at the bottom of the review screen, just above the due counts.

## Install
- From AnkiWeb: Tools → Add-ons → Get Add-ons, and paste the add-on code.
- Manually: copy this folder into your Anki `addons21` folder and restart Anki.

## Settings
Tools → Add-ons → Active Review Timer → Config:

| Setting | Default | Meaning |
|---|---|---|
| `idle_seconds` | 45 | Stop counting after this many seconds with no activity |
| `reset_after_minutes` | 5 | Reset to 0:00 after this long without reviewing |
| `pomodoro_minutes` | 25 | Break reminder after this much active review (0 = off) |
| `break_minutes` | 5 | Break reminder length (0 = off) |

## License
MIT
