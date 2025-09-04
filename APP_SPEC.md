# Overview

A web-based application for multi-user resume authoring, editing, and export, utilizing Markdown format and LLM assistance.

It is written using Python version 3.12.

# The `resume_writer` module

This app uses the `resume_writer` module for parsing and exporting. 
**Always** assume that the `resume_writer` library is available. 
**NEVER** check to see if it exists. If it isn't available, it should raise an `ImportError` and exit.
Use `resume_writer_docs.md` as reference for available functions and classes.
Pay attention to the `BasicBlockParse` class. It is a base class for many parsing models, and methods are added dynamically.

# Core Functionality

## User Management

* User registration, login (username/password), and logout.
* User-friendly authentication flow that redirects unauthenticated users to the login page when accessing web pages.
* An initial setup page for creating the first administrator account, enforced by middleware if no users exist.
* Secure user password change functionality, including a mandatory password change workflow.
* Secure storage of user settings, including LLM configurations (endpoints, model names) and encrypted API keys.
* Role-based access control with two roles: `user` and `admin`.
* Tracking of last login time for each user.
* Flexible user attribute system to support features like forcing a password change on next login.

## Admin Interface

* A dedicated, HTMX-powered web interface for administrative tasks.
* Full user management: create, list, edit, and delete users via the web UI.
* View detailed user information, including last login time and resume count.
* Ability to enforce password changes for users.
* Role management: assign and remove roles from users.
* User impersonation to provide support or troubleshoot issues.

## Web Dashboard

* An HTMX-powered web dashboard for managing resumes and user settings.
* View a list of all resumes for the current user.
* View resume details, including a rendered view of the Markdown.
* Create new resumes from a form.
* Edit all sections of a resume (personal, education, experience, etc.) through dedicated forms.
* Initiate actions like AI refinement and export from the dashboard, with real-time progress updates and error notifications for AI tasks.
* A dedicated settings page for managing LLM configurations and changing passwords.

## Resume Management

* Create new resumes via a web form; new resumes are pre-filled with valid placeholder content.
* Save resumes to a PostgreSQL database with user-assigned names.
* List, update, and delete resumes.
* Download resumes in Markdown or DOCX formats.

## Editing Features

* Edit a resume's name and raw Markdown content
* Edit structured candidate information (contact details, education, experience, etc.) through dedicated forms
* Dedicated interfaces for editing individual jobs and projects
* Per-item inclusion controls: Include, Not Relevant (summary only), Omit
* Filter jobs for export using customizable date ranges

## Export Formats

* Validated Markdown.
* DOCX formats:
   * `ATS_FRIENDLY`
   * `PLAIN`

## LLM Integration

* Refine resume content using LLMs.
* Analyze job descriptions with an LLM to extract key skills and qualifications.
* Multi-pass refinement of the "Experience" section, where each role is individually refined against the job analysis.
* Real-time progress feedback using Server-Sent Events (SSE) during refinement, with graceful error handling.
* Save and download LLM-refined versions.
* Configure custom OpenAI-compatible API endpoints and model names.

# Technical Requirements

## Architecture

* Single FastAPI application with API routes
* Middleware for initial application setup.
* HTMX for dynamic frontend interactions, with Server-Sent Events (SSE) for real-time updates.
* Tailwind CSS for styling
* PostgreSQL for data storage with Alembic migrations

## Security

* Multi-layered security approach
* Encrypted storage of sensitive user data
* Secure handling of API keys and database connections via environment variables

## Data Handling

* Resumes processed and stored in Markdown format
* Integrated document conversion from Markdown to DOCX
* Validated resume parsing and storage

## Development Principles

* Follow established coding conventions and documentation standards
* Implement defensive coding practices
* Maintain clear separation between frontend and backend logic
* Ensure all LLM interactions use proper output parsing and validation
