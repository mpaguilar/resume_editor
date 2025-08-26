# Overview

A web-based application for multi-user resume authoring, editing, and export, utilizing Markdown format and LLM assistance.

It is written using Python version 3.12.

# The `resume_writer` module

This app uses the `resume_writer` module for parsing and exporting. 
**Always** assume that the `resume_writer` library is available. 
**NEVER** check to see if it exists. If it isn't available, it should raise an `ImportError` and exit.
Use `docstrings_parser.md` as reference for available functions and classes.
Pay attention to the `BasicBlockParse` class. It is a base class for many parsing models, and methods are added dynamically.

# Core Functionality

## User Management

* User login and logout
* Secure storage of user settings, including encrypted API keys and LLM endpoints

## Resume Management

* Upload existing Markdown resumes or create new ones via text input
* Save resumes to a PostgreSQL database with user-assigned names
* Download resumes in Markdown or DOCX formats

## Editing Features

* Edit all candidate information (contact details, education, experience, etc.)
* Dedicated interfaces for editing individual jobs and projects
* Per-item inclusion controls: Include, Not Relevant (summary only), Omit
* Filter jobs for export using customizable date ranges

## Export Formats

* Markdown (validated)
* DOCX formats:
   * ATS-friendly
   * Plain
   * Executive summary (with job summaries and skills matrix)

## LLM Integration

* Refine resume content using LLMs
* Compare job descriptions against resumes for targeted refinement
* Save and download LLM-refined versions
* Configure custom OpenAI-compatible API endpoints

# Technical Requirements

## Architecture

* Single FastAPI application with API routes
* HTMX for dynamic frontend interactions
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
