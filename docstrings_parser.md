# Docstrings Reference

===
# File: `resume_writer/__init__.py`


===

===
# File: `resume_writer/main.py`

## function: `print_personal(personal: Personal) -> None`

Print the personal information.

Args:
    personal (Personal): The personal information object to print.

Returns:
    None

Notes:
    1. Extracts the name, email, and phone number from the personal object.
    2. Prints each field using rich formatting with bold labels.

---

## function: `career_years_of_experience(resume: Resume) -> None`

Calculate and print the total years of experience from resume roles.

Args:
    resume (Resume): The resume object containing role information.

Returns:
    None

Notes:
    1. Retrieves all roles from the resume.
    2. Initializes a DateStats object to manage date ranges.
    3. Iterates over each role and adds its start and end date range to the DateStats.
    4. Calculates the total years of experience using the date statistics.
    5. Prints the years of experience using rich formatting with a bold label.

---

## function: `dump_resume(resume: Resume) -> None`

Dump the entire resume data to the console.

Args:
    resume (Resume): The resume object to dump.

Returns:
    None

Notes:
    1. Calls print_personal to display personal contact details.
    2. Calls career_years_of_experience to display total years of experience.

---

## function: `load_settings(settings_file: str) -> dict`

Load resume rendering settings from a TOML file.

Args:
    settings_file (str): Path to the TOML settings file.

Returns:
    dict: A dictionary containing the parsed settings.

Notes:
    1. Converts the settings_file path to a Path object.
    2. Opens the TOML file in binary mode.
    3. Parses the TOML content using tomli.load.
    4. Prints the parsed settings using rich.
    5. Returns the settings dictionary.
    6. Disk access: Reads from the settings_file path.

---

## function: `basic_render(docx_doc: docx.document.Document, resume: Resume, settings: ResumeRenderSettings) -> None`

Render the resume using the basic rendering style.

Args:
    docx_doc (docx.document.Document): The Word document object to render into.
    resume (Resume): The resume object containing the content to render.
    settings (ResumeRenderSettings): The rendering settings for the output.

Returns:
    None

Notes:
    1. Validates that all inputs are of the correct type.
    2. Logs the start of the rendering process.
    3. Creates a BasicRenderResume instance with the provided document, resume, and settings.
    4. Calls the render method on the renderer to generate the document.
    5. Logs the completion of the rendering process.
    6. Disk access: Saves the rendered document to the output file path.

---

## function: `ats_render(docx_doc: docx.document.Document, resume: Resume, settings: ResumeRenderSettings) -> None`

Render the resume using the ATS (Applicant Tracking System) rendering style.

Args:
    docx_doc (docx.document.Document): The Word document object to render into.
    resume (Resume): The resume object containing the content to render.
    settings (ResumeRenderSettings): The rendering settings for the output.

Returns:
    None

Notes:
    1. Validates that all inputs are of the correct type.
    2. Logs the start of the rendering process.
    3. Creates an AtsRenderResume instance with the provided document, resume, and settings.
    4. Calls the render method on the renderer to generate the document.
    5. Logs the completion of the rendering process.
    6. Disk access: Saves the rendered document to the output file path.

---

## function: `plain_render(docx_doc: docx.document.Document, resume: Resume, settings: ResumeRenderSettings) -> None`

Render the resume using the plain (minimalist) rendering style.

Args:
    docx_doc (docx.document.Document): The Word document object to render into.
    resume (Resume): The resume object containing the content to render.
    settings (ResumeRenderSettings): The rendering settings for the output.

Returns:
    None

Notes:
    1. Validates that all inputs are of the correct type.
    2. Logs the start of the rendering process.
    3. Creates a PlainRenderResume instance with the provided document, resume, and settings.
    4. Calls the render method on the renderer to generate the document.
    5. Logs the completion of the rendering process.
    6. Disk access: Saves the rendered document to the output file path.

---

## function: `html_render(resume: Resume, settings: ResumeRenderSettings) -> None`

Render the resume as an HTML file.

Args:
    resume (Resume): The resume object containing the content to render.
    settings (ResumeRenderSettings): The rendering settings for the output.

Returns:
    None

Notes:
    1. Validates that all inputs are of the correct type.
    2. Logs the start of the HTML rendering process.
    3. Creates a RenderResumeHtml instance with the resume and settings.
    4. Calls the render method to generate the HTML content.
    5. Saves the rendered HTML to a file at "data/html_resume.html".
    6. Logs the completion of the rendering process.
    7. Disk access: Writes to the file "data/html_resume.html".

---

## function: `markdown_render(resume: Resume, settings: ResumeRenderSettings) -> None`

Render the resume as a Markdown file.

Args:
    resume (Resume): The resume object containing the content to render.
    settings (ResumeRenderSettings): The rendering settings for the output.

Returns:
    None

Notes:
    1. Validates that all inputs are of the correct type.
    2. Logs the start of the Markdown rendering process.
    3. Creates a RenderResumeMarkdown instance with the resume and settings.
    4. Calls the render method to generate the Markdown content.
    5. Saves the rendered Markdown to a file at "data/markdown_resume.md".
    6. Logs the completion of the rendering process.
    7. Disk access: Writes to the file "data/markdown_resume.md".

---

## function: `parse_text_resume(input_file: str) -> Resume`

Parse a text-based resume file and convert it into a Resume object.

Args:
    input_file (str): Path to the text file containing the resume content.

Returns:
    Resume: The parsed Resume object.

Notes:
    1. Opens the input file and reads its content.
    2. Splits the content into lines while preserving line endings.
    3. Creates a ParseContext object with the lines and initial line number.
    4. Parses the resume content using the Resume.parse method.
    5. Returns the resulting Resume object.
    6. Disk access: Reads from the input_file path.

---

## function: `main(input_file: str, output_file: str, settings_file: str, resume_type: str) -> None`

Convert a text resume to a .docx file with specified rendering style.

Args:
    input_file (str): Path to the input text resume file.
    output_file (str): Path where the output .docx file will be saved.
    settings_file (str): Path to the TOML file containing rendering settings.
    resume_type (str): Type of resume to generate ("ats", "basic", "plain", "html", "markdown").

Returns:
    None

Notes:
    1. Loads the settings from the settings_file using load_settings.
    2. Creates a ResumeRenderSettings object and updates it from the loaded settings.
    3. Parses the input resume text file into a Resume object using parse_text_resume.
    4. Based on resume_type, selects the appropriate rendering method:
        a. "basic": Uses basic_render to generate a .docx file.
        b. "plain": Uses plain_render to generate a .docx file.
        c. "ats": Uses ats_render to generate a .docx file.
        d. "html": Uses html_render to generate an HTML file.
        e. "markdown": Uses markdown_render to generate a Markdown file.
    5. Saves the rendered output to the specified output_file path if applicable.
    6. Logs the completion of the process.
    7. Prints the entire resume object using rich.
    8. Disk access: Reads from input_file and settings_file; writes to output_file (for .docx) and data/html_resume.html, data/markdown_resume.md (for html/markdown).

---


===

===
# File: `resume_writer/renderers/html_renderer.py`

## `RenderResumeHtml` class

Render a resume to HTML format using Jinja2 templates.

This class coordinates the rendering process by initializing the Jinja2 environment,
managing the rendering pipeline, and saving the final output.

Attributes:
    jinja_env (Environment): The Jinja2 environment configured with custom filters.
    resume (Resume): The resume data to be rendered.
    settings (ResumeRenderSettings): Configuration settings for rendering.
    renderer (RenderResume): The underlying renderer responsible for generating HTML.
    rendered (bool): Flag indicating whether the resume has been rendered.

---
## method: `RenderResumeHtml.__init__(self: UnknownType, resume: Resume, settings: ResumeRenderSettings) -> None`

Initialize the HTMLRenderer object.

Args:
    resume (Resume): The resume data to be rendered.
    settings (ResumeRenderSettings): The settings for rendering the resume.

Notes:
    1. Validates that resume is an instance of Resume and settings is an instance of ResumeRenderSettings.
    2. Initializes the Jinja2 environment.
    3. Stores the resume and settings data.
    4. Initializes the HTML renderer.
    5. Sets the rendered flag to False.

---
## method: `RenderResumeHtml.init_renderer(self: UnknownType) -> RenderResume`

Initialize and return a RenderResume object.

Returns:
    RenderResume: Initialized RenderResume object.

Notes:
    1. Creates an instance of HtmlDoc.
    2. Creates a RenderResume object with the HtmlDoc, Jinja environment, resume data, and settings.
    3. Returns the RenderResume object.

---
## method: `RenderResumeHtml.init_jinja(self: UnknownType) -> Environment`

Initialize the Jinja environment with custom filters.

Returns:
    Environment: The initialized Jinja environment.

Notes:
    1. Defines a date filter function to format dates in the Jinja template.
    2. Defines a line feed to HTML break function to convert line feeds to HTML breaks.
    3. Defines a list length function to calculate the length of a list.
    4. Initializes the Jinja environment with the custom filters.
    5. Loads templates from the 'resume_writer.resume_render.html' package.
    6. Enables autoescaping for HTML output.

---
## method: `RenderResumeHtml.render(self: UnknownType) -> str`

Render the resume using the HTML renderer.

Returns:
    str: The rendered resume as a string.

Notes:
    1. Logs an info message indicating the start of the HTML resume rendering.
    2. Calls the render method of the HTML renderer.
    3. Sets the rendered attribute to True.
    4. Logs an info message indicating the completion of the HTML resume rendering.

---
## method: `RenderResumeHtml.save(self: UnknownType, path: Path) -> None`

Save the rendered resume to a file.

Args:
    path (Path): The path where the resume will be saved.

Raises:
    AssertionError: If the provided path is not an instance of Path.

Notes:
    1. Checks if the provided path is an instance of Path.
    2. Checks if the resume has been rendered. If not, logs a warning and returns.
    3. Logs a debug message indicating the save location.
    4. Calls the renderer's save method to save the resume to the file.
    5. Logs an info message indicating the successful save.

---
## method: `RenderResumeHtml.content(self: UnknownType) -> str`

Return the rendered content of the resume.

Returns:
    str: The rendered content of the resume as a string.

Notes:
    1. Checks if the resume has been rendered.
    2. If not, logs a warning message and returns an empty string.
    3. If yes, returns the rendered content as a string.

---

===

===
# File: `resume_writer/renderers/markdown_renderer.py`

## `RenderResumeMarkdown` class

Render a resume in Markdown format using Jinja templates.

This class orchestrates the rendering process by initializing a Jinja environment
with custom filters and delegating the actual rendering to a RenderResume instance.

Attributes:
    resume (Resume): The resume data to be rendered.
    settings (ResumeRenderSettings): The settings for rendering the resume.
    renderer (RenderResume): The renderer responsible for generating the Markdown output.
    rendered (bool): Flag indicating whether the resume has been rendered.

---
## method: `RenderResumeMarkdown.__init__(self: UnknownType, resume: Resume, settings: ResumeRenderSettings) -> None`

Initialize the MarkdownRenderer object.

Parameters
----------
resume : Resume
    The resume data to be rendered.
settings : ResumeRenderSettings
    The settings for rendering the resume.

Notes
-----
1. Validate that the provided resume is an instance of Resume.
2. Validate that the provided settings is an instance of ResumeRenderSettings.
3. Store the resume and settings data.
4. Initialize the Markdown renderer.

---
## method: `RenderResumeMarkdown.init_renderer(self: UnknownType) -> RenderResume`

Initialize and return a RenderResume object.

Returns
-------
RenderResume
    Initialized RenderResume object.

Notes
-----
1. Create an instance of MarkdownDoc.
2. Create a RenderResume object with the MarkdownDoc, resume data, and settings.
3. Return the RenderResume object.

---
## method: `RenderResumeMarkdown.render(self: UnknownType) -> str`

Render the resume using the Markdown renderer.

Returns
-------
str
    The rendered resume as a string.

Notes
-----
1. Logs an info message indicating the start of the Markdown resume rendering.
2. Calls the render method of the Markdown renderer.
3. Sets the rendered attribute to True.
4. Logs an info message indicating the completion of the Markdown resume rendering.

---
## method: `RenderResumeMarkdown.save(self: UnknownType, path: Path) -> None`

Save the rendered resume to a file.

Parameters
----------
path : Path
    The path where the resume will be saved.

Raises
------
AssertionError
    If the provided path is not an instance of Path.

Notes
-----
1. Check if the resume is rendered. If not, log a warning and return.
2. Log a debug message indicating the save location.
3. Call the renderer's save method to save the resume to the file.
4. Log an info message indicating the successful save.
5. Writes the rendered content to disk at the specified path.

---
## method: `RenderResumeMarkdown.content(self: UnknownType) -> str`

Return the rendered content of the resume.

This method should be called after the `render()` method.

Returns
-------
str
    The rendered content of the resume as a string.

Notes
-----
1. Checks if the resume has been rendered.
2. If not, logs a warning message and returns an empty string.
3. If yes, returns the rendered content as a string.

---

===

===
# File: `resume_writer/renderers/__init__.py`


===

===
# File: `resume_writer/resume_render/docx_hyperlink.py`

## function: `get_or_create_hyperlink_style(d: Document) -> str`

Create a hyperlink style if one doesn't exist, or return existing style.

Args:
    d (Document): The Document object to check or modify for the hyperlink style.

Returns:
    str: The name of the style used for hyperlinks, which is "Hyperlink".

Notes:
    1. Check if a style named "Hyperlink" already exists in the document.
    2. If not, create a new style named "Default Character Font" with default character formatting.
    3. The "Default Character Font" style is set to be the default font and is hidden.
    4. Create a new style named "Hyperlink" based on the "Default Character Font" style.
    5. Set the hyperlink style to be visible when used and apply blue color and underline to the font.
    6. Return the name "Hyperlink" as the style identifier.

---

## function: `add_hyperlink(paragraph: Paragraph, text: str, url: str) -> docx.oxml.shared.OxmlElement`

Create a hyperlink object and add it to the paragraph.

Args:
    paragraph (Paragraph): The Paragraph object to which the hyperlink will be added.
    text (str): The text to display as the hyperlink.
    url (str): The URL that the hyperlink will point to.

Returns:
    docx.oxml.shared.OxmlElement: The OxmlElement representing the hyperlink, which is added to the paragraph.

Notes:
    1. Access the document part of the paragraph to manage relationships.
    2. Create a unique relationship ID for the hyperlink using the provided URL.
    3. Create an XML element for the hyperlink and set its relationship ID.
    4. Create a new run element to hold the hyperlink text.
    5. Set the text of the run to the provided display text.
    6. Apply the hyperlink style to the run by retrieving or creating it.
    7. Append the run element to the hyperlink XML element.
    8. Append the complete hyperlink element to the paragraph's XML content.
    9. Return the created hyperlink element.

---


===

===
# File: `resume_writer/resume_render/__init__.py`


===

===
# File: `resume_writer/resume_render/resume_render_base.py`

## `RenderBase` class

Base class for rendering docx files.

Used for common functionality between the different renderers,
primarily error and warning collection.

Attributes:
    errors (list): List of errors encountered during rendering.
    warnings (list): List of warnings encountered during rendering.
    document (docx.document.Document): The document object to render into.
    font_size (float): The font size used in the document, extracted from the Normal style.

Methods:
    add_horizontal_line: Adds a horizontal line to a paragraph with optional offset.

Notes:
    1. The class initializes error and warning lists.
    2. It sets up the document reference.
    3. It ensures the Normal style font size is set to 12pt if not already set.
    4. The font size is stored in the class for use by subclasses.

---
## method: `RenderBase.__init__(self: UnknownType, document: docx.document.Document) -> UnknownType`

Initialize superclass.

Args:
    document (docx.document.Document): The document object to render into.

Returns:
    None

Notes:
    1. Initialize errors and warnings lists.
    2. Store the document reference.
    3. Ensure the Normal style font size is set to 12pt if not already set.
    4. Store the font size from the Normal style in the class.
    5. Raise ValueError if the font size is not set.

---
## method: `RenderBase.add_horizontal_line(self: UnknownType, paragraph: Paragraph, offset: int) -> None`

Add a horizontal line to a paragraph with optional offset.

Args:
    paragraph (docx.text.paragraph.Paragraph): The paragraph to add the line to.
    offset (int): The indentation offset in inches (default is 0).

Returns:
    None

Notes:
    1. Access the paragraph's XML element.
    2. Create a new paragraph border element.
    3. Configure the bottom border with single line style, size 6, space 1, and auto color.
    4. Append the border to the paragraph properties.
    5. Set left and right indentation of the paragraph based on the offset.

---
## `ResumeRenderBase` class

Base class for rendering resumes.

Attributes:
    settings (ResumeRenderSettings): Configuration settings for the resume.
    resume (Resume): The resume object containing the data to render.
    font_size (float): The font size used in the document, extracted from the Normal style.

Methods:
    save: Saves the rendered document to a file.

Notes:
    1. The class initializes with a document, resume, and optional settings.
    2. If no settings are provided, it defaults to a new ResumeRenderSettings instance.
    3. It sets up the document's Normal style spacing and font size.
    4. It configures document margins based on settings.
    5. The settings are stored in the instance.

---
## method: `ResumeRenderBase.__init__(self: UnknownType, document: docx.document.Document, resume: Resume, settings: ResumeRenderSettings | None) -> UnknownType`

Initialize superclass.

Args:
    document (docx.document.Document): The document object to render into.
    resume (Resume): The resume object containing the data to render.
    settings (ResumeRenderSettings | None): Configuration settings for the resume (optional).

Returns:
    None

Notes:
    1. Validate that resume is of type Resume and settings is of type ResumeRenderSettings or None.
    2. If settings is None, create a new ResumeRenderSettings instance.
    3. Call the parent constructor to initialize common attributes.
    4. Store the settings and resume objects.
    5. Configure the Normal style to have no space before or after paragraphs.
    6. Set the font size from settings if provided.
    7. Configure document margins based on settings (left, right, top, bottom).

---
## method: `ResumeRenderBase.save(self: UnknownType, path: Path) -> None`

Save the document to a file.

Args:
    path (pathlib.Path): The file path to save the document to.

Returns:
    None

Notes:
    1. The document is saved to the specified path using the docx library.
    2. This operation writes to disk.

---
## `ResumeRenderPersonalBase` class

Base class for rendering resume personal section.

Attributes:
    settings (ResumePersonalSettings): Configuration settings for the personal section.
    personal (Personal): The personal information object to render.

Methods:
    None

Notes:
    1. The class initializes with a document, personal data, and settings.
    2. It validates the types of the inputs.
    3. If the document is a list of strings, it ensures all items are strings.
    4. It calls the parent constructor.

---
## method: `ResumeRenderPersonalBase.__init__(self: UnknownType, document: docx.document.Document | list[str], personal: Personal, settings: ResumePersonalSettings) -> UnknownType`

Initialize personal renderer.

Args:
    document (docx.document.Document | list[str]): The document object or a list of strings.
    personal (Personal): The personal information object to render.
    settings (ResumePersonalSettings): Configuration settings for the personal section.

Returns:
    None

Notes:
    1. Validate that document is either a docx document or a list of strings.
    2. If document is a list of strings, validate all items are strings.
    3. Validate that personal is of type Personal.
    4. Validate that settings is of type ResumePersonalSettings.
    5. Call the parent constructor to initialize common attributes.

---
## `ResumeRenderRolesBase` class

Base class for rendering resume roles section.

Attributes:
    _roles (Roles): The list of roles to render.
    settings (ResumeRolesSettings): Configuration settings for the roles section.

Methods:
    roles: Property to get filtered roles based on settings.

Notes:
    1. The class initializes with a document, roles, and settings.
    2. It validates the types of the inputs.
    3. It stores the roles and settings.
    4. The roles property filters roles older than the specified number of months.

---
## method: `ResumeRenderRolesBase.__init__(self: UnknownType, document: docx.document.Document, roles: Roles, settings: ResumeRolesSettings) -> UnknownType`

Initialize the roles section.

Args:
    document (docx.document.Document): The document object to render into.
    roles (Roles): The list of role objects to render.
    settings (ResumeRolesSettings): Configuration settings for the roles section.

Returns:
    None

Notes:
    1. Call the parent constructor.
    2. Validate that roles is of type Roles.
    3. Validate that settings is of type ResumeRolesSettings.
    4. Store the roles and settings.

---
## method: `ResumeRenderRolesBase.roles(self: UnknownType) -> list[Role]`

Return roles which have not been filtered out.

Args:
    None

Returns:
    list[Role]: A list of Role objects that are not older than the specified number of months.

Notes:
    1. Initialize an empty list to store filtered roles.
    2. Iterate through each role in _roles.
    3. If months_ago is set and greater than 0, calculate the date threshold.
    4. If the role's end date is older than the threshold, skip it.
    5. Otherwise, add the role to the result list.
    6. Return the filtered list.

---
## `ResumeRenderRoleBase` class

Base class for rendering resume role section.

Attributes:
    role (Role): The role object to render.
    settings (ResumeRolesSettings): Configuration settings for the role section.

Methods:
    None

Notes:
    1. The class initializes with a document, role, and settings.
    2. It validates the types of the inputs.
    3. It calls the parent constructor.

---
## method: `ResumeRenderRoleBase.__init__(self: UnknownType, document: docx.document.Document, role: Role, settings: ResumeRolesSettings) -> UnknownType`

Initialize the role section.

Args:
    document (docx.document.Document): The document object to render into.
    role (Role): The role object to render.
    settings (ResumeRolesSettings): Configuration settings for the role section.

Returns:
    None

Notes:
    1. Call the parent constructor.
    2. Validate that role is of type Role.
    3. Validate that settings is of type ResumeRolesSettings.
    4. Store the role and settings.

---
## `ResumeRenderProjectsBase` class

Base class for rendering resume projects section.

Attributes:
    document (docx.document.Document): The document object to render into.
    projects (Projects): The list of project objects to render.
    settings (ResumeProjectsSettings): Configuration settings for the projects section.

Methods:
    None

Notes:
    1. The class initializes with a document, projects, and settings.
    2. It validates the types of the inputs.
    3. It calls the parent constructor.

---
## method: `ResumeRenderProjectsBase.__init__(self: UnknownType, document: docx.document.Document, projects: Projects, settings: ResumeProjectsSettings) -> UnknownType`

Initialize the projects section.

Args:
    document (docx.document.Document): The document object to render into.
    projects (Projects): The list of project objects to render.
    settings (ResumeProjectsSettings): Configuration settings for the projects section.

Returns:
    None

Notes:
    1. Call the parent constructor.
    2. Validate that projects is of type Projects.
    3. Validate that settings is of type ResumeProjectsSettings.
    4. Store the document, projects, and settings.

---
## `ResumeRenderProjectBase` class

Base class for rendering resume project section.

Attributes:
    document (docx.document.Document): The document object to render into.
    project (Project): The project object to render.
    settings (ResumeProjectsSettings): Configuration settings for the project section.

Methods:
    None

Notes:
    1. The class initializes with a document, project, and settings.
    2. It validates the types of the inputs.
    3. It calls the parent constructor.

---
## method: `ResumeRenderProjectBase.__init__(self: UnknownType, document: docx.document.Document, project: Project, settings: ResumeProjectsSettings) -> UnknownType`

Initialize the project section.

Args:
    document (docx.document.Document): The document object to render into.
    project (Project): The project object to render.
    settings (ResumeProjectsSettings): Configuration settings for the project section.

Returns:
    None

Notes:
    1. Call the parent constructor.
    2. Validate that project is of type Project.
    3. Validate that settings is of type ResumeProjectsSettings.
    4. Store the document, project, and settings.

---
## `ResumeRenderExperienceBase` class

Base class for rendering resume experience section.

Attributes:
    experience (Experience): The experience object to render.
    document (docx.document.Document): The document object to render into.
    settings (ResumeRolesSettings): Configuration settings for the experience section.

Methods:
    None

Notes:
    1. The class initializes with a document, experience, and settings.
    2. It validates the types of the inputs.
    3. It calls the parent constructor.

---
## method: `ResumeRenderExperienceBase.__init__(self: UnknownType, document: docx.document.Document, experience: Experience, settings: ResumeRolesSettings) -> UnknownType`

Initialize the roles section.

Args:
    document (docx.document.Document): The document object to render into.
    experience (Experience): The experience object to render.
    settings (ResumeRolesSettings): Configuration settings for the experience section.

Returns:
    None

Notes:
    1. Call the parent constructor.
    2. Validate that experience is of type Experience.
    3. Validate that settings is of type ResumeExperienceSettings.
    4. Store the experience, document, and settings.

---
## `ResumeRenderDegreeBase` class

Base class for rendering a single degree.

Attributes:
    degree (Degree): The degree object to render.
    settings (ResumeEducationSettings): Configuration settings for the degree section.

Methods:
    None

Notes:
    1. The class initializes with a document, degree, and settings.
    2. It validates the types of the inputs.
    3. It calls the parent constructor.

---
## method: `ResumeRenderDegreeBase.__init__(self: UnknownType, document: docx.document.Document, degree: Degree, settings: ResumeEducationSettings) -> UnknownType`

Initialize the degree section.

Args:
    document (docx.document.Document): The document object to render into.
    degree (Degree): The degree object to render.
    settings (ResumeEducationSettings): Configuration settings for the degree section.

Returns:
    None

Notes:
    1. Validate that degree is of type Degree.
    2. Validate that settings is of type ResumeEducationSettings.
    3. Call the parent constructor.
    4. Store the degree and settings.

---
## `ResumeRenderEducationBase` class

Base class for rendering resume education section.

Attributes:
    education (Education): The education object to render.
    settings (ResumeEducationSettings): Configuration settings for the education section.
    document (docx.document.Document): The document object to render into.

Methods:
    degrees: Method to render the degrees section of education.
    render: Method to render the education section.

Notes:
    1. The class initializes with a document, education, and settings.
    2. It validates the types of the inputs.
    3. It calls the parent constructor.
    4. The degrees method is not implemented in this base class.
    5. The render method is not implemented in this base class.

---
## method: `ResumeRenderEducationBase.__init__(self: UnknownType, document: docx.document.Document, education: Education, settings: ResumeEducationSettings) -> UnknownType`

Initialize the education rendering section.

Args:
    document (docx.document.Document): The document object to render into.
    education (Education): The education object to render.
    settings (ResumeEducationSettings): Configuration settings for the education section.

Returns:
    None

Notes:
    1. Call the parent constructor.
    2. Validate that education is of type Education.
    3. Validate that settings is of type ResumeEducationSettings.
    4. Store the education, settings, and document.

---
## method: `ResumeRenderEducationBase.degrees(self: UnknownType) -> None`

Render degrees section of education.

Args:
    None

Returns:
    None

Notes:
    1. This method is not implemented in the base class.
    2. It must be implemented by subclasses.

---
## method: `ResumeRenderEducationBase.render(self: UnknownType) -> None`

Render education section.

Args:
    None

Returns:
    None

Notes:
    1. This method is not implemented in the base class.
    2. It must be implemented by subclasses.

---
## `ResumeRenderCertificationBase` class

Base class for rendering a single certification.

Attributes:
    certification (Certification): The certification object to render.
    settings (ResumeCertificationsSettings): Configuration settings for the certification section.

Methods:
    None

Notes:
    1. The class initializes with a document, certification, and settings.
    2. It validates the types of the inputs.
    3. It calls the parent constructor.

---
## method: `ResumeRenderCertificationBase.__init__(self: UnknownType, document: docx.document.Document, certification: Certification, settings: ResumeCertificationsSettings) -> UnknownType`

Initialize the certification section.

Args:
    document (docx.document.Document): The document object to render into.
    certification (Certification): The certification object to render.
    settings (ResumeCertificationsSettings): Configuration settings for the certification section.

Returns:
    None

Notes:
    1. Call the parent constructor.
    2. Validate that certification is of type Certification.
    3. Validate that settings is of type ResumeCertificationsSettings.
    4. Store the certification and settings.

---
## `ResumeRenderCertificationsBase` class

Base class for rendering resume certifications section.

Attributes:
    settings (ResumeCertificationsSettings): Configuration settings for the certifications section.
    certifications (Certifications): The list of certification objects to render.

Methods:
    None

Notes:
    1. The class initializes with a document, certifications, and settings.
    2. It validates the types of the inputs.
    3. It calls the parent constructor.

---
## method: `ResumeRenderCertificationsBase.__init__(self: UnknownType, document: docx.document.Document, certifications: Certifications, settings: ResumeCertificationsSettings) -> UnknownType`

Initialize certification renderer.

Args:
    document (docx.document.Document): The document object to render into.
    certifications (Certifications): The list of certification objects to render.
    settings (ResumeCertificationsSettings): Configuration settings for the certifications section.

Returns:
    None

Notes:
    1. Call the parent constructor.
    2. Validate that certifications is of type Certifications.
    3. Validate that settings is of type ResumeCertificationsSettings.
    4. Store the settings and certifications.

---
## `ResumeRenderExecutiveSummaryBase` class

Base class for rendering resume executive summary section.

Attributes:
    experience (Experience): The experience object containing data for the summary.
    document (docx.document.Document): The document object to render into.
    settings (ResumeExecutiveSummarySettings): Configuration settings for the summary section.

Methods:
    None

Notes:
    1. The class initializes with a document, experience, and settings.
    2. It validates the types of the inputs.
    3. It calls the parent constructor.

---
## method: `ResumeRenderExecutiveSummaryBase.__init__(self: UnknownType, document: docx.document.Document, experience: Experience, settings: ResumeExecutiveSummarySettings) -> None`

Initialize the executive summary section.

Args:
    document (docx.document.Document): The document object to render into.
    experience (Experience): The experience object to extract summary data from.
    settings (ResumeExecutiveSummarySettings): Configuration settings for the summary section.

Returns:
    None

Notes:
    1. Call the parent constructor.
    2. Validate that experience is of type Experience.
    3. Validate that settings is of type ResumeExecutiveSummarySettings.
    4. Store the experience, document, and settings.

---
## `ResumeRenderSkillsMatrixBase` class

Base class for rendering resume skills matrix section.

Attributes:
    experience (Experience): The experience object containing data for the skills matrix.
    document (docx.document.Document): The document object to render into.
    settings (ResumeSkillsMatrixSettings): Configuration settings for the skills matrix section.

Methods:
    None

Notes:
    1. The class initializes with a document, experience, and settings.
    2. It validates the types of the inputs.
    3. It calls the parent constructor.

---
## method: `ResumeRenderSkillsMatrixBase.__init__(self: UnknownType, document: docx.document.Document, experience: Experience, settings: ResumeSkillsMatrixSettings) -> None`

Initialize the skills matrix section.

Args:
    document (docx.document.Document): The document object to render into.
    experience (Experience): The experience object to extract skills data from.
    settings (ResumeSkillsMatrixSettings): Configuration settings for the skills matrix section.

