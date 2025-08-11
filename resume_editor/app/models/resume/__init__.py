"""
This module serves as the initialization file for the resume-related models in the application.

It provides a central location for importing and exposing resume-related data models,
such as certifications, education, and the main resume model, ensuring they are available
when the package is imported.

This module does not contain any classes or functions itself, but acts as a namespace
for the resume models defined in the submodules.

Notes:
1. This file is intentionally empty (or minimal) to serve as an export point for resume models.
2. It enables clean imports from the resume package, such as:
   from app.models.resume import Certification, Degree, Resume
3. No disk, network, or database access is performed in this file.
"""
