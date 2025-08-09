# Docstrings Reference

===
# File: `resume.py`

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
# File: `experience.py`

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
# File: `certifications.py`

## `Certification` class

Represents a professional certification.

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
# File: `personal.py`

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
    parse_context: The context used during parsing, containing metadata about the input.
    name: The full name of the person.
    email: The email address of the person, or None if not provided.
    phone: The phone number of the person, or None if not provided.
    location: The physical location (e.g., city and country) of the person, or None if not provided.

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
    parse_context: The context used during parsing, containing metadata about the input.
    website: The personal website URL, or None if not provided.
    github: The GitHub profile URL, or None if not provided.
    linkedin: The LinkedIn profile URL, or None if not provided.
    twitter: The Twitter profile URL, or None if not provided.

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
    parse_context: The context used during parsing, containing metadata about the input.
    work_authorization: The current work authorization status (e.g., "US Citizen", "H-1B"), or None if not provided.
    require_sponsorship: A boolean indicating if sponsorship is required, or a string ("yes"/"no") that will be converted to a boolean, or None if not provided.

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
    parse_context: The context used during parsing, containing metadata about the input.
    text_string: The raw text content of the banner, potentially including leading/trailing or internal blank lines.

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
    parse_context: The context used during parsing, containing metadata about the input.
    text_string: The raw text content of the note, potentially including leading/trailing or internal blank lines.

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
    parse_context: The context used during parsing, containing metadata about the input.
    contact_info: An instance of ContactInfo containing personal contact details, or None if not provided.
    websites: An instance of Websites containing personal website links, or None if not provided.
    visa_status: An instance of VisaStatus containing visa and sponsorship information, or None if not provided.
    banner: An instance of Banner containing a personal banner message, or None if not provided.
    note: An instance of Note containing a personal note, or None if not provided.

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
# File: `education.py`

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

---
## method: `Degree.__init__(self: UnknownType, parse_context: ParseContext, school: str, degree: str | None, start_date: str | datetime | None, end_date: str | datetime | None, major: str | None, gpa: str | None) -> UnknownType`

Initialize a Degree object with academic details.

Args:
    parse_context: The context in which the parsing occurred, used for error reporting.
    school: The name of the educational institution.
    degree: The type of degree (e.g., Bachelor, Master).
    start_date: The start date of the program, as a string or datetime object.
    end_date: The end date of the program, as a string or datetime object.
    major: The major field of study.
    gpa: The grade point average, as a string.

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

---
## method: `Degrees.__init__(self: UnknownType, degrees: list[Degree], parse_context: ParseContext) -> UnknownType`

Initialize a Degrees object with a list of degree records.

Args:
    degrees: A list of Degree objects representing educational achievements.
    parse_context: The context in which the parsing occurred, used for error reporting.

Returns:
    None

Notes:
    1. Validate that degrees is a list.
    2. Validate that all items in degrees are instances of Degree.
    3. Validate that parse_context is an instance of ParseContext.
    4. Log the number of degrees created.
    5. Store the degrees list and parse_context in the object.

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
    index: The index of the degree to retrieve.

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

---
## method: `Education.__init__(self: UnknownType, degrees: Degrees | None, parse_context: ParseContext) -> UnknownType`

Initialize an Education object with educational details.

Args:
    degrees: A Degrees object containing educational achievements, or None if no degrees.
    parse_context: The context in which the parsing occurred, used for error reporting.

Returns:
    None

Notes:
    1. Validate that degrees is either a Degrees object or None.
    2. Validate that parse_context is an instance of ParseContext.
    3. Log the number of degrees in the object.
    4. Store the degrees and parse_context in the object.

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
# File: `__init__.py`


===

===
# File: `parsers.py`

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