Returns:
    None

Notes:
    1. Call the parent constructor.
    2. Validate that experience is of type Experience.
    3. Validate that settings is of type ResumeSkillsMatrixSettings.
    4. Store the experience, document, and settings.

---

===

===
# File: `resume_writer/resume_render/render_settings.py`

## `ResumeSettingsBase` class

Base class for managing resume settings.

This class provides a method to update the settings from a dictionary.

Attributes:
    None

Methods:
    update_from_dict(data_dict: dict | None = None) -> None
        Update the settings from a dictionary.

---
## method: `ResumeSettingsBase.update_from_dict(self: UnknownType, data_dict: dict | None) -> None`

Update the settings from a dictionary.

Args:
    data_dict (dict | None): Dictionary containing the new settings. If None, no changes are made.

Returns:
    None

Notes:
    1. If data_dict is None, the method returns without making any changes.
    2. The method iterates over each key-value pair in data_dict.
    3. If the key is 'section', it is ignored to avoid unwanted updates.
    4. If the key exists as an attribute of the class instance, its value is updated.

---
## `ResumePersonalSettings` class

Control what parts of a resume's personal section are rendered.

Attributes:
    contact_info (bool): Include contact information.
    banner (bool): Include banner.
    visa_status (bool): Include visa status.
    websites (bool): Include websites.
    note (bool): Include note.
    name (bool): Include name.
    email (bool): Include email.
    phone (bool): Include phone number.
    location (bool): Include location.
    linkedin (bool): Include LinkedIn.
    github (bool): Include GitHub.
    website (bool): Include personal website.
    twitter (bool): Include Twitter.
    require_sponsorship (bool): Include sponsorship requirement.
    work_authorization (bool): Include work authorization status.

Methods:
    __init__(default_init: bool = True) -> None
        Initialize all attributes to default_init.
    to_dict() -> dict
        Return settings as a dictionary.

---
## method: `ResumePersonalSettings.__init__(self: UnknownType, default_init: bool) -> UnknownType`

Initialize everything to default_init.

Args:
    default_init (bool): Default initialization value for all attributes. Defaults to True.

Returns:
    None

Notes:
    1. All attributes are initialized to default_init.
    2. The to_dict method constructs and returns a dictionary mapping each attribute to its value.

---
## method: `ResumePersonalSettings.to_dict(self: UnknownType) -> dict`

Return settings as a dictionary.

Returns:
    dict: Dictionary containing all settings with their respective boolean values.

Notes:
    1. The method constructs and returns a dictionary mapping each attribute to its value.

---
## `ResumeEducationSettings` class

Control what parts of a resume's education section are rendered.

Attributes:
    degrees (bool): Render all degrees (default is True).
    school (bool): Render school name (default is True).
    degree (bool): Render degree name (default is True).
    start_date (bool): Render start date of degree (default is True).
    end_date (bool): Render end date of degree (default is True).
    gpa (bool): Render GPA (default is True).
    major (bool): Render major of study (default is True).

Methods:
    __init__(default_init: bool = True) -> None
        Initialize all attributes to default_init.
    to_dict() -> dict
        Return a dictionary representation of the settings.

---
## method: `ResumeEducationSettings.__init__(self: UnknownType, default_init: bool) -> UnknownType`

Initialize everything to default_init.

Args:
    default_init (bool): Default initialization value for all attributes. Defaults to True.

Returns:
    None

Notes:
    1. All attributes are initialized to default_init.
    2. The to_dict method constructs and returns a dictionary mapping each attribute to its value.

---
## method: `ResumeEducationSettings.to_dict(self: UnknownType) -> dict`

Return a dictionary representation of the settings.

Returns:
    dict: Dictionary containing all education settings with their respective boolean values.

Notes:
    1. The method constructs and returns a dictionary mapping each attribute to its value.

---
## `ResumeCertificationsSettings` class

Control what parts of a resume's certifications section are rendered.

Attributes:
    name (bool): Whether to render the name of the certification.
    issuer (bool): Whether to render the issuer of the certification.
    issued (bool): Whether to render the date of issuance.
    expires (bool): Whether to render the expiration date of the certification.
    certification_id (bool): Whether to render the id of the certification.

Methods:
    __init__(default_init: bool = True) -> None
        Initialize all attributes to True.
    to_dict() -> dict
        Return a dictionary representation of the object.

---
## method: `ResumeCertificationsSettings.__init__(self: UnknownType, default_init: bool) -> UnknownType`

Initialize everything to default_init.

Args:
    default_init (bool): Default initialization value for all attributes. Defaults to True.

Returns:
    None

Notes:
    1. All attributes are initialized to default_init.
    2. The to_dict method constructs and returns a dictionary mapping each attribute to its value.

---
## method: `ResumeCertificationsSettings.to_dict(self: UnknownType) -> dict`

Return a dictionary representation of the object.

Returns:
    dict: Dictionary containing all certification settings with their respective boolean values.

Notes:
    1. The method constructs and returns a dictionary mapping each attribute to its value.

---
## `ResumeProjectsSettings` class

Control what parts of a resume's projects section are rendered.

Attributes:
    overview (bool): Whether to include the project overview.
    description (bool): Whether to include the project description.
    skills (bool): Whether to include the skills used in the project.
    title (bool): Whether to include the project title.
    url (bool): Whether to include the project URL.
    url_description (bool): Whether to include the description for the project URL.
    start_date (bool): Whether to include the project start date.
    end_date (bool): Whether to include the project end date.

Methods:
    __init__(default_init: bool)
        Initialize all attributes to True.
    to_dict() -> dict
        Return a dictionary representation of the class.

---
## method: `ResumeProjectsSettings.__init__(self: UnknownType, default_init: bool) -> UnknownType`

Initialize everything to default_init.

Args:
    default_init (bool): Default initialization value for all attributes.

Returns:
    None

Notes:
    1. All attributes are initialized to default_init.
    2. The to_dict method constructs and returns a dictionary mapping each attribute to its value.

---
## method: `ResumeProjectsSettings.to_dict(self: UnknownType) -> dict`

Return a dictionary representation of the class.

Returns:
    dict: Dictionary containing all project settings with their respective boolean values.

Notes:
    1. The method constructs and returns a dictionary mapping each attribute to its value.

---
## `ResumeRolesSettings` class

Control what parts of a resume's roles section are rendered.

Attributes:
    summary (bool): Whether to include the role summary.
    skills (bool): Whether to include the role skills.
    responsibilities (bool): Whether to include role responsibilities.
    reason_for_change (bool): Whether to include the reason for change.
    location (bool): Whether to include the role location.
    job_category (bool): Whether to include the role job category.
    employment_type (bool): Whether to include the role employment type.
    agency_name (bool): Whether to include the agency name.
    start_date (bool): Whether to include the role start date.
    end_date (bool): Whether to include the role end date.
    months_ago (int): Number of months ago the role ended.
    highlight_skills (bool): Whether to bold skills inline.
    include_situation (bool): Whether to include the situation in the role description.
    include_tasks (bool): Whether to include the tasks in the role description.

Methods:
    __init__(default_init: bool = True) -> None
        Initialize everything to default_init.
    to_dict() -> dict
        Return a dictionary representation of the class.

---
## method: `ResumeRolesSettings.__init__(self: UnknownType, default_init: bool) -> None`

Initialize everything to default_init.

Args:
    default_init (bool): Default initialization value for all attributes. Defaults to True.

Returns:
    None

Notes:
    1. All attributes are initialized to default_init.
    2. The to_dict method constructs and returns a dictionary mapping each attribute to its value.

---
## method: `ResumeRolesSettings.to_dict(self: UnknownType) -> dict`

Return a dictionary representation of the class.

Returns:
    dict: Dictionary containing all role settings with their respective boolean values.

Notes:
    1. The method constructs and returns a dictionary mapping each attribute to its value.

---
## `ResumeExperienceSettings` class

Control what parts of a resume's experience section are rendered.

Attributes:
    roles (bool): Flag to include roles in the rendered experience section.
    roles_settings (ResumeRolesSettings): Settings for rendering roles in the experience section.
    projects (bool): Flag to include projects in the rendered experience section.
    projects_settings (ResumeProjectsSettings): Settings for rendering projects in the experience section.
    executive_summary (bool): Flag to include executive summary in the rendered experience section.
    executive_summary_settings (ResumeExecutiveSummarySettings): Settings for rendering executive summary in the experience section.
    skills_matrix (bool): Flag to include skills matrix in the rendered experience section.
    skills_matrix_settings (ResumeSkillsMatrixSettings): Settings for rendering skills matrix in the experience section.

Methods:
    update_from_dict(data_dict: dict | None = None) -> None
        Update settings for experience and subsections from a dictionary.
    to_dict() -> dict
        Convert settings for experience and subsections to a dictionary.

---
## method: `ResumeExperienceSettings.__init__(self: UnknownType, default_init: bool) -> None`

Initialize all attributes to default_init and create settings objects.

Args:
    default_init (bool): Default initialization value for all attributes. Defaults to True.

Returns:
    None

Notes:
    1. Initialize roles, projects, executive_summary, and skills_matrix to default_init.
    2. Create ResumeRolesSettings, ResumeProjectsSettings, ResumeExecutiveSummarySettings,
       and ResumeSkillsMatrixSettings objects.

---
## method: `ResumeExperienceSettings.update_from_dict(self: UnknownType, data_dict: dict | None) -> None`

Update settings for experience and subsections from a dictionary.

Args:
    data_dict (dict | None): Dictionary containing settings for experience and subsections.

Returns:
    None

Notes:
    1. The method updates settings for subsections by extracting the 'section' key
       from the dictionary and applying updates to corresponding settings objects.
    2. The method calls the parent class's update_from_dict method to update base settings.

---
## method: `ResumeExperienceSettings.to_dict(self: UnknownType) -> dict`

Convert settings for experience and subsections to a dictionary.

Returns:
    dict: Dictionary containing settings for experience and subsections.

Notes:
    1. The method constructs a dictionary with keys for roles, projects, executive_summary,
       and skills_matrix, and their corresponding values.
    2. If the value for a key is True, the corresponding settings object is converted to a dictionary
       and added to the dictionary.

---
## `ResumeExecutiveSummarySettings` class

Control settings for rendering the executive summary section of a resume.

Attributes:
    categories (list[str]): List of categories to include in the summary.

Methods:
    update_from_dict(data_dict: dict | None = None) -> None
        Update settings from a dictionary.
    to_dict() -> dict
        Return a dictionary representation of the settings.

---
## method: `ResumeExecutiveSummarySettings.__init__(self: UnknownType) -> None`

Initialize everything to True.

Returns:
    None

Notes:
    1. Initialize categories as an empty list.

---
## method: `ResumeExecutiveSummarySettings.update_from_dict(self: UnknownType, data_dict: dict | None) -> None`

Control what categories are rendered.

Args:
    data_dict (dict | None): Dictionary containing settings for the executive summary.

Returns:
    None

Notes:
    1. The method updates settings from a dictionary.
    2. If categories are provided in the dictionary, split them into a list.

---
## method: `ResumeExecutiveSummarySettings.to_dict(self: UnknownType) -> dict`

Return a dictionary representation of the settings.

Returns:
    dict: Dictionary containing the categories as a string separated by newlines.

Notes:
    1. The method returns a dictionary with categories joined by newlines.

---
## `ResumeSkillsMatrixSettings` class

Control what parts of a resume's skills matrix section are rendered.

Attributes:
    skills (list[str]): List of skills to be rendered.
    all_skills (bool): Flag to indicate if all skills should be rendered.

Methods:
    update_from_dict(data_dict: dict | None = None) -> None
        Update settings from a dictionary.
    to_dict() -> dict
        Return a dictionary representation of the settings.

---
## method: `ResumeSkillsMatrixSettings.__init__(self: UnknownType) -> None`

Initialize everything.

Returns:
    None

Notes:
    1. Initialize skills as an empty list and all_skills as False.

---
## method: `ResumeSkillsMatrixSettings.update_from_dict(self: UnknownType, data_dict: dict | None) -> None`

Control what skills are rendered.

Args:
    data_dict (dict | None): Dictionary containing settings for the skills matrix.

Returns:
    None

Notes:
    1. The method updates settings from a dictionary.
    2. If skills are provided, split the skills string into a list.

---
## method: `ResumeSkillsMatrixSettings.to_dict(self: UnknownType) -> dict`

Return a dictionary representation of the settings.

Returns:
    dict: Dictionary containing skills as a string separated by newlines and all_skills as a boolean.

Notes:
    1. The method returns a dictionary with skills joined by newlines.

---
## `ResumeRenderSettings` class

Control what parts of a resume are rendered.

Attributes:
    personal_settings (ResumePersonalSettings): Settings for personal information.
    personal (bool): Flag to include personal information.
    education_settings (ResumeEducationSettings): Settings for education information.
    education (bool): Flag to include education information.
    certifications_settings (ResumeCertificationsSettings): Settings for certifications information.
    certifications (bool): Flag to include certifications information.
    experience_settings (ResumeExperienceSettings): Settings for experience information.
    experience (bool): Flag to include experience information.
    skills_matrix (bool): Flag to include skills matrix information.
    skills_matrix_settings (ResumeSkillsMatrixSettings): Settings for skills matrix information.
    executive_summary (bool): Flag to include executive summary information.
    executive_summary_settings (ResumeExecutiveSummarySettings): Settings for executive summary information.
    font_size (int): Font size in points.
    margin_width (float): Margin width in inches.
    top_margin (float): Top margin in inches.
    bottom_margin (float): Bottom margin in inches.

Methods:
    update_from_dict(data_dict: dict | None = None) -> None
        Update settings for resume and subsections.
    to_dict() -> dict
        Convert settings for resume and subsections to a dictionary.

---
## method: `ResumeRenderSettings.__init__(self: UnknownType, default_init: bool) -> UnknownType`

Initialize all settings with appropriate objects.

Args:
    default_init (bool): Default initialization value for all attributes. Defaults to True.

Returns:
    None

Notes:
    1. Initialize all settings with appropriate objects.
    2. The font_size is set to 12.
    3. The margin_width is set to 0.5.
    4. The top_margin is set to 0.5.
    5. The bottom_margin is set to 0.5.

---
## method: `ResumeRenderSettings.update_from_dict(self: UnknownType, data_dict: dict | None) -> None`

Update settings for resume and subsections.

Args:
    data_dict (dict | None): Dictionary containing data to update settings.

Returns:
    None

Notes:
    1. The method updates settings for subsections by extracting the 'section' key
       from the dictionary and applying updates to corresponding settings objects.
    2. The method calls the parent class's update_from_dict method to update base settings.

---
## method: `ResumeRenderSettings.to_dict(self: UnknownType) -> dict`

Convert settings for resume and subsections to a dictionary.

Returns:
    dict: Dictionary containing all settings.

Notes:
    1. The method constructs and returns a dictionary containing all settings,
       including subsection settings.

---

===

===
# File: `resume_writer/resume_render/resume_render_text_base.py`

## `RenderBase` class

Base class for rendering HTML files.

Used for common functionality between the different renderers,
primarily error and warning collection.

Attributes:
    errors (list[str]): List of errors encountered during rendering.
    warnings (list[str]): List of warnings encountered during rendering.
    document (TextDoc): The text document to be rendered.
    jinja_env (Environment | None): The Jinja2 environment for template rendering.

Notes:
    1. Initializes the errors and warnings lists as empty.
    2. Validates that the document is an instance of TextDoc.
    3. Validates that jinja_env is either None or an instance of Environment.
    4. Assigns the provided document and jinja_env to instance attributes.

---
## method: `RenderBase.__init__(self: UnknownType, document: TextDoc, jinja_env: Environment | None) -> UnknownType`

Initialize superclass.

Args:
    document (TextDoc): The text document to be rendered.
    jinja_env (Environment | None): The Jinja2 environment for template rendering.

Notes:
    1. Initializes the errors and warnings lists as empty.
    2. Validates that the document is an instance of TextDoc.
    3. Validates that jinja_env is either None or an instance of Environment.
    4. Assigns the provided document and jinja_env to instance attributes.

---
## method: `RenderBase.save(self: UnknownType, path: Path) -> None`

Save the document to the given path.

Args:
    path (Path): The file system path to save the document.

Returns:
    None

Notes:
    1. Opens the file at the given path in write mode.
    2. Writes the document's text content to the file.
    3. Closes the file.

---
## method: `RenderBase.add_error(self: UnknownType, error: str) -> None`

Add an error to the list of errors.

Args:
    error (str): The error message to add.

Returns:
    None

Notes:
    1. Appends the error message to the errors list.

---
## method: `RenderBase.add_warning(self: UnknownType, warning: str) -> None`

Add a warning to the list of warnings.

Args:
    warning (str): The warning message to add.

Returns:
    None

Notes:
    1. Appends the warning message to the warnings list.

---
## `ResumeRenderBase` class

Base class for rendering resumes.

Attributes:
    settings (ResumeRenderSettings): The rendering settings for the resume.
    resume (Resume): The resume data to be rendered.
    errors (list[str]): List of errors encountered during rendering.
    warnings (list[str]): List of warnings encountered during rendering.
    document (TextDoc): The text document to be rendered.
    jinja_env (Environment | None): The Jinja2 environment for template rendering.

Notes:
    1. Validates that resume is an instance of Resume.
    2. Validates that settings is either None or an instance of ResumeRenderSettings.
    3. Validates that document is an instance of TextDoc.
    4. Validates that jinja_env is either None or an instance of Environment.
    5. If settings is None, initializes settings with a new ResumeRenderSettings instance.
    6. Calls the superclass constructor to initialize common attributes.

---
## method: `ResumeRenderBase.__init__(self: UnknownType, document: TextDoc, jinja_env: Environment | None, resume: Resume, settings: ResumeRenderSettings | None) -> UnknownType`

Initialize superclass.

Args:
    document (TextDoc): The text document to be rendered.
    jinja_env (Environment | None): The Jinja2 environment for template rendering.
    resume (Resume): The resume data to be rendered.
    settings (ResumeRenderSettings | None): The rendering settings for the resume.

Notes:
    1. Validates that resume is an instance of Resume.
    2. Validates that settings is either None or an instance of ResumeRenderSettings.
    3. Validates that document is an instance of TextDoc.
    4. Validates that jinja_env is either None or an instance of Environment.
    5. If settings is None, initializes settings with a new ResumeRenderSettings instance.
    6. Calls the superclass constructor to initialize common attributes.

---
## `ResumeRenderPersonalBase` class

Base class for rendering resume personal section.

This class handles rendering of personal information such as name, contact details, and profile summary.

Attributes:
    settings (ResumePersonalSettings): The rendering settings for the personal section.
    personal (Personal): The personal data to be rendered.
    template (Template | None): The Jinja2 template for rendering, if template_name is provided.
    errors (list[str]): List of errors encountered during rendering.
    warnings (list[str]): List of warnings encountered during rendering.
    document (TextDoc): The text document to be rendered.
    jinja_env (Environment): The Jinja2 environment for template rendering.

Notes:
    1. Validates that document is an instance of TextDoc.
    2. Validates that personal is an instance of Personal.
    3. Validates that settings is an instance of ResumePersonalSettings.
    4. Validates that template_name is a string.
    5. Calls the superclass constructor to initialize common attributes.
    6. Assigns the provided settings and personal data to instance attributes.
    7. If template_name is provided, loads the corresponding Jinja2 template.

---
## method: `ResumeRenderPersonalBase.__init__(self: UnknownType, document: TextDoc, jinja_env: Environment, personal: Personal, template_name: str, settings: ResumePersonalSettings) -> UnknownType`

Initialize personal renderer.

Args:
    document (TextDoc): The text document to be rendered.
    jinja_env (Environment): The Jinja2 environment for template rendering.
    personal (Personal): The personal data to be rendered.
    template_name (str): The name of the Jinja2 template to use for rendering.
    settings (ResumePersonalSettings): The rendering settings for the personal section.

Notes:
    1. Validates that document is an instance of TextDoc.
    2. Validates that personal is an instance of Personal.
    3. Validates that settings is an instance of ResumePersonalSettings.
    4. Validates that template_name is a string.
    5. Calls the superclass constructor to initialize common attributes.
    6. Assigns the provided settings and personal data to instance attributes.
    7. If template_name is provided, loads the corresponding Jinja2 template.

---
## `ResumeRenderRolesBase` class

Base class for rendering resume roles section.

This class handles filtering and rendering of job roles based on time constraints.

Attributes:
    _roles (Roles): The list of job roles to be rendered.
    settings (ResumeRolesSettings): The rendering settings for the roles section.
    template (Template | None): The Jinja2 template for rendering, if template_name is provided.
    errors (list[str]): List of errors encountered during rendering.
    warnings (list[str]): List of warnings encountered during rendering.
    document (TextDoc): The text document to be rendered.
    jinja_env (Environment | None): The Jinja2 environment for template rendering.

Notes:
    1. Validates that document is an instance of TextDoc.
    2. Validates that roles is an instance of Roles.
    3. Validates that settings is an instance of ResumeRolesSettings.
    4. Validates that template_name is a string.
    5. Validates that jinja_env is either None or an instance of Environment.
    6. Calls the superclass constructor to initialize common attributes.
    7. Assigns the provided roles and settings to instance attributes.
    8. If template_name is provided, loads the corresponding Jinja2 template.

---
## method: `ResumeRenderRolesBase.__init__(self: UnknownType, document: TextDoc, jinja_env: Environment | None, roles: Roles, template_name: str, settings: ResumeRolesSettings) -> UnknownType`

Initialize the roles section.

Args:
    document (TextDoc): The text document to be rendered.
    jinja_env (Environment | None): The Jinja2 environment for template rendering.
    roles (Roles): The list of job roles to be rendered.
    template_name (str): The name of the Jinja2 template to use for rendering.
    settings (ResumeRolesSettings): The rendering settings for the roles section.

Notes:
    1. Validates that document is an instance of TextDoc.
    2. Validates that roles is an instance of Roles.
    3. Validates that settings is an instance of ResumeRolesSettings.
    4. Validates that template_name is a string.
    5. Validates that jinja_env is either None or an instance of Environment.
    6. Calls the superclass constructor to initialize common attributes.
    7. Assigns the provided roles and settings to instance attributes.
    8. If template_name is provided, loads the corresponding Jinja2 template.

---
## method: `ResumeRenderRolesBase.roles(self: UnknownType) -> list[Role]`

Return roles which have not been filtered out.

Returns:
    list[Role]: A list of roles that are not older than the specified number of months.

Notes:
    1. Initializes an empty list to store filtered roles.
    2. Iterates over each role in the _roles list.
    3. If the settings specify a number of months ago, checks if the role's end date is older than that time.
    4. If the role is older than the specified time, skips it.
    5. Otherwise, adds the role to the filtered list.
    6. Returns the filtered list of roles.

---
## `ResumeRenderProjectsBase` class

Base class for rendering resume projects section.

This class handles rendering of projects based on provided settings.

Attributes:
    projects (Projects): The list of projects to be rendered.
    settings (ResumeProjectsSettings): The rendering settings for the projects section.
    template (Template | None): The Jinja2 template for rendering, if template_name is provided.
    errors (list[str]): List of errors encountered during rendering.
    warnings (list[str]): List of warnings encountered during rendering.
    document (TextDoc): The text document to be rendered.
    jinja_env (Environment): The Jinja2 environment for template rendering.

Notes:
    1. Validates that document is an instance of TextDoc.
    2. Validates that projects is an instance of Projects.
    3. Validates that settings is an instance of ResumeProjectsSettings.
    4. Validates that template_name is a string.
    5. Validates that jinja_env is either None or an instance of Environment.
    6. Calls the superclass constructor to initialize common attributes.
    7. Assigns the provided projects and settings to instance attributes.
    8. If template_name is provided, loads the corresponding Jinja2 template.

---
## method: `ResumeRenderProjectsBase.__init__(self: UnknownType, document: TextDoc, jinja_env: Environment, projects: Projects, template_name: str, settings: ResumeProjectsSettings) -> UnknownType`

Initialize the projects section.

Args:
    document (TextDoc): The text document to be rendered.
    jinja_env (Environment): The Jinja2 environment for template rendering.
    projects (Projects): The list of projects to be rendered.
    template_name (str): The name of the Jinja2 template to use for rendering.
    settings (ResumeProjectsSettings): The rendering settings for the projects section.

Notes:
    1. Validates that document is an instance of TextDoc.
    2. Validates that projects is an instance of Projects.
    3. Validates that settings is an instance of ResumeProjectsSettings.
    4. Validates that template_name is a string.
    5. Validates that jinja_env is either None or an instance of Environment.
    6. Calls the superclass constructor to initialize common attributes.
    7. Assigns the provided projects and settings to instance attributes.
    8. If template_name is provided, loads the corresponding Jinja2 template.

---
## `ResumeRenderExperienceBase` class

Base class for rendering resume experience section.

This class handles rendering of experience sections, including roles.

Attributes:
    experience (Experience): The experience data to be rendered.
    settings (ResumeRolesSettings): The rendering settings for the roles section.
    document (TextDoc): The text document to be rendered.
    jinja_env (Environment): The Jinja2 environment for template rendering.
    errors (list[str]): List of errors encountered during rendering.
    warnings (list[str]): List of warnings encountered during rendering.

Notes:
    1. Validates that experience is an instance of Experience.
    2. Validates that settings is an instance of ResumeExperienceSettings.
    3. Validates that jinja_env is either None or an instance of Environment.
    4. Validates that document is an instance of TextDoc.
    5. Calls the superclass constructor to initialize common attributes.
    6. Assigns the provided experience and settings to instance attributes.

---
## method: `ResumeRenderExperienceBase.__init__(self: UnknownType, document: TextDoc, jinja_env: Environment, experience: Experience, settings: ResumeRolesSettings) -> UnknownType`

Initialize the roles section.

Args:
    document (TextDoc): The text document to be rendered.
    jinja_env (Environment): The Jinja2 environment for template rendering.
    experience (Experience): The experience data to be rendered.
    settings (ResumeRolesSettings): The rendering settings for the roles section.

Notes:
    1. Validates that experience is an instance of Experience.
    2. Validates that settings is an instance of ResumeExperienceSettings.
    3. Validates that jinja_env is either None or an instance of Environment.
    4. Validates that document is an instance of TextDoc.
    5. Calls the superclass constructor to initialize common attributes.
    6. Assigns the provided experience and settings to instance attributes.

---
## `ResumeRenderEducationBase` class

Base class for rendering resume education section.

This class handles rendering of educational qualifications.

Attributes:
    education (Education): The education data to be rendered.
    settings (ResumeEducationSettings): The rendering settings for the education section.
    template (Template | None): The Jinja2 template for rendering, if template_name is provided.
    document (TextDoc): The text document to be rendered.
    jinja_env (Environment): The Jinja2 environment for template rendering.
    errors (list[str]): List of errors encountered during rendering.
    warnings (list[str]): List of warnings encountered during rendering.

Notes:
    1. Validates that education is an instance of Education.
    2. Validates that settings is an instance of ResumeEducationSettings.
    3. Validates that template_name is a string.
    4. Validates that jinja_env is either None or an instance of Environment.
    5. Calls the superclass constructor to initialize common attributes.
    6. Assigns the provided education and settings to instance attributes.
    7. If template_name is provided, loads the corresponding Jinja2 template.

---
## method: `ResumeRenderEducationBase.__init__(self: UnknownType, document: TextDoc, jinja_env: Environment, education: Education, template_name: str, settings: ResumeEducationSettings) -> UnknownType`

Initialize the education rendering section.

Args:
    document (TextDoc): The text document to be rendered.
    jinja_env (Environment): The Jinja2 environment for template rendering.
    education (Education): The education data to be rendered.
    template_name (str): The name of the Jinja2 template to use for rendering.
    settings (ResumeEducationSettings): The rendering settings for the education section.

Notes:
    1. Validates that education is an instance of Education.
    2. Validates that settings is an instance of ResumeEducationSettings.
    3. Validates that template_name is a string.
    4. Validates that jinja_env is either None or an instance of Environment.
    5. Calls the superclass constructor to initialize common attributes.
    6. Assigns the provided education and settings to instance attributes.
    7. If template_name is provided, loads the corresponding Jinja2 template.

---
## method: `ResumeRenderEducationBase.degrees(self: UnknownType) -> None`

Render degrees section of education.

Returns:
    None

Notes:
    1. This method is currently a placeholder and not implemented.

---
## method: `ResumeRenderEducationBase.render(self: UnknownType) -> None`

Render education section.

Returns:
    None

Notes:
    1. This method is currently a placeholder and not implemented.

---
## `ResumeRenderCertificationsBase` class

Base class for rendering resume certifications section.

This class handles rendering of certifications based on provided settings.

Attributes:
    settings (ResumeCertificationsSettings): The rendering settings for the certifications section.
    certifications (Certifications): The certifications data to be rendered.
    template (Template | None): The Jinja2 template for rendering, if template_name is provided.
    document (str): The text document to be rendered.
    jinja_env (Environment): The Jinja2 environment for template rendering.
    errors (list[str]): List of errors encountered during rendering.
    warnings (list[str]): List of warnings encountered during rendering.

Notes:
    1. Validates that certifications is an instance of Certifications.
    2. Validates that settings is an instance of ResumeCertificationsSettings.
    3. Validates that template_name is a string.
    4. Validates that jinja_env is either None or an instance of Environment.
    5. Calls the superclass constructor to initialize common attributes.
    6. Assigns the provided settings and certifications to instance attributes.
    7. If template_name is provided, loads the corresponding Jinja2 template.

---
## method: `ResumeRenderCertificationsBase.__init__(self: UnknownType, document: str, certifications: Certifications, jinja_env: Environment, template_name: str, settings: ResumeCertificationsSettings) -> UnknownType`

Initialize certification renderer.

Args:
    document (str): The text document to be rendered.
    certifications (Certifications): The certifications data to be rendered.
    jinja_env (Environment): The Jinja2 environment for template rendering.
    template_name (str): The name of the Jinja2 template to use for rendering.
    settings (ResumeCertificationsSettings): The rendering settings for the certifications section.

Notes:
    1. Validates that certifications is an instance of Certifications.
    2. Validates that settings is an instance of ResumeCertificationsSettings.
    3. Validates that template_name is a string.
    4. Validates that jinja_env is either None or an instance of Environment.
    5. Calls the superclass constructor to initialize common attributes.
    6. Assigns the provided settings and certifications to instance attributes.
    7. If template_name is provided, loads the corresponding Jinja2 template.

---
## `ResumeRenderExecutiveSummaryBase` class

Base class for rendering resume executive summary section.

This class handles rendering of executive summary based on experience data.

