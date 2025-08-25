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