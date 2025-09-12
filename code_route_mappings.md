# Overview

A FastAPI application can have many routes, for different purposes.

Routes are generally separated based on their function:

1.  **API Routes**: These are located in the `resume_editor/app/api/routes/` directory. They handle data-centric operations, typically returning JSON or, in the case of HTMX, HTML fragments for swapping into a page. The `resume.py` router you have access to is an example of this.
2.  **Web Page Routes**: These routes serve full HTML pages, usually by rendering a Jinja2 template with `TemplateResponse`. Currently, these routes are located directly in `resume_editor/app/main.py`. This includes top-level pages like `/login` and `/dashboard`, as well as the `/resumes/{resume_id}/edit` page. Newer web-related routes are also being organized under `resume_editor/app/web/`

This file contains a list of known code->route mappings. It should not be considered definitive. Update this file as mappings are discovered.

It is a list of routes with their corresponding file name, for example `/login->resume_editor/app/main.py`
Many routes may point to one file.

## Code->route file mappings

These are the known mappings:
- `/login->resume_editor/app/main.py`
- `/resumes/{resume_id}/edit->resume_editor/app/main.py`
- `/api/resumes/parse->resume_editor/app/api/routes/resume.py`
- `/resumes/create->resume_editor/app/main.py`
- `/api/resumes/{resume_id}/refine->resume_editor/app/api/routes/resume.py`
- `/resumes/{resume_id}/refine/start->resume_editor/app/main.py`
- `/api/resumes/{resume_id}/refine/stream->resume_editor/app/api/routes/resume.py`