Attributes:
    experience (Experience): The experience data to be used for generating the summary.
    document (str): The text document to be rendered.
    settings (ResumeExecutiveSummarySettings): The rendering settings for the executive summary.
    errors (list[str]): List of errors encountered during rendering.
    warnings (list[str]): List of warnings encountered during rendering.

Notes:
    1. Validates that experience is an instance of Experience.
    2. Validates that settings is an instance of ResumeExecutiveSummarySettings.
    3. Calls the superclass constructor to initialize common attributes.
    4. Assigns the provided experience and settings to instance attributes.

---
## method: `ResumeRenderExecutiveSummaryBase.__init__(self: UnknownType, document: str, experience: Experience, settings: ResumeExecutiveSummarySettings) -> None`

Initialize the executive summary section.

Args:
    document (str): The text document to be rendered.
    experience (Experience): The experience data to be used for generating the summary.
    settings (ResumeExecutiveSummarySettings): The rendering settings for the executive summary.

Notes:
    1. Validates that experience is an instance of Experience.
    2. Validates that settings is an instance of ResumeExecutiveSummarySettings.
    3. Calls the superclass constructor to initialize common attributes.
    4. Assigns the provided experience and settings to instance attributes.

---
## `ResumeRenderSkillsMatrixBase` class

Base class for rendering resume skills matrix section.

This class handles rendering of skills matrix based on experience data.

Attributes:
    experience (Experience): The experience data to be used for generating the skills matrix.
    document (str): The text document to be rendered.
    settings (ResumeSkillsMatrixSettings): The rendering settings for the skills matrix.
    errors (list[str]): List of errors encountered during rendering.
    warnings (list[str]): List of warnings encountered during rendering.

Notes:
    1. Validates that experience is an instance of Experience.
    2. Validates that settings is an instance of ResumeSkillsMatrixSettings.
    3. Calls the superclass constructor to initialize common attributes.
    4. Assigns the provided experience and settings to instance attributes.

---
## method: `ResumeRenderSkillsMatrixBase.__init__(self: UnknownType, document: str, experience: Experience, settings: ResumeSkillsMatrixSettings) -> None`

Initialize the skills matrix section.

Args:
    document (str): The text document to be rendered.
    experience (Experience): The experience data to be used for generating the skills matrix.
    settings (ResumeSkillsMatrixSettings): The rendering settings for the skills matrix.

Notes:
    1. Validates that experience is an instance of Experience.
    2. Validates that settings is an instance of ResumeSkillsMatrixSettings.
    3. Calls the superclass constructor to initialize common attributes.
    4. Assigns the provided experience and settings to instance attributes.

---

===

===
# File: `resume_writer/resume_render/plain/__init__.py`

## function: `render_resume(resume: Resume, output_file: str) -> None`

Render a resume object to plain text format and save it to a file.

Args:
    resume (Resume): The resume object containing all resume data.
    output_file (str): The path to the output file where the plain text resume will be saved.

Returns:
    None: This function does not return a value.

Notes:
    1. The function retrieves the resume data from the Resume object using the to_dict() method.
    2. It constructs a list of strings representing each line of the plain text resume.
    3. For each key-value pair in the resume data:
        a. If the value is a list, it appends the key followed by a colon to the lines list.
        b. Then, for each item in the list, it appends a line with two spaces of indentation and a dash.
    4. If the value is not a list, it appends a line with the key, a colon, and the value.
    5. The function writes the resulting plain text content to the specified output file.
    6. The function performs disk access to write the plain text content to the output file.

---


===

===
# File: `resume_writer/resume_render/plain/executive_summary_section.py`

## `RenderExecutiveSummarySection` class

Render executive summary section for a functional resume.

Attributes:
    document (docx.document.Document): The Word document object to render the section into.
    experience (Experience): The experience data to be rendered.
    settings (ResumeExecutiveSummarySettings): Configuration settings for rendering the executive summary.

---
## method: `RenderExecutiveSummarySection.__init__(self: UnknownType, document: docx.document.Document, experience: Experience, settings: ResumeExecutiveSummarySettings) -> None`

Initialize executive summary render object.

Args:
    document (docx.document.Document): The Word document object to render the section into.
    experience (Experience): The experience data to be rendered.
    settings (ResumeExecutiveSummarySettings): Configuration settings for rendering the executive summary.

Returns:
    None

Notes:
    1. Set up the base class with the provided document, experience, and settings.
    2. Log the initialization process for debugging.

---
## method: `RenderExecutiveSummarySection.render(self: UnknownType) -> None`

Render executive summary section for functional resume.

Args:
    None

Returns:
    None

Notes:
    1. Validate that the experience has at least one role; raise ValueError if not.
    2. Create an ExecutiveSummary instance using the experience data.
    3. Generate the executive summary using the specified categories from settings.
    4. For each category in the summary:
        a. Add a heading with level 4 to the document.
        b. For each summary entry in the category:
            i. Add a new paragraph with the bullet point style.
            ii. Add the summary text as a run in the paragraph.
            iii. If no company is available, log a warning.
            iv. Otherwise, format the company and date:
                - If a last_date is present, format it as YYYY.
                - Otherwise, use "Present".
            v. Add the company and date as italicized text to the paragraph.
    5. No disk or network access occurs during this function.

---

===

===
# File: `resume_writer/resume_render/plain/personal_section.py`

## `RenderPersonalSection` class

Render personal contact info section.

This class is responsible for rendering the personal information section of a resume,
including contact details, banner, note, websites, and visa status.

Attributes:
    document (docx.document.Document): The Word document to which the personal section will be added.
    personal (Personal): The personal information object containing contact details, banner, note, websites, and visa status.
    settings (ResumePersonalSettings): The settings object that controls which elements of the personal section are rendered.

---
## method: `RenderPersonalSection.__init__(self: UnknownType, document: docx.document.Document, personal: Personal, settings: ResumePersonalSettings) -> UnknownType`

Initialize the personal section renderer.

Parameters
----------
document : docx.document.Document
    The Word document object to which the personal section will be added.
personal : Personal
    The personal information object containing contact details, banner, note, websites, and visa status.
settings : ResumePersonalSettings
    The settings object that controls which elements of the personal section are rendered.

Notes
-----
1. Initialize the base class with the provided document, personal data, and settings.
2. Log a debug message indicating initialization is complete.

---
## method: `RenderPersonalSection._contact_info(self: UnknownType) -> None`

Render the contact information section of the resume.

Parameters
----------
self : RenderPersonalSection
    The instance of the class containing the personal and settings attributes.

Notes
-----
1. Log a debug message indicating the section being rendered.
2. Extract the contact information from the personal attribute.
3. If a name is present in both the contact info and settings, add it as a heading.
4. Determine which contact details to render based on the settings.
5. If any contact details are to be rendered, add a new paragraph to the document.
6. If the email is to be rendered, add it as a hyperlink to the paragraph.
7. If the phone number is to be rendered, add it to the paragraph.
8. If the location is to be rendered, add it to the paragraph.

Returns
-------
None
    The method modifies the document in-place.

---
## method: `RenderPersonalSection._banner(self: UnknownType) -> None`

Render the banner section.

Parameters
----------
self : RenderPersonalSection
    The instance of the class containing the personal and settings attributes.

Notes
-----
1. Log a debug message indicating the section being rendered.
2. Retrieve the banner text from the personal object.
3. If the banner text is not empty, add a heading and the banner text to the document.

Returns
-------
None
    The method modifies the document in-place.

---
## method: `RenderPersonalSection._note(self: UnknownType) -> None`

Render the note section.

Parameters
----------
self : RenderPersonalSection
    The instance of the class containing the personal and settings attributes.

Notes
-----
1. Log a debug message indicating the section being rendered.
2. Retrieve the note text from the personal object.
3. If the note text is not empty, add a heading and the note text to the document.

Returns
-------
None
    The method modifies the document in-place.

---
## method: `RenderPersonalSection._websites(self: UnknownType) -> str | None`

Render the websites section of a resume.

Parameters
----------
self : RenderPersonalSection
    The instance of the class containing the personal and settings attributes.

Notes
-----
1. Log a debug message indicating that the websites section is being rendered.
2. Retrieve the user's websites from the personal object.
3. Initialize an empty string for the paragraph text and a new paragraph object.
4. Check if the user's GitHub profile is provided and if the GitHub setting is enabled. If so, add a hyperlink to the GitHub profile to the paragraph and set the has_content flag to True.
5. Repeat step 4 for the LinkedIn, website, and Twitter profiles.
6. If the paragraph has content, set its alignment to center.

Returns
-------
None
    The method modifies the document in-place.

---
## method: `RenderPersonalSection._visa_status(self: UnknownType) -> None`

Render the visa status section.

Parameters
----------
self : RenderPersonalSection
    The instance of the class containing the personal and settings attributes.

Notes
-----
1. Create a new paragraph and set its alignment to center.
2. Retrieve the visa status object from the personal data.
3. If work authorization is enabled and present, add it to the paragraph.
4. If sponsorship requirement is enabled, determine if the value is "Yes" or "No" and add the appropriate text.
5. If both work authorization and sponsorship are present, add a separator "|".

Returns
-------
None
    The method modifies the document in-place.

---
## method: `RenderPersonalSection.render(self: UnknownType) -> None`

Render the personal section of a document.

Parameters
----------
self : RenderPersonalSection
    The instance of the class containing the personal information.

Notes
-----
1. Log a debug message indicating the start of personal section rendering.
2. Initialize an empty list for banner lines.
3. Add contact information to the document if enabled in settings.
4. Add websites to the document if enabled in settings.
5. Append banner text to banner lines if enabled in settings and not empty.
6. Append note text to banner lines if enabled in settings and not empty.
7. Add banner lines to the document if any exist.
8. Add visa status to the document if enabled in settings.

Returns
-------
None
    The method modifies the document in-place.

---

===

===
# File: `resume_writer/resume_render/plain/resume_main.py`

## `RenderResume` class

Render a resume in basic format.

Attributes:
    document (docx.document.Document): The Word document object to render into.
    resume (Resume): The parsed resume data structure containing personal, education, experience, certifications, and other sections.
    settings (ResumeRenderSettings): Configuration settings for rendering, including which sections to render and their formatting options.
    parse_context (ParseContext): The context used for parsing the resume data.

---
## method: `RenderResume.__init__(self: UnknownType, document: docx.document.Document, resume: Resume, settings: ResumeRenderSettings) -> UnknownType`

Initialize basic resume renderer.

Args:
    document (docx.document.Document): The Word document object to render into.
    resume (Resume): The parsed resume data structure containing personal, education, experience, certifications, and other sections.
    settings (ResumeRenderSettings): Configuration settings for rendering, including which sections to render and their formatting options.

Returns:
    None

Notes:
    1. Stores the provided document, resume, and settings as instance attributes.
    2. Initializes the base class ResumeRenderBase with the provided document, resume, and settings.
    3. No external disk, network, or database access occurs during initialization.

---
## method: `RenderResume.render(self: UnknownType) -> None`

Render the resume by sequentially rendering each enabled section.

Args:
    None

Returns:
    None

Notes:
    1. If personal information is present in the resume and personal section rendering is enabled, render the personal section.
    2. If certifications are present and certification section rendering is enabled, render the certifications section.
    3. If education data exists and education section rendering is enabled, render the education section.
    4. If experience data exists and executive summary rendering is enabled, add a centered heading "Executive Summary", then render the executive summary section using experience data.
    5. If experience data exists and skills matrix rendering is enabled (but not necessarily executive summary), render the skills matrix section using experience data.
    6. If both experience and executive summary rendering are enabled, insert a page break after the executive summary.
    7. If experience data exists and experience section rendering is enabled, render the full experience section.
    8. No external disk, network, or database access occurs during rendering.

---

===

===
# File: `resume_writer/resume_render/plain/skills_matrix_section.py`

## `RenderSkillsMatrixSection` class

Render skills for a functional resume.

Attributes:
    document (docx.document.Document): The DOCX document object to render the skills matrix into.
    experience (Experience): The experience data containing roles and skill information.
    settings (ResumeSkillsMatrixSettings): Configuration settings for rendering the skills matrix.
    parse_context (ParseContext): The context used for parsing input data (e.g., from resume text).

---
## method: `RenderSkillsMatrixSection.__init__(self: UnknownType, document: docx.document.Document, experience: Experience, settings: ResumeSkillsMatrixSettings, parse_context: ParseContext) -> None`

Initialize skills render object.

Args:
    document (docx.document.Document): The DOCX document object to render the skills matrix into.
    experience (Experience): The experience data containing roles and skill information.
    settings (ResumeSkillsMatrixSettings): Configuration settings for rendering the skills matrix.
    parse_context (ParseContext): The context used for parsing input data (e.g., from resume text).

Returns:
    None

Notes:
    1. Validate that the parse_context is an instance of ParseContext.
    2. Store the parse_context for later use during rendering.
    3. Call the parent class's constructor to initialize shared functionality.

---
## method: `RenderSkillsMatrixSection.render(self: UnknownType) -> None`

Render skills section for functional resume.

Args:
    None

Returns:
    None

Notes:
    1. Check if the experience object has any roles. Raise a ValueError if not.
    2. Create a SkillsMatrix instance from the experience's roles.
    3. If the settings specify all_skills, generate a matrix for all skills using "*" as the skill name.
    4. Otherwise, generate a matrix for the skills specified in settings.skills.
    5. Calculate the number of table rows needed to display the skills (two skills per row).
    6. Add a table with the calculated rows and 4 columns, using the "Table Grid" style.
    7. Add a header row with bolded labels for "Skill" and "YOE (from - to)" in alternating columns.
    8. Iterate through the sorted skills and their data:
        a. Determine the correct row and column index for placement.
        b. Insert the skill name into the first column of the row.
        c. Align the skill text vertically in the center.
        d. Format the YOE string as "X years (from - to)" using first_used and last_used dates.
        e. Insert the formatted YOE string into the second column.
    9. Enable automatic table fitting to adjust column widths.
    10. No disk or network access is performed during this function.

---

===

===
# File: `resume_writer/resume_render/plain/certifications_section.py`

## `RenderCertificationSection` class

Render a single certification entry in a resume document.

Attributes:
    document (docx.document.Document): The Word document object to render into.
    certification (Certification): The certification data to render.
    settings (ResumeCertificationsSettings): The rendering settings for the certification section.

Base Class:
    ResumeRenderCertificationBase: Base class providing shared rendering functionality.

---
## method: `RenderCertificationSection.__init__(self: UnknownType, document: docx.document.Document, certification: Certification, settings: ResumeCertificationsSettings) -> UnknownType`

Initialize the basic certification renderer.

Args:
    document (docx.document.Document): The Word document object to render into.
    certification (Certification): The certification data to render.
    settings (ResumeCertificationsSettings): The rendering settings for the certification section.

Notes:
    1. Initializes the parent class with the provided document, certification, and settings.

---
## method: `RenderCertificationSection.render(self: UnknownType) -> None`

Render the certification section in the document.

Args:
    None

Returns:
    None: This method modifies the document in-place and does not return a value.

Notes:
    1. Retrieve the certification data from the instance.
    2. Create a new paragraph in the document with no space after it.
    3. Add a right-aligned tab stop at 7.4 inches.
    4. If the certification name exists and the name setting is enabled:
       a. Add a bold run with the certification name.
    5. If the issuer exists and the issuer setting is enabled:
       a. Add a tab character if the name was previously added.
       b. Add a run with the issuer name.
    6. If the issued date exists and the issued setting is enabled:
       a. Add a newline if a previous field (name or issuer) was added.
       b. Format the issued date as "Month YYYY".
       c. Add a run with "Issued: " followed by the formatted date.
    7. If the expiration date exists and the expires setting is enabled:
       a. Add a " - " separator if the issued date was added.
       b. Format the expiration date as "Month YYYY".
       c. Add a run with "Expires: " followed by the formatted date.
    8. This function modifies the document in-place and does not write to disk.

---
## `RenderCertificationsSection` class

Render the entire certifications section of a resume document.

Attributes:
    document (docx.document.Document): The Word document object to render into.
    certifications (Certifications): A list of certification data to render.
    settings (ResumeCertificationsSettings): The rendering settings for the certifications section.

Base Class:
    ResumeRenderCertificationsBase: Base class providing shared rendering functionality for multiple certifications.

---
## method: `RenderCertificationsSection.__init__(self: UnknownType, document: docx.document.Document, certifications: Certifications, settings: ResumeCertificationsSettings) -> UnknownType`

Initialize the basic certifications renderer.

Args:
    document (docx.document.Document): The Word document object to render into.
    certifications (Certifications): A list of certification data to render.
    settings (ResumeCertificationsSettings): The rendering settings for the certifications section.

Notes:
    1. Initializes the parent class with the provided document, certifications, and settings.

---
## method: `RenderCertificationsSection.render(self: UnknownType) -> None`

Render the certifications section of a document.

Args:
    None

Returns:
    None: This method modifies the document in-place and does not return a value.

Notes:
    1. Log the start of the certifications section rendering.
    2. If there are no certifications, return early without adding anything.
    3. Add a level-2 heading titled "Certifications".
    4. For each certification in the list:
       a. Create a new RenderCertificationSection instance.
       b. Call the render method on that instance to add the certification to the document.
    5. This function modifies the document in-place and does not write to disk.

---

===

===
# File: `resume_writer/resume_render/plain/education_section.py`

## `RenderDegreeSection` class

Render a single academic degree in a resume document.

This class handles the visual formatting and layout of a degree entry,
including school name, degree name, dates, and GPA, using a structured
paragraph with tab stops for alignment.

Inherits from:
    ResumeRenderDegreeBase: Base class providing shared rendering logic.

Attributes:
    document (docx.document.Document): The Word document being rendered.
    degree (Degree): The academic degree data to render.
    settings (ResumeEducationSettings): Configuration settings for rendering.
    font_size (int): Base font size used for text (in points).

---
## method: `RenderDegreeSection.__init__(self: UnknownType, document: docx.document.Document, degree: Degree, settings: ResumeEducationSettings) -> UnknownType`

Initialize the degree renderer.

Args:
    document (docx.document.Document): The DOCX document to render into.
    degree (Degree): The academic degree data to render.
    settings (ResumeEducationSettings): Rendering configuration for degrees.

Returns:
    None

Notes:
    1. Calls the parent constructor with the provided document, degree, and settings.

---
## method: `RenderDegreeSection.render(self: UnknownType) -> None`

Render a single academic degree entry into the document.

Args:
    None

Returns:
    None

Notes:
    1. Logs a debug message indicating the start of degree rendering.
    2. Creates a new paragraph in the document.
    3. Adds a right-aligned tab stop at 7.4 inches to align text elements.
    4. If the school name is provided and enabled in settings, adds it in bold with a larger font size.
    5. If the degree name is provided and enabled in settings, adds it after a tab, in bold, followed by a line break.
    6. If the start date is provided and enabled in settings, formats it as "Month Year" and adds it to the paragraph.
    7. If the end date is provided and enabled in settings, formats it as "Month Year" and adds it with a dash to the paragraph.
    8. If the GPA is provided and enabled in settings, adds it after a tab with the label "GPA: ".

---
## `RenderEducationSection` class

Render the entire education section of a resume.

This class manages the rendering of the education section, including
a centered heading and individual degree entries formatted via
RenderDegreeSection.

Inherits from:
    ResumeRenderEducationBase: Base class providing shared rendering logic.

Attributes:
    document (docx.document.Document): The Word document being rendered.
    education (Education): The education data to render.
    settings (ResumeEducationSettings): Configuration settings for rendering.

---
## method: `RenderEducationSection.__init__(self: UnknownType, document: docx.document.Document, education: Education, settings: ResumeEducationSettings) -> UnknownType`

Initialize the education renderer.

Args:
    document (docx.document.Document): The DOCX document to render into.
    education (Education): The education data to render.
    settings (ResumeEducationSettings): Rendering configuration for education.

Returns:
    None

Notes:
    1. Calls the parent constructor with the provided document, education, and settings.

---
## method: `RenderEducationSection.render(self: UnknownType) -> None`

Render the education section into the document.

Args:
    None

Returns:
    None

Notes:
    1. Logs a debug message indicating the start of education rendering.
    2. Exits early if degree rendering is disabled in settings.
    3. Adds a centered heading titled "Education" with level 2.
    4. Iterates through each degree in the education data.
    5. For each degree, creates a RenderDegreeSection instance and calls its render method.
    6. Adds a blank paragraph between degrees to provide visual separation.

---

===

===
# File: `resume_writer/resume_render/plain/experience_section.py`

## `RenderRoleSection` class

Render experience roles section.

Attributes:
    document (docx.document.Document): The DOCX document object to render into.
    role (Role): The role data to render.
    settings (ResumeRolesSettings): The rendering settings for roles.
    font_size (int): The base font size for rendering.
    errors (list[str]): List of error messages encountered during rendering.

---
## method: `RenderRoleSection.__init__(self: UnknownType, document: docx.document.Document, role: Role, settings: ResumeRolesSettings) -> UnknownType`

Initialize roles render object.

Args:
    document (docx.document.Document): The DOCX document object to render into.
    role (Role): The role data to render.
    settings (ResumeRolesSettings): The rendering settings for roles.

Returns:
    None

Notes:
    1. Initializes the base class with the provided document, role, and settings.
    2. Logs a debug message indicating initialization has started.

---
## method: `RenderRoleSection._skills(self: UnknownType) -> list[str]`

Render role skills section.

Args:
    None

Returns:
    A list containing strings of skills. The list is empty if no skills are present.

Notes:
    1. Creates a new paragraph in the document.
    2. Checks if skills are present in the role and if the settings allow displaying skills.
    3. If skills are present, joins them with commas and adds them as italicized text.
    4. Sets the font size to be two points smaller than the base font size.
    5. Logs a debug message about the skills rendering process.

---
## method: `RenderRoleSection._details(self: UnknownType) -> list[str]`

Render role details section.

Args:
    None

Returns:
    A list of strings containing details like job category, location, agency name, and employment type.

Notes:
    1. Initializes an empty list to store the details.
    2. Checks if job category is present and if it should be displayed.
    3. Adds job category to the list if applicable.
    4. Checks if location is present and if it should be displayed.
    5. Adds location to the list if applicable.
    6. Checks if agency name is present and if it should be displayed.
    7. Adds agency name to the list if applicable.
    8. Checks if employment type is present and if it should be displayed.
    9. Adds employment type to the list if applicable.
    10. Returns the list of details.

---
## method: `RenderRoleSection._title_and_company(self: UnknownType, paragraph: docx.text.paragraph.Paragraph) -> None`

Render role title and company section.

Args:
    paragraph (docx.text.paragraph.Paragraph): The paragraph object to add the title and company to.

Returns:
    None

Notes:
    1. Logs a debug message indicating the start of title and company rendering.
    2. Retrieves the basics information from the role.
    3. Checks if the title is present; if not, raises a ValueError with an error message.
    4. Adds the title as bold and underlined text to the paragraph.
    5. Sets the font size to be two points larger than the base font size.
    6. Checks if the company name is present; if not, raises a ValueError with an error message.
    7. Adds the company name with a tab character and bold formatting to the paragraph.
    8. Sets the font size to be two points larger than the base font size.

---
## method: `RenderRoleSection._dates_and_location(self: UnknownType, paragraph: docx.text.paragraph.Paragraph) -> list[str]`

Render role dates section.

Args:
    paragraph (docx.text.paragraph.Paragraph): The paragraph object to add the dates and location to.

Returns:
    A list of strings containing the formatted date and location information.

Notes:
    1. Logs a debug message indicating the start of date and location rendering.
    2. Retrieves the basics information from the role.
    3. Creates a new run object for the date information.
    4. Checks if the start date is present; if not, logs a warning message.
    5. Formats the start date as "Month Year" and adds it to the run.
    6. If an end date is present, formats it as "Month Year" and adds it to the run with a hyphen.
    7. If no end date is present, adds "Present" to the run.
    8. If location is present and should be displayed, adds it to the paragraph with a tab.
    9. Returns the list of formatted date and location strings.

---
## method: `RenderRoleSection._render_task(self: UnknownType, paragraph: docx.text.paragraph.Paragraph, task_line: str) -> None`

Render a single task line with skill highlighting.

Args:
    paragraph (docx.text.paragraph.Paragraph): The paragraph object to add the task to.
    task_line (str): The task text to render.

Returns:
    None

Notes:
    1. Checks if skills are present and if the settings allow including tasks.
    2. Splits the task line using the skills splitter function.
    3. Initializes leading and trailing space flags.
    4. Iterates through each fragment in the task line.
    5. Creates a new run for each fragment.
    6. Determines if a trailing space is needed based on punctuation.
    7. If the fragment is a skill, adds it in bold.
    8. Adds leading space if needed.
    9. Adds the fragment text to the run.
    10. Adds trailing space if needed.
    11. Adds a line break after the last fragment.

---
## method: `RenderRoleSection._responsibilities(self: UnknownType) -> None`

Render role responsibilities section.

Args:
    None

Returns:
    None

Notes:
    1. Logs a debug message indicating the start of responsibilities rendering.
    2. Creates two paragraphs: one for situation and one for tasks.
    3. Sets spacing before and after both paragraphs.
    4. Splits the responsibilities text by double newlines and then by single newlines.
    5. Iterates through each line in the responsibilities.
    6. If the line starts with "* ", renders it as a task if tasks are included.
    7. If the line doesn't start with "* ", adds it to the situation paragraph if situation is included.
    8. Adds line breaks as needed.

---
## method: `RenderRoleSection._description(self: UnknownType) -> None`

Render role summary and details section.

Args:
    None

Returns:
    None

Notes:
    1. Checks if a summary is present and if the settings allow displaying it.
    2. If a summary is present, creates a new paragraph and adds the summary text in bold and italic.
    3. Sets the spacing after the paragraph.
    4. Sets the spacing before the paragraph.
    5. Checks if responsibilities are present and if the settings allow displaying them.
    6. If responsibilities are present, calls the responsibilities rendering method.

---
## method: `RenderRoleSection.render(self: UnknownType) -> None`

Render role overview/basics section.

Args:
    None

Returns:
    None

Notes:
    1. Logs a debug message indicating the start of rendering.
    2. Creates a paragraph for basics information.
    3. Sets spacing after the paragraph.
    4. Renders the title and company information.
    5. Adds tab stops to the basics paragraph for formatting.
    6. Creates a paragraph for dates and location.
    7. Adds tab stops to the dates paragraph for formatting.
    8. Renders the dates and location information.
    9. Sets spacing after the dates paragraph.
    10. Renders the description section.
    11. Renders the skills section.

---
## `RenderRolesSection` class

Render experience roles section.

Attributes:
    document (docx.document.Document): The DOCX document object to render into.
    roles (Roles): The list of role data to render.
    settings (ResumeRolesSettings): The rendering settings for roles.
    font_size (int): The base font size for rendering.
    errors (list[str]): List of error messages encountered during rendering.

---
## method: `RenderRolesSection.__init__(self: UnknownType, document: docx.document.Document, roles: Roles, settings: ResumeRolesSettings) -> UnknownType`

Initialize roles render object.

Args:
    document (docx.document.Document): The DOCX document object to render into.
    roles (Roles): The list of role data to render.
    settings (ResumeRolesSettings): The rendering settings for roles.

Returns:
    None

Notes:
    1. Initializes the base class with the provided document, roles, and settings.
    2. Logs a debug message indicating initialization has started.

---
## method: `RenderRolesSection.render(self: UnknownType) -> None`

Render roles section.

Args:
    None

Returns:
    None

Notes:
    1. Logs a debug message indicating the start of rendering.
    2. Checks if there are any roles to render.
    3. If roles exist, adds a centered heading with the text "Work History".
    4. If no roles exist, logs an info message.
    5. Iterates through each role and renders it using the RenderRoleSection class.
    6. Adds a blank paragraph after each role with 12 points of spacing after.
    7. Adds a horizontal line after each role.

---
## `RenderProjectSection` class

Render experience project section.

Attributes:
    document (docx.document.Document): The DOCX document object to render into.
    project (Project): The project data to render.
    settings (ResumeProjectsSettings): The rendering settings for projects.
    font_size (int): The base font size for rendering.
    errors (list[str]): List of error messages encountered during rendering.

---
## method: `RenderProjectSection.__init__(self: UnknownType, document: docx.document.Document, project: Project, settings: ResumeProjectsSettings) -> UnknownType`

Initialize project render object.

Args:
    document (docx.document.Document): The DOCX document object to render into.
    project (Project): The project data to render.
    settings (ResumeProjectsSettings): The rendering settings for projects.

Returns:
    None

Notes:
    1. Initializes the base class with the provided document, project, and settings.
    2. Logs a debug message indicating initialization has started.

---
## method: `RenderProjectSection._overview(self: UnknownType, paragraph: docx.text.paragraph.Paragraph) -> None`

Render project overview section.

Args:
    paragraph (docx.text.paragraph.Paragraph): The paragraph object to add the overview to.

Returns:
    None

Notes:
    1. Logs a debug message indicating the start of overview rendering.
    2. Retrieves the overview information from the project.
    3. Adds the project title as bold text to the paragraph.
    4. Adds a tab character to the paragraph.
    5. Sets spacing after the paragraph.
    6. Adds a hyperlink to the project website using the add_hyperlink function.

---
## method: `RenderProjectSection._skills(self: UnknownType, paragraph: docx.text.paragraph.Paragraph) -> list[str]`

Render project skills section.

Args:
    paragraph (docx.text.paragraph.Paragraph): The paragraph object to add the skills to.

Returns:
    A list of strings containing the project skills.

Notes:
    1. Logs a debug message indicating the start of skills rendering.
    2. Joins the project skills with commas.
    3. Creates a new run object for the skills text.
    4. Adds the skills text with "Skills: " prefix.
    5. Sets the text to be italic.
    6. Returns the list of skills.

---
## method: `RenderProjectSection.render(self: UnknownType) -> None`

Render project section.

Args:
    None

Returns:
    None

Notes:
    1. Logs a debug message indicating the start of project rendering.
    2. Creates a paragraph for the project information.
    3. Adds tab stops to the paragraph for formatting.
    4. Checks if the overview should be displayed and if it exists.
    5. If the overview should be displayed, renders the overview section.
    6. Sets spacing after the overview paragraph.
    7. Checks if the description should be displayed and if it exists.
    8. If the description should be displayed, adds each line of the description as a separate run with line breaks.
    9. Sets spacing before and after the description paragraph.
    10. Checks if skills should be displayed and if they exist.
    11. If skills should be displayed, adds a new paragraph for skills and renders them.

---
## `RenderProjectsSection` class

Render experience projects section.

Attributes:
    document (docx.document.Document): The DOCX document object to render into.
    projects (Projects): The list of project data to render.
    settings (ResumeProjectsSettings): The rendering settings for projects.
    font_size (int): The base font size for rendering.
    errors (list[str]): List of error messages encountered during rendering.

