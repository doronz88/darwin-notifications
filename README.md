# darwin-notifications

A tiny, dependency‑light macOS Notification Center helper that posts banners from Python without PyObjC, using ctypes +
the Objective‑C runtime. Ships a simple CLI implemented with Typer and a small Python API you can call from your
scripts.

> ⚠️ Apple deprecated NSUserNotification in favor of UserNotifications.framework. For quick, fire‑and‑forget banners
> from non‑sandboxed tools, NSUserNotification still works on current macOS releases. This package sticks to ctypes on
> purpose—no extra bridge layers.
>

## Features

- Pure ctypes: no `PyObjC` required
- One‑liner CLI to send a notification banner
- Minimal Python API for programmatic use
- Works from Terminal/iTerm (GUI session)
- Optional default sound toggle

## Install

With pip:

```shell
python3 -m pip install darwin_notifications
```

With uv:

```shell
uv pip install darwin_notifications
```

## Quick Start

### CLI

```shell
# Basic
notify --title "Build finished"

# With subtitle and body
notify -t "Hello" -s "From darwin_notifications" -m "Deployed successfully" --sound
```

Run `--help` for all options:

```shell
notify --help
```

### Python API

```python
from darwin_notifications.api import notify

notify(
    title="Hello from Python",
    subtitle="Optional subtitle",
    text="Optional informative text",
    sound=True,
)
```

## Troubleshooting

- No banner appears at all
    - Check that Notifications are enabled for the app delivering the toast (often Python, python3, or your terminal
      app) in `System Settings → Notifications`.
    - Make sure the alert style is set to Banners or Alerts, not None.
    - Run in a GUI session (not via SSH or headless server).

- Notification appears only in History, not as a pop‑up
    - Make sure Focus / Do Not Disturb is off.

- Notifications vanish when docked / using external monitor
    - By default, macOS mutes banners when mirroring or when a dock (e.g., DisplayLink) is active.
        - **Fix:** In `System Settings → Notifications`, scroll to the bottom and enable: `Allow notifications when
          mirroring or sharing the display`.
    - Also check which display has the menu bar: banners show on the primary menu bar display.

- Still not working?
    - Try changing alert style to Alerts for visibility.
    - Confirm Focus automations aren’t muting notifications when docking/screen‑sharing.