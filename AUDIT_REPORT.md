# Code Audit Report — discord-project-manager-bot

**Auditor:** Subagent (Shawn)  
**Date:** 2026-04-11  
**Branch:** `audit/code-review`  
**Files Audited:** 24 Python files (~4,177 lines)

---

## EXECUTIVE SUMMARY

The codebase has **moderate-to-high technical debt** with several security gaps, significant dead code, incomplete feature stubs, and missing best practices. No critical CVEs were found (no remote code execution, no SQL injection vectors given no DB, no hardcoded secrets in committed code). However, the **webhook signature verification bypass** and **unbounded cache growth** are the most urgent issues to address.

---

## 🔴 CRITICAL

### 1. Webhook Server Bypasses Signature Verification in Dev Mode
- **File:** `webhooks/webhook_server.py`, line 62
- **Type:** Security
- **Severity:** Critical
- **Description:**
  ```python
  if not self.webhook_secret:
      logger.warning("Webhook secret not configured, skipping verification")
      return True  # ← ALLOWS ALL REQUESTS IN PRODUCTION IF SECRET IS MISSING
  ```
  When `webhook_secret` is empty/unset, the server accepts **any** POST request without verifying the GitHub HMAC signature. If this server is deployed to production without the secret configured, attackers can send arbitrary payloads.
- **Suggested Fix:** Require the secret in production; raise an error if missing:
  ```python
  if not self.webhook_secret:
      raise ValueError("WEBHOOK_SECRET must be set in production")
  ```

### 2. Unbounded Cache Growth — Memory Leak
- **File:** `services/webapp_query_service.py`, lines 12–13
- **Type:** Performance / Memory
- **Severity:** Critical
- **Description:**
  ```python
  self.cache: Dict[str, Any] = {}  # Never cleaned up
  ```
  The cache dict grows indefinitely. Only `self.cache[key]` is overwritten on TTL miss, but expired entries are never purged. Under high load, this will consume all available memory.
- **Suggested Fix:** Add a `_cleanup_expired()` method called on each cache access, or use `functools.lru_cache` with `maxsize`. Alternatively, use `time.time()` to check expiry on every `get_cached` call and delete stale keys.

### 3. Discord User ID Cast to int Without Validation
- **File:** `bot.py`, lines 1120–1122 (`set_channel` command)
- **Type:** Security / Error Handling
- **Severity:** Critical
- **Description:**
  ```python
  c_id = int(channel_id)
  channel = bot.get_channel(c_id)
  ```
  `channel_id` comes directly from user input. Non-integer strings cause `ValueError` which is caught by the bare `except Exception`. But more critically, `SPECIFIC_DISCORD_USER_ID` in config.py is cast with `int(os.getenv(...))` — if the env var is an empty string `''`, this raises `ValueError` at startup, not at runtime.
- **Suggested Fix:** Validate input with try/except around `int()` conversion and return a user-friendly error. For config, use a guard:
  ```python
  val = os.getenv('SPECIFIC_DISCORD_USER_ID')
  SPECIFIC_DISCORD_USER_ID = int(val) if val else None
  ```

---

## 🟠 HIGH

### 4. Hardcoded API Base URL with No HTTPS Enforcement
- **File:** `config.py`, line 12
- **Type:** Security
- **Severity:** High
- **Description:**
  ```python
  API_BASE_URL = os.getenv('WEBAPP_API_URL', 'https://benevolent-kookabura-514.convex.site')
  ```
  The fallback URL uses HTTPS (good), but there's no code that enforces HTTPS. A misconfigured env var with `http://` would send Discord tokens and project data over plain HTTP.
- **Suggested Fix:** Add runtime validation:
  ```python
  if API_BASE_URL.startswith('http://'):
      logger.warning("Using HTTP is insecure! Consider HTTPS.")
  ```

### 5. No Rate Limiting on GitHub Polling Loop
- **File:** `bot.py`, `poll_github_for_reviews()`, lines 292–332
- **Type:** Security / Performance
- **Severity:** High
- **Description:** The polling loop checks `CODE_REVIEW_CHECK_INTERVAL` (default 300s) but has no exponential backoff if the GitHub API returns errors. A temporary API outage could cause rapid reconnection attempts.
- **Suggested Fix:** Implement exponential backoff on API errors:
  ```python
  backoff = CODE_REVIEW_CHECK_INTERVAL
  for pr_info in merged_prs:
      try:
          # ... process PR
          backoff = CODE_REVIEW_CHECK_INTERVAL  # reset on success
      except Exception as e:
          backoff = min(backoff * 2, 3600)  # cap at 1 hour
          await asyncio.sleep(backoff)
  ```