---
## method: `RenderProjectsSection.__init__(self: UnknownType, document: docx.document.Document, projects: Projects, settings: ResumeProjectsSettings) -> UnknownType`

Initialize projects render object.

Args:
    document (docx.document.Document): The DOCX document object to render into.
    projects (Projects): The list of project data to render.
    settings (ResumeProjectsSettings): The rendering settings for projects.

Returns:
    None

Notes:
    1. Initializes the base class with the provided document, projects, and settings.
    2. Logs a debug message indicating initialization has started.

---
## method: `RenderProjectsSection.render(self: UnknownType) -> None`

Render projects section.

Args:
    None

Returns:
    None

Notes:
    1. Logs a debug message indicating the start of projects rendering.
    2. Checks if there are any projects to render.
    3. If projects exist, adds a heading with the text "Projects".
    4. Iterates through each project and renders it using the RenderProjectSection class.

---
## `RenderExperienceSection` class

Render experience section.

Attributes:
    document (docx.document.Document): The DOCX document object to render into.
    experience (Experience): The experience data to render.
    settings (ResumeExperienceSettings): The rendering settings for experience.
    font_size (int): The base font size for rendering.
    errors (list[str]): List of error messages encountered during rendering.

---
## method: `RenderExperienceSection.__init__(self: UnknownType, document: docx.document.Document, experience: Experience, settings: ResumeExperienceSettings) -> None`

Initialize experience render object.

Args:
    document (docx.document.Document): The DOCX document object to render into.
    experience (Experience): The experience data to render.
    settings (ResumeExperienceSettings): The rendering settings for experience.

Returns:
    None

Notes:
    1. Initializes the base class with the provided document, experience, and settings.
    2. Logs a debug message indicating initialization has started.

---
## method: `RenderExperienceSection.render(self: UnknownType) -> None`

Render experience section.

Args:
    None

Returns:
    None

Notes:
    1. Logs a debug message indicating the start of experience rendering.
    2. Checks if roles should be rendered and if they exist.
    3. If roles should be rendered and they exist, creates a roles section with the appropriate settings.
    4. Checks if projects should be rendered and if they exist.
    5. If projects should be rendered and they exist, creates a projects section with the appropriate settings.

---

===

===
# File: `resume_writer/resume_render/basic/__init__.py`


===

===
# File: `resume_writer/resume_render/basic/certifications_section.py`

## `RenderCertificationSection` class

Render a single certification entry in a resume.

Attributes:
    document (docx.document.Document): The Word document object to which the certification will be added.
    certification (Certification): The certification object containing details about the certification.
    settings (ResumeCertificationsSettings): The settings object that determines which fields to include in the rendered output.

---
## method: `RenderCertificationSection.__init__(self: UnknownType, document: docx.document.Document, certification: Certification, settings: ResumeCertificationsSettings) -> UnknownType`

Initialize the basic certification renderer.

Args:
    document (docx.document.Document): The Word document object to which the certification will be added.
    certification (Certification): The Certification object containing details about the certification.
    settings (ResumeCertificationsSettings): The settings object that determines which fields to include in the rendered output.

Notes:
    1. Calls the parent class constructor to initialize base functionality.
    2. Stores the provided document, certification, and settings as instance attributes.

---
## method: `RenderCertificationSection.render(self: UnknownType) -> None`

Render the certification section in the document.

Args:
    None

Returns:
    None

Notes:
    1. Initializes an empty list to hold the lines of text to be rendered.
    2. Checks if the certification name exists and the name setting is enabled, and adds it to the lines if so.
    3. Checks if the issuer exists and the issuer setting is enabled, and adds it to the lines if so.
    4. Checks if the issued date exists and the issued setting is enabled, formats it as "Month Year", and adds it to the lines if so.
    5. Checks if the expiration date exists and the expires setting is enabled, formats it as "Month Year", and adds it to the lines if so.
    6. If any lines were collected, joins them with newlines and adds a new paragraph to the document with the resulting text.
    7. No disk, network, or database access occurs during this method.

---
## `RenderCertificationsSection` class

Render the entire certifications section in a resume.

Attributes:
    document (docx.document.Document): The Word document object to which the certifications will be added.
    certifications (Certifications): A list of Certification objects to be rendered.
    settings (ResumeCertificationsSettings): The settings object that determines which fields to include in the rendered output.

---
## method: `RenderCertificationsSection.__init__(self: UnknownType, document: docx.document.Document, certifications: Certifications, settings: ResumeCertificationsSettings) -> UnknownType`

Initialize the basic certifications renderer.

Args:
    document (docx.document.Document): The Word document object to which the certifications will be added.
    certifications (Certifications): A list of Certification objects to be rendered.
    settings (ResumeCertificationsSettings): The settings object that determines which fields to include in the rendered output.

Notes:
    1. Calls the parent class constructor to initialize base functionality.
    2. Stores the provided document, certifications, and settings as instance attributes.

---
## method: `RenderCertificationsSection.render(self: UnknownType) -> None`

Render the certifications section in the document.

Args:
    None

Returns:
    None

Notes:
    1. Checks if there are any certifications to render.
    2. If certifications exist, adds a level-2 heading titled "Certifications" to the document.
    3. Iterates through each certification in the list.
    4. For each certification, creates a new RenderCertificationSection instance and calls its render method to add the certification details to the document.
    5. No disk, network, or database access occurs during this method.

---

===

===
# File: `resume_writer/resume_render/basic/experience_section.py`

## `RenderRoleSection` class

Render experience roles section.

This class is responsible for rendering individual job roles in a resume document.
It formats and adds role details such as company, title, dates, skills, and responsibilities.

Attributes:
    document (docx.document.Document): The Word document object to which content will be added.
    role (Role): The role object containing job-specific details.
    settings (ResumeRolesSettings): Configuration settings for which role details to render.
    errors (list[str]): List of error messages encountered during rendering.

---
## method: `RenderRoleSection.__init__(self: UnknownType, document: docx.document.Document, role: Role, settings: ResumeRolesSettings) -> UnknownType`

Initialize roles render object.

Args:
    document (docx.document.Document): The Word document object to which the role content will be added.
    role (Role): The Role object containing role-specific details such as company, title, dates, etc.
    settings (ResumeRolesSettings): The settings object that controls which parts of the role to render.

Returns:
    None.

Notes:
    1. Initialize the base class with the provided document, role, and settings.
    2. Log a debug message indicating initialization.

---
## method: `RenderRoleSection._skills(self: UnknownType) -> list[str]`

Render role skills section.

Args:
    None.

Returns:
    A list of strings, each representing a formatted line for skills. If no skills are present or settings are disabled, returns an empty list.

Notes:
    1. Initialize an empty list to hold the skill lines.
    2. Check if the role has skills and if the skills setting is enabled.
    3. If both conditions are true, join the skills into a comma-separated string and append it to the list with the label "Skills: ".
    4. Return the list of skill lines.

---
## method: `RenderRoleSection._details(self: UnknownType) -> list[str]`

Render role details section.

Args:
    None.

Returns:
    A list of strings, each representing a formatted line for role details such as job category, location, agency, or employment type. Returns an empty list if no details are to be rendered.

Notes:
    1. Initialize an empty list to store detail lines.
    2. Extract the role's basics information.
    3. Check if job category is present and if the job_category setting is enabled, then append the formatted line.
    4. Repeat for location, agency name, and employment type if applicable and settings are enabled.
    5. Return the list of detail lines.

---
## method: `RenderRoleSection._dates(self: UnknownType) -> list[str]`

Render role dates section.

Args:
    None.

Returns:
    A list of strings, with a single entry containing the formatted date range (e.g., "01-2020 - 12-2022" or "01-2020 - Present").

Notes:
    1. Initialize an empty list to hold date lines.
    2. Extract the role's basics information.
    3. Validate that a start date is present; if not, append a warning to errors and return.
    4. Format the start date as "MM-YYYY".
    5. If an end date is present, format it as "MM-YYYY" and append it with a hyphen.
    6. If no end date is present, append " - Present".
    7. Return the formatted date string as a list with one element.

---
## method: `RenderRoleSection.render(self: UnknownType) -> None`

Render role overview/basics section.

Args:
    None.

Returns:
    None.

Notes:
    1. Initialize an empty list to hold paragraph lines.
    2. Extract the role's basics information.
    3. Check if the company name is present; if not, append a warning and log it.
    4. Append the formatted "Company: <name>" line.
    5. Render the dates using _dates method and extend the paragraph lines.
    6. Check if the title is present; if not, append a warning and log it.
    7. Append the formatted "Title: <title>" line.
    8. Render the details using _details method and extend the paragraph lines.
    9. Clean the paragraph lines by replacing double newlines with single newlines.
    10. If any paragraph lines exist, add a paragraph to the document with the joined lines.
    11. If a summary exists and summary setting is enabled, add it as a paragraph.
    12. If responsibilities exist and responsibilities setting is enabled, add them as a paragraph with cleaned text.
    13. Render the skills using _skills method and add them as a paragraph if any exist.

---
## `RenderRolesSection` class

Render experience roles section.

This class is responsible for rendering multiple job roles in a resume document.
It manages the formatting and ordering of job roles, adding appropriate headings and spacing.

Attributes:
    document (docx.document.Document): The Word document object to which the roles content will be added.
    roles (Roles): A list of Role objects representing job roles to be rendered.
    settings (ResumeRolesSettings): Configuration settings for which role details to render.
    errors (list[str]): List of error messages encountered during rendering.

---
## method: `RenderRolesSection.__init__(self: UnknownType, document: docx.document.Document, roles: Roles, settings: ResumeRolesSettings) -> UnknownType`

Initialize roles render object.

Args:
    document (docx.document.Document): The Docx document object to which the roles content will be added.
    roles (Roles): A list of Role objects representing job roles to be rendered.
    settings (ResumeRolesSettings): The settings object that controls which parts of the roles to render.

Returns:
    None.

Notes:
    1. Initialize the base class with the provided document, roles, and settings.

---
## method: `RenderRolesSection.render(self: UnknownType) -> None`

Render roles section.

Args:
    None.

Returns:
    None.

Notes:
    1. Log a debug message indicating the start of rendering.
    2. Store the roles list to avoid filtering twice.
    3. Add a heading "Work History" at level 2 if any roles exist.
    4. If no roles exist, log an info message and return.
    5. Iterate over each role in the roles list.
    6. For each role, create a RenderRoleSection instance and call its render method.
    7. After each role (except the last), add two blank paragraphs to separate entries.

---
## `RenderProjectSection` class

Render experience project section.

This class is responsible for rendering individual projects in a resume document.
It formats and adds project details such as description, skills, URLs, and dates.

Attributes:
    document (docx.document.Document): The Word document object to which the project content will be added.
    project (Project): The Project object containing project details such as description, skills, URLs, etc.
    settings (ResumeProjectsSettings): Configuration settings for which project details to render.
    errors (list[str]): List of error messages encountered during rendering.

---
## method: `RenderProjectSection.__init__(self: UnknownType, document: docx.document.Document, project: Project, settings: ResumeProjectsSettings) -> UnknownType`

Initialize project render object.

Args:
    document (docx.document.Document): The Docx document object to which the project content will be added.
    project (Project): The Project object containing project details such as description, skills, URLs, etc.
    settings (ResumeProjectsSettings): The settings object that controls which parts of the project to render.

Returns:
    None.

Notes:
    1. Initialize the base class with the provided document, project, and settings.
    2. Log a debug message indicating initialization.

---
## method: `RenderProjectSection._overview(self: UnknownType) -> list[str]`

Render project overview section.

Args:
    None.

Returns:
    A list of strings, each representing a formatted line for the project overview such as URL description, URL, start date, or end date. Returns an empty list if no overview data is to be rendered.

Notes:
    1. Initialize an empty list to store overview lines.
    2. Extract the project's overview information.
    3. If URL description is enabled and present, format it as a string.
    4. If URL is enabled and present, add it in parentheses to the URL description line.
    5. Strip and add the resulting URL line if it is not empty.
    6. If start date is enabled and present, format the date as "Month Year" and add it.
    7. If end date is enabled and present, format the date as "Month Year" and add it.
    8. Return the list of overview lines.

---
## method: `RenderProjectSection._skills(self: UnknownType) -> list[str]`

Render project skills section.

Args:
    None.

Returns:
    A list of strings, with a single entry containing "Skills: <comma-separated skills>" if skills are present and enabled. Returns an empty list otherwise.

Notes:
    1. Initialize an empty list to store skill lines.
    2. Join the project's skills into a comma-separated string.
    3. Append a formatted "Skills: ..." line to the list.
    4. Return the list of skill lines.

---
## method: `RenderProjectSection.render(self: UnknownType) -> None`

Render project section.

Args:
    None.

Returns:
    None.

Notes:
    1. Log a debug message indicating the start of rendering.
    2. Initialize an empty list to store paragraph lines.
    3. If overview is enabled and the project has an overview, render it using _overview method and extend the paragraph lines.
    4. If description is enabled and the project has a description, append the description text.
    5. If skills are enabled and the project has skills, render them using _skills method and extend the paragraph lines.
    6. If any paragraph lines exist, add a paragraph to the document with the joined lines.

---
## `RenderProjectsSection` class

Render experience projects section.

This class is responsible for rendering multiple projects in a resume document.
It manages the formatting and ordering of projects, adding appropriate headings and spacing.

Attributes:
    document (docx.document.Document): The Word document object to which the projects content will be added.
    projects (Projects): A list of Project objects representing projects to be rendered.
    settings (ResumeProjectsSettings): Configuration settings for which project details to render.
    errors (list[str]): List of error messages encountered during rendering.

---
## method: `RenderProjectsSection.__init__(self: UnknownType, document: docx.document.Document, projects: Projects, settings: ResumeProjectsSettings) -> UnknownType`

Initialize projects render object.

Args:
    document (docx.document.Document): The Docx document object to which the projects content will be added.
    projects (Projects): A list of Project objects representing projects to be rendered.
    settings (ResumeProjectsSettings): The settings object that controls which parts of the projects to render.

Returns:
    None.

Notes:
    1. Initialize the base class with the provided document, projects, and settings.
    2. Log a debug message indicating initialization.

---
## method: `RenderProjectsSection.render(self: UnknownType) -> None`

Render projects section.

Args:
    None.

Returns:
    None.

Notes:
    1. Log a debug message indicating the start of rendering.
    2. If any projects exist, add a heading "Projects" at level 2.
    3. Iterate over each project in the projects list.
    4. For each project, create a RenderProjectSection instance and call its render method.

---
## `RenderExperienceSection` class

Render experience section.

This class is responsible for rendering the entire experience section of a resume.
It coordinates the rendering of roles and projects, applying appropriate formatting and settings.

Attributes:
    document (docx.document.Document): The Word document object to which the experience content will be added.
    experience (Experience): The Experience object containing roles and projects to be rendered.
    settings (ResumeExperienceSettings): Configuration settings for which experience details to render.
    errors (list[str]): List of error messages encountered during rendering.

---
## method: `RenderExperienceSection.__init__(self: UnknownType, document: docx.document.Document, experience: Experience, settings: ResumeExperienceSettings) -> None`

Initialize experience render object.

Args:
    document (docx.document.Document): The Docx document object to which the experience content will be added.
    experience (Experience): The Experience object containing roles and projects to be rendered.
    settings (ResumeExperienceSettings): The settings object that controls which parts of experience to render.

Returns:
    None.

Notes:
    1. Initialize the base class with the provided document, experience, and settings.
    2. Log a debug message indicating initialization.

---
## method: `RenderExperienceSection.render(self: UnknownType) -> None`

Render experience section.

Args:
    None.

Returns:
    None.

Notes:
    1. Log a debug message indicating the start of rendering.
    2. If roles are enabled and the experience has roles, render them using RenderRolesSection.
    3. If projects are enabled and the experience has projects, render them using RenderProjectsSection.

---

===

===
# File: `resume_writer/resume_render/basic/executive_summary_section.py`

## `RenderExecutiveSummarySection` class

Render experience for a functional resume.

Inherits from:
    ResumeRenderExecutiveSummaryBase: Base class for rendering executive summaries.

Attributes:
    document (docx.document.Document): The Docx document object to which the executive summary will be added.
    experience (Experience): The Experience object containing role and job data to summarize.
    settings (ResumeExecutiveSummarySettings): The settings object that defines which categories to include in the summary.

---
## method: `RenderExecutiveSummarySection.__init__(self: UnknownType, document: docx.document.Document, experience: Experience, settings: ResumeExecutiveSummarySettings) -> None`

Initialize experience render object.

Args:
    document (docx.document.Document): The Docx document object to which the executive summary will be added.
    experience (Experience): The Experience object containing role and job data to summarize.
    settings (ResumeExecutiveSummarySettings): The settings object that defines which categories to include in the summary.

Returns:
    None

Notes:
    1. Initialize the parent class (ResumeRenderExecutiveSummaryBase) with the provided document, experience, and settings.
    2. Log a debug message indicating that the functional experience render object is being initialized.

---
## method: `RenderExecutiveSummarySection.render(self: UnknownType) -> None`

Render experience section for functional resume.

Args:
    None

Returns:
    None

Notes:
    1. Log a debug message indicating that the functional experience section is being rendered.
    2. Check if the experience object has any roles; if not, raise a ValueError.
    3. Create an ExecutiveSummary object using the experience data.
    4. Generate the executive summary using the specified categories from the settings.
    5. For each category in the summary:
        a. Add a heading to the document with level 4.
        b. For each summary entry in the category:
            i. Create a new paragraph and apply the "List Bullet" style.
            ii. Add the summary text as a run.
            iii. If no company is available, log a warning.
            iv. If a company is available, determine the date string (either the last date formatted to year or "Present").
            v. Add an italicized run with the company and date information.
    6. This function performs no disk, network, or database access.

---

===

===
# File: `resume_writer/resume_render/basic/personal_section.py`

## `RenderPersonalSection` class

Render personal contact info section.

Attributes:
    document (docx.document.Document): The Word document object to which content will be added.
    personal (Personal): The personal information model containing contact details, banner, note, websites, and visa status.
    settings (ResumePersonalSettings): The rendering settings that control which sections are enabled or disabled.

---
## method: `RenderPersonalSection.__init__(self: UnknownType, document: docx.document.Document, personal: Personal, settings: ResumePersonalSettings) -> UnknownType`

Initialize the personal section renderer.

Args:
    document (docx.document.Document): The Word document object to which content will be added.
    personal (Personal): The personal information model containing contact details, banner, note, websites, and visa status.
    settings (ResumePersonalSettings): The rendering settings that control which sections are enabled or disabled.

Returns:
    None

Notes:
    1. Initialize the base class with the provided document, personal data, and settings.
    2. Log debug message indicating the initialization of the personal basic render object.

---
## method: `RenderPersonalSection._contact_info(self: UnknownType) -> None`

Render the contact info section.

Args:
    None

Returns:
    None

Notes:
    1. Initialize an empty list to hold lines of contact information.
    2. Extract the contact info from the personal data.
    3. If the name is present and enabled in settings, add "Name: <name>" to the list.
    4. If the email is present and enabled in settings, add "Email: <email>" to the list.
    5. If the phone is present and enabled in settings, add "Phone: <phone>" to the list.
    6. If the location is present and enabled in settings, add "Location: <location>" to the list.
    7. If any lines were added, join them with newlines and add the combined text as a paragraph in the document.

---
## method: `RenderPersonalSection._banner(self: UnknownType) -> None`

Render the banner section.

Args:
    None

Returns:
    None

Notes:
    1. Extract the banner text from the personal data.
    2. If the banner text is present, add a level 3 heading titled "Banner".
    3. Add the banner text as a paragraph immediately after the heading.

---
## method: `RenderPersonalSection._note(self: UnknownType) -> None`

Render the note section.

Args:
    None

Returns:
    None

Notes:
    1. Extract the note text from the personal data.
    2. If the note text is present, add a level 3 heading titled "Note".
    3. Add the note text as a paragraph immediately after the heading.

---
## method: `RenderPersonalSection._websites(self: UnknownType) -> None`

Render the websites section.

Args:
    None

Returns:
    None

Notes:
    1. Initialize an empty list to hold lines of website information.
    2. Extract the websites data from the personal data.
    3. If GitHub URL is present and enabled in settings, add "GitHub: <url>" to the list.
    4. If LinkedIn URL is present and enabled in settings, add "LinkedIn: <url>" to the list.
    5. If personal website URL is present and enabled in settings, add "Website: <url>" to the list.
    6. If Twitter URL is present and enabled in settings, add "Twitter: <url>" to the list.
    7. If any lines were added, add a level 3 heading titled "Websites".
    8. Join the lines with newlines and add the combined text as a paragraph in the document.

---
## method: `RenderPersonalSection._visa_status(self: UnknownType) -> None`

Render the visa status section.

Args:
    None

Returns:
    None

Notes:
    1. Initialize an empty list to hold lines of visa status information.
    2. Extract the visa status data from the personal data.
    3. If work authorization is present and enabled in settings, add "Work Authorization: <status>" to the list.
    4. If sponsorship requirement is defined and enabled in settings, determine the value ("Yes" if True, "No" if False) and add "Require Sponsorship: <value>" to the list.
    5. If any lines were added, add a level 3 heading titled "Visa Status".
    6. Join the lines with newlines and add the combined text as a paragraph in the document.

---
## method: `RenderPersonalSection.render(self: UnknownType) -> None`

Render the personal section.

Args:
    None

Returns:
    None

Notes:
    1. If contact info exists and is enabled in settings, render the contact info section.
    2. If banner exists and is enabled in settings, render the banner section.
    3. If note exists and is enabled in settings, render the note section.
    4. If websites exist and are enabled in settings, render the websites section.
    5. If visa status exists and is enabled in settings, render the visa status section.

---

===

===
# File: `resume_writer/resume_render/basic/resume_main.py`

## `RenderResume` class

Render a resume in basic format.

Attributes:
    document (docx.document.Document): The Word document object to render the resume into.
    resume (Resume): The resume data model containing personal, education, experience, certifications, and other sections.
    settings (ResumeRenderSettings): Configuration settings for rendering specific sections of the resume.

Args:
    document: The Word document object to render the resume into.
    resume: The resume data model containing personal, education, experience, certifications, and other sections.
    settings: Configuration settings for rendering specific sections of the resume.

Notes:
    1. The super().__init__() method is called to initialize the base class with the provided document, resume, and settings.
    2. No external file, network, or database access occurs during initialization.

---
## method: `RenderResume.__init__(self: UnknownType, document: docx.document.Document, resume: Resume, settings: ResumeRenderSettings) -> UnknownType`

Initialize basic resume renderer.

Args:
    document (docx.document.Document): The Word document object to render the resume into.
    resume (Resume): The resume data model containing personal, education, experience, certifications, and other sections.
    settings (ResumeRenderSettings): Configuration settings for rendering specific sections of the resume.

Notes:
    1. The super().__init__() method is called to initialize the base class with the provided document, resume, and settings.
    2. No external file, network, or database access occurs during initialization.

---
## method: `RenderResume.render(self: UnknownType) -> None`

Render the resume by conditionally adding sections based on data and settings.

Args:
    None: This method does not take any arguments.

Returns:
    None: This method does not return any value.

Notes:
    1. Check if the resume has personal information and if the personal section is enabled in settings.
    2. If both conditions are true, render the personal section using RenderPersonalSection.
    3. Check if the resume has education data and if the education section is enabled in settings.
    4. If both conditions are true, render the education section using RenderEducationSection.
    5. Check if the resume has certifications and if the certifications section is enabled in settings.
    6. If both conditions are true, render the certifications section using RenderCertificationsSection.
    7. Check if the resume has experience data and if the executive summary section is enabled in settings.
    8. If both conditions are true, add a heading titled "Executive Summary" and render the summary using RenderExecutiveSummarySection.
    9. Check if the resume has experience data and if the skills matrix section is enabled in settings.
    10. If both conditions are true, render the skills matrix section using RenderSkillsMatrixSection.
    11. Check if the resume has experience data and if the experience section is enabled in settings.
    12. If both conditions are true, render the experience section using RenderExperienceSection.
    13. No external file, network, or database access occurs during rendering.

---

===

===
# File: `resume_writer/resume_render/basic/skills_matrix_section.py`

## `RenderSkillsMatrixSection` class

Render skills for a functional resume.

This class generates a skills matrix table in a DOCX document based on experience data,
showing skills and their years of experience (YOE) with date ranges.

Attributes:
    document (docx.document.Document): The DOCX document to which the skills section will be added.
    experience (Experience): The experience data containing roles and skill usage history.
    settings (ResumeSkillsMatrixSettings): Configuration settings for rendering the skills matrix.
    parse_context (ParseContext): Contextual information used during parsing (not directly used in rendering).

Base Class:
    ResumeRenderSkillsMatrixBase: Provides base functionality for rendering skills matrices.

Methods:
    __init__: Initializes the render object with required parameters.
    render: Generates and adds the skills matrix table to the document.

---
## method: `RenderSkillsMatrixSection.__init__(self: UnknownType, document: docx.document.Document, experience: Experience, settings: ResumeSkillsMatrixSettings, parse_context: ParseContext) -> UnknownType`

Initialize skills render object.

Args:
    document (docx.document.Document): The DOCX document to which the skills section will be added.
    experience (Experience): The experience data containing roles and skill usage history.
    settings (ResumeSkillsMatrixSettings): Configuration settings for rendering the skills matrix.
    parse_context (ParseContext): Contextual information used during parsing, not directly used here.

Returns:
    None

Notes:
    1. Validate that the provided parse_context is an instance of ParseContext.
    2. Store the parse_context for potential future use.
    3. Initialize the parent class (ResumeRenderSkillsMatrixBase) with the given parameters.

---
## method: `RenderSkillsMatrixSection.render(self: UnknownType) -> None`

Render skills section for functional resume.

Args:
    None

Returns:
    None

Notes:
    1. Check if the experience object has any roles; if not, raise a ValueError.
    2. Create a SkillsMatrix instance from the experience roles.
    3. If settings.all_skills is True, generate a matrix for all skills using the special value "*all*".
    4. Otherwise, generate a matrix only for the skills specified in settings.skills.
    5. Calculate the number of rows needed for the table based on the number of skills (each row holds two skills).
    6. Create a new table with the calculated number of rows and 4 columns, using the "Table Grid" style.
    7. Add a header row with bolded column titles: "Skill", "YOE (from - to)", "Skill", "YOE (from - to)".
    8. Iterate through the sorted skills and their data.
    9. For each skill, determine its row and column position in the table.
    10. Insert the skill name into the appropriate cell and center it vertically.
    11. Format the YOE string using the first_used and last_used dates, along with the calculated YOE value.
    12. Insert the formatted YOE string into the adjacent cell.
    13. Set the table to auto-fit its contents.

Disk Access:
    - The function writes to the DOCX document via the `document.add_table` and cell text operations.

---

===

===
# File: `resume_writer/resume_render/basic/education_section.py`

## `RenderDegreeSection` class

Render a single degree section in a resume document.

This class handles formatting and rendering of a single academic degree,
including school, degree name, dates, major, and GPA, based on provided settings.

Inherits from:
    ResumeRenderDegreeBase: Base class providing common rendering functionality.

Attributes:
    document (docx.document.Document): The Word document being rendered.
    degree (Degree): The degree object containing education details.
    settings (ResumeEducationSettings): Configuration settings for rendering fields.
    font_size (int): Font size used for rendering (inherited from base class).

---
## method: `RenderDegreeSection.__init__(self: UnknownType, document: docx.document.Document, degree: Degree, settings: ResumeEducationSettings) -> UnknownType`

Initialize the basic degree renderer.

Args:
    document (docx.document.Document): The Word document to render the degree section into.
    degree (Degree): The degree object containing education details such as school, degree name, dates, major, and GPA.
    settings (ResumeEducationSettings): Configuration settings that control which degree fields are rendered (e.g., school, degree, dates, major, GPA).

Returns:
    None

Notes:
    1. Store the provided document, degree, and settings as instance attributes.
    2. No disk, network, or database access occurs during initialization.

---
## method: `RenderDegreeSection.render(self: UnknownType) -> None`

Render a single degree with formatted details in the document.

Args:
    None

Returns:
    None

Notes:
    1. Create a new paragraph in the document to hold the degree details.
    2. If the school name is present and enabled in settings, add it in bold, underlined, and larger font size.
    3. If the degree name is present and enabled in settings, add it in bold.
    4. If the start date is present and enabled in settings, format it as "Month Year" and add it.
    5. If the end date is present and enabled in settings, format it as "Month Year" (or "Present" if None) and add it.
    6. If the major is present and enabled in settings, add it.
    7. If the GPA is present and enabled in settings, add it in the format "GPA: X.XX".
    8. All text additions use runs and breaks to format the output properly.
    9. No disk, network, or database access occurs during rendering.

---
## `RenderEducationSection` class

Render the entire education section of a resume document.

This class manages the rendering of a resume's education section, including
a heading and a list of degrees, with formatting based on user-defined settings.

Inherits from:
    ResumeRenderEducationBase: Base class providing common education rendering behavior.

Attributes:
    document (docx.document.Document): The Word document being rendered.
    education (Education): The education object containing a list of degrees and related data.
    settings (ResumeEducationSettings): Configuration settings for rendering behavior.
    font_size (int): Font size used for rendering (inherited from base class).

---
## method: `RenderEducationSection.__init__(self: UnknownType, document: docx.document.Document, education: Education, settings: ResumeEducationSettings) -> UnknownType`

Initialize the basic education renderer.

Args:
    document (docx.document.Document): The Word document to render the education section into.
    education (Education): The education object containing a list of degrees and related data.
    settings (ResumeEducationSettings): Configuration settings that control rendering behavior, including whether to render degrees and which fields to include.

Returns:
    None

Notes:
    1. Store the provided document, education, and settings as instance attributes.
    2. No disk, network, or database access occurs during initialization.

---
## method: `RenderEducationSection.render(self: UnknownType) -> None`

Render the education section with heading and degrees.

Args:
    None

Returns:
    None

Notes:
    1. If the 'degrees' setting is disabled, exit early without rendering.
    2. Add a level-2 heading titled "Education" to the document.
    3. For each degree in the education object, create a RenderDegreeSection instance and call its render method.
    4. Rendering each degree is delegated to the RenderDegreeSection class.
    5. No disk, network, or database access occurs during rendering.

---

===

===
# File: `resume_writer/resume_render/ats/resume_main.py`

## `RenderResume` class

Render a resume in basic format.

