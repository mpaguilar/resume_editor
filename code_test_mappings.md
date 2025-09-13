# Overview

All code should have tests. The code file name may not exactly match the test file name. For example, the tests for `app/api/routes/user.py` are in `tests/app/api/routes/test_user_route.py`, not in `tests/app/api/routes/test_user.py`. This is to prevent a naming collision which causes errors during test collection.

This file contains a list of known code->test mappings. It should not be considered definitive. Update this file as mappings are discovered.

A single file may have multiple test files.

## Code->test file mappings

These are known mappings:

- `resume_editor/app/api/dependencies.py` -> `tests/app/api/test_dependencies.py`
- `resume_editor/app/api/routes/html_fragments.py` -> `tests/app/api/routes/test_html_fragments.py`
- `resume_editor/app/api/routes/resume_ai.py` -> `tests/app/api/routes/test_resume_ai.py`
- `resume_editor/app/api/routes/resume_edit.py` -> `tests/app/api/routes/test_resume_edit.py`
- `resume_editor/app/api/routes/resume_export.py` -> `tests/app/api/routes/test_resume_export.py`
- `resume_editor/app/api/routes/user.py` -> `tests/app/api/routes/test_user_route.py`
- `resume_editor/app/main.py` -> `tests/app/web/test_main_web.py`
- `resume_editor/app/main.py` -> `tests/app/web/test_resume_web.py`
- `resume_editor/app/api/routes/resume.py` -> `tests/app/api/routes/test_resume.py`
- `resume_editor/app/models/user_settings.py` -> `tests/app/models/test_user_settings.py`
- `resume_editor/app/api/routes/route_logic/settings_crud.py` -> `tests/app/api/routes/route_logic/test_settings_crud.py`
- `resume_editor/app/llm/orchestration.py` -> `tests/app/llm/test_orchestration.py`
- `resume_editor/app/api/routes/route_logic/resume_serialization.py` -> `tests/app/api/routes/route_logic/test_resume_serialization.py`
- `resume_editor/app/api/routes/route_logic/resume_parsing.py` -> `tests/app/api/routes/route_logic/test_resume_parsing.py`
