## Layout Templates

These are base templates that provide a common structure for other pages.

*   `resume_editor/app/templates/layouts/base.html`
    *   **Type**: Layout
    *   **Purpose**: The main application layout. Includes `<html>` and `<body>` tags, loads global CSS and JavaScript (HTMX, SSE extension), and defines content blocks for other pages to extend.

*   `resume_editor/app/templates/admin/layout.html`
    *   **Type**: Layout
    *   **Purpose**: The standard layout for the admin section. Features a two-column design with a persistent sidebar for navigation and a main content area. It also defines a global modal for hosting forms.

---

## Full Page Templates

These templates render complete HTML pages for specific routes.

*   `resume_editor/app/templates/dashboard.html`
    *   **Type**: Page
    *   **Purpose**: The main user dashboard. Displays a header with navigation, a "New Resume" button, and an empty `<div id="resume-list">` that is populated via an HTMX call on page load.

*   `resume_editor/app/templates/editor.html`
    *   **Type**: Page
    *   **Purpose**: The primary resume editor interface. Provides a large text area to edit resume content and a field for the resume name. Changes are saved via an `hx-put` request. Includes "Export" and "Refine with AI" buttons.

*   `resume_editor/app/templates/refine.html`
    *   **Type**: Page
    *   **Purpose**: Dedicated page to initiate the AI refinement process. Contains a form to submit a job description, which triggers a Server-Sent Events (SSE) stream for real-time progress updates.

*   `resume_editor/app/templates/pages/resume_view.html`
    *   **Type**: Page
    *   **Purpose**: Provides a read-only view of a saved resume, typically a refined one. Displays the content, job description, introduction, and notes. Includes an "Export" modal.

*   `resume_editor/app/templates/create_resume.html`
    *   **Type**: Page
    *   **Purpose**: A form to create a new resume. It includes fields for a name and the main content, pre-populated with a valid Markdown template.

*   `resume_editor/app/templates/login.html`
    *   **Type**: Page
    *   **Purpose**: The user login page. Contains a simple form for username and password.

*   `resume_editor/app/templates/settings.html`
    *   **Type**: Page
    *   **Purpose**: Allows users to manage their settings. Contains two forms: one for LLM configuration (endpoint, model, API key) and another for changing their password.

*   `resume_editor/app/templates/pages/change_password.html` & `change-password.html`
    *   **Type**: Page
    *   **Purpose**: A dedicated page for changing a password. It is used when a password change is forced by an administrator.

*   `resume_editor/app/templates/pages/setup.html`
    *   **Type**: Page
    *   **Purpose**: The initial setup page, shown only when no admin user exists. It contains a form to create the first administrator account.

*   `resume_editor/app/templates/admin/users.html`
    *   **Type**: Page (Extends `admin/layout.html`)
    *   **Purpose**: The main user management dashboard for administrators. It includes a "Create User" button and renders the `user_list.html` partial to display all users.

---

## Partial/Fragment Templates

These are snippets of HTML intended to be swapped into a page dynamically via HTMX.

*   `resume_editor/app/templates/partials/resume/_resume_list.html`
    *   **Type**: Partial
    *   **Purpose**: Renders the complete list of "Base" and "Applied" resumes. Includes controls for sorting and buttons for "Edit"/"View" and "Delete" actions on each resume. It's loaded into `dashboard.html`.

*   `resume_editor/app/templates/partials/resume/_resume_detail.html`
    *   **Type**: Partial
    *   **Purpose**: Displays the content and metadata of a single selected resume. Includes buttons for "AI Refine", "Export", and "Edit". It is intended to be loaded into a detail pane on the dashboard.

*   `resume_editor/app/templates/partials/resume/_refine_sse_loader.html`
    *   **Type**: Partial
    *   **Purpose**: A loading state indicator shown during AI refinement. It connects to an SSE stream to display real-time progress messages and is replaced by the result or an error.

*   `resume_editor/app/templates/partials/resume/_refine_result.html`
    *   **Type**: Partial
    *   **Purpose**: Displays the suggested AI refinement in a text area. Includes buttons to "Discard" the suggestion or "Save as New" resume.

*   `resume_editor/app/templates/partials/resume/_refine_result_intro.html`
    *   **Type**: Partial
    *   **Purpose**: An out-of-band (OOB) swap target for displaying a generated introduction during AI refinement. It is swapped into the `_refine_result.html` view.

*   `resume_editor/app/templates/admin/partials/user_list.html`
    *   **Type**: Partial
    *   **Purpose**: Renders the HTML `<table>` of users for the admin dashboard. Each row has HTMX-powered "Edit" and "Delete" buttons.

*   `resume_editor/app/templates/admin/partials/create_user_form.html`
    *   **Type**: Partial
    *   **Purpose**: A form for creating a new user. It is loaded into the modal in the admin layout.

*   `resume_editor/app/templates/admin/partials/edit_user_form.html`
    *   **Type**: Partial
    *   **Purpose**: A form for editing an existing user's details (email, force password change). It is also loaded into the admin modal.