Attributes:
    document (docx.document.Document): The Word document object to render the resume into.
    resume (Resume): The parsed resume data structure containing personal, education,
                     experience, certifications, and other sections.
    settings (ResumeRenderSettings): Configuration settings for rendering the resume,
                                     including which sections to include and how they should be formatted.

---
## method: `RenderResume.__init__(self: UnknownType, document: docx.document.Document, resume: Resume, settings: ResumeRenderSettings) -> None`

Initialize ATS resume renderer.

Args:
    document (docx.document.Document): The Word document object to render the resume into.
    resume (Resume): The parsed resume data structure containing personal, education,
                     experience, certifications, and other sections.
    settings (ResumeRenderSettings): Configuration settings for rendering the resume,
                                     including which sections to include and how they should be formatted.

Returns:
    None

Notes:
    1. Calls the parent class constructor to initialize common rendering state.
    2. Applies default settings overrides specific to ATS resume formatting.

---
## method: `RenderResume._settings_override(self: UnknownType) -> None`

Apply default settings overrides for ATS resumes.

Args:
    None

Returns:
    None

Notes:
    1. Disables the inclusion of role summaries in the experience section.
    2. Disables the executive summary section.
    3. Disables the skills matrix section.
    4. These settings are enforced to ensure compatibility with applicant tracking systems.

---
## method: `RenderResume.render(self: UnknownType) -> None`

Render the resume by processing each enabled section.

Args:
    None

Returns:
    None

Notes:
    1. Checks if personal information exists and the personal section is enabled.
    2. If enabled, renders the personal section using RenderPersonalSection.
    3. Checks if education data exists and the education section is enabled.
    4. If enabled, renders the education section using RenderEducationSection.
    5. Checks if certifications exist and the certifications section is enabled.
    6. If enabled, renders the certifications section using RenderCertificationsSection.
    7. Checks if experience data exists and the executive summary is enabled.
    8. If enabled, adds a heading "Executive Summary" and renders the summary using RenderExecutiveSummarySection.
    9. Checks if experience data exists and the skills matrix is enabled.
    10. If enabled, renders the skills matrix using RenderSkillsMatrixSection.
    11. Checks if experience data exists and the experience section is enabled.
    12. If enabled, renders the experience section using RenderExperienceSection.

---

===

===
# File: `resume_writer/resume_render/ats/experience_section.py`

## `RenderRoleSection` class

Render experience roles section.

Inherits from:
    ResumeRenderRoleBase: Base class for rendering role-specific content.

Attributes:
    document (docx.document.Document): The Docx document object to render into.
    role (Role): The role data to render.
    settings (ResumeRolesSettings): The settings for rendering the role.
    errors (list[str]): List to store any errors encountered during rendering.

Methods:
    _skills: Render role skills section.
    _details: Render role details section.
    _dates: Generate dates string for role.
    render: Render role overview/basics section.

---
## method: `RenderRoleSection.__init__(self: UnknownType, document: docx.document.Document, role: Role, settings: ResumeRolesSettings) -> UnknownType`

Initialize roles render object.

Args:
    document (docx.document.Document): The Docx document object to render into.
    role (Role): The role data to render.
    settings (ResumeRolesSettings): The settings for rendering the role.

Notes:
    1. Initializes the parent class with the provided document, role, and settings.
    2. Logs the initialization process for debugging.

---
## method: `RenderRoleSection._skills(self: UnknownType) -> list[str]`

Render role skills section.

Returns:
    A list of strings containing the formatted skills text.

Notes:
    1. Initialize an empty list to store the output lines.
    2. Check if the role has skills and the settings allow rendering skills.
    3. If skills exist, join them into a comma-separated string.
    4. Append the formatted "Skills: <skills>" string to the output list.
    5. Return the list of formatted skill lines.

---
## method: `RenderRoleSection._details(self: UnknownType) -> list[str]`

Render role details section.

Returns:
    A list of strings containing the formatted detail lines.

Notes:
    1. Initialize an empty list to store the output lines.
    2. Extract the basics information from the role.
    3. If job category is present and enabled in settings, append it to the output list.
    4. If location is present and enabled in settings, append it to the output list.
    5. If agency name is present and enabled in settings, append it to the output list.
    6. If employment type is present and enabled in settings, append it to the output list.
    7. Return the list of formatted detail lines.

---
## method: `RenderRoleSection._dates(self: UnknownType) -> str`

Generate dates string for role.

Returns:
    A formatted string containing start date and optional end date.

Notes:
    1. Extract the basics information from the role.
    2. If start date is missing, log a warning and append an error.
    3. Format the start date as "mm-YYYY".
    4. If end date is present, format it as "mm-YYYY" and append to the string.
    5. If end date is missing, append " - Present" to the string.
    6. Return the final formatted date string.

---
## method: `RenderRoleSection.render(self: UnknownType) -> None`

Render role overview/basics section.

Notes:
    1. Initialize an empty list to store paragraph lines.
    2. Create a paragraph for the role basics.
    3. If company name is missing, log an error and append to errors list.
    4. Add the company name as bold and underlined text with increased font size.
    5. Insert a line break.
    6. If title is missing, log an error and append to errors list.
    7. Add the title as bold text.
    8. Insert a line break.
    9. Generate and add the formatted dates to the paragraph.
    10. Create a paragraph for the details section.
    11. Collect and clean the detail lines.
    12. If any detail lines exist, add them to the details paragraph.
    13. If summary is present and enabled, add it as italicized text with spacing.
    14. If responsibilities are present and enabled, add them with spacing.
    15. If skills are present and enabled, add them with spacing.

---
## `RenderRolesSection` class

Render experience roles section.

Inherits from:
    ResumeRenderRolesBase: Base class for rendering roles-related content.

Attributes:
    document (docx.document.Document): The Docx document object to render into.
    roles (Roles): The list of role data to render.
    settings (ResumeRolesSettings): The settings for rendering the roles.
    errors (list[str]): List to store any errors encountered during rendering.

Methods:
    render: Render roles section.

---
## method: `RenderRolesSection.__init__(self: UnknownType, document: docx.document.Document, roles: Roles, settings: ResumeRolesSettings) -> UnknownType`

Initialize roles render object.

Args:
    document (docx.document.Document): The Docx document object to render into.
    roles (Roles): The list of role data to render.
    settings (ResumeRolesSettings): The settings for rendering the roles.

Notes:
    1. Initializes the parent class with the provided document, roles, and settings.

---
## method: `RenderRolesSection.render(self: UnknownType) -> None`

Render roles section.

Notes:
    1. If no roles are present, log info and return.
    2. Add a heading "Work History" with level 2.
    3. For each role:
    4. If it's the first role, add a horizontal line.
    5. Render the role using RenderRoleSection.
    6. If it's not last role, add a horizontal line and a blank paragraph.

---
## `RenderProjectSection` class

Render experience project section.

Inherits from:
    ResumeRenderProjectBase: Base class for rendering project-specific content.

Attributes:
    document (docx.document.Document): The Docx document object to render into.
    project (Project): The project data to render.
    settings (ResumeProjectsSettings): The settings for rendering the project.
    errors (list[str]): List to store any errors encountered during rendering.

Methods:
    _overview: Render project overview section.
    _skills: Render project skills section.
    render: Render project section.

---
## method: `RenderProjectSection.__init__(self: UnknownType, document: docx.document.Document, project: Project, settings: ResumeProjectsSettings) -> UnknownType`

Initialize project render object.

Args:
    document (docx.document.Document): The Docx document object to render into.
    project (Project): The project data to render.
    settings (ResumeProjectsSettings): The settings for rendering the project.

Notes:
    1. Initializes the parent class with the provided document, project, and settings.
    2. Logs the initialization process for debugging.

---
## method: `RenderProjectSection._overview(self: UnknownType) -> list[str]`

Render project overview section.

Returns:
    A list of strings containing the formatted overview lines.

Notes:
    1. Initialize an empty list to store output lines.
    2. Extract the project overview data.
    3. If URL description and URL are present and enabled, create a formatted URL line.
    4. If start date is present and enabled, format it and append.
    5. If end date is present and enabled, format it and append.
    6. Return the list of formatted lines.

---
## method: `RenderProjectSection._skills(self: UnknownType) -> list[str]`

Render project skills section.

Returns:
    A list of strings containing the formatted skills text.

Notes:
    1. Initialize an empty list to store output lines.
    2. Join the project skills into a comma-separated string.
    3. Append the formatted "Skills: <skills>" string to the output list.
    4. Return the list of formatted skill lines.

---
## method: `RenderProjectSection.render(self: UnknownType) -> None`

Render project section.

Notes:
    1. Initialize an empty list to store paragraph lines.
    2. If overview is present and enabled, collect its lines.
    3. If description is present and enabled, add it to the lines.
    4. If skills are present and enabled, collect their lines.
    5. If any lines exist, add them to the document as a single paragraph.

---
## `RenderProjectsSection` class

Render experience projects section.

Inherits from:
    ResumeRenderProjectsBase: Base class for rendering projects-related content.

Attributes:
    document (docx.document.Document): The Docx document object to render into.
    projects (Projects): The list of project data to render.
    settings (ResumeProjectsSettings): The settings for rendering the projects.
    errors (list[str]): List to store any errors encountered during rendering.

Methods:
    render: Render projects section.

---
## method: `RenderProjectsSection.__init__(self: UnknownType, document: docx.document.Document, projects: Projects, settings: ResumeProjectsSettings) -> UnknownType`

Initialize projects render object.

Args:
    document (docx.document.Document): The Docx document object to render into.
    projects (Projects): The list of project data to render.
    settings (ResumeProjectsSettings): The settings for rendering the projects.

Notes:
    1. Initializes the parent class with the provided document, projects, and settings.
    2. Logs the initialization process for debugging.

---
## method: `RenderProjectsSection.render(self: UnknownType) -> None`

Render projects section.

Notes:
    1. If no projects are present, log info and return.
    2. Add a heading "Projects" with level 2.
    3. For each project:
    4. Create a RenderProjectSection object.
    5. Render the project.

---
## `RenderExperienceSection` class

Render experience section.

Inherits from:
    ResumeRenderExperienceBase: Base class for rendering experience-related content.

Attributes:
    document (docx.document.Document): The Docx document object to render into.
    experience (Experience): The experience data to render.
    settings (ResumeExperienceSettings): The settings for rendering the experience.
    errors (list[str]): List to store any errors encountered during rendering.

Methods:
    render: Render experience section.

---
## method: `RenderExperienceSection.__init__(self: UnknownType, document: docx.document.Document, experience: Experience, settings: ResumeExperienceSettings) -> None`

Initialize experience render object.

Args:
    document (docx.document.Document): The Docx document object to render into.
    experience (Experience): The experience data to render.
    settings (ResumeExperienceSettings): The settings for rendering the experience.

Notes:
    1. Initializes the parent class with the provided document, experience, and settings.
    2. Logs the initialization process for debugging.

---
## method: `RenderExperienceSection.render(self: UnknownType) -> None`

Render experience section.

Notes:
    1. If roles are present and enabled, render the roles section.
    2. If projects are present and enabled, render the projects section.

---

===

===
# File: `resume_writer/resume_render/ats/executive_summary_section.py`

## `RenderExecutiveSummarySection` class

Render experience for a functional resume.

Attributes:
    document (docx.document.Document): The Word document object to which the executive summary will be added.
    experience (Experience): The experience data containing roles and related information.
    settings (ResumeExecutiveSummarySettings): Configuration settings for rendering the executive summary section.

Inherits from:
    ResumeRenderExecutiveSummaryBase: Base class for rendering executive summary sections.

---
## method: `RenderExecutiveSummarySection.__init__(self: UnknownType, document: docx.document.Document, experience: Experience, settings: ResumeExecutiveSummarySettings) -> None`

Initialize experience render object.

Args:
    document (docx.document.Document): The Word document object to which the executive summary will be added.
    experience (Experience): The experience data containing roles and related information.
    settings (ResumeExecutiveSummarySettings): Configuration settings for rendering the executive summary section.

Returns:
    None

Notes:
    1. Initialize the parent class with the provided document, experience, and settings.
    2. Log a debug message indicating the initialization of the functional experience render object.

---
## method: `RenderExecutiveSummarySection.render(self: UnknownType) -> None`

Render experience section for functional resume.

Args:
    None

Returns:
    None

Notes:
    1. Log a debug message indicating the start of rendering the functional experience section.
    2. Validate that the experience object contains at least one role; raise a ValueError if not.
    3. Collect all unique job categories from the roles in the experience.
    4. For each job category specified in the settings:
        a. Filter roles belonging to the current category.
        b. If no roles are found for the category, log a warning and skip to the next category.
        c. Add a heading for the category with level 4.
        d. For each role in the category:
            i. If no summary is available for the role, log a warning and skip to the next role.
            ii. If no company is available for the role, log a warning and skip to the next role.
            iii. Create a new paragraph with the bullet style.
            iv. Add the role summary as a run to the paragraph.
            v. Add the company name in italic as a run to the paragraph, appended to the summary.

---

===

===
# File: `resume_writer/resume_render/ats/education_section.py`

## `RenderDegreeSection` class

Render a single academic degree section in a resume document.

This class is responsible for formatting and adding a single degree's details
to a Word document, including school name, degree type, dates, major, and GPA
based on the provided settings.

Attributes:
    document (docx.document.Document): The Word document object to which the degree section will be added.
    degree (Degree): The Degree object containing the academic details (school, degree, dates, major, GPA).
    settings (ResumeEducationSettings): Configuration object specifying which fields to render.

Args:
    document (docx.document.Document): The Word document object to which the degree section will be added.
    degree (Degree): The Degree object containing the academic details (school, degree, dates, major, GPA).
    settings (ResumeEducationSettings): Configuration object specifying which fields to render.

Notes:
    1. The method initializes the rendering process for a single degree.
    2. It adds a paragraph to the document.
    3. If the school name is present and the school setting is enabled, it adds the school name in bold, underlined, and slightly larger font.
    4. If the degree name is present and the degree setting is enabled, it adds the degree name in bold.
    5. If the start date is present and the start date setting is enabled, it formats and adds the start date (e.g., "January 2020").
    6. If the end date is present and the end date setting is enabled, it formats and adds the end date (e.g., "December 2024") or "Present" if no end date is provided.
    7. If the major is present and the major setting is enabled, it adds the major name.
    8. If the GPA is present and the GPA setting is enabled, it adds the GPA label and value.
    9. The method does not perform any disk, network, or database access.

---
## method: `RenderDegreeSection.__init__(self: UnknownType, document: docx.document.Document, degree: Degree, settings: ResumeEducationSettings) -> UnknownType`

Initialize the basic degree renderer.

Args:
    document (docx.document.Document): The Word document object to which the degree section will be added.
    degree (Degree): The Degree object containing the academic details (school, degree, dates, major, GPA).
    settings (ResumeEducationSettings): Configuration object specifying which fields to render.

Returns:
    None: This method does not return a value.

Notes:
    1. Calls the parent class constructor to initialize base functionality.
    2. Sets the document, degree, and settings as instance attributes.
    3. The method does not perform any disk, network, or database access.

---
## method: `RenderDegreeSection.render(self: UnknownType) -> None`

Render a single degree.

This method constructs and adds a formatted paragraph to the document
representing a single degree, including school, degree, dates, major, and GPA
as specified by the settings.

Args:
    None: This method does not take any arguments.

Returns:
    None: This method does not return a value.

Notes:
    1. Logs debugging information about the rendering process.
    2. Creates a new paragraph in the document.
    3. Adds the school name (if enabled and present) with bold, underline, and increased font size.
    4. Adds a line break after the school name.
    5. Adds the degree name (if enabled and present) in bold.
    6. Adds a line break after the degree name.
    7. Adds the start date (if enabled and present) in "Month Year" format.
    8. Adds a " - " separator if the end date will be rendered.
    9. Adds a line break after the start date if no end date is rendered.
    10. Adds the end date (if enabled and present) in "Month Year" format or "Present" if no end date is provided.
    11. Adds a line break after the end date.
    12. Adds the major (if enabled and present).
    13. Adds a line break after the major.
    14. Adds the GPA (if enabled and present) with the label "GPA: ".
    15. The method does not perform any disk, network, or database access.

---
## `RenderEducationSection` class

Render the Education section of a resume in a Word document.

This class is responsible for formatting and adding an entire education section
to a Word document, including a heading and a list of rendered degree sections
based on the provided settings.

Attributes:
    document (docx.document.Document): The Word document object to which the education section will be added.
    education (Education): The Education object containing a list of Degree objects.
    settings (ResumeEducationSettings): Configuration object specifying which fields to render.

Args:
    document (docx.document.Document): The Word document object to which the education section will be added.
    education (Education): The Education object containing a list of Degree objects.
    settings (ResumeEducationSettings): Configuration object specifying which fields to render.

Returns:
    None: This method does not return a value.

Notes:
    1. Logs debugging information about the rendering process.
    2. Checks if the degrees setting is disabled; if so, returns early without rendering.
    3. Adds a level-2 heading labeled "Education" to the document.
    4. Iterates over each degree in the education's degrees list.
    5. For each degree, creates and calls RenderDegreeSection to render that degree.
    6. Adds a blank paragraph between degrees to separate them visually, except after the last degree.
    7. The method does not perform any disk, network, or database access.

---
## method: `RenderEducationSection.__init__(self: UnknownType, document: docx.document.Document, education: Education, settings: ResumeEducationSettings) -> UnknownType`

Initialize the basic education renderer.

Args:
    document (docx.document.Document): The Word document object to which the education section will be added.
    education (Education): The Education object containing a list of Degree objects.
    settings (ResumeEducationSettings): Configuration object specifying which fields to render.

Returns:
    None: This method does not return a value.

Notes:
    1. Calls the parent class constructor to initialize base functionality.
    2. Sets the document, education, and settings as instance attributes.
    3. The method does not perform any disk, network, or database access.

---
## method: `RenderEducationSection.render(self: UnknownType) -> None`

Render the education section.

This method adds a formatted heading and a list of degree sections to the document,
using the provided education data and rendering settings.

Args:
    None: This method does not take any arguments.

Returns:
    None: This method does not return a value.

Notes:
    1. Logs debugging information about the rendering process.
    2. Checks if the degrees setting is disabled; if so, returns early.
    3. Adds a heading "Education" at level 2 to the document.
    4. Iterates through each degree in the education's degrees list.
    5. For each degree, instantiates a RenderDegreeSection and calls its render method.
    6. Adds a blank paragraph after each degree except the last one to provide visual separation.
    7. The method does not perform any disk, network, or database access.

---

===

===
# File: `resume_writer/resume_render/ats/certifications_section.py`

## `RenderCertificationSection` class

Render Certification Section.

This class is responsible for rendering a single certification entry in a Word document.
It uses the provided certification details and settings to format and add the information
to the document as a formatted paragraph.

Inherits from:
    ResumeRenderCertificationBase: Base class providing shared functionality for rendering certifications.

Attributes:
    document (docx.document.Document): The Word document to which the certification will be added.
    certification (Certification): The certification object containing details such as name, issuer, issued date, and expiration date.
    settings (ResumeCertificationsSettings): Configuration settings that determine which fields to display in the rendered output.

Methods:
    render: Renders the certification details into the document based on enabled settings.

---
## method: `RenderCertificationSection.__init__(self: UnknownType, document: docx.document.Document, certification: Certification, settings: ResumeCertificationsSettings) -> UnknownType`

Initialize the basic certification renderer.

Args:
    document (docx.document.Document): The Word document to which the certification will be added.
    certification (Certification): The certification object containing details such as name, issuer, issued date, and expiration date.
    settings (ResumeCertificationsSettings): Configuration settings that determine which fields to display in the rendered output.

Notes:
    1. Calls the parent class constructor to initialize common attributes.

---
## method: `RenderCertificationSection.render(self: UnknownType) -> None`

Render the certification section in the document.

This method builds and adds a formatted paragraph for the certification based on enabled settings
such as showing the name, issuer, issued date, or expiration date.

Args:
    None: This method does not accept any arguments.

Returns:
    None: This method does not return any value.

Notes:
    1. Initializes an empty list to store lines of text for the certification.
    2. If the certification name exists and the name setting is enabled, adds the name to the lines.
    3. If the issuer exists and the issuer setting is enabled, adds the issuer to the lines.
    4. If the issued date exists and the issued setting is enabled, formats the date to "Month Year" and adds it to the lines.
    5. If the expiration date exists and the expires setting is enabled, formats the date to "Month Year" and adds it to the lines.
    6. If any lines were generated, joins them with newline characters and adds the resulting paragraph to the document.

---
## `RenderCertificationsSection` class

Render Certifications Section.

This class is responsible for rendering the entire certifications section of a resume in a Word document.
It adds a level-2 heading and then iterates over each certification to render it using the
RenderCertificationSection class.

Inherits from:
    ResumeRenderCertificationsBase: Base class providing shared functionality for rendering multiple certifications.

Attributes:
    document (docx.document.Document): The Word document to which the certifications section will be added.
    certifications (Certifications): A collection of Certification objects to be rendered.
    settings (ResumeCertificationsSettings): Configuration settings that determine which fields to display for each certification.

Methods:
    render: Renders the entire certifications section with a heading and individual certification entries.

---
## method: `RenderCertificationsSection.__init__(self: UnknownType, document: docx.document.Document, certifications: Certifications, settings: ResumeCertificationsSettings) -> UnknownType`

Initialize the basic certifications renderer.

Args:
    document (docx.document.Document): The Word document to which the certifications section will be added.
    certifications (Certifications): A collection of Certification objects to be rendered.
    settings (ResumeCertificationsSettings): Configuration settings that determine which fields to display for each certification.

Notes:
    1. Calls the parent class constructor to initialize common attributes.

---
## method: `RenderCertificationsSection.render(self: UnknownType) -> None`

Render the certifications section in the document.

This method adds a level-2 heading titled "Certifications" and then renders each certification
in the collection using the RenderCertificationSection class.

Args:
    None: This method does not accept any arguments.

Returns:
    None: This method does not return any value.

Notes:
    1. If there are certifications to render, adds a level-2 heading titled "Certifications".
    2. Iterates through each certification in the collection.
    3. For each certification, creates a RenderCertificationSection instance and renders it into the document.

---

===

===
# File: `resume_writer/resume_render/ats/skills_matrix_section.py`

## `RenderSkillsMatrixSection` class

Render skills for a functional resume.

Attributes:
    document (docx.document.Document): The Word document to render into.
    experience (Experience): The parsed experience data containing roles and skill history.
    settings (ResumeSkillsMatrixSettings): Configuration settings for rendering skills matrix.
    parse_context (ParseContext): Contextual information used during parsing, used to track state.

---
## method: `RenderSkillsMatrixSection.__init__(self: UnknownType, document: docx.document.Document, experience: Experience, settings: ResumeSkillsMatrixSettings, parse_context: ParseContext) -> UnknownType`

Initialize skills render object.

Args:
    document (docx.document.Document): The Word document to render into.
    experience (Experience): The parsed experience data containing roles and skill history.
    settings (ResumeSkillsMatrixSettings): Configuration settings for rendering skills matrix.
    parse_context (ParseContext): Contextual information used during parsing, used to track state.

Returns:
    None

Notes:
    1. Validate that the provided parse_context is an instance of ParseContext.
    2. Store the parse_context for later use during rendering.
    3. Call the parent class constructor with the provided document, experience, and settings.

---
## method: `RenderSkillsMatrixSection.render(self: UnknownType) -> None`

Render skills section for functional resume.

Args:
    None

Returns:
    None

Notes:
    1. Check if the experience object contains any roles; if not, raise a ValueError.
    2. Create a SkillsMatrix instance from the experience roles.
    3. If settings.all_skills is True, generate a matrix containing all skills; otherwise, use only the specified skills from settings.skills.
    4. Determine the number of rows needed in the table based on the number of skills (with two skills per row).
    5. Add a table with the calculated number of rows and 4 columns, using the "Table Grid" style.
    6. Add a header row with bolded column labels: "Skill", "YOE (from - to)", "Skill", and "YOE (from - to)".
    7. Iterate through the sorted skills and their associated data.
    8. For each skill, place it in the appropriate cell (alternating between columns 0 and 2).
    9. Format the years of experience (YOE) string as "{yoe} ({first_used} - {last_used})", using "N/A" if dates are missing.
    10. Place the formatted YOE string in the corresponding cell to the right of the skill.
    11. Set vertical center alignment for both skill and YOE cells.
    12. Automatically adjust table column widths to fit content.

---

===

===
# File: `resume_writer/resume_render/ats/__init__.py`


===

===
# File: `resume_writer/resume_render/ats/personal_section.py`

## `RenderPersonalSection` class

Render personal contact info section.

Attributes:
    document (docx.document.Document): The Docx document object to render into.
    personal (Personal): The Personal model containing personal information.
    settings (ResumePersonalSettings): The ResumePersonalSettings object controlling which sections to render.

---
## method: `RenderPersonalSection.__init__(self: UnknownType, document: docx.document.Document, personal: Personal, settings: ResumePersonalSettings) -> UnknownType`

Initialize the personal section renderer.

Args:
    document (docx.document.Document): The Docx document object to render into.
    personal (Personal): The Personal model containing personal information.
    settings (ResumePersonalSettings): The ResumePersonalSettings object controlling which sections to render.

Returns:
    None.

Notes:
    1. Logs the initialization of the personal basic render object.
    2. Calls the parent class constructor with the provided arguments.

---
## method: `RenderPersonalSection._contact_info(self: UnknownType) -> None`

Render the contact info section.

Args:
    None.

Returns:
    None.

Notes:
    1. Creates a new paragraph in the document.
    2. Extracts contact info from the personal model.
    3. If name is present and enabled in settings, adds the name as a bold, larger font run and adds a line break.
    4. If email is present and enabled in settings, adds the email as a run and adds a line break.
    5. If phone is present and enabled in settings, adds the phone as a run and adds a line break.
    6. If location is present and enabled in settings, adds the location as a run and adds a line break.

---
## method: `RenderPersonalSection._banner(self: UnknownType) -> None`

Render the banner section.

Args:
    None.

Returns:
    None.

Notes:
    1. Extracts the banner text from the personal model.
    2. If banner text is present, adds a level 3 heading "Banner".
    3. Adds the banner text as a paragraph.

---
## method: `RenderPersonalSection._note(self: UnknownType) -> None`

Render the note section.

Args:
    None.

Returns:
    None.

Notes:
    1. Extracts the note text from the personal model.
    2. If note text is present, adds a level 3 heading "Note".
    3. Adds the note text as a paragraph.

---
## method: `RenderPersonalSection._websites(self: UnknownType) -> None`

Render the websites section.

Args:
    None.

Returns:
    None.

Notes:
    1. Initializes an empty list to store website lines.
    2. Extracts websites from the personal model.
    3. If GitHub is present and enabled in settings, appends "GitHub: <url>" to the list.
    4. If LinkedIn is present and enabled in settings, appends "LinkedIn: <url>" to the list.
    5. If website is present and enabled in settings, appends "Website: <url>" to the list.
    6. If Twitter is present and enabled in settings, appends "Twitter: <url>" to the list.
    7. If the list is not empty, adds a level 3 heading "Websites".
    8. Joins the list with newlines and adds it as a paragraph.

---
## method: `RenderPersonalSection._visa_status(self: UnknownType) -> None`

Render the visa status section.

Args:
    None.

Returns:
    None.

Notes:
    1. Initializes an empty list to store visa status lines.
    2. Extracts visa status from the personal model.
    3. If work authorization is present and enabled in settings, appends "Work Authorization: <value>" to the list.
    4. If require_sponsorship is not None and enabled in settings, appends "Require Sponsorship: Yes" or "No" based on the value.
    5. If the list is not empty, adds a level 3 heading "Visa Status".
    6. Joins the list with newlines and adds it as a paragraph.

---
## method: `RenderPersonalSection.render(self: UnknownType) -> None`

Render the personal section.

Args:
    None.

Returns:
    None.

Notes:
    1. If contact info exists and enabled in settings, calls _contact_info.
    2. If banner exists and enabled in settings, calls _banner.
    3. If note exists and enabled in settings, calls _note.
    4. If websites exist and enabled in settings, calls _websites.
    5. If visa status exists and enabled in settings, calls _visa_status.

---

===

===
# File: `resume_writer/resume_render/html/certifications_section.py`

## `RenderCertificationsSection` class

Render Certifications Section.

---
## method: `RenderCertificationsSection.__init__(self: UnknownType, document: HtmlDoc, jinja_env: Environment, certifications: Certifications, settings: ResumeCertificationsSettings) -> UnknownType`

Initialize the basic certifications renderer.

---
## method: `RenderCertificationsSection.render(self: UnknownType) -> None`

Render the certifications section.

---

===

===
# File: `resume_writer/resume_render/html/__init__.py`

## function: `render_resume_to_html(resume_data: Resume, template_path: str, output_path: str) -> None`

Renders a resume object to an HTML file using a specified template.

Args:
    resume_data (Resume): The resume object containing all the personal, professional, and
                          other relevant resume details to be rendered.
    template_path (str): The file path to the HTML template used for rendering the resume.
                         This template should contain placeholders for dynamic content.
    output_path (str): The file path where the generated HTML resume will be saved.

Returns:
    None: This function does not return a value; it writes the rendered HTML to the specified file.

Notes:
    1. Loads the HTML template from the file specified by `template_path`.
    2. Parses the `resume_data` structure to extract relevant fields such as name, contact info,
       work experience, education, skills, etc.
    3. Replaces placeholders in the template with actual resume content using a templating engine
       (e.g., Jinja2 or similar).
    4. Saves the rendered HTML to the file specified by `output_path`.
    5. The function performs disk I/O operations to read the template and write the output file.
    6. The function assumes that the template file is valid and contains the expected placeholders.

---


===

===
# File: `resume_writer/resume_render/html/resume_main.py`

## `RenderResume` class

Render a resume in HTML format.

Attributes:
    document (HtmlDoc): The HTML document to render into.
    jinja_env (Environment): The Jinja2 environment used for templating.
    resume (Resume): The resume data to render.
    settings (ResumeRenderSettings): The rendering settings for the resume.

Inherits from:
    ResumeRenderBase: Base class for rendering resume sections.

---
## method: `RenderResume.__init__(self: UnknownType, document: HtmlDoc, jinja_env: Environment, resume: Resume, settings: ResumeRenderSettings) -> UnknownType`

Initialize the HTML resume renderer.

Args:
    document (HtmlDoc): The HTML document to render into.
    jinja_env (Environment): The Jinja2 environment used for templating.
    resume (Resume): The resume data to render.
    settings (ResumeRenderSettings): The rendering settings for the resume.

Notes:
    1. Calls the parent constructor with the provided arguments.

---
## method: `RenderResume.render(self: UnknownType) -> None`

Render the resume by processing each section.

Args:
    None

Returns:
    None: This function does not return a value.

