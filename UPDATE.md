# UPDATE PLAN — skill-browser-session

> Audit date: 2026-04-21 | Grade: **B** | Priority: Medium

---

## Vấn đề tìm thấy

### 1. Schemas chưa khai báo properties (CRITICAL)
Tất cả 6 capabilities đều dùng `input_schema: {type: object}` và `output_schema: {type: object}` — không có `properties`, `required`, hay `additionalProperties: false`.

Từ implementation thực tế, các fields đang được dùng:
- Input: `target`, `dry_run`, `confirmed`, `confirmation_token`, `policy_approved`, `timeout_seconds`
- Output hiện tại chưa được schema hóa

### 2. Test coverage tối thiểu
Chỉ có `test_skill_manifest_exists.py` — kiểm tra file tồn tại.  
Không có:
- Test `execute()` với mock `BrowserSessionAdapter`
- Test error path (adapter unavailable, timeout)
- Test confirmation flow (`confirmation_required: true`)

### 3. Dependencies không được khai báo
`pyproject.toml` chỉ có `setuptools` — không khai báo rõ dependency vào core ecosystem.

---

## Fix cần làm

### Fix 1 — Cập nhật input_schema cho từng capability

```yaml
# browser_session.observe_page
input_schema:
  type: object
  properties:
    target:
      type: string
      description: "URL or window title to observe. Omit to use current active window."
    timeout_seconds:
      type: integer
      default: 30
  additionalProperties: false
output_schema:
  type: object
  properties:
    status:
      type: string
      enum: [ok, error, timeout]
    page_title:
      type: string
    page_url:
      type: string
    visible_text:
      type: string
    screenshot_path:
      type: ["string", "null"]
  required: [status]

# browser_session.type_text / click_text / fill_field (confirmation_required: true)
input_schema:
  type: object
  required: [target]
  properties:
    target:
      type: string
      description: "Text to type, or selector/text to click/fill"
    dry_run:
      type: boolean
      default: false
    confirmed:
      type: boolean
      default: false
    confirmation_token:
      type: ["string", "null"]
    policy_approved:
      type: boolean
      default: false
    timeout_seconds:
      type: integer
      default: 30
  additionalProperties: false

# browser_session.fill_form
input_schema:
  type: object
  required: [fields]
  properties:
    fields:
      type: object
      description: "Mapping of field label/selector to value"
    dry_run:
      type: boolean
      default: false
    confirmed:
      type: boolean
      default: false
    confirmation_token:
      type: ["string", "null"]
    policy_approved:
      type: boolean
      default: false
  additionalProperties: false

# browser_session.follow_link
input_schema:
  type: object
  required: [target]
  properties:
    target:
      type: string
      description: "Link text or URL to follow"
    dry_run:
      type: boolean
      default: false
    confirmed:
      type: boolean
      default: false
    confirmation_token:
      type: ["string", "null"]
  additionalProperties: false
```

### Fix 2 — Thêm functional tests

```python
# tests/test_execute.py
from unittest.mock import MagicMock, patch
from src.skill_browser_session.main import Skill

def make_request(capability_id, **params):
    req = MagicMock()
    req.capability_id = capability_id
    req.parameters = params
    return req

def test_observe_page_returns_ok():
    skill = Skill()
    with patch.object(skill, '_adapter') as mock_adapter:
        mock_adapter.observe_page.return_value = {"status": "ok", "page_title": "Test"}
        result = skill.execute(make_request("browser_session.observe_page", target="https://example.com"))
    assert result["status"] == "ok"

def test_type_text_dry_run_no_side_effect():
    skill = Skill()
    result = skill.execute(make_request("browser_session.type_text", target="hello", dry_run=True))
    assert result.get("status") in ("preview", "ok", "confirmation_required")

def test_unknown_capability_raises():
    skill = Skill()
    import pytest
    with pytest.raises(Exception):
        skill.execute(make_request("browser_session.unknown"))
```

### Fix 3 — Khai báo dependency rõ ràng trong pyproject.toml

```toml
[project]
# Thêm comment giải thích
# Core ecosystem is provided by the parent JARVIS runtime.
# This skill requires the core ecosystem to be importable (sys.path must include core repo).
dependencies = []  # runtime dependency: ecosystem (injected by loader)
```

---

## Không cần làm
- Không cần refactor implementation (BrowserSessionAdapter integration đã tốt)
- Không cần thay đổi confirmation flow (đúng rồi)
- Không cần thay đổi healthcheck pattern
