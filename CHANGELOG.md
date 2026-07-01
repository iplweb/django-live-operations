# Changelog

All notable changes to this project are documented here. The format is based
on [Keep a Changelog](https://keepachangelog.com/) and this project adheres to
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Initial release of **django-live-operations**.
- `LiveOperation` abstract model + ergonomic `run(self, p)` API.
- `Progress` with pluggable backends: `WebProgress` (WebSocket + HTML
  out-of-band swaps, no reload, no polling) and `TextProgress` (tqdm/CLI).
- Live progress API: `status`, `percent`, `track` (tqdm-style), `log`,
  `stage` (multi-stage stepper), `result`, `error`, `check_cancelled`,
  `chain_to` (chain operations without reload); web-only `swap`/`html`.
- Transport via `django-channels-broadcast` (`addMessage` OOB-swap plugin);
  HTML in a JSON envelope; snapshot-on-connect (terminal state = source of
  truth); subscription tokens binding a user to one operation channel.
- Reusable class-based views + `{% live_operation %}` templatetag +
  auto-derived templates/channel names.
- `run_liveop` management command (text/CLI mode).
- Example demo project with one-command Docker stack (`make demo`).
- Full MkDocs documentation and a three-tier test suite (consumer unit,
  `Progress` unit, worker→Redis round-trip via testcontainers).