Notes:
    1. If the resume has personal information and personal rendering is enabled, render the personal section.
    2. If the resume has education data and education rendering is enabled, render the education section.
    3. If the resume has certifications and certifications rendering is enabled, render the certifications section.
    4. If the resume has experience data and experience rendering is enabled, render the experience section.
    5. No disk, network, or database access occurs during this process.

---

===

===
# File: `resume_writer/resume_render/html/skills_matrix_section.py`

## `RenderSkillsMatrixSection` class

Render skills for a functional resume.

Attributes:
    document (docx.document.Document): The Word document object to which the skills section will be added.
    experience (Experience): The experience data containing roles and associated skills.
    settings (ResumeSkillsMatrixSettings): Configuration settings for rendering the skills matrix, including
                                          which skills to include and whether to include all skills.

Base class:
    ResumeRenderSkillsMatrixBase: Base class for rendering skills matrix sections.

---
## method: `RenderSkillsMatrixSection.__init__(self: UnknownType, document: docx.document.Document, experience: Experience, settings: ResumeSkillsMatrixSettings) -> UnknownType`

Initialize skills render object.

Args:
    document (docx.document.Document): The Word document object to which the skills section will be added.
    experience (Experience): The experience data containing roles and associated skills.
    settings (ResumeSkillsMatrixSettings): Configuration settings for rendering the skills matrix, including
                                          which skills to include and whether to include all skills.

Notes:
    1. Initializes the base class with the provided document, experience, and settings.
    2. Logs the initialization process.

---
## method: `RenderSkillsMatrixSection.find_skill_date_range(self: UnknownType, skill: str) -> tuple[datetime | None, datetime | None]`

Find the earliest start date and latest end date for a given skill across roles.

Args:
    skill (str): The name of the skill to search for in roles.

Returns:
    tuple[datetime | None, datetime | None]: A tuple containing:
        - The earliest start date for any role that includes the skill (or None if not found).
        - The latest end date for any role that includes the skill (or None if not found).

Notes:
    1. Collects all start dates from roles where the skill appears.
    2. Collects all end dates from roles where the skill appears.
    3. If any roles contain the skill, finds the minimum start date and maximum end date.
    4. Returns the earliest start date and latest end date as a tuple.

---
## method: `RenderSkillsMatrixSection._get_skills_matrix(self: UnknownType) -> dict[str, float]`

Compute and filter skills matrix based on settings.

Returns:
    dict[str, float]: A dictionary mapping skill names to years of experience (float), sorted in descending order.

Notes:
    1. Retrieves all roles from the experience object.
    2. Filters the skills specified in the settings, removing any blank entries.
    3. Creates a SkillsMatrix object from the roles and computes the experience for each skill.
    4. Filters the skills to include only those present in the settings, unless all_skills is True.
    5. Sorts the resulting dictionary by years of experience in descending order.
    6. Returns the filtered and sorted dictionary.

---
## method: `RenderSkillsMatrixSection.render(self: UnknownType) -> None`

Render the skills matrix section in the document.

Notes:
    1. Validates that the experience object contains at least one role.
    2. Retrieves the filtered skills matrix with years of experience.
    3. Ensures the returned skills dictionary is valid and properly typed.
    4. Calculates the number of rows needed for the table based on the number of skills.
    5. Creates a 4-column table with the calculated number of rows.
    6. Sets a fixed height for each row.
    7. Populates the first two columns with skill names and years of experience (including date range).
    8. Populates the last two columns with the remaining skills and their experience (including date range).
    9. Enables automatic fitting of the table to its content.

---

===

===
# File: `resume_writer/resume_render/html/experience_section.py`

## `RenderRolesSection` class

Render experience roles section.

This class is responsible for rendering a section of job roles within a resume
using a Jinja2 template. It processes role data and outputs formatted HTML.

Attributes:
    document (HtmlDoc): The HTML document object to which rendered content will be added.
    jinja_env (Environment): The Jinja2 environment used to render templates.
    roles (Roles): A collection of job roles to be rendered.
    template_name (str): Name of the Jinja2 template file for rendering roles.
    settings (ResumeRolesSettings): Configuration settings for how roles should be rendered.

Args:
    document (HtmlDoc): The HTML document object to which rendered content will be added.
    jinja_env (Environment): The Jinja2 environment used to render templates.
    roles (Roles): A collection of job roles to be rendered.
    settings (ResumeRolesSettings): Configuration settings for how roles should be rendered.

Notes:
    1. Initializes the parent class with the provided document, Jinja2 environment,
       roles, template name, and settings.
    2. The `render` method checks if roles exist.
    3. If roles exist, it uses the Jinja2 template to render the roles with the given settings.
    4. The rendered content is added to the document using `add_text`.
    5. No disk, network, or database access is performed.

Returns:
    None

---
## method: `RenderRolesSection.__init__(self: UnknownType, document: HtmlDoc, jinja_env: Environment, roles: Roles, settings: ResumeRolesSettings) -> UnknownType`

Initialize roles render object.

Args:
    document (HtmlDoc): The HTML document object to which rendered content will be added.
    jinja_env (Environment): The Jinja2 environment used to render templates.
    roles (Roles): A collection of job roles to be rendered.
    settings (ResumeRolesSettings): Configuration settings for how roles should be rendered.

Notes:
    1. Initializes the parent class with the provided document, Jinja2 environment,
       roles, template name, and settings.

Returns:
    None

---
## method: `RenderRolesSection.render(self: UnknownType) -> None`

Render roles section.

Renders the job roles section into the HTML document using a Jinja2 template.

Args:
    None

Returns:
    None: The method adds rendered HTML directly to the document.

Notes:
    1. Checks if `self.roles` is empty; if so, logs a debug message and exits.
    2. Logs a debug message indicating rendering has started.
    3. Renders the Jinja2 template with `settings` and `roles` as context.
    4. Adds the rendered string to the document using `add_text`.
    5. No disk, network, or database access is used.

---
## `RenderProjectsSection` class

Render experience projects section.

This class renders a section of projects associated with a resume using a Jinja2 template.

Attributes:
    document (HtmlDoc): The HTML document object to which rendered content will be added.
    jinja_env (Environment): The Jinja2 environment used to render templates.
    projects (Projects): A collection of projects to be rendered.
    template_name (str): Name of the Jinja2 template file for rendering projects.
    settings (ResumeProjectsSettings): Configuration settings for how projects should be rendered.

Args:
    document (HtmlDoc): The HTML document object to which rendered content will be added.
    jinja_env (Environment): The Jinja2 environment used to render templates.
    projects (Projects): A collection of projects to be rendered.
    settings (ResumeProjectsSettings): Configuration settings for how projects should be rendered.

Notes:
    1. Initializes the parent class with the provided document, Jinja2 environment,
       projects, template name, and settings.
    2. The `render` method checks if projects exist.
    3. If projects exist, it uses the Jinja2 template to render the projects with the given settings.
    4. The rendered content is added to the document using `add_text`.
    5. No disk, network, or database access is performed.

Returns:
    None

---
## method: `RenderProjectsSection.__init__(self: UnknownType, document: HtmlDoc, jinja_env: Environment, projects: Projects, settings: ResumeProjectsSettings) -> UnknownType`

Initialize projects render object.

Args:
    document (HtmlDoc): The HTML document object to which rendered content will be added.
    jinja_env (Environment): The Jinja2 environment used to render templates.
    projects (Projects): A collection of projects to be rendered.
    settings (ResumeProjectsSettings): Configuration settings for how projects should be rendered.

Notes:
    1. Initializes the parent class with the provided document, Jinja2 environment,
       projects, template name, and settings.

Returns:
    None

---
## method: `RenderProjectsSection.render(self: UnknownType) -> None`

Render projects section.

Renders the projects section into the HTML document using a Jinja2 template.

Args:
    None

Returns:
    None: The method adds rendered HTML directly to the document.

Notes:
    1. Checks if `len(self.projects)` is zero; if so, logs a debug message and returns.
    2. Logs a debug message indicating rendering has started.
    3. Renders the Jinja2 template with `settings` and `projects` as context.
    4. Adds the rendered string to the document using `add_text`.
    5. No disk, network, or database access is used.

---
## `RenderExperienceSection` class

Render experience section.

This class is responsible for rendering the entire experience section of a resume,
including roles and projects, using a Jinja2 template. It aggregates data from
`Experience`, and uses separate renderers for roles and projects.

Attributes:
    document (HtmlDoc): The HTML document where output will be added.
    jinja_env (Environment): Jinja2 environment for template rendering.
    experience (Experience): The experience data (roles and projects).
    settings (ResumeExperienceSettings): Rendering configuration for experience.

Args:
    document (HtmlDoc): The HTML document object to which rendered content will be added.
    jinja_env (Environment): The Jinja2 environment used to render templates.
    experience (Experience): The experience data (roles and projects) to be rendered.
    settings (ResumeExperienceSettings): Configuration settings for how experience should be rendered.

Notes:
    1. Initializes the parent class with the provided document, Jinja2 environment,
       experience, and settings.
    2. Calculates the total number of items (roles + projects) to render.
    3. If no items are present, exits early.
    4. Adds an HTML heading "Experience" to the document.
    5. If roles are enabled in settings and `experience.roles` is not empty,
       creates and renders a `RenderRolesSection`.
    6. If projects are enabled in settings and `experience.projects` is not empty,
       creates and renders a `RenderProjectsSection`.
    7. No disk, network, or database access is performed.

Returns:
    None

---
## method: `RenderExperienceSection.__init__(self: UnknownType, document: HtmlDoc, jinja_env: Environment, experience: Experience, settings: ResumeExperienceSettings) -> None`

Initialize experience render object.

Args:
    document (HtmlDoc): The HTML document object to which rendered content will be added.
    jinja_env (Environment): The Jinja2 environment used to render templates.
    experience (Experience): The experience data (roles and projects) to be rendered.
    settings (ResumeExperienceSettings): Configuration settings for how experience should be rendered.

Notes:
    1. Initializes the parent class with the provided document, Jinja2 environment,
       experience, and settings.

Returns:
    None

---
## method: `RenderExperienceSection.render(self: UnknownType) -> None`

Render experience section.

Renders the experience section into the HTML document, including roles and projects.

Args:
    None

Returns:
    None: The method adds rendered HTML directly to the document.

Notes:
    1. Calculates the total number of roles and projects that will be rendered.
    2. If no roles or projects exist, returns early.
    3. Adds an HTML heading "Experience" to the document.
    4. If roles are enabled and roles exist, creates and renders a `RenderRolesSection`.
    5. If projects are enabled and projects exist, creates and renders a `RenderProjectsSection`.
    6. No disk, network, or database access is used.

---

===

===
# File: `resume_writer/resume_render/html/executive_summary_section.py`

## `RenderExecutiveSummarySection` class

Render executive summary section for a functional resume.

This class is responsible for rendering the executive summary section of a resume based on experience data.
It processes roles and their categories, formatting them into a structured document with headings and bullet points.

Inherits from:
    ResumeRenderExecutiveSummaryBase: Base class providing common rendering functionality.

Attributes:
    document (docx.document.Document): The Word document object to render into.
    experience (Experience): The experience data containing roles and their details.
    settings (ResumeExecutiveSummarySettings): The rendering settings that control which categories are included and how they are formatted.

---
## method: `RenderExecutiveSummarySection.__init__(self: UnknownType, document: docx.document.Document, experience: Experience, settings: ResumeExecutiveSummarySettings) -> None`

Initialize the executive summary render object.

Args:
    document (docx.document.Document): The Word document object to render into.
    experience (Experience): The experience data containing roles and their details.
    settings (ResumeExecutiveSummarySettings): The rendering settings that control which categories are included and how they are formatted.

Returns:
    None

Notes:
    1. Logs a debug message indicating initialization.
    2. Calls the parent class constructor to initialize base rendering functionality.

---
## method: `RenderExecutiveSummarySection.render(self: UnknownType) -> None`

Render the executive summary section of the resume.

This method generates the executive summary by processing experience data and formatting it into a Word document.

Args:
    None

Returns:
    None

Notes:
    1. Logs a debug message indicating the start of rendering.
    2. Checks if the experience object contains any roles; if not, raises a ValueError.
    3. Collects all unique job categories from the roles in the experience data.
    4. Iterates over the job categories specified in the settings.
    5. For each category, filters roles that belong to that category.
    6. If no roles are found for a category, logs a warning and skips to the next category.
    7. Adds a heading for the current job category to the document with level 4.
    8. For each role in the category:
       a. Checks if a summary is available; if not, logs a warning and skips.
       b. Checks if a company name is available; if not, logs a warning and skips.
       c. Creates a new paragraph with a bullet point style.
       d. Adds the role summary as plain text.
       e. Adds the company name in italics, appended to the summary.
    9. No network, disk, or database access occurs during execution.

---

===

===
# File: `resume_writer/resume_render/html/personal_section.py`

## `RenderPersonalSection` class

Render personal contact info section.

Attributes:
    document (HtmlDoc): The HTML document to which the rendered personal section will be added.
    jinja_env (Environment): The Jinja2 environment used to render the template.
    personal (Personal): The personal information object containing contact details.
    settings (ResumePersonalSettings): The settings object that controls the rendering behavior of the personal section.

---
## method: `RenderPersonalSection.__init__(self: UnknownType, document: HtmlDoc, jinja_env: Environment, personal: Personal, settings: ResumePersonalSettings) -> None`

Initialize the personal section renderer.

Args:
    document (HtmlDoc): The HTML document to which the rendered personal section will be added.
    jinja_env (Environment): The Jinja2 environment used to render the template.
    personal (Personal): The personal information object containing contact details.
    settings (ResumePersonalSettings): The settings object that controls the rendering behavior of the personal section.

Returns:
    None

Notes:
    1. Logs a debug message indicating the initialization of the personal section renderer.
    2. Calls the parent class's __init__ method with the provided arguments to set up the base renderer.

---
## method: `RenderPersonalSection.render(self: UnknownType) -> None`

Render the personal section into the HTML document.

Args:
    None

Returns:
    None

Notes:
    1. Renders the Jinja2 template using the settings and personal data.
    2. Adds the rendered HTML content to the document.
    3. No network, disk, or database access is performed.

---

===

===
# File: `resume_writer/resume_render/html/education_section.py`

## `RenderEducationSection` class

Render Education Section.

---
## method: `RenderEducationSection.__init__(self: UnknownType, document: HtmlDoc, jinja_env: Environment, education: Education, settings: ResumeEducationSettings) -> UnknownType`

Initialize the basic education renderer.

---
## method: `RenderEducationSection.render(self: UnknownType) -> None`

Render the education section.

---

===

===
# File: `resume_writer/resume_render/markdown/certifications_section.py`

## `RenderCertificationsSection` class

Render Certifications Section.

Inherits from:
    ResumeRenderCertificationsBase: Base class for rendering certifications in a resume.

Attributes:
    document (MarkdownDoc): The Markdown document instance to which the rendered content will be added.
    certifications (Certifications): The list of certifications to render.
    settings (ResumeCertificationsSettings): Configuration settings for what information to include in the output.

---
## method: `RenderCertificationsSection.__init__(self: UnknownType, document: MarkdownDoc, certifications: Certifications, settings: ResumeCertificationsSettings) -> UnknownType`

Initialize the basic certifications renderer.

Args:
    document (MarkdownDoc): The Markdown document instance to which the rendered content will be added.
    certifications (Certifications): The list of certifications to render.
    settings (ResumeCertificationsSettings): Configuration settings for what information to include in the output.

Returns:
    None

Notes:
    1. Validate that the document is an instance of MarkdownDoc.
    2. Validate that the certifications is an instance of Certifications.
    3. Validate that the settings is an instance of ResumeCertificationsSettings.
    4. Call the parent class constructor with the provided arguments.
    5. No disk, network, or database access occurs during initialization.

---
## method: `RenderCertificationsSection.render_certification(self: UnknownType, certification: Certification) -> None`

Render a single certification in the document.

Args:
    certification (Certification): The certification object containing the details of a single certification to render.

Returns:
    None

Notes:
    1. Extract references to the document and settings for convenience.
    2. Add a header for the certification section.
    3. If the settings require the issuer and the certification has an issuer, add the issuer to the document.
    4. If the settings require the name and the certification has a name, add the name to the document.
    5. If the settings require the issued date and the certification has an issued date, add the issued date to the document.
    6. If the settings require the expiration date and the certification has an expiration date, add the expiration date to the document.
    7. If the settings require the certification ID and the certification has a certification ID, add the certification ID to the document.
    8. No disk, network, or database access occurs during rendering.

---
## method: `RenderCertificationsSection.render(self: UnknownType) -> None`

Render the certifications section into the document.

Args:
    None

Returns:
    None

Notes:
    1. Extract references to the document and certifications for convenience.
    2. If there are no certifications, log a debug message and return early.
    3. Log a debug message indicating that rendering has started.
    4. Add a top-level header for the certifications section.
    5. Iterate over each certification in the certifications list.
    6. For each certification, call the render_certification method to render its details.
    7. No disk, network, or database access occurs during rendering.

---

===

===
# File: `resume_writer/resume_render/markdown/resume_main.py`

## `RenderResume` class

Render a resume in basic Markdown format.

Attributes:
    document (MarkdownDoc): The Markdown document to render the resume into.
    resume (Resume): The resume data to render.
    settings (ResumeRenderSettings): The rendering settings for the resume.

---
## method: `RenderResume.__init__(self: UnknownType, document: MarkdownDoc, resume: Resume, settings: ResumeRenderSettings) -> UnknownType`

Initialize the basic resume renderer.

Args:
    document (MarkdownDoc): The Markdown document to render the resume into.
    resume (Resume): The resume data to render.
    settings (ResumeRenderSettings): The rendering settings for the resume.

Returns:
    None: This method does not return anything.

Notes:
    1. Calls the parent class constructor to initialize the base renderer.
    2. Stores the provided document, resume, and settings for later use during rendering.

---
## method: `RenderResume.render(self: UnknownType) -> None`

Render the resume by generating sections based on provided data and settings.

Args:
    None: This method does not take any arguments.

Returns:
    None: This method does not return anything.

Notes:
    1. Checks if the resume has personal information and if personal section rendering is enabled.
    2. If both conditions are true, renders the personal section.
    3. Checks if the resume has education information and if education section rendering is enabled.
    4. If both conditions are true, renders the education section.
    5. Checks if the resume has certifications and if certifications section rendering is enabled.
    6. If both conditions are true, renders the certifications section.
    7. Checks if the resume has experience information and if experience section rendering is enabled.
    8. If both conditions are true, renders the experience section.
    9. This method performs no disk, network, or database access.

---

===

===
# File: `resume_writer/resume_render/markdown/personal_section.py`

## `RenderPersonalSection` class

Render personal contact info section.

Attributes:
    document (MarkdownDoc): The MarkdownDoc instance to write rendered content to.
    personal (Personal): The Personal instance containing personal contact information.
    settings (ResumePersonalSettings): The ResumePersonalSettings instance defining which fields to render.

Base class:
    ResumeRenderPersonalBase

---
## method: `RenderPersonalSection.__init__(self: UnknownType, document: MarkdownDoc, personal: Personal, settings: ResumePersonalSettings) -> UnknownType`

Initialize the personal section renderer.

Args:
    document (MarkdownDoc): The MarkdownDoc instance to write rendered content to.
    personal (Personal): The Personal instance containing personal contact information.
    settings (ResumePersonalSettings): The ResumePersonalSettings instance defining which fields to render.

Returns:
    None

Notes:
    1. Validate that document is an instance of MarkdownDoc.
    2. Validate that personal is an instance of Personal.
    3. Validate that settings is an instance of ResumePersonalSettings.
    4. Call the parent class constructor with provided arguments.

---
## method: `RenderPersonalSection.websites(self: UnknownType) -> None`

Render the websites section.

Args:
    None

Returns:
    None

Notes:
    1. Retrieve references to document, personal, and settings from self.
    2. If websites rendering is enabled in settings and personal has websites data, render the section header.
    3. If GitHub URL is enabled in settings and personal has a GitHub URL, add it to the document.
    4. If LinkedIn URL is enabled in settings and personal has a LinkedIn URL, add it to the document.
    5. If Website URL is enabled in settings and personal has a Website URL, add it to the document.
    6. If Twitter URL is enabled in settings and personal has a Twitter URL, add it to the document.

---
## method: `RenderPersonalSection.contact_info(self: UnknownType) -> None`

Render the contact information section.

Args:
    None

Returns:
    None

Notes:
    1. Retrieve references to document, personal, and settings from self.
    2. Add the section header for "Contact Information".
    3. If contact info rendering is enabled in settings and personal has contact info data:
        a. If name rendering is enabled and personal has a name, add the name to the document.
        b. If email rendering is enabled and personal has an email, add the email to the document.
        c. If phone rendering is enabled and personal has a phone number, add the phone number to the document.
        d. If location rendering is enabled and personal has a location, add the location to the document.

---
## method: `RenderPersonalSection.render(self: UnknownType) -> None`

Render the personal section.

Args:
    None

Returns:
    None

Notes:
    1. Retrieve references to document, personal, and settings from self.
    2. Add the main section header "# Personal".
    3. Render the contact information section.
    4. If visa status rendering is enabled in settings and personal has visa status data:
        a. Add the section header "## Visa Status".
        b. If work authorization rendering is enabled and personal has work authorization data, add it to the document.
        c. If sponsorship requirement rendering is enabled and personal has a sponsorship requirement, add it to the document.
    5. If banner rendering is enabled in settings and personal has a banner with text, add the banner section header and text.
    6. If note rendering is enabled in settings and personal has a note with text, add the note section header and text.

---

===

===
# File: `resume_writer/resume_render/markdown/__init__.py`


===

===
# File: `resume_writer/resume_render/markdown/education_section.py`

## `RenderEducationSection` class

Render Education Section.

Attributes:
    document (MarkdownDoc): The Markdown document to which the education section will be added.
    education (Education): The Education object containing degree information to render.
    settings (ResumeEducationSettings): The settings object defining which fields to include in the rendered output.

---
## method: `RenderEducationSection.__init__(self: UnknownType, document: MarkdownDoc, education: Education, settings: ResumeEducationSettings) -> None`

Initialize the basic education renderer.

Args:
    document (MarkdownDoc): The Markdown document to which rendered content will be added.
    education (Education): The Education object containing degree information to be rendered.
    settings (ResumeEducationSettings): The settings object defining which fields to render.

Returns:
    None

Notes:
    1. Validate that the provided document is an instance of MarkdownDoc.
    2. Validate that the provided education is an instance of Education.
    3. Validate that the provided settings is an instance of ResumeEducationSettings.
    4. Call the parent class constructor with the provided arguments.

---
## method: `RenderEducationSection.render_degree(self: UnknownType, degree: Degree) -> None`

Render a single degree in the education section.

Args:
    degree (Degree): The Degree object containing details such as school, degree, major, dates, and GPA.

Returns:
    None

Notes:
    1. Retrieve shortcuts for the document and settings.
    2. Add a header for the degree section with "### Degree".
    3. If the settings flag for school is enabled and the degree has a school, add the school to the document.
    4. If the settings flag for degree is enabled and the degree has a degree name, add the degree to the document.
    5. If the settings flag for major is enabled and the degree has a major, add the major to the document.
    6. If the settings flag for start_date is enabled and the degree has a start date, format and add the start date to the document.
    7. If the settings flag for end_date is enabled and the degree has an end date, format and add the end date to the document.
    8. If the settings flag for gpa is enabled and the degree has a GPA, add the GPA to the document.

---
## method: `RenderEducationSection.render(self: UnknownType) -> None`

Render the complete education section.

Args:
    None

Returns:
    None

Notes:
    1. Retrieve shortcuts for the document, settings, and education.
    2. If the settings flag for degrees is disabled, log a debug message and return.
    3. Log a debug message indicating that the education section is being rendered.
    4. Add a top-level header for the education section with "# Education".
    5. Add a sub-header for the degrees section with "## Degrees".
    6. Iterate over each degree in the education object and call render_degree for each.

---

===

===
# File: `resume_writer/resume_render/markdown/experience_section.py`

## `RenderRolesSection` class

Render experience roles section.

This class is responsible for rendering individual roles within the experience section of a resume.
It inherits from ResumeRenderRolesBase, which provides base functionality for rendering role-related content.

Attributes:
    document (MarkdownDoc): The MarkdownDoc object to render the content into.
    roles (Roles): The list of Role objects to render.
    settings (ResumeRolesSettings): The settings object controlling what fields to render.

---
## method: `RenderRolesSection.__init__(self: UnknownType, document: MarkdownDoc, roles: Roles, settings: ResumeRolesSettings) -> UnknownType`

Initialize roles render object.

Args:
    document (MarkdownDoc): The MarkdownDoc object to render the content into.
    roles (Roles): The list of Role objects to render.
    settings (ResumeRolesSettings): The settings object controlling what fields to render.

Returns:
    None

Notes:
    1. Validate that `document` is an instance of MarkdownDoc.
    2. Validate that `roles` is an instance of Roles.
    3. Validate that `settings` is an instance of ResumeRolesSettings.
    4. Call the parent class constructor with the provided arguments.

---
## method: `RenderRolesSection.render_basics(self: UnknownType, role: Role) -> None`

Render role basics.

Args:
    role (Role): The Role object containing the basic information to render.

Returns:
    None

Notes:
    1. Extract shortcuts for the document and settings.
    2. Add a header for the basics section.
    3. Render the company name if present.
    4. Render the agency name if the setting is enabled and the field is present.
    5. Render the job category if the setting is enabled and the field is present.
    6. Render the employment type if the setting is enabled and the field is present.
    7. Render the start date if the setting is enabled and the field is present.
    8. Render the end date if the setting is enabled and the field is present.
    9. Render the title if present.
    10. Render the reason for change if the setting is enabled and the field is present.
    11. Render the location if the setting is enabled and the field is present.

---
## method: `RenderRolesSection.render_highlights(self: UnknownType, role: Role) -> None`

Render role highlights.

Args:
    role (Role): The Role object containing the highlights to render.

Returns:
    None

Notes:
    1. Extract shortcuts for the document and settings.
    2. If highlights are enabled in settings and the role has highlights, add a header for highlights.
    3. For each highlight in the role, add a bullet point to the document.

---
## method: `RenderRolesSection.render_responsibilities(self: UnknownType, role: Role) -> None`

Render role responsibilities.

Args:
    role (Role): The Role object containing the responsibilities to render.

Returns:
    None

Notes:
    1. Extract shortcuts for the document and settings.
    2. If responsibilities are enabled in settings and the role has responsibilities, add a header for responsibilities.
    3. For each responsibility in the role, add a bullet point to the document.

---
## method: `RenderRolesSection.render_skills(self: UnknownType, role: Role) -> None`

Render role skills.

Args:
    role (Role): The Role object containing the skills to render.

Returns:
    None

Notes:
    1. Extract shortcuts for the document and settings.
    2. If skills are enabled in settings and the role has skills, add a header for skills.
    3. For each skill in the role, add a bullet point to the document.

---
## method: `RenderRolesSection.render_projects(self: UnknownType, role: Role) -> None`

Render role projects.

Args:
    role (Role): The Role object containing the projects to render.

Returns:
    None

Notes:
    1. Extract shortcuts for the document and settings.
    2. If projects are enabled in settings and the role has projects, add a header for projects.
    3. For each project in the role, add a bullet point to the document.

---
## method: `RenderRolesSection.render_role(self: UnknownType, role: Role) -> None`

Render a single role.

Args:
    role (Role): The Role object to render.

Returns:
    None

Notes:
    1. Extract shortcuts for the document and settings.
    2. Add a header for the role section.
    3. Render the role basics.
    4. If summary is enabled and the role has a non-empty summary, add a header and render the summary.
    5. If responsibilities are enabled and the role has a text field for responsibilities, add a header and render the text.
    6. If skills are enabled and the role has skills, add a header and render each skill with an asterisk bullet.

---
## method: `RenderRolesSection.render(self: UnknownType) -> None`

Render roles section.

Args:
    None

Returns:
    None

Notes:
    1. Extract shortcuts for the document and roles.
    2. If no roles are present, log a debug message and return.
    3. Log a debug message indicating that rendering is starting.
    4. Add a header for the roles section.
    5. For each role in the roles list, render the role.

---
## `RenderProjectsSection` class

Render experience projects section.

This class is responsible for rendering individual projects within the experience section of a resume.
It inherits from ResumeRenderProjectsBase, which provides base functionality for rendering project-related content.

Attributes:
    document (MarkdownDoc): The MarkdownDoc object to render the content into.
    projects (Projects): The list of Project objects to render.
    settings (ResumeProjectsSettings): The settings object controlling what fields to render.

---
## method: `RenderProjectsSection.__init__(self: UnknownType, document: MarkdownDoc, projects: Projects, settings: ResumeProjectsSettings) -> UnknownType`

Initialize projects render object.

Args:
    document (MarkdownDoc): The MarkdownDoc object to render the content into.
    projects (Projects): The list of Project objects to render.
    settings (ResumeProjectsSettings): The settings object controlling what fields to render.

Returns:
    None

Notes:
    1. Log a debug message indicating initialization.
    2. Validate that `document` is an instance of MarkdownDoc.
    3. Validate that `projects` is an instance of Projects.
    4. Validate that `settings` is an instance of ResumeProjectsSettings.
    5. Call the parent class constructor with the provided arguments.

---
## method: `RenderProjectsSection.render_project(self: UnknownType, project: Project) -> None`

Render a single project.

Args:
    project (Project): The Project object to render.

Returns:
    None

Notes:
    1. Extract shortcuts for the document and settings.
    2. Add a header for the project section.
    3. Add a header for the overview section.
    4. Render the project title if enabled in settings and present.
    5. Render the project URL if enabled in settings and present.
    6. Render the URL description if enabled in settings and present.
    7. Render the start date if enabled in settings and present.
    8. Render the end date if enabled in settings and present.
    9. If a description is enabled in settings and present, add a header and render the description.
    10. If skills are enabled in settings and present, add a header and render each skill with an asterisk bullet.

---
## method: `RenderProjectsSection.render(self: UnknownType) -> None`

Render projects section.

Args:
    None

Returns:
    None

Notes:
    1. Extract shortcuts for the document, settings, and projects.
    2. If no projects are present, log a debug message and return.
    3. Log a debug message indicating that rendering is starting.
    4. Add a header for the projects section.
    5. For each project in the projects list, render the project.

---
## `RenderExperienceSection` class

Render experience section.

This class is responsible for orchestrating the rendering of both roles and projects within the experience section of a resume.
It inherits from ResumeRenderExperienceBase, which provides base functionality for rendering experience-related content.

