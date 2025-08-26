# Markdown Resume Specification

This document provides a detailed specification for parsing, generating, and serializing Markdown resume documents. It outlines the required structure, headers, fields, and formatting conventions.
---
### 1. General Structure and Rules
-   The document is divided into four top-level sections, each introduced by a level 1 header (`#`).

-   The required top-level sections are:
    -   `# Personal`
    -   `# Education`
    -   `# Certifications`
    -   `# Experience`

-   Each top-level section must be separated by exactly one blank line.

-   Subsections are denoted by headers of level 2 (`##`), 3 (`###`), or 4 (`####`). Header titles are case-insensitive for parsing but should be written in title case for consistency.

-   Content under a header is parsed based on its type: key-value pairs (`LabelBlockParse`), free text (`TextBlockParse`), or bulleted lists (`ListBlockParse`).

---

### 2. Section Details
#### 2.1. `# Personal`

Contains personal contact information, online presence, and other metadata.

-   **`## Contact Information`** (Required)
    -   **Format**: Key-value pairs.
    -   **Required Fields**:
        -   `Name: <Full Name>`
    -   **Optional Fields**:
        -   `Email: <Email Address>`
        -   `Phone: <Phone Number>`
        -   `Location: <City, State/Country>`

-   **`## Websites`** (Optional)
    -   **Format**: Key-value pairs. All fields are optional.
    -   **Optional Fields**:
        -   `GitHub: <URL>`
        -   `LinkedIn: <URL>`
        -   `Website: <URL>`
        -   `Twitter: <URL>`

-   **`## Visa Status`** (Optional)
    -   **Format**: Key-value pairs. All fields are optional.
    -   **Optional Fields**:
        -   `Work Authorization: <Status>`
        -   `Require sponsorship: <Yes/No>`

-   **`## Banner`** (Optional)
    -   **Format**: Free text block.

-   **`## Note`** (Optional)
    -   **Format**: Free text block.

---

#### 2.2. `# Education`
Details academic qualifications.

-   **`## Degrees`** (Required)
    -   **Format**: A container for one or more `### Degree` subsections.

-   **`### Degree`** (At least one is required within `## Degrees`)
    -   **Format**: Key-value pairs.
    -   **Required Fields**:
        -   `School: <Institution Name>`
    -   **Optional Fields**:
        -   `Degree: <Degree Title>`
        -   `Start date: <MM/YYYY>`
        -   `End date: <MM/YYYY>`
        -   `Major: <Field of Study>`
        -   `GPA: <Grade Point Average>`

---

#### 2.3. `# Certifications`
Lists professional certifications.

-   **`## Certification`** (One or more subsections if the top-level section exists)
    -   **Format**: Key-value pairs.
    -   **Required Fields**:
        -   `Name: <Certification Name>`
    -   **Optional Fields**:
        -   `Issuer: <Issuing Organization>`
        -   `Issued: <MM/YYYY>`
        -   `Expires: <MM/YYYY>`
        -   `Certification ID: <ID Number>`

---
#### 2.4. `# Experience`
Details professional roles and projects. Contains two optional subsections: `## Projects` and `## Roles`.

-   **`## Projects`** (Optional)
    -   **Format**: A container for one or more `### Project` subsections.

    -   **`### Project`**
        -   **`#### Overview`** (Required)
            -   **Format**: Key-value pairs.
            -   **Required Fields**:
                -   `Title: <Project Title>`
            -   **Optional Fields**:
                -   `Url: <URL>`
                -   `Url Description: <Text>`
                -   `Start date: <MM/YYYY>`
                -   `End date: <MM/YYYY>`
        -   **`#### Description`** (Required)
            -   **Format**: Free text block.
        -   **`#### Skills`** (Optional)
            -   **Format**: Bulleted list. Each item must start with `* `.
            -   Example: `* Python`

-   **`## Roles`** (Optional)

    -   **Format**: A container for one or more `### Role` subsections.
    -   **`### Role`**
        -   **`#### Basics`** (Required)
            -   **Format**: Key-value pairs.
            -   **Required Fields**:
                -   `Company: <Company Name>`
                -   `Title: <Job Title>`
                -   `Start date: <MM/YYYY>`
            -   **Optional Fields**:
                -   `Agency: <Agency Name>`
                -   `Job category: <Category>`
                -   `Employment type: <Type>`
                -   `End date: <MM/YYYY>`
                -   `Reason for change: <Text>`
                -   `Location: <City, State/Country>`
        -   **`#### Summary`** (Optional)
            -   **Format**: Free text block.
        -   **`#### Responsibilities`** (Optional)
            -   **Format**: Free text block.
        -   **`#### Skills`** (Optional)
            -   **Format**: Bulleted list. Each item must start with `* `.
            -   Example: `* Agile`

---

### 3. Minimal Valid Resume Example


# Personal
## Contact Information

Name: Jane Doe
# Education
## Degrees
### Degree

School: State University
# Certifications
## Certification

Name: Certified Professional
# Experience
## Roles
### Role
#### Basics

Company: A Company, LLC

Title: Engineer

Start date: 01/2020
## Projects
### Project
#### Overview

Title: A Project
#### Description

A description of the project.