### 6. Dead Code — Webhook Server Never Used
- **File:** `webhooks/webhook_server.py`
- **Type:** Code Quality
- **Severity:** High
- **Description:** The `WebhookServer` class is defined but **never instantiated or started** anywhere in `bot.py`. The project switched to polling (`GitHubPollService`) instead of webhooks, but the webhook server code was left behind. It has security issues (see #1) and adds maintenance burden.
- **Suggested Fix:** Either remove the file entirely, or remove it and add a comment in `bot.py` explaining why polling was chosen over webhooks.

### 7. Dead Code — Service Placeholders
- **Files:**
  - `services/deadline_reminder_service.py` (103 lines — mostly placeholder comments)
  - `services/health_report_builder.py` (28 lines — placeholder)
  - `services/health_score_service.py` (114 lines — mostly placeholder logger.info stubs)
  - `services/time_report_builder.py` (50 lines — placeholder)
  - `services/time_tracking_service.py` (17 lines — placeholder)
  - `services/reminder_preferences_service.py` (26 lines — no-op implementation)
- **Type:** Code Quality
- **Severity:** High
- **Description:** ~340 lines of placeholder/stub code that provides zero functionality. These appear to be features planned but never completed ("Feature integration: X.X" logging).
- **Suggested Fix:** Remove all placeholder files. Implement properly when needed, or create GitHub issues instead of leaving dead code.

### 8. Bare `except Exception` Swallows All Errors
- **File:** `bot.py`, line 1109 (`set_channel` command)
- **Type:** Error Handling
- **Severity:** High
- **Description:**
  ```python
  except Exception as e:
      logger.error(...)
      await ctx.send(f"❌ Failed to set channel: {str(e)}")
  ```
  This catches **everything** including `KeyboardInterrupt`, `SystemExit`, and `asyncio.CancelledError`. If `project_manager.set_config()` raises a runtime exception, the error is silently logged and a generic message sent.
- **Suggested Fix:** Catch specific exceptions:
  ```python
  except (IOError, OSError) as e:
      await ctx.send("❌ Failed to write configuration.")
  except Exception as e:
      logger.error(f"Unexpected error in set_channel: {e}", exc_info=True)
      await ctx.send("❌ An unexpected error occurred.")
  ```

### 9. Missing Input Validation on Task Status
- **File:** `services/project_manager_service.py`, line 86
- **Type:** Security
- **Severity:** High
- **Description:**
  ```python
  def update_task_status(self, task_id: str, status: str) -> bool:
      if status not in ['todo', 'in_progress', 'done']:
          return False
  ```
  The service validates status, but `bot.py` also validates UUID format before calling it. However, `bot.py` line 692 does **not** validate `status` before passing to the service:
  ```python
  @bot.command(name='t_status')
  async def update_task_status(ctx, task_id: str, status: str):
  ```
  The `status` argument is accepted as any string, and while the service returns `False`, the bot responds with a generic failure message. No injection risk here (status is used as a dict key), but the error message is misleading.
- **Suggested Fix:** Add validation in the command:
  ```python
  VALID_STATUSES = {'todo', 'in_progress', 'done'}
  if status not in VALID_STATUSES:
      await ctx.send(f"❌ Invalid status. Use: {', '.join(VALID_STATUSES)}")
      return
  ```

### 10. GitHub Token Logged on Connection Failure
- **File:** `services/github_pr_service.py`, line 15–16
- **Type:** Security
- **Severity:** High
- **Description:**
  ```python
  if not self.github:
      logger.warning("GitHub token not provided. PR fetching will not work.")
  ```
  While the token itself is not logged, the `Github` client is initialized with the token, and PyGithub may log URL/debug info that includes the token in some error traces. More critically, if `github_token` is passed as empty string `''`, `Github('')` connects without auth and may expose public repo data unexpectedly.
- **Suggested Fix:** Validate token is non-empty before initializing:
  ```python
  if not github_token or not github_token.strip():
      logger.error("GitHub token is empty")
      self.github = None
  else:
      self.github = Github(github_token)
  ```

---

## 🟡 MEDIUM

### 11. Duplicate Code — `enable_reports` Command
- **File:** `bot.py`, lines ~1064–1104 AND ~1105–1138
- **Type:** Code Quality
- **Severity:** Medium
- **Description:** The `!enable` command appears to be defined twice in `bot.py` (lines ~1064–1104 and ~1105–1138). The second definition (after `set_channel`) likely overrides the first. The first definition contains dead code after its `await ctx.send(embed=embed)` that is unreachable (the footer/embed setup code at lines 1101–1104).
- **Suggested Fix:** Remove the first duplicate definition and keep the cleaner second one.

### 12. Magic Numbers Without Named Constants
- **Files:** Multiple
- **Type:** Code Quality
- **Severity:** Medium
- **Description:** Numerous magic numbers scattered throughout:
  - `bot.py`: `30` (status rotation seconds), `20` (max files in PR diff), `12` (default report hours), `5` (max users in team performance)
  - `api_service.py`: `3` (retry total), `1` (backoff factor)
  - `github_pr_service.py`: `5000` (patch truncation limit)
  - `conversational_ai_service.py`: `400` (max response words), `2000` (question truncation), `10` (max history messages), `500` (num_predict)
  - `webapp_query_service.py`: `300` (cache TTL seconds), `24*7` (task fetch hours)
  - `bot.py`: `8, 20` (report hours hardcoded defaults in REPORT_HOURS)
- **Suggested Fix:** Define all magic numbers as named constants at the top of each file or in `config.py`.

### 13. Missing Type Hints Throughout
- **Files:** Most service files
- **Type:** Code Quality
- **Severity:** Medium
- **Description:** Most functions in `bot.py` and service files lack return type annotations. Several parameter types are also missing (e.g., `hours: int = 12` is present in some places but not others).
- **Suggested Fix:** Add `from __future__ import annotations` and add type hints to all function signatures.

### 14. No Docstrings on Public Methods
- **Files:** Most service files
- **Type:** Best Practices
- **Severity:** Medium
- **Description:** `APIService`, `GitHubPRService`, `GitHubPollService`, `ProjectManagerService`, and others have no class docstrings. Many public methods lack docstrings explaining parameters and return values.
- **Suggested Fix:** Add Google-style or NumPy docstrings to all public methods.

### 15. Error Messages Not User-Friendly
- **File:** Multiple
- **Type:** Best Practices
- **Severity:** Medium
- **Description:** Error messages like `"❌ Failed to generate reports: {str(e)}"` expose internal error strings to end users, which is both confusing and potentially a security concern (stack traces, file paths, etc.).
- **Suggested Fix:** Use structured error messages that don't expose raw exception content:
  ```python
  await ctx.send(f"❌ Failed to generate reports. Please try again later.")
  logger.error(f"Report generation failed: {e}", exc_info=True)  # detailed info in logs only
  ```

### 16. `format_time_ago` Has Timezone Bug
- **File:** `utils/formatters.py`, line 6–18
- **Type:** Bug
- **Severity:** Medium
- **Description:**
  ```python
  task_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
  now = datetime.utcnow().replace(tzinfo=task_time.tzinfo)  # ← BUG
  ```
  If `task_time` has no timezone (the `replace('Z', ...)` handles ISO Z notation but not naive timestamps), `task_time.tzinfo` is `None`, so `now` becomes naive. Comparing naive and aware datetimes raises `TypeError` in Python 3.
- **Suggested Fix:**
  ```python
  from datetime import timezone
  task_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).astimezone(timezone.utc)
  now = datetime.now(timezone.utc)
  ```

### 17. JSON File Race Condition
- **Files:** `services/conversation_manager.py`, `services/project_manager_service.py`, `services/user_mapping_service.py`
- **Type:** Concurrency
- **Severity:** Medium
- **Description:** All three services read/write JSON files without any locking mechanism. If two coroutines/processes access the same file simultaneously (e.g., two bot instances, or a health check hitting during a write), data can be corrupted or lost.
- **Suggested Fix:** Use `fcntl.flock()` on Linux/macOS for file locking, or use an atomic write pattern (write to temp file, then rename).

### 18. GitHub Poll Service PR Deduplication Bug
- **File:** `services/github_poll_service.py`, lines 51–55
- **Type:** Bug
- **Severity:** Medium
- **Description:**
  ```python
  last_pr_id = self.last_checked.get(repo_name, 0)
  if pr.number <= last_pr_id:
      continue
  ```
  This deduplication strategy fails if:
  1. A PR is merged, then closed without merging, then reopened and merged — the second merge would be skipped.
  2. PR numbers wrap (unlikely in practice).
  3. More than `N` PRs merge between checks — only the highest-numbered one is tracked.
- **Suggested Fix:** Track merged PR IDs (not numbers) in a set per repo, persisted to disk. Use `pr.id` (GitHub's internal numeric ID) rather than `pr.number`.

### 19. No SSL Certificate Verification Toggle
- **File:** `services/api_service.py`
- **Type:** Security
- **Severity:** Medium
- **Description:** The `requests.Session` is created without any SSL verification configuration. While certifi is used in `bot.py` for Discord, the API service does not configure it. If the backend uses a self-signed certificate, the code will fail; there's no way to configure verification.
- **Suggested Fix:** Allow SSL verification to be configured via env var:
  ```python
  SSL_VERIFY = os.getenv('API_SSL_VERIFY', 'true').lower() == 'true'
  if not SSL_VERIFY:
      adapter = HTTPAdapter(max_retries=retry_strategy)
      session.mount("https://", adapter)  # no verify= argument
  ```

### 20. Health Check Server Runs on Port 8080 with No Authentication
- **File:** `bot.py`, `start_health_server()`, lines 1239–1248
- **Type:** Security
- **Severity:** Medium
- **Description:** The health check server on `0.0.0.0:8080` has no authentication or rate limiting. An attacker could probe it to confirm the bot is running, or potentially exploit it if Flask has known CVEs.
- **Suggested Fix:** Either bind to localhost only (`127.0.0.1`), or add a simple secret token check:
  ```python
  async def health_check(request):
      if request.headers.get('X-Health-Token') != os.getenv('HEALTH_TOKEN'):
          return web.Response(status=401)
      return web.Response(text="", status=200)
  ```

---

## 🟢 LOW

### 21. Duplicate Import in `config.py`
- **File:** `config.py`, lines 1 and 30
- **Type:** Code Quality
- **Severity:** Low
- **Description:** `import os` appears at line 1 and again at line 30. Minor style issue.
- **Suggested Fix:** Remove duplicate.

### 22. `utils/formatters.py` Has No Type Hints
- **File:** `utils/formatters.py`
- **Type:** Code Quality
- **Severity:** Low
- **Description:** All functions in `formatters.py` lack type hints and return type annotations.
- **Suggested Fix:** Add type hints.

### 23. `APIService` Uses `requests` (Sync) in Async Bot
- **File:** `services/api_service.py`
- **Type:** Performance
- **Severity:** Low
- **Description:** The entire `APIService` uses synchronous `requests` library inside an async Discord bot. All API calls block the event loop. Under load, this could cause latency spikes for other Discord commands.
- **Suggested Fix:** Migrate to `aiohttp` (already in requirements.txt) for fully async HTTP calls.

### 24. `Github` Object Not Closed / No Context Manager
- **File:** `services/github_pr_service.py`, line 13
- **Type:** Resource Management
- **Severity:** Low
- **Description:** `Github(github_token)` opens a connection pool that is never explicitly closed. While Python's GC will eventually clean it up, it's not best practice.
- **Suggested Fix:** Use `self.github = Github(github_token)` and call `self.github.close()` in a `finally` block, or use it as a context manager.

### 25. Missing `__all__` Exports in Modules
- **Files:** All `services/*.py` and `utils/*.py`
- **Type:** Best Practices
- **Severity:** Low
- **Description:** No module defines `__all__`, making it unclear what is public API vs. internal.
- **Suggested Fix:** Add `__all__ = [...]` to each module defining the public interface.

### 26. `.env.example` Contains Real Example Data
- **File:** `.env.example`, lines 11–15
- **Type:** Security
- **Severity:** Low
- **Description:** The example file contains a real Convex site URL (`https://benevolent-kookabura-514.convex.site`) and real Discord channel/user IDs. While these aren't secrets, they shouldn't be in the example file.
- **Suggested Fix:** Replace with placeholder values that clearly indicate "replace with your value."

### 27. `PROJECT_MANAGER_SERVICE` JSON Data File Not in `.gitignore`
- **File:** `.gitignore` doesn't mention `data/local_projects.json` or `user_mappings.json`
- **Type:** Security / Data
- **Severity:** Low
- **Description:** Local project data files could be accidentally committed to version control, potentially exposing project names and Discord user IDs.
- **Suggested Fix:** Add to `.gitignore`:
  ```
  data/
  user_mappings.json
  enabled_projects.json
  bot.log
  ```

### 28. `Github.get_repo()` Called Without Error Handling for Rate Limits
- **File:** `services/github_poll_service.py`, line 40
- **Type:** Error Handling
- **Severity:** Low
- **Description:** `repo = self.github_service.github.get_repo(repo_name)` can raise `RateLimitExceededException` from PyGithub. Currently caught by the bare `except Exception` above it, but the error message to the user will be confusing.
- **Suggested Fix:** Add specific handling for rate limit errors with a user-friendly message and proper backoff.

### 29. Inconsistent Logging Levels
- **Files:** All files
- **Type:** Best Practices
- **Severity:** Low
- **Description:** Some errors use `logger.error` with `exc_info=True`, others just `logger.error(message)`. Some info messages use `logger.info`, others use `print()`. This makes log analysis difficult.
- **Suggested Fix:** Standardize: use `logger.error(..., exc_info=True)` for all exceptions, use `logger.info/warning/error` consistently (no `print()`).

### 30. `STATUS_MESSAGES` Rotation Has No Error Recovery Beyond Log
- **File:** `bot.py`, `rotate_status()`, lines 157–167
- **Type:** Reliability
- **Severity:** Low
- **Description:** If `bot.change_presence()` fails repeatedly, the rotation loop logs the error but keeps spinning every 30 seconds. Over time, repeated failures could indicate a deeper issue.
- **Suggested Fix:** After N consecutive failures, increase sleep interval or stop rotation:
  ```python
  failures = 0
  while not bot.is_closed():
      try:
          await bot.change_presence(...)
          failures = 0
      except Exception as e:
          failures += 1
          if failures > 5:
              await asyncio.sleep(300)  # back off
              failures = 0
  ```

---

## 📊 SUMMARY TABLE

| # | File | Line(s) | Issue | Severity |
|---|------|---------|-------|----------|
| 1 | `webhooks/webhook_server.py` | 62 | Signature verification bypasses when secret missing | 🔴 Critical |
| 2 | `services/webapp_query_service.py` | 12–13 | Unbounded cache growth (memory leak) | 🔴 Critical |
| 3 | `bot.py` | 1120–1122 | Discord ID cast without input validation | 🔴 Critical |
| 4 | `config.py` | 12 | No HTTPS enforcement on API URL | 🟠 High |
| 5 | `bot.py` | 292–332 | No rate limiting on GitHub polling loop | 🟠 High |
| 6 | `webhooks/webhook_server.py` | entire file | Dead code — webhook server never used | 🟠 High |
| 7 | `services/*.py` | multiple | Dead code — ~340 lines of placeholder stubs | 🟠 High |
| 8 | `bot.py` | 1109 | Bare `except Exception` swallows all errors | 🟠 High |
| 9 | `services/project_manager_service.py` | 86 | Missing status validation | 🟠 High |
| 10 | `services/github_pr_service.py` | 15–16 | Empty token string bypasses auth | 🟠 High |
| 11 | `bot.py` | ~1064–1138 | Duplicate `enable_reports` command | 🟡 Medium |
| 12 | Multiple | various | Magic numbers without constants | 🟡 Medium |
| 13 | Most service files | — | Missing type hints | 🟡 Medium |
| 14 | Most service files | — | Missing docstrings | 🟡 Medium |
| 15 | Multiple | — | Raw exception strings exposed to users | 🟡 Medium |
| 16 | `utils/formatters.py` | 6–18 | Timezone-aware vs naive datetime bug | 🟡 Medium |
| 17 | `services/conversation_manager.py` + 2 | — | JSON file race condition | 🟡 Medium |
| 18 | `services/github_poll_service.py` | 51–55 | PR deduplication by number is flawed | 🟡 Medium |
| 19 | `services/api_service.py` | — | No SSL verification toggle | 🟡 Medium |
| 20 | `bot.py` | 1239–1248 | Health check server unauthenticated | 🟡 Medium |
| 21 | `config.py` | 1, 30 | Duplicate `import os` | 🟢 Low |
| 22 | `utils/formatters.py` | — | No type hints | 🟢 Low |
| 23 | `services/api_service.py` | — | Sync `requests` in async bot | 🟢 Low |
| 24 | `services/github_pr_service.py` | 13 | `Github` object never closed | 🟢 Low |
| 25 | All service files | — | Missing `__all__` exports | 🟢 Low |
| 26 | `.env.example` | — | Real URLs/IDs in example file | 🟢 Low |
| 27 | `.gitignore` | — | Data files not gitignored | 🟢 Low |
| 28 | `services/github_poll_service.py` | 40 | No rate limit error handling | 🟢 Low |
| 29 | All files | — | Inconsistent logging levels | 🟢 Low |
| 30 | `bot.py` | 157–167 | Status rotation has no backoff on failure | 🟢 Low |

**Total: 30 issues** — 3 Critical, 7 High, 10 Medium, 10 Low

---

## 🏆 TOP 5 PRIORITY FIXES

1. **Fix webhook signature bypass** (`webhooks/webhook_server.py:62`) — security
2. **Fix unbounded cache** (`services/webapp_query_service.py`) — memory leak
3. **Add input validation on user IDs** (`bot.py:1120`) — security
4. **Remove dead code** (webhook_server.py + all placeholder services) — maintenance
5. **Fix timezone bug in `format_time_ago`** (`utils/formatters.py:6`) — correctness bug affecting displayed timestamps