Attributes:
    document (MarkdownDoc): The MarkdownDoc object to render the content into.
    experience (Experience): The Experience object containing the data to render.
    settings (ResumeExperienceSettings): The settings object controlling what fields to render.

---
## method: `RenderExperienceSection.__init__(self: UnknownType, document: MarkdownDoc, experience: Experience, settings: ResumeExperienceSettings) -> None`

Initialize experience render object.

Args:
    document (MarkdownDoc): The MarkdownDoc object to render the content into.
    experience (Experience): The Experience object containing the data to render.
    settings (ResumeExperienceSettings): The settings object controlling what fields to render.

Returns:
    None

Notes:
    1. Log a debug message indicating initialization.
    2. Call the parent class constructor with the provided arguments.

---
## method: `RenderExperienceSection.render(self: UnknownType) -> None`

Render experience section.

Args:
    None

Returns:
    None

Notes:
    1. Log a debug message indicating that rendering is starting.
    2. Add a header for the experience section.
    3. If projects are enabled in settings and the experience has projects, render the projects section.
    4. If roles are enabled in settings and the experience has roles, render the roles section.

---

===

===
# File: `resume_writer/personal_data/regen.py`

## function: `run_command(command: list[str]) -> None`

Run a shell command.

---

## function: `resume_matrix() -> dict[dict[str, str]]`

Return a matrix of input resumes, settings files, output files.

---

## function: `go() -> None`

Run the main loop.

---


===

===
# File: `resume_writer/utils/html_doc.py`

## `HtmlDoc` class

HTML document.

Attributes:
    text (str): The HTML content of the document, accumulated through add_text calls.

---
## method: `HtmlDoc.__init__(self: UnknownType) -> UnknownType`

Initialize HTML document.

Notes:
    1. Initializes the text attribute to an empty string.

---
## method: `HtmlDoc.add_text(self: UnknownType, text: str) -> None`

Add text to HTML document.

Args:
    text (str): The text to append to the document. This text is added as-is to the HTML content.

Returns:
    None: This function does not return a value.

Notes:
    1. Concatenates the provided text to the existing document content.
    2. No disk, network, or database access occurs.

---

===

===
# File: `resume_writer/utils/resume_stats.py`

## `DateStats` class

Provide date-range related statistics.

Attributes:
    date_ranges (list[tuple[datetime, datetime]]): A list of date ranges
        represented as tuples of start and end datetimes.

---
## method: `DateStats.__init__(self: UnknownType) -> UnknownType`

Initialize the DateStats class.

Initializes an empty list to store date ranges.

---
## method: `DateStats.add_date_range(self: UnknownType, start_date: datetime, end_date: datetime | None) -> None`

Add a date range to the list of date ranges.

Args:
    start_date (datetime): The start date of the range.
    end_date (datetime | None): The end date of the range. If None,
        the current date is used.

Returns:
    None

Notes:
    1. Validate that start_date is not after end_date.
    2. If end_date is None, use the current date as end_date.
    3. Append the (start_date, end_date) tuple to the date_ranges list.

---
## method: `DateStats.merge_date_ranges(self: UnknownType) -> list[tuple[datetime, datetime]]`

Take a list of date ranges, and consolidate them.

This function merges overlapping or adjacent date ranges into a single
continuous range.

Returns:
    list[tuple[datetime, datetime]]: A list of merged date ranges,
        each represented as a tuple of start and end datetimes.

Notes:
    1. If no date ranges exist, return an empty list.
    2. Sort date ranges by start date.
    3. Initialize the first range as the current range.
    4. Iterate through the remaining ranges:
        a. If the current range overlaps with the next range (next start <= current end),
           extend the current end date to the maximum of the two.
        b. Otherwise, add the current range to the merged list and start a new range.
    5. Add the final current range to the merged list.
    6. Return the merged ranges.

---
## method: `DateStats.days_of_experience(self: UnknownType) -> int`

Return the total number of days across all merged date ranges.

Returns:
    int: The total number of days of experience.

Notes:
    1. Merge all date ranges using merge_date_ranges.
    2. Initialize a counter for total days.
    3. For each merged date range, add the number of days between start and end dates.
    4. Return the total.

---
## method: `DateStats.years_of_experience(self: UnknownType) -> float`

Return the number of years of experience.

Returns:
    float: The number of years of experience, rounded to one decimal place.

Notes:
    1. Compute the total days of experience.
    2. Divide by 365.25 to account for leap years.
    3. Round to one decimal place.

---
## method: `DateStats.span_of_experience(self: UnknownType) -> float`

Return the span of experience from first to last date.

Returns:
    float: The span of experience in years, rounded to one decimal place.

Notes:
    1. Merge all date ranges using merge_date_ranges.
    2. Get the first start date and the last end date from the merged ranges.
    3. Calculate the difference between last end and first start.
    4. Divide by 365.25 to get years.
    5. Round to one decimal place.

---

===

===
# File: `resume_writer/utils/__init__.py`


===

===
# File: `resume_writer/utils/markdown_doc.py`

## `MarkdownDoc` class

Represents a Markdown document used for generating and managing markdown content.

Attributes:
    text (str): The current content of the markdown document, accumulated as text is added.

---
## method: `MarkdownDoc.__init__(self: UnknownType) -> UnknownType`

Initialize an empty Markdown document.

Notes:
    1. Initializes the internal `text` attribute as an empty string.

---
## method: `MarkdownDoc.add_text(self: UnknownType, text: str) -> None`

Add formatted text to the Markdown document.

Args:
    text (str): The text to be added to the document. This may include markdown formatting such as headers.

Returns:
    None

Notes:
    1. Strips leading and trailing whitespace from the input text.
    2. If the text starts with a '#' (indicating a heading), adds a newline before and after the text to ensure proper formatting in the document.
    3. Appends the processed text to the document's internal `text` attribute.
    4. No disk, network, or database access is performed.

---

===

===
# File: `resume_writer/utils/date_format.py`

## function: `format_date(date: datetime | None) -> str`

Format date as MM/YYYY.

Args:
    date (datetime | None): The datetime object to format. If None, returns an empty string.

Returns:
    str: Formatted date string as MM/YYYY or empty string if date is None.

Notes:
    1. Check if the date is None. If so, return an empty string.
    2. If date is not None, use the strftime method to format the date as MM/YYYY.
    3. The formatted string is returned.

---


===

===
# File: `resume_writer/utils/skills_matrix.py`

## `SkillsMatrix` class

A matrix of skills, includes years and spans of experience.

Attributes:
    roles (Roles): A collection of Role objects representing the user's work experience.

Notes:
    1. The class processes skill data from roles to calculate experience metrics.
    2. It supports calculating total career experience, span of experience, and skill-specific metrics.
    3. The matrix can filter skills based on a provided list or include all skills if "*all*" is specified.
    4. The matrix includes years of experience and first/last usage dates for each skill.
    5. Results are sorted by years of experience in descending order.

---
## method: `SkillsMatrix.__init__(self: UnknownType, roles: Roles) -> UnknownType`

Initialize the matrix with a list of roles.

Args:
    roles (Roles): A collection of Role objects representing the user's work experience.

Raises:
    AssertionError: If roles is not an instance of Roles or if any role is not a Role instance.

---
## method: `SkillsMatrix.career_experience_total(self: UnknownType) -> float`

Return the total years of career experience across all roles.

Returns:
    float: The total years of experience calculated from all role date ranges.

Notes:
    1. Creates a DateStats instance to manage date ranges.
    2. Iterates through each role and adds its start and end dates to the date stats.
    3. Returns the total years of experience from the date stats.

---
## method: `SkillsMatrix.career_experience_span(self: UnknownType) -> float`

Return the span of career experience, from first to last role.

Returns:
    float: The span of years between the earliest start date and latest end date.

Notes:
    1. Creates a DateStats instance to manage date ranges.
    2. Iterates through each role and adds its start and end dates to the date stats.
    3. Returns the span of experience from the date stats.

---
## method: `SkillsMatrix.skills_list(self: UnknownType) -> list`

Return a list of unique skills from all roles.

Returns:
    list: A list of unique skill strings found across all roles.

Notes:
    1. Initializes an empty list to store unique skills.
    2. Iterates through each role and adds each skill to the list if not already present.
    3. Returns the list of unique skills.

---
## method: `SkillsMatrix.skill_experience(self: UnknownType, skill: str) -> float`

Return the total years of experience with a specific skill.

Args:
    skill (str): The name of the skill to evaluate.

Returns:
    float: The total years of experience with the skill across all roles.

Notes:
    1. Creates a DateStats instance to track date ranges for the skill.
    2. Iterates through each role and checks if the skill is present.
    3. If the skill is found, adds the role's date range to the date stats.
    4. Returns the total years of experience from the date stats.

---
## method: `SkillsMatrix.skills_experience(self: UnknownType) -> dict`

Return a dictionary mapping each skill to its years of experience.

Returns:
    dict: A dictionary where keys are skill names and values are float years of experience.

Notes:
    1. Retrieves the list of unique skills using skills_list.
    2. For each skill, calculates its years of experience using skill_experience.
    3. Filters out skills with zero experience.
    4. Returns the resulting dictionary with only non-zero experience entries.

---
## method: `SkillsMatrix.matrix(self: UnknownType, skills: list[str]) -> dict`

Return a dictionary of skills with years of experience and usage dates.

Args:
    skills (list[str]): List of skills to include. If "*all*" is provided, all skills are included.

Returns:
    dict: A dictionary where each key is a skill name and the value is a dict with:
        - "yoe" (float): Years of experience with the skill.
        - "first_used" (datetime | None): Earliest date the skill was used.
        - "last_used" (datetime | None): Latest date the skill was used.

Raises:
    AssertionError: If skills is not a list or if any element is not a string.

Notes:
    1. Validates input to ensure skills is a list of strings.
    2. Retrieves the full list of unique skills from the resume.
    3. If the skills list is ["*all*"], uses all skills; otherwise, filters to only those present.
    4. Removes empty strings and skills not found in the resume.
    5. Returns an empty dict if no valid skills are found.
    6. For each valid skill, retrieves years of experience and first/last usage dates.
    7. Constructs the result dictionary with skill data.
    8. Sorts the result by years of experience in descending order.
    9. No external I/O (network, disk, or database) is performed.

---
## method: `SkillsMatrix.find_skill_date_range(self: UnknownType, skill: str) -> tuple[datetime | None, datetime | None]`

Return the first and last usage dates for a specific skill.

Args:
    skill (str): The name of the skill to evaluate.

Returns:
    tuple[datetime | None, datetime | None]: A tuple containing:
        - The earliest start date the skill was used, or None if not used.
        - The latest end date the skill was used, or None if not used.

Notes:
    1. Initializes variables to track the earliest start and latest end dates.
    2. Collects all start dates from roles where the skill is present.
    3. Collects all end dates from roles where the skill is present.
    4. If any start dates exist, finds the earliest and latest end date.
    5. Returns the earliest and latest dates as a tuple.
    6. No external I/O (network, disk, or database) is performed.

---

===

===
# File: `resume_writer/utils/skills_splitter.py`

## function: `download_nltk_data() -> None`

Ensure the nltk data is present.

Notes:
    1. Checks if the 'punkt' NLTK data is installed.
    2. If not installed, downloads 'punkt' data.
    3. Checks if the 'punkt_tab' NLTK data is installed.
    4. If not installed, downloads 'punkt_tab' data.
    5. This function performs disk access to download required NLTK data.

---

## function: `normalize_sentence_fragment(fragment: str) -> str`

Normalize a sentence by removing extra spaces and punctuation.

Args:
    fragment: The input sentence fragment to normalize.

Returns:
    The normalized sentence fragment with consistent spacing and punctuation.

Notes:
    1. Strips leading and trailing whitespace from the fragment.
    2. Splits the fragment into words and rejoins with single spaces to remove extra spaces.
    3. Strips leading and trailing spaces again.
    4. Fixes spacing before punctuation marks by removing spaces before them.
    5. Fixes spacing after opening punctuation (e.g., '(', '[', '{') by removing spaces after them.

---

## function: `nltk_normalize_fragment(fragment: str) -> str`

Use a more advanced detokenizer to reassemble fragments.

Args:
    fragment: The input sentence fragment to normalize.

Returns:
    The normalized sentence fragment after detokenization and punctuation fixes.

Notes:
    1. Strips leading and trailing whitespace from the fragment.
    2. Uses nltk.sent_tokenize to split the fragment into sentences, taking the first.
    3. Fixes trailing punctuation by removing extra spaces before punctuation.
    4. Fixes punctuation spacing after opening pairs (e.g., '(', '[', '{').
    5. This function performs network access if NLTK data is not present, via nltk.download.

---

## function: `skills_splitter(sentence: str, skills: list[str]) -> list[str]`

Split a sentence into parts based on a list of skills.

This function identifies skills within a sentence and separates them into distinct parts,
allowing for individual highlighting or processing of each skill.

Args:
    sentence: The input sentence to be split.
    skills: A list of skill strings to search for in the sentence. Skills with more words
            should be listed first for accurate matching.

Returns:
    A list of strings where each element is either a skill or a fragment of text between skills.

Notes:
    1. Ensures required NLTK data ('punkt', 'punkt_tab') are downloaded if missing.
    2. Tokenizes the input sentence into individual words and punctuation.
    3. Sorts the skills by length in descending order to prioritize longer, more specific skills.
    4. Iterates through each token in the sentence, checking for matches with any skill.
    5. When a skill is found, adds the current fragment (if any) and the skill to the result.
    6. Skips over tokens that are part of the matched skill.
    7. Continues until all tokens are processed.
    8. Adds any remaining fragment to the result.
    9. Normalizes each part of the result using nltk_normalize_fragment.
    10. Returns the final list of normalized fragments and skills.
    11. This function performs disk access if NLTK data is not present.

---


===

===
# File: `resume_writer/utils/text_doc.py`

## `TextDoc` class

Base class for text documents.

This abstract base class provides a common interface for different types of text documents.
It defines the contract for adding text to a document through the `add_text` method.

Attributes:
    None

---
## method: `TextDoc.add_text(self: UnknownType, text: str) -> None`

Provide abstract method for `add_text` interface.

This method is intended to be implemented by subclasses to add text to the document.

Args:
    text: The text to be added to the document.
    **kwargs: Additional keyword arguments that may be used by subclasses to customize behavior.

Returns:
    None: This method does not return any value.

Notes:
    1. This method is abstract and must be implemented by subclasses.

---
## `MarkdownDoc` class

Markdown document.

This class represents a document that follows Markdown formatting rules.
It supports adding text and headers while managing line breaks and formatting.

Attributes:
    text (str): The current content of the document as a string.
    previous_line_was_header (bool): Flag indicating whether the previous line was a header.
    first_line (bool): Flag indicating whether this is the first line being added to the document.

---
## method: `MarkdownDoc.__init__(self: UnknownType) -> UnknownType`

Initialize Markdown document.

Initializes the text content to an empty string and sets flags to track the document state.

---
## method: `MarkdownDoc.add_text(self: UnknownType, text: str, line_breaks: Literal['preserve', 'strip']) -> None`

Add text to a Markdown document.

        Processes the input text and appends it to the document with appropriate formatting.
        Handles line breaks based on the specified mode.

        Args:
            text: The text to be added to the document.
            line_breaks: Controls how line breaks in the input text are handled.
                - "preserve": Retains all line breaks as-is.
                - "strip": Removes blank lines and collapses multiple line breaks.

        Returns:
            None: This method modifies the internal state of the object.

        Notes:
            1. The input text is split into lines using `
`.
            2. Each line is stripped of newline characters.
            3. If `line_breaks` is "strip" and the line is empty, it is skipped.
            4. The processed line is appended with a newline.
            5. If the previous line was a header, a blank line is added before the new text.
            6. The `previous_line_was_header` flag is updated after processing.
            7. The `first_line` flag is updated to False after the first addition.
            8. The processed text is appended to the document's `text` attribute.
        

---
## method: `MarkdownDoc.add_header(self: UnknownType, header: str) -> None`

Add a markdown header.

Adds a header line to the document. Ensures proper spacing before the header if needed.

Args:
    header: The text to be used as the header.

Returns:
    None: This method modifies the internal state of the object.

Notes:
    1. If this is not the first line, a blank line is added before the header.
    2. The header is added to the document with a newline.
    3. The `previous_line_was_header` flag is set to True.
    4. The `first_line` flag is updated to False.

---
## `HtmlDoc` class

HTML document.

This class represents an HTML document that supports adding raw HTML text.
It does not perform any parsing or formatting; it appends text as-is.

Attributes:
    text (str): The current content of the HTML document as a string.

---
## method: `HtmlDoc.__init__(self: UnknownType) -> UnknownType`

Initialize HTML document.

Initializes the text content to an empty string.

---
## method: `HtmlDoc.add_text(self: UnknownType, text: str) -> None`

Add text to the HTML document.

Appends the provided text to the existing content of the HTML document.

Args:
    text: The text to be added to the HTML document.

Returns:
    None: This method modifies the internal state of the object by appending the input text.

Notes:
    1. The input text is appended directly to the document's `text` attribute.
    2. No formatting, validation, or transformation is applied to the input.
    3. This method performs no disk, network, or database access.

---

===

===
# File: `resume_writer/utils/executive_summary.py`

## `ExecutiveSummary` class

Collect and return job summaries for given categories.

Attributes:
    experience (Experience): The experience data to summarize, must be an instance of the Experience class.

Args:
    experience (Experience): The experience data to summarize.

---
## method: `ExecutiveSummary.__init__(self: UnknownType, experience: Experience) -> UnknownType`

Initialize the ExecutiveSummary class.

Args:
    experience (Experience): The experience data to summarize.

Notes:
    1. Validates that the provided experience is an instance of the Experience class.
    2. If not, raises an AssertionError with a descriptive message.
    3. Stores the experience instance as an instance variable.

---
## method: `ExecutiveSummary.summary(self: UnknownType, categories: list[str]) -> dict[str, dict]`

Create a dictionary of roles and their summaries.

Args:
    categories (list[str]): A list of job categories to generate summaries for.

Returns:
    dict[str, dict]: A dictionary where keys are category names and values are lists of summary dictionaries.
    Each summary dictionary contains:
        - "summary" (str): The role summary text.
        - "company" (str): The company name.
        - "first_date" (str): The start date of the role.
        - "last_date" (str): The end date of the role.
        - "title" (str): The job title.

Notes:
    1. Initializes an empty dictionary to hold summaries by category.
    2. Iterates over each provided category.
    3. Filters roles belonging to the current category from the experience data.
    4. Skips categories with no matching roles and logs a warning.
    5. For each role in the category:
        a. Checks if a summary exists; if not, logs a warning and skips.
        b. Constructs a summary dictionary with relevant role details.
        c. Appends the dictionary to a list for the category.
    6. Adds the list of summaries to the result dictionary under the category key.
    7. Returns the final dictionary.

---
## method: `ExecutiveSummary.available_categories(self: UnknownType) -> list[str]`

Return a list of role categories.

Returns:
    list[str]: A list of unique job categories found in the experience data.

Notes:
    1. Extracts the job category from each role in the experience data.
    2. Converts the list of categories to a set to remove duplicates.
    3. Converts the set back to a list.
    4. Returns the list of unique categories.

---

===

===
# File: `resume_writer/models/resume.py`

## `Resume` class

Represents a resume.

This class models a resume document, organizing personal information, education, work experience, and certifications.
It uses a parsing framework to extract structured data from a text-based resume input.

Attributes:
    personal (Personal | None): Personal information such as name, contact details, and summary.
    education (Education | None): Educational background, including degrees and institutions.
    experience (Experience | None): Work history, including job titles, companies, and responsibilities.
    certifications (Certifications | None): Professional certifications held by the individual.
    parse_context (ParseContext): Contextual information used during parsing of the resume.

---
## method: `Resume.__init__(self: UnknownType, parse_context: ParseContext, personal: Personal | None, education: Education | None, experience: Experience | None, certifications: Certifications | None) -> UnknownType`

Initialize a Resume instance.

Args:
    parse_context (ParseContext): The parsing context containing the input lines and line numbers.
    personal (Personal | None): Parsed personal information, or None if not present.
    education (Education | None): Parsed education details, or None if not present.
    experience (Experience | None): Parsed work experience, or None if not present.
    certifications (Certifications | None): Parsed certifications, or None if not present.

Returns:
    None: This method initializes the instance and does not return a value.

Notes:
    1. Validate that parse_context is an instance of ParseContext.
    2. Validate that personal is either an instance of Personal or None.
    3. Validate that education is either an instance of Education or None.
    4. Validate that experience is either an instance of Experience or None.
    5. Validate that certifications is either an instance of Certifications or None.
    6. Assign the provided arguments to instance attributes.
    7. No disk, network, or database access occurs during initialization.

---
## method: `Resume.expected_blocks() -> dict[str, str]`

Return the expected block names and their corresponding constructor arguments.

Args:
    None: This method takes no arguments.

Returns:
    dict[str, str]: A dictionary mapping block names (e.g., "personal") to their constructor argument names (e.g., "personal").
    The keys are strings representing block types, and the values are identical strings matching the constructor parameter names.

Notes:
    1. Return a dictionary with keys "personal", "education", "experience", and "certifications".
    2. Each key maps to the same string value (e.g., "personal" → "personal").
    3. This method is used by the parsing framework to determine how to process each block.
    4. No disk, network, or database access occurs.

---
## method: `Resume.block_classes() -> dict[str, type]`

Return the class types for each expected block.

Args:
    None: This method takes no arguments.

Returns:
    dict[str, type]: A dictionary mapping block names (strings) to their corresponding class types.
    The keys are block names such as "personal", and the values are the corresponding class types (e.g., Personal).

Notes:
    1. Return a dictionary with keys "personal", "education", "experience", "certifications".
    2. Each key maps to the corresponding class (Personal, Education, Experience, Certifications).
    3. This method is used by the parsing framework to instantiate each block during parsing.
    4. No disk, network, or database access occurs.

---

===

===
# File: `resume_writer/models/experience.py`

## `RoleSummary` class

Represents a brief description of a professional role.

Attributes:
    summary (str): The text content of the role summary.
    parse_context (ParseContext): The context object used for parsing.

---
## method: `RoleSummary.__init__(self: UnknownType, text_string: str, parse_context: ParseContext) -> UnknownType`

Initialize the object.

Args:
    text_string (str): The text content of the role summary.
    parse_context (ParseContext): The context object used for parsing.

Returns:
    None

Notes:
    1. Validate that text_string is a string.
    2. Validate that parse_context is a ParseContext object.
    3. Store the text_string as the summary and parse_context as the context.

---
## `RoleResponsibilities` class

Represents detailed descriptions of role responsibilities.

Attributes:
    text (str): The text content of the responsibilities.
    parse_context (ParseContext): The context object used for parsing.

---
## method: `RoleResponsibilities.__init__(self: UnknownType, text_string: str, parse_context: ParseContext) -> UnknownType`

Initialize the object.

Args:
    text_string (str): The text content of the responsibilities.
    parse_context (ParseContext): The context object used for parsing.

Returns:
    None

Notes:
    1. Validate that parse_context is a ParseContext object.
    2. Validate that text_string is a string.
    3. Raise a ParseError if text_string is not a string.
    4. Store the text_string as the text and parse_context as the context.

---
## `RoleSkills` class

Represents skills used in a professional role.

Attributes:
    skills (List[str]): A list of non-empty, stripped skill strings.
    parse_context (ParseContext): The context object used for parsing.

---
## method: `RoleSkills.__init__(self: UnknownType, skills: list[str], parse_context: ParseContext) -> None`

Initialize the object.

Args:
    skills (List[str]): A list of skill strings.
    parse_context (ParseContext): The context object used for parsing.

Returns:
    None

Notes:
    1. Validate that parse_context is a ParseContext object.
    2. Validate that skills is a list.
    3. Validate that all items in skills are strings.
    4. Strip whitespace from each skill and filter out empty strings.
    5. Store the cleaned list of skills and parse_context.

---
## method: `RoleSkills.__iter__(self: UnknownType) -> UnknownType`

Iterate over the skills.

Returns:
    Iterator over the skills list.

---
## method: `RoleSkills.__len__(self: UnknownType) -> UnknownType`

Return the number of skills.

Returns:
    int: The number of skills.

---
## method: `RoleSkills.__getitem__(self: UnknownType, index: int) -> UnknownType`

Return the skill at the given index.

Args:
    index (int): The index of the skill to return.

Returns:
    str: The skill at the specified index.

---
## `RoleBasics` class

Represents basic information about a professional role.

Attributes:
    company (str): The name of the company.
    start_date (datetime): The start date of the role.
    end_date (datetime | None): The end date of the role or None if still ongoing.
    title (str): The job title.
    reason_for_change (str | None): The reason for leaving the role or None.
    location (str | None): The job location or None.
    job_category (str | None): The category of the job or None.
    employment_type (str | None): The employment type or None.
    agency_name (str | None): The name of the agency or None.
    parse_context (ParseContext): The context object used for parsing.

---
## method: `RoleBasics.__init__(self: UnknownType, parse_context: ParseContext, company: str, start_date: str | datetime, end_date: str | datetime | None, reason_for_change: str | None, title: str, location: str | None, job_category: str | None, employment_type: str | None, agency_name: str | None) -> UnknownType`

Initialize the object.

Args:
    parse_context (ParseContext): The context object used for parsing.
    company (str): The name of the company.
    start_date (str | datetime): The start date of the role as a string or datetime object.
    end_date (str | datetime | None): The end date of the role as a string, datetime object, or None.
    reason_for_change (str | None): The reason for leaving the role as a string or None.
    title (str): The job title.
    location (str | None, optional): The job location as a string or None.
    job_category (str | None, optional): The category of the job as a string or None.
    employment_type (str | None, optional): The employment type as a string or None.
    agency_name (str | None, optional): The name of the agency as a string or None.

Returns:
    None

Notes:
    1. Validate that parse_context is a ParseContext object.
    2. Validate that company and title are strings.
    3. Validate that start_date is either a string or datetime.
    4. Validate that end_date is a string, datetime, or None.
    5. Validate that all other fields are appropriate types.
    6. Parse start_date and end_date using dateparser with UTC timezone.
    7. Store all fields as instance attributes.

---
## method: `RoleBasics.expected_fields() -> dict[str, str]`

Return the expected fields for this object.

Returns:
    A dictionary mapping label names to constructor argument names.

---
## `Role` class

Represents a complete professional role with all associated details.

Attributes:
    basics (RoleBasics | None): The RoleBasics object containing role metadata.
    summary (RoleSummary | None): The RoleSummary object describing the role.
    responsibilities (RoleResponsibilities | None): The RoleResponsibilities object listing duties.
    skills (RoleSkills | None): The RoleSkills object listing skills used.
    parse_context (ParseContext): The context object used for parsing.

---
## method: `Role.__init__(self: UnknownType, parse_context: ParseContext, basics: RoleBasics | None, summary: RoleSummary | None, responsibilities: RoleResponsibilities | None, skills: RoleSkills | None) -> UnknownType`

Initialize the object.

Args:
    parse_context (ParseContext): The context object used for parsing.
    basics (RoleBasics | None): The RoleBasics object containing role metadata.
    summary (RoleSummary | None): The RoleSummary object describing the role.
    responsibilities (RoleResponsibilities | None): The RoleResponsibilities object listing duties.
    skills (RoleSkills | None): The RoleSkills object listing skills used.

Returns:
    None

Notes:
    1. Validate that parse_context is a ParseContext object.
    2. Validate that basics is either a RoleBasics object or None.
    3. Validate that summary is either a RoleSummary object or None.
    4. Validate that responsibilities is either a RoleResponsibilities object or None.
    5. Validate that skills is either a RoleSkills object or None.
    6. Store the provided components as instance attributes.

---
## method: `Role.expected_blocks() -> dict[str, str]`

Return the expected blocks for this object.

Returns:
    A dictionary mapping block names to constructor argument names.

---
## method: `Role.block_classes() -> dict[str, type]`

Return the classes for the blocks.

Returns:
    A dictionary mapping block names to their corresponding classes.

---
## `Roles` class

Represents a collection of professional roles.

Attributes:
    roles (List[Role]): A list of Role objects.
    parse_context (ParseContext): The context object used for parsing.

---
## method: `Roles.__init__(self: UnknownType, roles: list[Role], parse_context: ParseContext) -> UnknownType`

Initialize the object.

Args:
    roles (List[Role]): A list of Role objects.
    parse_context (ParseContext): The context object used for parsing.

Returns:
    None

Notes:
    1. Validate that roles is a list.
    2. Validate that all items in roles are Role objects.
    3. Validate that parse_context is a ParseContext object.
    4. Store the roles list and parse_context.

---
## method: `Roles.__iter__(self: UnknownType) -> UnknownType`

Iterate over the roles.

Returns:
    Iterator over the roles list.

---
## method: `Roles.__len__(self: UnknownType) -> UnknownType`

Return the number of roles.

Returns:
    int: The number of roles.

---
## method: `Roles.__getitem__(self: UnknownType, index: int) -> UnknownType`

Return the role at the given index.

Args:
    index (int): The index of the role to return.

Returns:
    Role: The role at the specified index.

---
## method: `Roles.list_class() -> type`

Return the class for the list.

Returns:
    The Role class.

---
## `ProjectSkills` class

Represents skills used in a project.

Attributes:
    skills (List[str]): A list of non-empty, stripped skill strings.
    parse_context (ParseContext): The context object used for parsing.

---
## method: `ProjectSkills.__init__(self: UnknownType, skills: list[str], parse_context: ParseContext) -> UnknownType`

Initialize the object.

Args:
    skills (List[str]): A list of skill strings.
    parse_context (ParseContext): The context object used for parsing.

Returns:
    None

Notes:
    1. Validate that skills is a list.
    2. Validate that all items in skills are strings.
    3. Validate that parse_context is a ParseContext object.
    4. Strip whitespace from each skill and filter out empty strings.
    5. Store the cleaned list of skills.

---
## method: `ProjectSkills.__iter__(self: UnknownType) -> UnknownType`

Iterate over the skills.

Returns:
    Iterator over the skills list.

---
## method: `ProjectSkills.__len__(self: UnknownType) -> UnknownType`

Return the number of skills.

Returns:
    int: The number of skills.

---
## method: `ProjectSkills.__getitem__(self: UnknownType, index: int) -> UnknownType`

Return the skill at the given index.

Args:
    index (int): The index of the skill to return.

Returns:
    str: The skill at the specified index.

---
## `ProjectOverview` class

Represents basic details of a project.

Attributes:
    title (str): The title of the project.
    url (str | None): The URL for the project or None.
    url_description (str | None): A description of the URL or None.
    start_date (datetime | None): The start date as a datetime object or None.
    end_date (datetime | None): The end date as a datetime object or None.
    parse_context (ParseContext): The context object used for parsing.

