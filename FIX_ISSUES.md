# Fix GitHub Issues - Discord Project Manager Bot

## Context
You are fixing code quality issues found in the discord-project-manager-bot repository at `~/OpenWork/discord-project-manager-bot/`.

## Issues to Fix (Issue #1)

The following 10 issues were submitted by Sanshit. Fix ALL of them:

### Issue 1: Duplicate Import Statement
- **File:** `bot.py:33-34`
- **Problem:** `WebAppQueryService` from `services.webapp_query_service` is imported twice in consecutive lines
- **Fix:** Remove one of the two identical import statements

### Issue 2: Dead Code at End of File
- **File:** `bot.py:1359-1461`
- **Problem:** Multiple blocks of placeholder code like `logger.info("Feature integration: 2.3")` at end of file, ~100 lines
- **Fix:** Remove all dead code blocks at the end of the file

### Issue 3: Missing certifi Dependency
- **File:** `bot.py:57-61`, `requirements.txt`
- **Problem:** Code uses `certifi` library but it's not in requirements.txt
- **Fix:** Add `certifi` to requirements.txt

### Issue 4: Potential Division by Zero Risk
- **File:** `services/report_builder.py:30`
- **Problem:** `completion_rate = (total_completed / total_tasks * 100) if total_tasks > 0 else 0` could be more robust
- **Fix:** Add additional validation to handle edge cases

### Issue 5: Inconsistent Error Handling in mytasks Command
- **File:** `bot.py:669-676`
- **Problem:** Nested try-except blocks with bare `except:` clauses that catch all exceptions including system-exit ones
- **Fix:** Flatten error handling structure or use specific exception types

### Issue 6: Hardcoded Year in Status Message
- **File:** `bot.py:134`
- **Problem:** Status message says `"🎮 Project Manager 2024"` with hardcoded year
- **Fix:** Use `datetime.now().year` to dynamically generate the current year

### Issue 7: No UUID Validation in t_status Command
- **File:** `bot.py:922-933`
- **Problem:** The `t_status` command accepts any string without validating it's a valid UUID
- **Fix:** Add UUID validation using Python's uuid module

### Issue 8: Hardcoded API Timeout Configuration
- **File:** `services/api_service.py:15`
- **Problem:** Timeout is hardcoded to 10 seconds with no configuration option
- **Fix:** Make timeout configurable via environment variable or config.py

### Issue 9: Missing Directory Creation on Initialization
- **File:** `services/project_manager_service.py`
- **Problem:** `data/` directory only created when `_save_data()` is called, may fail on first crash
- **Fix:** Ensure data directory is created during initialization

### Issue 10: Missing Encoding Specification for JSON Files
- **File:** `services/conversation_manager.py`
- **Problem:** JSON files read/written without specifying encoding
- **Fix:** Add `encoding='utf-8'` to all file open operations

## Instructions
1. Read each file and understand the context
2. Make the minimal changes required to fix each issue
3. Do NOT change any unrelated code
4. After fixing, verify the changes work by checking syntax (python3 -m py_compile)
5. Create a new branch called `fix/code-quality-issues`
6. Commit all fixes with message: `fix: resolve 10 code quality issues (#1)`
7. Push the branch to origin
8. Do NOT create a PR yet - just push the branch

## Important
- Work in the repo at `~/OpenWork/discord-project-manager-bot/`
- Be careful with Issue 2 (dead code) - make sure you don't delete code that's actually being used
- For Issue 5 (error handling), preserve the intended error handling logic while making it more specific
