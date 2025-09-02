# Overview

All code should have tests. The code file name may not exactly match the test file name. For example, the tests for `app/api/routes/user.py` are in `tests/app/api/routes/test_user_route.py`, not in `tests/app/api/routes/test_user.py`. This is to prevent a naming collision which causes errors during test collection.

This file contains a list of known code->test mappings. It should not be considered definitive. Update this file as mappings are discovered.

A single file may have multiple test files.

## Code->test file mappings

These are known mappings:

- `resume_editor/app/api/routes/user.py` -> `resume_editor/tests/app/api/routes/test_user_route.py`
- `resume_editor/app/main.py` -> `resume_editor/tests/app/web/test_main_web.py`
- `resume_editor/app/api/routes/resume.py` -> `resume_editor/tests/app/api/routes/test_resume.py`