---
## method: `ProjectOverview.__init__(self: UnknownType, title: str, parse_context: ParseContext, url: str | None, url_description: str | None, start_date: str | datetime | None, end_date: str | datetime | None) -> UnknownType`

Initialize ProjectOverview object.

Args:
    title (str): The title of the project.
    parse_context (ParseContext): The context object used for parsing.
    url (str | None, optional): The URL for the project as a string or None.
    url_description (str | None, optional): A description of the URL as a string or None.
    start_date (str | datetime | None, optional): The start date as a string, datetime, or None.
    end_date (str | datetime | None, optional): The end date as a string, datetime, or None.

Returns:
    None

Notes:
    1. Validate that title is a string.
    2. Validate that url and url_description are strings or None.
    3. Validate that start_date and end_date are strings, datetimes, or None.
    4. Validate that parse_context is a ParseContext object.
    5. Parse start_date and end_date using dateparser with UTC timezone.
    6. Store all fields as instance attributes.

---
## method: `ProjectOverview.expected_fields() -> dict[str, str]`

Return the expected fields for this object.

Returns:
    A dictionary mapping label names to constructor argument names.

---
## `ProjectDescription` class

Represents a brief description of a project.

Attributes:
    text (str): The text content of the project description.
    parse_context (ParseContext): The context object used for parsing.

---
## method: `ProjectDescription.__init__(self: UnknownType, text_string: str, parse_context: ParseContext) -> UnknownType`

Initialize the object.

Args:
    text_string (str): The text content of the project description.
    parse_context (ParseContext): The context object used for parsing.

Returns:
    None

Notes:
    1. Validate that text_string is a string.
    2. Validate that parse_context is a ParseContext object.
    3. Store the text_string as the text.

---
## `Project` class

Represents a complete project with all associated details.

Attributes:
    overview (ProjectOverview): The ProjectOverview object containing project metadata.
    description (ProjectDescription): The ProjectDescription object describing the project.
    skills (ProjectSkills | None): The ProjectSkills object listing skills used.
    parse_context (ParseContext): The context object used for parsing.

---
## method: `Project.__init__(self: UnknownType, overview: ProjectOverview, description: ProjectDescription, skills: ProjectSkills | None, parse_context: ParseContext) -> UnknownType`

Initialize the object.

Args:
    overview (ProjectOverview): The ProjectOverview object containing project metadata.
    description (ProjectDescription): The ProjectDescription object describing the project.
    skills (ProjectSkills | None): The ProjectSkills object listing skills used.
    parse_context (ParseContext): The context object used for parsing.

Returns:
    None

Notes:
    1. Validate that overview is a ProjectOverview object.
    2. Validate that description is a ProjectDescription object.
    3. Validate that skills is a ProjectSkills object or None.
    4. Validate that parse_context is a ParseContext object.
    5. Store all components as instance attributes.

---
## method: `Project.expected_blocks() -> dict[str, str]`

Return the expected blocks for this object.

Returns:
    A dictionary mapping block names to constructor argument names.

---
## method: `Project.block_classes() -> dict[str, type]`

Return the classes for the blocks.

Returns:
    A dictionary mapping block names to their corresponding classes.

---
## `Projects` class

Represents a collection of projects.

Attributes:
    projects (List[Project]): A list of Project objects.
    parse_context (ParseContext): The context object used for parsing.

---
## method: `Projects.__init__(self: UnknownType, projects: list[Project], parse_context: ParseContext) -> UnknownType`

Initialize the object.

Args:
    projects (List[Project]): A list of Project objects.
    parse_context (ParseContext): The context object used for parsing.

Returns:
    None

Notes:
    1. Validate that projects is a list.
    2. Validate that all items in projects are Project objects.
    3. Validate that parse_context is a ParseContext object.
    4. Store the projects list.

---
## method: `Projects.__iter__(self: UnknownType) -> UnknownType`

Iterate over the projects.

Returns:
    Iterator over the projects list.

---
## method: `Projects.__len__(self: UnknownType) -> UnknownType`

Return the number of projects.

Returns:
    int: The number of projects.

---
## method: `Projects.__getitem__(self: UnknownType, index: int) -> UnknownType`

Return the project at the given index.

Args:
    index (int): The index of the project to return.

Returns:
    Project: The project at the specified index.

---
## method: `Projects.list_class() -> type`

Return the class of the list.

Returns:
    The Project class.

---
## `Experience` class

Represents a collection of professional experience including roles and projects.

Attributes:
    roles (Roles | None): A Roles object containing work experience.
    projects (Projects | None): A Projects object containing project details.
    parse_context (ParseContext): The context object used for parsing.

---
## method: `Experience.__init__(self: UnknownType, roles: Roles | None, projects: Projects | None, parse_context: ParseContext) -> UnknownType`

Initialize with a list of Role objects.

Args:
    roles (Roles | None): A Roles object containing work experience.
    projects (Projects | None): A Projects object containing project details.
    parse_context (ParseContext): The context object used for parsing.

Returns:
    None

Notes:
    1. Validate that roles is a Roles object or None.
    2. Validate that projects is a Projects object or None.
    3. Validate that parse_context is a ParseContext object.
    4. Log the creation of an Experience object.
    5. Store the roles and projects as instance attributes.

---
## method: `Experience.expected_blocks() -> dict[str, str]`

Return the expected blocks for this object.

Returns:
    A dictionary mapping block names to constructor argument names.

---
## method: `Experience.block_classes() -> dict[str, type]`

Return the classes for the blocks.

Returns:
    A dictionary mapping block names to their corresponding classes.

---

===

===
# File: `resume_writer/models/certifications.py`

## `Certification` class

Represents a professional certification.

Base class:
    LabelBlockParse

Attributes:
    name (str): The name of the certification.
    issuer (str | None): The organization that issued the certification.
    issued (datetime | None): The date the certification was issued.
    expires (datetime | None): The date the certification expires.
    certification_id (str | None): An identifier for the certification.
    parse_context (ParseContext): The context used during parsing, tracking line information.

---
## method: `Certification.__init__(self: UnknownType, name: str, issuer: str | None, issued: datetime | str | None, expires: datetime | str | None, certification_id: str | None, parse_context: ParseContext) -> UnknownType`

Initialize a Certification object.

Args:
    name: The name of the certification.
    issuer: The organization that issued the certification. Can be None.
    issued: The date the certification was issued. Can be a datetime object or a string.
    expires: The date the certification expires. Can be a datetime object or a string.
    certification_id: An identifier for the certification. Can be None.
    parse_context: The context used during parsing, tracking line information.

Returns:
    None

Notes:
    1. Validate that all inputs are of the correct type.
    2. If `issued` is a string, parse it into a datetime object using dateparser with PREFER_DAY_OF_MONTH set to "first".
    3. If `expires` is a string, parse it into a datetime object using dateparser with PREFER_DAY_OF_MONTH set to "first".
    4. Assign the parsed or original values to instance attributes.

---
## method: `Certification.expected_fields() -> dict[str, str]`

Return the expected fields for this object.

Args:
    None

Returns:
    A dictionary mapping field names (as strings) to their corresponding constructor argument names.

Notes:
    1. The keys are field names as they appear in the input, and the values are the argument names used in the constructor.
    2. The field "certification id" maps to "certification_id" in the constructor.

---
## `Certifications` class

Represents a collection of professional certifications.

Base class:
    MultiBlockParse

Attributes:
    certifications (list[Certification]): A list of Certification objects.
    parse_context (ParseContext): The context used during parsing, tracking line information.

---
## method: `Certifications.__init__(self: UnknownType, certifications: list[Certification], parse_context: ParseContext) -> UnknownType`

Initialize a Certifications object.

Args:
    certifications: A list of Certification objects.
    parse_context: The context used during parsing, tracking line information.

Returns:
    None

Notes:
    1. Assign the provided list of certifications to the instance attribute `certifications`.
    2. Assign the provided parse_context to the instance attribute `parse_context`.

---
## method: `Certifications.__iter__(self: UnknownType) -> UnknownType`

Iterate over the certifications.

Args:
    None

Returns:
    An iterator over the list of certification objects.

Notes:
    1. Return an iterator over the `certifications` list.

---
## method: `Certifications.__len__(self: UnknownType) -> UnknownType`

Return the number of certifications.

Args:
    None

Returns:
    The integer count of certifications in the list.

Notes:
    1. Return the length of the `certifications` list.

---
## method: `Certifications.list_class() -> type`

Return the type that will be contained in the list.

Args:
    None

Returns:
    The Certification class.

Notes:
    1. Return the Certification class, which is the type of objects in the list.

---

===

===
# File: `resume_writer/models/personal.py`

## `ContactInfo` class

Holds personal contact details such as name, email, phone, and location.

Attributes:
    name (str): The full name of the person.
    email (str | None): The email address of the person, or None if not provided.
    phone (str | None): The phone number of the person, or None if not provided.
    location (str | None): The physical location (e.g., city and country) of the person, or None if not provided.
    parse_context (ParseContext): The context used during parsing, containing metadata about the input.

---
## method: `ContactInfo.__init__(self: UnknownType, parse_context: ParseContext, name: str, email: str | None, phone: str | None, location: str | None) -> UnknownType`

Initialize the contact information with provided details.

Args:
    parse_context (ParseContext): The context used during parsing, containing metadata about the input.
    name (str): The full name of the person.
    email (str | None): The email address of the person, or None if not provided.
    phone (str | None): The phone number of the person, or None if not provided.
    location (str | None): The physical location (e.g., city and country) of the person, or None if not provided.

Returns:
    None

Notes:
    1. Validate that parse_context is an instance of ParseContext.
    2. Validate that name is a string.
    3. Validate that email is either a string or None.
    4. Validate that phone is either a string or None.
    5. Validate that location is either a string or None.
    6. Assign the provided values to instance attributes.

---
## method: `ContactInfo.expected_fields() -> dict[str, str]`

Return the expected labels for contact information fields.

Args:
    None

Returns:
    A dictionary mapping label names (e.g., "name", "email") to their corresponding attribute names in the ContactInfo class.

Notes:
    1. The returned dictionary defines the expected field names in the input data for ContactInfo.
    2. The keys are the labels found in the input (e.g., "name", "email"), and the values are the corresponding attribute names in the class (e.g., "name").

---
## `Websites` class

Holds personal website and social media links.

Attributes:
    website (str | None): The personal website URL, or None if not provided.
    github (str | None): The GitHub profile URL, or None if not provided.
    linkedin (str | None): The LinkedIn profile URL, or None if not provided.
    twitter (str | None): The Twitter profile URL, or None if not provided.
    parse_context (ParseContext): The context used during parsing, containing metadata about the input.

---
## method: `Websites.__init__(self: UnknownType, parse_context: ParseContext, website: str | None, github: str | None, linkedin: str | None, twitter: str | None) -> UnknownType`

Initialize the websites information with provided links.

Args:
    parse_context (ParseContext): The context used during parsing, containing metadata about the input.
    website (str | None): The personal website URL, or None if not provided.
    github (str | None): The GitHub profile URL, or None if not provided.
    linkedin (str | None): The LinkedIn profile URL, or None if not provided.
    twitter (str | None): The Twitter profile URL, or None if not provided.

Returns:
    None

Notes:
    1. Validate that parse_context is an instance of ParseContext.
    2. Validate that website is either a string or None.
    3. Validate that github is either a string or None.
    4. Validate that linkedin is either a string or None.
    5. Validate that twitter is either a string or None.
    6. Assign the provided values to instance attributes.

---
## method: `Websites.expected_fields() -> dict[str, str]`

Return the expected labels for website and social media fields.

Args:
    None

Returns:
    A dictionary mapping label names (e.g., "website", "github") to their corresponding attribute names in the Websites class.

Notes:
    1. The returned dictionary defines the expected field names in the input data for Websites.
    2. The keys are the labels found in the input (e.g., "website", "github"), and the values are the corresponding attribute names in the class (e.g., "website").

---
## `VisaStatus` class

Holds information about work authorization and sponsorship requirements.

Attributes:
    work_authorization (str | None): The current work authorization status (e.g., "US Citizen", "H-1B"), or None if not provided.
    require_sponsorship (bool | None): A boolean indicating if sponsorship is required, or None if not provided.
    parse_context (ParseContext): The context used during parsing, containing metadata about the input.

---
## method: `VisaStatus.__init__(self: UnknownType, parse_context: ParseContext, work_authorization: str | None, require_sponsorship: bool | str | None) -> UnknownType`

Initialize the visa status with provided authorization and sponsorship details.

Args:
    parse_context (ParseContext): The context used during parsing, containing metadata about the input.
    work_authorization (str | None): The current work authorization status (e.g., "US Citizen", "H-1B"), or None if not provided.
    require_sponsorship (bool | str | None): A boolean indicating if sponsorship is required, or a string ("yes"/"no") that will be converted to a boolean, or None if not provided.

Returns:
    None

Notes:
    1. Validate that parse_context is an instance of ParseContext.
    2. Validate that work_authorization is either a string or None.
    3. Validate that require_sponsorship is a boolean, string ("yes"/"no"), or None.
    4. Assign the provided work_authorization value to the instance attribute.
    5. If require_sponsorship is a string, convert "yes" to True and "no" to False.
    6. If require_sponsorship is not None and not a string, assign it directly.
    7. Otherwise, set require_sponsorship to None.

---
## method: `VisaStatus.expected_fields() -> dict[str, str]`

Return the expected labels for visa and sponsorship fields.

Args:
    None

Returns:
    A dictionary mapping label names (e.g., "work authorization", "require sponsorship") to their corresponding attribute names in the VisaStatus class.

Notes:
    1. The returned dictionary defines the expected field names in the input data for VisaStatus.
    2. The keys are the labels found in the input (e.g., "work authorization", "require sponsorship"), and the values are the corresponding attribute names in the class (e.g., "work_authorization").

---
## `Banner` class

Holds a personal banner message with cleaned text content.

Attributes:
    text (str): The cleaned text content of the banner, with leading/trailing and internal blank lines removed.
    parse_context (ParseContext): The context used during parsing, containing metadata about the input.

---
## method: `Banner.__init__(self: UnknownType, parse_context: ParseContext, text_string: str) -> UnknownType`

Initialize the banner with cleaned text content.

Args:
    parse_context (ParseContext): The context used during parsing, containing metadata about the input.
    text_string (str): The raw text content of the banner, potentially including leading/trailing or internal blank lines.

Returns:
    None

Notes:
    1. Validate that parse_context is an instance of ParseContext.
    2. Validate that text_string is a string.
    3. Split the input text_string into lines.
    4. Remove leading blank lines.
    5. Remove trailing blank lines.
    6. Filter out any lines that are blank after stripping whitespace.
    7. Join the remaining lines back into a single string and assign to self.text.

---
## `Note` class

Holds a personal note with cleaned text content.

Attributes:
    text (str): The cleaned text content of the note, with leading/trailing and internal blank lines removed.
    parse_context (ParseContext): The context used during parsing, containing metadata about the input.

---
## method: `Note.__init__(self: UnknownType, parse_context: ParseContext, text_string: str) -> UnknownType`

Initialize the note with cleaned text content.

Args:
    parse_context (ParseContext): The context used during parsing, containing metadata about the input.
    text_string (str): The raw text content of the note, potentially including leading/trailing or internal blank lines.

Returns:
    None

Notes:
    1. Validate that parse_context is an instance of ParseContext.
    2. Validate that text_string is a string.
    3. Split the input text_string into lines.
    4. Remove leading blank lines.
    5. Remove trailing blank lines.
    6. Filter out any lines that are blank after stripping whitespace.
    7. Join the remaining lines back into a single string and assign to self.text.

---
## `Personal` class

Holds all personal information including contact details, websites, visa status, banner, and note.

Attributes:
    contact_info (ContactInfo | None): An instance of ContactInfo containing personal contact details, or None if not provided.
    websites (Websites | None): An instance of Websites containing personal website links, or None if not provided.
    visa_status (VisaStatus | None): An instance of VisaStatus containing visa and sponsorship information, or None if not provided.
    banner (Banner | None): An instance of Banner containing a personal banner message, or None if not provided.
    note (Note | None): An instance of Note containing a personal note, or None if not provided.
    parse_context (ParseContext): The context used during parsing, containing metadata about the input.

---
## method: `Personal.__init__(self: UnknownType, parse_context: ParseContext, contact_info: ContactInfo | None, websites: Websites | None, visa_status: VisaStatus | None, banner: Banner | None, note: Note | None) -> UnknownType`

Initialize the personal information block with provided components.

Args:
    parse_context (ParseContext): The context used during parsing, containing metadata about the input.
    contact_info (ContactInfo | None): An instance of ContactInfo containing personal contact details, or None if not provided.
    websites (Websites | None): An instance of Websites containing personal website links, or None if not provided.
    visa_status (VisaStatus | None): An instance of VisaStatus containing visa and sponsorship information, or None if not provided.
    banner (Banner | None): An instance of Banner containing a personal banner message, or None if not provided.
    note (Note | None): An instance of Note containing a personal note, or None if not provided.

Returns:
    None

Notes:
    1. Validate that parse_context is an instance of ParseContext.
    2. Validate that contact_info is either a ContactInfo instance or None.
    3. Validate that websites is either a Websites instance or None.
    4. Validate that visa_status is either a VisaStatus instance or None.
    5. Validate that banner is either a Banner instance or None.
    6. Validate that note is either a Note instance or None.
    7. Assign the provided values to instance attributes.

---
## method: `Personal.expected_blocks() -> dict[str, str]`

Return the expected block names for parsing personal information.

Args:
    None

Returns:
    A dictionary mapping block names (e.g., "contact information") to their corresponding attribute names in the Personal class.

Notes:
    1. The returned dictionary defines the expected block names in the input data for Personal.
    2. The keys are the block names found in the input (e.g., "contact information"), and the values are the corresponding attribute names in the class (e.g., "contact_info").

---
## method: `Personal.block_classes() -> dict[str, type]`

Return the classes used to parse each block of personal information.

Args:
    None

Returns:
    A dictionary mapping block names (e.g., "contact information") to the corresponding class types for parsing.

Notes:
    1. The returned dictionary defines which classes should be used to parse each block.
    2. The keys are the block names found in the input (e.g., "contact information"), and the values are the corresponding class types (e.g., ContactInfo).

---

===

===
# File: `resume_writer/models/education.py`

## `Degree` class

Represents details of a specific academic degree earned.

Attributes:
    school (str): The name of the educational institution.
    degree (str | None): The type of degree (e.g., Bachelor, Master).
    start_date (datetime | None): The start date of the program.
    end_date (datetime | None): The end date of the program.
    major (str | None): The major field of study.
    gpa (str | None): The grade point average.
    parse_context (ParseContext): The context in which the parsing occurred.

Args:
    parse_context (ParseContext): The context in which the parsing occurred, used for error reporting.
    school (str): The name of the educational institution.
    degree (str | None): The type of degree (e.g., Bachelor, Master).
    start_date (str | datetime | None): The start date of the program, as a string or datetime object.
    end_date (str | datetime | None): The end date of the program, as a string or datetime object.
    major (str | None): The major field of study.
    gpa (str | None): The grade point average, as a string.

Returns:
    None

Notes:
    1. Validate that parse_context is an instance of ParseContext.
    2. Validate that school is a non-empty string.
    3. Validate that degree, major, and gpa are either strings or None.
    4. Validate that start_date and end_date are either strings, datetime objects, or None.
    5. If end_date is provided but start_date is not, raise a ParseError.
    6. Parse start_date and end_date from strings into datetime objects using dateparser.
    7. If both start_date and end_date are provided, ensure start_date is not after end_date.
    8. Store the parsed values in the object's attributes.

---
## method: `Degree.__init__(self: UnknownType, parse_context: ParseContext, school: str, degree: str | None, start_date: str | datetime | None, end_date: str | datetime | None, major: str | None, gpa: str | None) -> UnknownType`



---
## method: `Degree.expected_fields() -> dict[str, str]`

Return the expected fields for this object.

Args:
    None

Returns:
    A dictionary mapping field names to argument names.

Notes:
    1. Return a dictionary with keys: "school", "degree", "start date", "end date", "major", "gpa".
    2. Each key maps to the corresponding argument name in the __init__ method.

---
## `Degrees` class

Represents a collection of academic degrees earned.

Attributes:
    degrees (list[Degree]): A list of Degree objects representing educational achievements.
    parse_context (ParseContext): The context in which the parsing occurred.

Args:
    degrees (list[Degree]): A list of Degree objects representing educational achievements.
    parse_context (ParseContext): The context in which the parsing occurred, used for error reporting.

Returns:
    None

Notes:
    1. Validate that degrees is a list.
    2. Validate that all items in degrees are instances of Degree.
    3. Validate that parse_context is an instance of ParseContext.
    4. Log the number of degrees created.
    5. Store the degrees list and parse_context in the object.

---
## method: `Degrees.__init__(self: UnknownType, degrees: list[Degree], parse_context: ParseContext) -> UnknownType`



---
## method: `Degrees.__iter__(self: UnknownType) -> UnknownType`

Iterate over the degrees.

Args:
    None

Returns:
    An iterator over the degrees list.

Notes:
    1. Return an iterator over the degrees list.

---
## method: `Degrees.__len__(self: UnknownType) -> UnknownType`

Return the number of degrees.

Args:
    None

Returns:
    The number of degrees in the list.

Notes:
    1. Return the length of the degrees list.

---
## method: `Degrees.__getitem__(self: UnknownType, index: int) -> UnknownType`

Return the degree at the given index.

Args:
    index (int): The index of the degree to retrieve.

Returns:
    The Degree object at the specified index.

Notes:
    1. Return the degree at the given index from the degrees list.

---
## method: `Degrees.list_class() -> type`

Return the list class for this object.

Args:
    None

Returns:
    The Degree class.

Notes:
    1. Return the Degree class as the list class for this object.

---
## `Education` class

Represents the educational background section of a resume.

Attributes:
    degrees (Degrees | None): A Degrees object containing educational achievements, or None if no degrees.
    parse_context (ParseContext): The context in which the parsing occurred.

Args:
    degrees (Degrees | None): A Degrees object containing educational achievements, or None if no degrees.
    parse_context (ParseContext): The context in which the parsing occurred, used for error reporting.

Returns:
    None

Notes:
    1. Validate that degrees is either a Degrees object or None.
    2. Validate that parse_context is an instance of ParseContext.
    3. Log the number of degrees in the object.
    4. Store the degrees and parse_context in the object.

---
## method: `Education.__init__(self: UnknownType, degrees: Degrees | None, parse_context: ParseContext) -> UnknownType`



---
## method: `Education.expected_blocks() -> dict[str, type]`

Return the expected blocks for the Education object.

Args:
    None

Returns:
    A dictionary mapping block names to their corresponding classes.

Notes:
    1. Return a dictionary with a single key "degrees" mapping to the Degrees class.

---
## method: `Education.block_classes() -> dict[str, type]`

Return the block classes for the Education object.

Args:
    None

Returns:
    A dictionary mapping block names to their corresponding classes.

Notes:
    1. Return a dictionary with a single key "degrees" mapping to the Degrees class.

---

===

===
# File: `resume_writer/models/__init__.py`


===

===
# File: `resume_writer/models/parsers.py`

## `ParseContext` class

Tracking context while parsing.

Attributes:
    lines (list[str]): The list of lines to be parsed.
    line_num (int): The current line number in the parsing process (1-indexed).
    doc_line_num (int): The current line number in the original document.

Args:
    lines: A list of strings representing the lines to be parsed.
    doc_line_num: The current line number in the document (used for tracking).

Returns:
    An initialized ParseContext object.

Notes:
    1. The input lines are validated to ensure they are a list.
    2. The line_num is initialized to 1 (human-readable line numbering).
    3. The doc_line_num is initialized to the provided value.
    4. The ParseContext supports iteration using __iter__ and __next__.
    5. The __next__ method returns one line at a time, advancing line_num and doc_line_num.
    6. The __len__ method returns the number of lines in the context.
    7. The append method adds a string to the lines list.
    8. The clear method empties the lines list and resets line_num.

---
## method: `ParseContext.__init__(self: UnknownType, lines: list[str], doc_line_num: int) -> UnknownType`

Initialize ParseContext class instance.

---
## method: `ParseContext.__iter__(self: UnknownType) -> UnknownType`

Return iterator.

---
## method: `ParseContext.__next__(self: UnknownType) -> str`

Return next line.

---
## method: `ParseContext.__len__(self: UnknownType) -> int`

Return number of lines in the context.

---
## method: `ParseContext.append(self: UnknownType, line: str) -> None`

Add a line to the list of lines.

---
## method: `ParseContext.clear(self: UnknownType) -> None`

Clear the list of lines.

---
## `ListBlockParse` class

Mixin for parsing bullet points into a list.

Args:
    parse_context: The current parsing context, containing lines to parse.

Returns:
    An instance of the class with parsed items.

Notes:
    1. The parse_context is validated to ensure it is a ParseContext.
    2. An empty list _items is initialized to store parsed items.
    3. Each line in the parse_context is processed:
        a. Empty lines are skipped.
        b. Lines starting with "* " or "- " are split into a label and value.
        c. The label is discarded, and the value is added to _items if not empty.
        d. Other non-empty lines are logged as skipped.
    4. All items in _items must be non-empty strings.
    5. The parsed list is returned as an instance of the class.

---
## method: `ListBlockParse.parse(cls: T, parse_context: ParseContext) -> T`

Parse the bullet list into lines of text.

---
## `TextBlockParse` class

Mixin for parsing blocks of text.

Args:
    parse_context: The current parsing context, containing lines to parse.

Returns:
    An instance of the class with the concatenated and cleaned text.

Notes:
    1. The parse_context is validated to ensure it is a ParseContext.
    2. An empty list _block_lines is initialized to collect lines.
    3. Each line in the parse_context is added to _block_lines.
    4. The lines are joined with newlines and stripped of leading/trailing whitespace.
    5. The resulting string is returned as an instance of the class.

---
## method: `TextBlockParse.parse(cls: T, parse_context: ParseContext) -> T`

Parse the block of lines into an object.

---
## `LabelBlockParse` class

Mixin for parsing blocks for labels.

Inheriting classes must implement `expected_fields` method, which
is a mapping between the label and the argument name for the
constructor.

Example:
-------
@staticmethod
def expected_fields() -> dict[str, str]:
    return {
        "school": "school",
        "degree": "degree",
        "start date": "start_date",
        "end date": "end_date",
    }

Args:
    parse_context: The current parsing context, containing lines to parse.

Returns:
    An instance of the class with parsed fields.

Notes:
    1. The parse_context is validated to ensure it is a ParseContext.
    2. A dictionary _expected_fields is retrieved from the class's expected_fields method.
    3. A dictionary _init_kwargs is initialized to store parsed field values.
    4. Each line in the parse_context is processed:
        a. Empty lines are skipped.
        b. Lines not containing a colon are skipped.
        c. The label part is extracted and converted to lowercase for lookup.
        d. If the label is in _expected_fields, the value is extracted, and the key-value pair is added to _init_kwargs.
        e. If the value is empty, it is skipped.
        f. Other non-empty lines are logged as skipped.
    5. Remaining keys in _expected_fields are added to _init_kwargs with None values.
    6. The parse_context is added to _init_kwargs.
    7. The class is instantiated with the populated _init_kwargs.

---
## method: `LabelBlockParse.parse(cls: T, parse_context: ParseContext) -> T`

Parse the block of lines into an object.

---
## `BasicBlockParse` class

Mixin for blocks containing a mix of top level blocks.

Subclasses must include two static methods:
* `expected_blocks`: a dictionary of block names and their init arg names
* `block_classes`: a dictionary of block names and the class to instanciate
for that block.

Example:
-------
@staticmethod
def expected_blocks() -> dict[str, str]:
    return {
        "basics": "basics",
        "description": "description",
        "responsibilities": "responsibilities",
        "skills": "skills",
    }

@staticmethod
def block_classes() -> dict[str, type]:
    return {
        "basics": RoleBasics,
        "description": RoleDescription,
        "responsibilities": RoleResponsibilities,
        "skills": RoleSkills,
    }

Args:
    parse_context: The current parsing context, containing lines to parse.

Returns:
    An instance of the class with parsed blocks.

Notes:
    1. The parse_context is validated to ensure it is a ParseContext.
    2. A dictionary _blocks is initialized to store parsed blocks.
    3. A variable _section_header is initialized to track the current section.
    4. Each line in the parse_context is processed:
        a. If the line starts with "# ", it is a section header, and _section_header is set.
        b. If there is no section header yet, the line is logged as unexpected.
        c. If the line does not start with "#", it is added to the current section.
    5. The section header is used to store the block context.
    6. After processing, the block contexts are converted to blocks using parse_blocks.
    7. The kwargs_parse method is called to process the blocks.
    8. The class is instantiated with the parsed kwargs.

---
## method: `BasicBlockParse.parse_blocks(cls: T, parse_context: ParseContext) -> dict[str, str]`

Parse the block of lines into a dictionary of blocks.

---
## method: `BasicBlockParse.kwargs_parse(cls: T, parse_context: ParseContext) -> dict[str, str]`

Parse the block of lines into an dict.

Use this when more processing has to be done.

---
## method: `BasicBlockParse.parse(cls: T, parse_context: ParseContext) -> T`

Parse the block of lines into an object.

---
## `MultiBlockParse` class

Mixin for blocks containing multiple blocks with the same name.

Args:
    parse_context: The current parsing context, containing lines to parse.

Returns:
    An instance of the class with a list of parsed objects.

Notes:
    1. The parse_context is validated to ensure it is a ParseContext.
    2. A list _blocks is initialized to store parsed block contexts.
    3. A variable _current_block is initialized to collect lines for the current block.
    4. A variable _section_header is initialized to track the current section.
    5. Each line in the parse_context is processed:
        a. Empty lines are skipped.
        b. Lines starting with "# " are section headers, and _section_header is set.
        c. If a new section header is found and _current_block is non-empty, it is added to _blocks.
        d. If _section_header is set, the line is added to _current_block.
    6. After processing, the last _current_block is added to _blocks if non-empty.
    7. The block contexts in _blocks are validated.
    8. The list_class method is called to get the type of the list items.
    9. Each block context is parsed into an object using the list_class type.
    10. The list of objects is returned as an instance of the class.

---
## method: `MultiBlockParse.parse_blocks(cls: T, parse_context: ParseContext) -> list[list[str]]`

Parse the block of lines into a list of blocks.

Requires a static method named `list_class` which returns
the `type` of the list items.

---
## method: `MultiBlockParse.parse(cls: T, parse_context: ParseContext) -> T`

Parse the blocks and return a list of objects.

---

===

===
# File: `resume_writer/utils/__main__.py`


===

