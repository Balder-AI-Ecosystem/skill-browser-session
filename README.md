# skill-browser-session

Standalone browser session skill repo for observed and interactive browser automation.

## Responsibility

This repo owns the browser-session boundary for observation, typing, clicking, and form interaction. Core should route interactive browser work here through the shared skill contract.

Capabilities declared in `skill.yaml`:

- `browser_session.observe_page`
- `browser_session.type_text`
- `browser_session.click_text`
- `browser_session.fill_field`
- `browser_session.fill_form`
- `browser_session.follow_link`

## Contract

- Mode: `local_plugin`
- Entrypoint: `src.skill_browser_session.main:Skill`
- Healthcheck: `src.skill_browser_session.main:healthcheck`
- Core API compatibility: `>=1.0,<2.0`

## Permissions

- `external_actions: true`
- `internet_access: true`
- `file_write: false`
- `read_memory: false`
- `write_memory: false`

## Integration rule

Core integration must stay at the skill boundary defined by `skill.yaml`. Core should not bypass this repo and call internal browser-session adapters directly.
## Verification

- Recommended command: `python -m pytest -q`
- Current minimum coverage: manifest and contract smoke tests inside `tests/`

## Implementation status

This repo is still a transitional bridge around existing browser-session adapters. The bridge is acceptable for now because the capability boundary and risk controls already live at the skill contract layer.

Current dependency note: the runtime path still resolves the core repo location, so implementation independence is not complete yet.
