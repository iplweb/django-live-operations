# Design: Live operations list

Status: **proposed — awaiting review**
Date: 2026-07-03

## Goal

Make the operations list page (`liveops/templates/liveops/operation_list.html`)
live instead of a static server render:

1. New operations appear without a full reload.
2. A running operation's row updates (its status flips to Completed / Failed
   when it finishes).
3. No work happens while everything is idle (all operations terminal, nothing
   new) — the page stays silent.
4. The whole behaviour is optional (opt-out), defaulting to on.
5. The list stays ordered newest-first (already the case via the model's
   `ordering = ["-created_on"]`).

## Chosen approach: B — WebSocket event-driven refresh

Reuse the existing WebSocket stack. `channels_broadcast` already:
- subscribes every authenticated socket to a **per-user channel**
  (`_audience_channels` yields `get_channel_name_for_user(user)`), and
- exposes a send helper to that channel.

So the framework can push a lightweight "your operations changed" signal to the
owner's channel at the moments that matter, and the list page re-fetches itself
when it receives one. Pure event-driven: instant on change, silent when idle,
no polling loop to start/stop.

Rejected alternatives:
- **A (conditional polling):** simplest, but a new op created while the page is
  idle wouldn't appear until reload, and it needs a start/stop poll loop.
- **C (hybrid WS + polling):** only needed if the list must show a
  continuously-ticking progress % per row. A list needs status, not a live bar,
  so this is out of scope (YAGNI).

## Components

### 1. Per-user "list changed" signal (package)

New helper in `liveops`:

```python
# liveops/notifications.py (new)
def notify_list_changed(operation) -> None:
    """Ping the operation owner's channel so any open list page refreshes."""
    from channels_broadcast.core import _send, get_channel_name_for_user
    _send(get_channel_name_for_user(operation.owner),
          {"type": "chat_message", "liveop_list_changed": True})
```

Guarded by the opt-out setting (below) and by a best-effort try/except so a
missing channel layer never breaks the operation.

Called at exactly three transition points (coarse — not per progress tick):
- **created / enqueued** — in `LiveOperation.enqueue()` (runs in the request).
- **started** — in `runner._task_run`, right after `started_on` is saved.
- **finished** (any terminal outcome) — in `runner._task_run`'s `finally`,
  next to `notify_finished()`.

That is 2–3 signals per operation lifecycle, regardless of progress volume.

### 2. List page connects the WS and refreshes (package + demo)

`operation_list.html` gains (only when the opt-out setting is on):
- the `channels_broadcast` client + a tiny handler that, on a
  `liveop_list_changed` message, re-fetches the table via htmx and swaps it in
  place. The authenticated socket is auto-subscribed to the user's channel — no
  per-operation token needed.

The table is wrapped in `#liveop-list` so htmx can target/swap just that
fragment.

### 3. List view returns a fragment on htmx requests (package)

`LiveOperationListView` renders the full page normally, but when the request
carries the `HX-Request` header it returns only the `#liveop-list` table
fragment (via a template `{% if %}` or a separate partial). This keeps the
refresh cheap and avoids nesting the base template.

### 4. Opt-out (package)

New setting key, default on:

```python
LIVEOPS = { "LIST_LIVE": True }   # set False to disable the live list
```

`get_setting("LIST_LIVE")` defaults to `True`. When False:
- `notify_list_changed` is a no-op, and
- the list template omits the WS client/handler (static render).

## Data flow

```
create/enqueue ─┐
start ──────────┼─► notify_list_changed(op) ─► _send(user channel,
finish ─────────┘                                {liveop_list_changed})
                                                        │  (WebSocket)
                                                        ▼
                          list page JS ── on liveop_list_changed ──►
                          htmx GET (HX-Request) ─► #liveop-list fragment
                          ─► swap table in place
```

## Sorting

Newest-first only, which the model already guarantees
(`ordering = ["-created_on"]`). No interactive column sorting in this iteration
(can be a later add). The design note records this as a deliberate scope call.

## Testing

- **Unit:** `notify_list_changed` sends the right payload to the owner's channel
  (FakeChannelLayer), and is a no-op when `LIST_LIVE=False` or no channel layer.
- **Unit:** `_task_run` emits a list-changed signal on start and finish;
  `enqueue()` emits one on create.
- **View:** the list view returns the full page normally and only the
  `#liveop-list` fragment under an `HX-Request` header.
- **End-to-end (Docker):** with two browser tabs, creating an operation in one
  makes it appear in the other's list, and its row flips to Completed when the
  worker finishes — with no polling traffic while idle.

## Open decisions (defaulted; change on review)

These were my recommended picks (chosen while you were away):
- **Mechanism:** B (WebSocket event-driven). — vs A (polling) / C (hybrid).
- **Sorting:** newest-first only. — vs adding clickable column sort.
- **Opt-out:** a single `LIVEOPS["LIST_LIVE"]` setting. — vs a per-user UI
  toggle, or both.
