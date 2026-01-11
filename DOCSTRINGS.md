# Docstrings Reference

===
# File: `./resume_editor/app/__init__.py`


===

===
# File: `./resume_editor/app/main.py`

## function: `create_app() -> FastAPI`

Create and configure the FastAPI application.

Args:
    None

Returns:
    FastAPI: The configured FastAPI application instance.

Notes:
    1. Initialize the FastAPI application with the title "Resume Editor API".
    2. Add CORS middleware to allow requests from any origin (for development only).
    3. Include the user router to handle user-related API endpoints.
    4. Include the resume router to handle resume-related API endpoints.
    5. Include the admin router to handle administrative API endpoints.
    6. Define a health check endpoint at "/health" that returns a JSON object with status "ok".
    7. Add static file serving for CSS/JS assets.
    8. Add template rendering for HTML pages.
    9. Define dashboard routes for the HTMX-based interface.
    10. Log a success message indicating the application was created.

---

## function: `initialize_database() -> UnknownType`

Initialize the database.

Args:
    None

Returns:
    None

Notes:
    1. Database initialization is now handled by Alembic migrations.
    2. This function is kept for structural consistency but performs no actions.

---

## function: `main() -> UnknownType`

Entry point for running the application directly.

---


===

===
# File: `./resume_editor/app/api/__init__.py`

## function: `get_app() -> FastAPI`

Creates and configures the FastAPI application instance.

This function initializes a FastAPI app with the following features:
- Includes the authentication and resume management routes.
- Configures middleware for logging and error handling.
- Sets up CORS to allow frontend access from different origins.

Args:
    None.

Returns:
    FastAPI: A configured FastAPI application instance.

Raises:
    None.

Notes:
    1. The application is initialized with a title, version, and description.
    2. Routes are included from the main application setup.
    3. CORS is enabled with allow_origins set to allow requests from 'http://localhost:3000'.
    4. The middleware stack includes logging and exception handling.
    5. The database session is provided via dependency injection through the 'get_db' function.
    6. The function performs no disk or network I/O.
    7. The function does not perform any database access.

---


===

===
# File: `./resume_editor/app/api/routes/resume.py`

## function: `_generate_resume_list_html(resumes: list[DatabaseResume], selected_resume_id: int | None) -> str`

Generates HTML for a list of resumes, marking one as selected.

Args:
    resumes (list[DatabaseResume]): The list of resumes to display.
    selected_resume_id (int | None): The ID of the resume to mark as selected.

Returns:
    str: HTML string for the resume list.

Notes:
    1. Checks if the resumes list is empty.
    2. If empty, returns a message indicating no resumes were found.
    3. Otherwise, generates HTML for each resume item with a selected class if it matches the selected ID.
    4. Returns the concatenated HTML string.

---

## function: `_generate_resume_detail_html(resume: DatabaseResume) -> str`

Generate the HTML for the resume detail view.

Args:
    resume (DatabaseResume): The resume object to generate HTML for.

Returns:
    str: HTML string for the resume detail view.

Notes:
    1. Creates HTML for the resume detail section with a header, content area, and footer.
    2. Includes buttons for refining with AI, exporting, and editing.
    3. Creates modal dialogs for export and refine actions with appropriate event handlers.
    4. Returns the complete HTML string.

---


===

===
# File: `./resume_editor/app/api/routes/user.py`

## function: `get_user_by_username(db: Session, username: str) -> User | None`

Retrieve a user from the database using their username.

Args:
    db: Database session dependency used to query the database.
    username: The unique username to search for in the database.

Returns:
    User | None: The User object if found, otherwise None.

Notes:
    1. Query the database for a user with the given username.
    2. Return the first match or None if no user is found.
    3. Database access: Performs a read operation on the User table.

---

## function: `get_user_by_email(db: Session, email: str) -> User | None`

Retrieve a user from the database using their email address.

Args:
    db: Database session dependency used to query the database.
    email: The unique email address to search for in the database.

Returns:
    User | None: The User object if found, otherwise None.

Notes:
    1. Query the database for a user with the given email.
    2. Return the first match or None if no user is found.
    3. Database access: Performs a read operation on the User table.

---

## function: `create_new_user(db: Session, user_data: UserCreate) -> User`

Create a new user in the database with the provided data.

Args:
    db: Database session dependency used to persist the new user.
    user_data: Data required to create a new user, including username, email, and password.

Returns:
    User: The newly created User object with all fields populated.

Notes:
    1. Hash the provided password using a secure hashing algorithm.
    2. Instantiate a new User object with the username, email, and hashed password.
    3. Add the new user object to the database session.
    4. Commit the transaction to persist the user to the database.
    5. Refresh the object to ensure it contains the latest state from the database.
    6. Database access: Performs a write operation on the User table.

---

## function: `get_users(db: Session) -> list[User]`

Retrieve all users from the database.

Args:
    db (Session): The database session.

Returns:
    list[User]: A list of all user objects.

---

## function: `get_user_by_id(db: Session, user_id: int) -> User | None`

Retrieve a single user by ID.

Args:
    db (Session): The database session.
    user_id (int): The ID of the user to retrieve.

Returns:
    User | None: The user object if found, otherwise None.

---

## function: `delete_user(db: Session, user: User) -> None`

Delete a user from the database.

Args:
    db (Session): The database session.
    user (User): The user object to delete.

---

## function: `register_user(user: UserCreate, db: Session) -> UserResponse`

Register a new user with the provided credentials.

Args:
    user: Data containing username, email, and password for the new user.
    db: Database session dependency used to interact with the user database.

Returns:
    UserResponse: The created user's data, excluding the password.

Raises:
    HTTPException: If the username or email is already registered.

Notes:
    1. Check if the provided username already exists in the database.
    2. If the username exists, raise a 400 error.
    3. Check if the provided email already exists in the database.
    4. If the email exists, raise a 400 error.
    5. Create a new user with the provided data and store it in the database.
    6. Return the newly created user's data (without the password).
    7. Database access: Performs read and write operations on the User table.

---

## function: `get_user_settings(db: Session, current_user: User) -> UnknownType`

Get the current user's settings.

Args:
    db (Session): The database session.
    current_user (User): The authenticated user.

Returns:
    UserSettingsResponse: The user's settings.

Notes:
    1. Retrieve the user's settings from the database.
    2. If no settings exist, return an empty response.
    3. Database access: Performs a read operation on the UserSettings table.

---

## function: `update_user_settings(settings_data: UserSettingsUpdateRequest, db: Session, current_user: User) -> UnknownType`

Update the current user's settings.

Args:
    settings_data (UserSettingsUpdateRequest): The settings data to update.
    db (Session): The database session.
    current_user (User): The authenticated user.

Returns:
    UserSettingsResponse: The updated user's settings.

Notes:
    1. Update the user's settings in the database with the provided data.
    2. Return the updated settings.
    3. Database access: Performs a write operation on the UserSettings table.

---

## function: `login_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session, settings: Settings) -> Token`

Authenticate a user and return an access token.

Args:
    form_data: Form data containing username and password for authentication.
    db: Database session dependency used to verify user credentials.

Returns:
    Token: An access token for the authenticated user, formatted as a JWT.

Raises:
    HTTPException: If the username or password is incorrect.

Notes:
    1. Attempt to authenticate the user using the provided username and password.
    2. If authentication fails, raise a 401 error.
    3. Generate a JWT access token with a defined expiration time.
    4. Return the access token to the client.
    5. Database access: Performs a read operation on the User table to verify credentials.

---


===

===
# File: `./resume_editor/app/api/routes/route_models.py`


===

===
# File: `./resume_editor/app/api/routes/admin.py`

## function: `admin_create_user(user_data: AdminUserCreate, db: Session) -> UnknownType`

Admin endpoint to create a new user.

Args:
    user_data (AdminUserCreate): The data required to create a new user, including username, password, and optional email.
    db (Session): The database session used to interact with the database.

Returns:
    UserResponse: The created user's data, including the user's ID, username, and any other public fields.

Notes:
    1. Logs the admin's attempt to create a user.
    2. Reuses the existing logic from create_new_user to create the user.
    3. Commits the new user to the database.
    4. Logs the completion of user creation.
    5. Database access occurs during user creation and commit.

---

## function: `admin_get_users(db: Session) -> UnknownType`

Admin endpoint to list all users.

Args:
    db (Session): The database session used to interact with the database.

Returns:
    list[UserResponse]: A list of all users' data, including their ID, username, and other public fields.

Notes:
    1. Logs the admin's request to fetch all users.
    2. Retrieves all users from the database using db_get_users.
    3. Logs the completion of the fetch operation.
    4. Database access occurs during the retrieval of users.

---

## function: `admin_get_user(user_id: int, db: Session) -> UnknownType`

Admin endpoint to get a single user by ID.

Args:
    user_id (int): The unique identifier of the user to retrieve.
    db (Session): The database session used to interact with the database.

Returns:
    UserResponse: The data of the requested user, including their ID, username, and other public fields.

Raises:
    HTTPException: If the user with the given ID is not found, raises a 404 error.

Notes:
    1. Logs the admin's request to fetch a user by ID.
    2. Retrieves the user from the database using get_user_by_id.
    3. If the user is not found, raises a 404 HTTPException.
    4. Logs the completion of the fetch operation.
    5. Database access occurs during the user retrieval.

---

## function: `admin_delete_user(user_id: int, db: Session) -> UnknownType`

Admin endpoint to delete a user.

Args:
    user_id (int): The unique identifier of the user to delete.
    db (Session): The database session used to interact with the database.

Raises:
    HTTPException: If the user with the given ID is not found, raises a 404 error.

Notes:
    1. Logs the admin's request to delete a user.
    2. Retrieves the user from the database using get_user_by_id.
    3. If the user is not found, raises a 404 HTTPException.
    4. Deletes the user from the database using db_delete_user.
    5. Commits the deletion to the database.
    6. Logs the completion of the deletion.
    7. Database access occurs during user retrieval, deletion, and commit.

---

## function: `admin_assign_role_to_user(user_id: int, role_name: str, db: Session) -> UnknownType`

Admin endpoint to assign a role to a user.

Args:
    user_id (int): The unique identifier of the user to assign the role to.
    role_name (str): The name of the role to assign.
    db (Session): The database session used to interact with the database.

Returns:
    UserResponse: The updated user data, including the newly assigned role.

Raises:
    HTTPException: If the user or role is not found (404 error), or if the user already has the role (400 error).

Notes:
    1. Logs the admin's attempt to assign a role to a user.
    2. Retrieves the user from the database using get_user_by_id.
    3. If the user is not found, raises a 404 HTTPException.
    4. Retrieves the role from the database using get_role_by_name.
    5. If the role is not found, raises a 404 HTTPException.
    6. Checks if the user already has the role; if so, returns the user without modification.
    7. Appends the role to the user's roles list.
    8. Commits the change to the database.
    9. Refreshes the user object from the database.
    10. Logs the completion of the role assignment.
    11. Database access occurs during user and role retrieval, modification, and commit.

---

## function: `admin_remove_role_from_user(user_id: int, role_name: str, db: Session) -> UnknownType`

Admin endpoint to remove a role from a user.

Args:
    user_id (int): The unique identifier of the user to remove the role from.
    role_name (str): The name of the role to remove.
    db (Session): The database session used to interact with the database.

Returns:
    UserResponse: The updated user data, excluding the removed role.

Raises:
    HTTPException: If the user or role is not found (404 error), or if the user does not have the role (400 error).

Notes:
    1. Logs the admin's attempt to remove a role from a user.
    2. Retrieves the user from the database using get_user_by_id.
    3. If the user is not found, raises a 404 HTTPException.
    4. Retrieves the role from the database using get_role_by_name.
    5. If the role is not found, raises a 404 HTTPException.
    6. Checks if the user has the role; if not, raises a 400 HTTPException.
    7. Removes the role from the user's roles list.
    8. Commits the change to the database.
    9. Refreshes the user object from the database.
    10. Logs the completion of the role removal.
    11. Database access occurs during user and role retrieval, modification, and commit.

---

## function: `admin_impersonate_user(username: str, db: Session, admin_user: User, settings: Settings) -> UnknownType`

Admin endpoint to impersonate a user.

Args:
    username (str): The username of the user to impersonate.
    db (Session): The database session used to interact with the database.
    admin_user (User): The currently authenticated admin user.

Returns:
    Token: A JWT access token for the impersonated user, with the admin's username as the impersonator.

Raises:
    HTTPException: If the user to impersonate is not found, raises a 404 error.

Notes:
    1. Logs the admin's attempt to impersonate a user.
    2. Retrieves the target user from the database by username.
    3. If the target user is not found, raises a 404 HTTPException.
    4. Creates a JWT access token with the admin's username as the impersonator.
    5. Logs the successful creation of the impersonation token.

---


===

===
# File: `./resume_editor/app/api/routes/route_logic/resume_crud.py`

## function: `get_resume_by_id_and_user(db: Session, resume_id: int, user_id: int) -> DatabaseResume`

Retrieve a resume by its ID and verify it belongs to the specified user.

Args:
    db (Session): The SQLAlchemy database session used to query the database.
    resume_id (int): The unique identifier for the resume to retrieve.
    user_id (int): The unique identifier for the user who owns the resume.

Returns:
    DatabaseResume: The resume object matching the provided ID and user ID.

Raises:
    HTTPException: If no resume is found with the given ID and user ID, raises a 404 error with detail "Resume not found".

Notes:
    1. Query the DatabaseResume table for a record where the id matches resume_id and the user_id matches user_id.
    2. If no matching record is found, raise an HTTPException with status code 404 and detail "Resume not found".
    3. Return the found DatabaseResume object.
    4. This function performs a single database query to retrieve a resume.

---

## function: `get_user_resumes(db: Session, user_id: int) -> list[DatabaseResume]`

Retrieve all resumes associated with a specific user.

Args:
    db (Session): The SQLAlchemy database session used to query the database.
    user_id (int): The unique identifier for the user whose resumes are to be retrieved.

Returns:
    list[DatabaseResume]: A list of DatabaseResume objects belonging to the specified user.

Notes:
    1. Query the DatabaseResume table for all records where the user_id matches the provided user_id.
    2. Return the list of matching DatabaseResume objects.
    3. This function performs a single database query to retrieve all resumes for a user.

---

## function: `create_resume(db: Session, user_id: int, name: str, content: str) -> DatabaseResume`

Create and save a new resume.

Args:
    db (Session): The database session.
    user_id (int): The ID of the user who owns the resume.
    name (str): The name of the resume.
    content (str): The content of the resume.

Returns:
    DatabaseResume: The newly created resume object.

Notes:
    1. Create a new DatabaseResume instance with the provided user_id, name, and content.
    2. Add the instance to the database session.
    3. Commit the transaction to persist the changes.
    4. Refresh the instance to ensure it has the latest state, including the generated ID.
    5. Return the created resume.
    6. This function performs a database write operation.

---

## function: `update_resume(db: Session, resume: DatabaseResume, name: str | None, content: str | None) -> DatabaseResume`

Update a resume's name and/or content.

Args:
    db (Session): The database session.
    resume (DatabaseResume): The resume to update.
    name (str, optional): The new name for the resume. If None, the name is not updated.
    content (str, optional): The new content for the resume. If None, the content is not updated.

Returns:
    DatabaseResume: The updated resume object.

Notes:
    1. If a new name is provided (not None), update the resume's name attribute.
    2. If new content is provided (not None), update the resume's content attribute.
    3. Commit the transaction to save the changes to the database.
    4. Refresh the resume object to ensure it reflects the latest state from the database.
    5. Return the updated resume.
    6. This function performs a database write operation.

---

## function: `delete_resume(db: Session, resume: DatabaseResume) -> None`

Delete a resume.

Args:
    db (Session): The database session.
    resume (DatabaseResume): The resume to delete.

Returns:
    None

Notes:
    1. Delete the resume object from the database session.
    2. Commit the transaction to persist the deletion.
    3. This function performs a database write operation.

---


===

===
# File: `./resume_editor/app/api/routes/route_logic/resume_validation.py`

## function: `perform_pre_save_validation(markdown_content: str, original_content: str | None) -> None`

Perform comprehensive pre-save validation on resume content.

Args:
    markdown_content (str): The updated resume Markdown content to validate.
    original_content (str | None): The original resume content for comparison.

Returns:
    None: This function does not return any value.

Raises:
    HTTPException: If validation fails with status code 422.

Notes:
    1. Run the updated Markdown through the existing parser to ensure it's still valid.
    2. If any validation fails, raise an HTTPException with detailed error messages.
    3. This function performs validation checks on resume content before saving to ensure data integrity.
    4. Validation includes parsing the Markdown content to verify its structure and format.
    5. The function accesses the resume parsing module to validate the content structure.

---


===

===
# File: `./resume_editor/app/api/routes/route_logic/resume_filtering.py`

## function: `_get_date_from_optional_datetime(dt: datetime | None) -> date | None`

Extract the date portion from an optional datetime object.

Args:
    dt (datetime | None): The datetime object to extract the date from, or None.

Returns:
    date | None: The date portion of the datetime object, or None if input is None.

Notes:
    1. If the input dt is None, return None.
    2. Otherwise, extract and return the date portion of the datetime object using the date() method.

---

## function: `_is_in_date_range(item_start_date: date | None, item_end_date: date | None, filter_start_date: date | None, filter_end_date: date | None) -> bool`

Check if an item's date range overlaps with the filter's date range.

Args:
    item_start_date (date | None): The start date of the item being evaluated.
    item_end_date (date | None): The end date of the item (or None if ongoing).
    filter_start_date (date | None): The start date of the filtering period.
    filter_end_date (date | None): The end date of the filtering period.

Returns:
    bool: True if the item overlaps with the filter's date range, False otherwise.

Notes:
    1. If the filter has a start date and the item ends before that date, the item is out of range.
    2. If the filter has an end date and the item starts after that date, the item is out of range.
    3. Otherwise, the item is considered to be in range.

---

## function: `filter_experience_by_date(experience: ExperienceResponse, start_date: date | None, end_date: date | None) -> ExperienceResponse`

Filter roles and projects in an ExperienceResponse based on a date range.

Args:
    experience (ExperienceResponse): The experience data to filter.
    start_date (date | None): The start of the filtering period. If None, no start constraint is applied.
    end_date (date | None): The end of the filtering period. If None, no end constraint is applied.

Returns:
    ExperienceResponse: A new ExperienceResponse object containing only roles and projects that overlap with the specified date range.

Notes:
    1. If both start_date and end_date are None, return the original experience object unmodified.
    2. Iterate through the roles in the experience object and check if each role's date range overlaps with the filter range using _is_in_date_range.
    3. For each role that overlaps, add it to the filtered_roles list.
    4. Iterate through the projects in the experience object and check if each project's date range overlaps with the filter range.
    5. Projects without an end date are treated as single-day events occurring on their start date.
    6. For each project that overlaps, add it to the filtered_projects list.
    7. Return a new ExperienceResponse object with the filtered roles and projects.

---


===

===
# File: `./resume_editor/app/api/routes/route_logic/resume_llm.py`

## function: `_get_section_content(resume_content: str, section_name: str) -> str`

Extracts the Markdown content for a specific section of the resume.

Args:
    resume_content (str): The full resume content in Markdown.
    section_name (str): The name of the section to extract ("personal", "education", "experience", "certifications", or "full").

Returns:
    str: The Markdown content of the specified section. Returns the full content if "full" is specified.

Raises:
    ValueError: If the section_name is not one of the valid options.

Notes:
    1. If section_name is "full", return the entire resume_content.
    2. Otherwise, map the section_name to a tuple of extractor and serializer functions.
    3. Validate that section_name is in the valid set of keys.
    4. Extract the data using the extractor function.
    5. Serialize the extracted data using the serializer function.
    6. Return the serialized result.

---

## function: `refine_resume_section_with_llm(resume_content: str, job_description: str, target_section: str, llm_endpoint: str | None, api_key: str | None) -> str`

Uses an LLM to refine a specific section of a resume based on a job description.

Args:
    resume_content (str): The full Markdown content of the resume.
    job_description (str): The job description to align the resume with.
    target_section (str): The section of the resume to refine (e.g., "experience").
    llm_endpoint (str | None): The custom LLM endpoint URL.
    api_key (str | None): The user's decrypted LLM API key.

Returns:
    str: The refined Markdown content for the target section. Returns an empty string if the target section is empty.

Notes:
    1. Extract the target section content from the resume using _get_section_content.
    2. If the extracted content is empty, return an empty string.
    3. Set up a PydanticOutputParser for structured output based on the RefinedSection model.
    4. Create a PromptTemplate with instructions for the LLM, including format instructions.
    5. Initialize the ChatOpenAI client with the specified model, temperature, API base, and API key.
    6. Create a chain combining the prompt, LLM, and parser.
    7. Invoke the chain with the job description and resume section content.
    8. Parse the LLM's JSON-Markdown output using parse_json_markdown if the result is a string.
    9. Validate the parsed JSON against the RefinedSection model.
    10. Return the refined_markdown field from the validated result.

Network access:
    - This function makes a network request to the LLM endpoint specified by llm_endpoint.

---


===

===
# File: `./resume_editor/app/api/routes/route_logic/settings_crud.py`

## function: `get_user_settings(db: Session, user_id: int) -> UserSettings | None`

Retrieves the settings for a given user.

Args:
    db (Session): The database session used to query the database.
    user_id (int): The unique identifier of the user whose settings are being retrieved.

Returns:
    UserSettings | None: The user's settings if found, otherwise None.

Notes:
    1. Queries the database for a UserSettings record where user_id matches the provided user_id.
    2. Returns the first matching record or None if no record is found.
    3. This function performs a single database read operation.

---

## function: `update_user_settings(db: Session, user_id: int, settings_data: 'UserSettingsUpdateRequest') -> UserSettings`

Creates or updates settings for a user.

Args:
    db (Session): The database session used to perform database operations.
    user_id (int): The unique identifier of the user whose settings are being updated.
    settings_data (UserSettingsUpdateRequest): The data containing the updated settings.

Returns:
    UserSettings: The updated or newly created UserSettings object.

Notes:
    1. Attempts to retrieve existing settings for the given user_id using get_user_settings.
    2. If no settings are found, creates a new UserSettings object with the provided user_id and adds it to the session.
    3. Updates the llm_endpoint field if settings_data.llm_endpoint is provided and not None.
    4. If settings_data.api_key is provided and not empty, encrypts the API key using encrypt_data and stores it in encrypted_api_key; otherwise, sets encrypted_api_key to None.
    5. Commits the transaction to the database.
    6. Refreshes the session to ensure the returned object has the latest data from the database.
    7. This function performs a database read and possibly a write operation.

---


===

===
# File: `./resume_editor/app/api/routes/route_logic/resume_reconstruction.py`

## function: `reconstruct_resume_markdown(personal_info: PersonalInfoResponse | None, education: EducationResponse | None, certifications: CertificationsResponse | None, experience: ExperienceResponse | None) -> str`

Reconstruct a complete resume Markdown document from structured data sections.

Args:
    personal_info (PersonalInfoResponse | None): Personal information data structure. If None, the personal info section is omitted.
    education (EducationResponse | None): Education information data structure. If None, the education section is omitted.
    certifications (CertificationsResponse | None): Certifications information data structure. If None, the certifications section is omitted.
    experience (ExperienceResponse | None): Experience information data structure, containing roles and projects. If None, the experience section is omitted.

Returns:
    str: A complete Markdown formatted resume document with all provided sections joined by double newlines.

Notes:
    1. Initialize an empty list to collect resume sections.
    2. Serialize each provided section using the corresponding serialization function.
    3. Append each serialized section to the sections list if it is not empty.
    4. Filter out any empty strings and strip whitespace from each section.
    5. Join all sections with double newlines to ensure proper spacing.
    6. Return the complete Markdown resume content.
    7. No network, disk, or database access is performed.

---

## function: `build_complete_resume_from_sections(personal_info: PersonalInfoResponse, education: EducationResponse, certifications: CertificationsResponse, experience: ExperienceResponse) -> str`

Build a complete resume Markdown document from all structured sections.

Args:
    personal_info (PersonalInfoResponse): Personal information data structure.
    education (EducationResponse): Education information data structure.
    certifications (CertificationsResponse): Certifications information data structure.
    experience (ExperienceResponse): Experience information data structure.

Returns:
    str: A complete Markdown formatted resume document with all sections in the order: personal, education, certifications, experience.

Notes:
    1. Calls reconstruct_resume_markdown with all sections.
    2. Ensures proper section ordering (personal, education, certifications, experience).
    3. Returns the complete Markdown resume content.
    4. No network, disk, or database access is performed.

---


===

===
# File: `./resume_editor/app/api/routes/route_logic/admin_crud.py`

## function: `create_user_admin(db: Session, user_data: AdminUserCreate) -> User`

Create a new user as an administrator.

Args:
    db (Session): The database session used to interact with the database.
    user_data (AdminUserCreate): The data required to create a new user, including username, email, password, and other attributes.

Returns:
    User: The newly created user object with all fields populated, including the generated ID.

Notes:
    1. Hashes the provided password using the `get_password_hash` utility.
    2. Creates a new `User` instance with the provided data and the hashed password.
    3. Adds the new user to the database session.
    4. Commits the transaction to persist the user to the database.
    5. Refreshes the user object to ensure it contains the latest data from the database (e.g., auto-generated ID).
    6. This function performs a database write operation.

---

## function: `get_user_by_id_admin(db: Session, user_id: int) -> User | None`

Retrieve a single user by their unique ID as an administrator.

Args:
    db (Session): The database session used to query the database.
    user_id (int): The unique identifier of the user to retrieve.

Returns:
    User | None: The user object if found, otherwise None.

Notes:
    1. Queries the database for a user with the specified ID.
    2. This function performs a database read operation.

---

## function: `get_users_admin(db: Session) -> list[User]`

Retrieve all users from the database as an administrator.

Args:
    db (Session): The database session used to query the database.

Returns:
    list[User]: A list of all user objects in the database.

Notes:
    1. Queries the database for all users.
    2. This function performs a database read operation.

---

## function: `get_user_by_username_admin(db: Session, username: str) -> User | None`

Retrieve a single user by their username as an administrator.

Args:
    db (Session): The database session used to query the database.
    username (str): The unique username of the user to retrieve.

Returns:
    User | None: The user object if found, otherwise None.

Notes:
    1. Queries the database for a user with the specified username.
    2. This function performs a database read operation.

---

## function: `delete_user_admin(db: Session, user: User) -> None`

Delete a user from the database as an administrator.

Args:
    db (Session): The database session used to interact with the database.
    user (User): The user object to be deleted.

Returns:
    None

Notes:
    1. Removes the specified user from the database session.
    2. Commits the transaction to permanently delete the user from the database.
    3. This function performs a database write operation.

---

## function: `get_role_by_name_admin(db: Session, name: str) -> Role | None`

Retrieve a role from the database by its unique name.

This function is intended for administrative use to fetch a role before
performing actions like assigning it to or removing it from a user.

Args:
    db (Session): The SQLAlchemy database session.
    name (str): The unique name of the role to retrieve.

Returns:
    Role | None: The `Role` object if found, otherwise `None`.

Notes:
    1. Queries the database for a role with the given name.
    2. This function performs a database read operation.

---

## function: `assign_role_to_user_admin(db: Session, user: User, role: Role) -> User`

Assign a role to a user if they do not already have it.

This administrative function associates a `Role` with a `User`.
It checks for the role's existence on the user before appending to prevent duplicates.
Changes are committed to the database.

Args:
    db (Session): The SQLAlchemy database session.
    user (User): The user object to which the role will be assigned.
    role (Role): The role object to assign.

Returns:
    User: The updated user object, refreshed from the database if changes were made.

Notes:
    1. Checks if the user already has the role.
    2. If not, adds the role to the user's roles and commits the change.
    3. This function performs a database write operation if the role is added.

---

## function: `remove_role_from_user_admin(db: Session, user: User, role: Role) -> User`

Remove a role from a user if they have it.

This administrative function disassociates a `Role` from a `User`.
It checks if the user has the role before attempting removal.
Changes are committed to the database.

Args:
    db (Session): The SQLAlchemy database session.
    user (User): The user object from which the role will be removed.
    role (Role): The role object to remove.

Returns:
    User: The updated user object, refreshed from the database if changes were made.

Notes:
    1. Checks if the user has the role.
    2. If so, removes the role from the user's roles and commits the change.
    3. This function performs a database write operation if the role is removed.

---

## function: `impersonate_user_admin(db: Session, user_id: int) -> str | None`

Generate an impersonation token for a user.

Args:
    db (Session): The database session used to interact with the database.
    user_id (int): The unique identifier of the user to impersonate.

Returns:
    str | None: The access token if the user is found, otherwise None.

Notes:
    1. Retrieves the user by ID using `get_user_by_id_admin`.
    2. If the user exists, creates an access token for them using `SecurityManager`.
    3. Returns the token, or None if the user was not found.
    4. This function performs a database read operation.

---


===

===
# File: `./resume_editor/app/api/routes/route_logic/resume_parsing.py`

## function: `parse_resume_to_writer_object(markdown_content: str) -> WriterResume`

Parse Markdown resume content into a resume_writer Resume object.

Args:
    markdown_content (str): The Markdown content to parse, expected to follow a valid resume format.

Returns:
    WriterResume: The parsed resume object from the resume_writer library, containing structured data for personal info, experience, education, certifications, etc.

Raises:
    ValueError: If the parsed content contains no valid resume sections (e.g., no personal, education, experience, or certifications data).

Notes:
    1. Split the input Markdown content into individual lines.
    2. Skip any lines before the first valid top-level section header (i.e., lines starting with "# " but not "##").
    3. Identify valid section headers by checking against the keys in WriterResume.expected_blocks().
    4. If a valid header is found, truncate the lines list to start from that header.
    5. Create a ParseContext object using the processed lines and indentation level 1.
    6. Use the Resume.parse method to parse the content into a WriterResume object.
    7. Check if any of the main resume sections (personal, education, experience, certifications) were successfully parsed.
    8. Raise ValueError if no valid sections were parsed.
    9. Return the fully parsed WriterResume object.

---

## function: `parse_resume(markdown_content: str) -> dict[str, Any]`

Parse Markdown resume content using resume_writer parser and return a dictionary.

Args:
    markdown_content (str): The Markdown content to parse, expected to follow a valid resume format.

Returns:
    dict[str, Any]: A dictionary representation of the parsed resume data, including:
        - personal: Personal information (e.g., name, email, phone).
        - experience: List of work experience entries.
        - education: List of educational qualifications.
        - certifications: List of certifications.
        - Any other sections supported by resume_writer.

Raises:
    HTTPException: If parsing fails due to invalid format or content, with status 422 and a descriptive message.

Notes:
    1. Log the start of the parsing process.
    2. Call parse_resume_to_writer_object to parse the Markdown content into a WriterResume object.
    3. Convert the WriterResume object to a dictionary using vars().
    4. Log successful completion.
    5. Return the dictionary representation.
    6. No disk, network, or database access is performed.

---

## function: `parse_resume_content(markdown_content: str) -> dict[str, Any]`

Parse Markdown resume content and return structured data as a dictionary.

Args:
    markdown_content (str): The Markdown content to parse, expected to follow a valid resume format.

Returns:
    dict: A dictionary containing the structured resume data, including:
        - personal: Personal information (e.g., name, email, phone).
        - experience: List of work experience entries.
        - education: List of educational qualifications.
        - certifications: List of certifications.
        - Any other sections supported by resume_writer.

Raises:
    HTTPException: If parsing fails due to invalid format or content, with status 400 and a descriptive message.

Notes:
    1. Log the start of the parsing process.
    2. Use the parse_resume function to parse the provided markdown_content.
    3. Return the result of parse_resume as a dictionary.
    4. Log successful completion.
    5. No disk, network, or database access is performed.

---

## function: `validate_resume_content(content: str) -> None`

Validate resume Markdown content for proper format.

Args:
    content (str): The Markdown content to validate, expected to be in a format compatible with resume_writer.

Returns:
    None: The function returns nothing if validation passes.

Raises:
    HTTPException: If parsing fails due to invalid format, with status 422 and a descriptive message.

Notes:
    1. Log the start of the validation process.
    2. Attempt to parse the provided content using the parse_resume function.
    3. If parsing fails, raise an HTTPException with a descriptive error message.
    4. Log successful completion if no exception is raised.
    5. No disk, network, or database access is performed.

---


===

===
# File: `./resume_editor/app/api/routes/route_logic/resume_serialization.py`

## function: `extract_personal_info(resume_content: str) -> PersonalInfoResponse`

Extract personal information from resume content.

Args:
    resume_content (str): The Markdown content of the resume to parse.

Returns:
    PersonalInfoResponse: Extracted personal information containing name, email, phone, location, and website.

Raises:
    ValueError: If parsing fails due to invalid or malformed resume content.

Notes:
    1. Splits the resume content into lines.
    2. Creates a ParseContext for parsing.
    3. Parses the resume using the resume_writer module.
    4. Retrieves the personal section from the parsed resume.
    5. Checks if contact information is present; if not, returns an empty response.
    6. Extracts contact info and websites from the parsed personal section.
    7. Maps the extracted data to the PersonalInfoResponse fields.
    8. Returns the populated response or an empty one if parsing fails.
    9. No network, disk, or database access is performed during this function.

---

## function: `extract_education_info(resume_content: str) -> EducationResponse`

Extract education information from resume content.

Args:
    resume_content (str): The Markdown content of the resume to parse.

Returns:
    EducationResponse: Extracted education information containing a list of degree entries.

Raises:
    ValueError: If parsing fails due to invalid or malformed resume content.

Notes:
    1. Splits the resume content into lines.
    2. Creates a ParseContext for parsing.
    3. Parses the resume using the resume_writer module.
    4. Retrieves the education section from the parsed resume.
    5. Checks if education data is present; if not, returns an empty response.
    6. Loops through each degree and extracts school, degree, major, start_date, end_date, and gpa.
    7. Maps each degree's fields into a dictionary.
    8. Returns a list of dictionaries wrapped in the EducationResponse model.
    9. If parsing fails, returns an empty response.
    10. No network, disk, or database access is performed during this function.

---

## function: `extract_experience_info(resume_content: str) -> ExperienceResponse`

Extract experience information from resume content.

Args:
    resume_content (str): The Markdown content of the resume to parse.

Returns:
    ExperienceResponse: Extracted experience information containing a list of roles and projects.

Raises:
    ValueError: If parsing fails due to invalid or malformed resume content.

Notes:
    1. Splits the resume content into lines.
    2. Creates a ParseContext for parsing.
    3. Parses the resume using the resume_writer module.
    4. Retrieves the experience section from the parsed resume.
    5. Checks if experience data is present; if not, returns an empty response.
    6. Loops through each role and extracts basics, summary, responsibilities and skills.
    7. Loops through each project and extracts overview, description, and skills.
    8. Maps the extracted data into a dictionary with nested structure.
    9. Returns a list of dictionaries wrapped in the ExperienceResponse model.
    10. If parsing fails, returns an empty response.
    11. No network, disk, or database access is performed during this function.

---

## function: `extract_certifications_info(resume_content: str) -> CertificationsResponse`

Extract certifications information from resume content.

Args:
    resume_content (str): The Markdown content of the resume to parse.

Returns:
    CertificationsResponse: Extracted certifications information containing a list of certifications.

Raises:
    ValueError: If parsing fails due to invalid or malformed resume content.

Notes:
    1. Splits the resume content into lines.
    2. Creates a ParseContext for parsing.
    3. Parses the resume using the resume_writer module.
    4. Retrieves the certifications section from the parsed resume.
    5. Checks if certifications data is present; if not, returns an empty response.
    6. Loops through each certification and extracts name, issuer, certification_id, issued, and expires.
    7. Maps the extracted data into a dictionary.
    8. Returns a list of dictionaries wrapped in the CertificationsResponse model.
    9. If parsing fails, returns an empty response.
    10. No network, disk, or database access is performed during this function.

---

## function: `serialize_personal_info_to_markdown(personal_info: UnknownType) -> str`

Serialize personal information to Markdown format.

Args:
    personal_info: Personal information to serialize, containing name, email, phone, location, and website.

Returns:
    str: Markdown formatted personal information section.

Notes:
    1. Initializes an empty list of lines and adds a heading.
    2. Adds each field (name, email, phone, location) as a direct field if present.
    3. Adds a Websites section if website is present.
    4. Joins the lines with newlines.
    5. Returns the formatted string with a trailing newline.
    6. Returns an empty string if no personal data is present.
    7. No network, disk, or database access is performed during this function.

---

## function: `serialize_education_to_markdown(education: UnknownType) -> str`

Serialize education information to Markdown format.

Args:
    education: Education information to serialize, containing a list of degree entries.

Returns:
    str: Markdown formatted education section.

Notes:
    1. Initializes an empty list of lines and adds a heading.
    2. For each degree in the list:
        a. Adds a subsection header.
        b. Adds each field (school, degree, major, start_date, end_date, gpa) as a direct field if present.
        c. Adds a blank line after each degree.
    3. Joins the lines with newlines.
    4. Returns the formatted string with a trailing newline.
    5. No network, disk, or database access is performed during this function.

---

## function: `_serialize_project_to_markdown(project: UnknownType) -> list[str]`

Serialize a single project to markdown lines.

Args:
    project: A project object to serialize.

Returns:
    list[str]: A list of markdown lines representing the project.

Notes:
    1. Gets the overview from the project.
    2. Checks if the inclusion status is OMIT; if so, returns an empty list.
    3. Builds the overview content with title, URL, URL description, start date, and end date.
    4. Adds the overview section to the project content.
    5. If the inclusion status is not NOT_RELEVANT:
        a. Adds the description if present.
        b. Adds the skills if present.
    6. Returns the full project content as a list of lines.

---

## function: `_serialize_role_to_markdown(role: UnknownType) -> list[str]`

Serialize a single role to markdown lines.

Args:
    role: A role object to serialize.

Returns:
    list[str]: A list of markdown lines representing the role.

Notes:
    1. Gets the basics from the role.
    2. Checks if the inclusion status is OMIT; if so, returns an empty list.
    3. Builds the basics content with company, title, employment type, job category, agency name, start date, end date, reason for change, and location.
    4. Adds the basics section to the role content.
    5. If the inclusion status is not NOT_RELEVANT:
        a. Adds the summary if present.
        b. Adds the responsibilities if present.
        c. Adds the skills if present.
    6. Returns the full role content as a list of lines.

---

## function: `serialize_experience_to_markdown(experience: UnknownType) -> str`

Serialize experience information to Markdown format.

Args:
    experience: Experience information to serialize, containing a list of roles.

Returns:
    str: Markdown formatted experience section.

Notes:
    1. Checks if the experience list is empty.
    2. Initializes an empty list of lines and adds a heading.
    3. For each role in the list:
        a. Adds a subsection header.
        b. Adds each field (company, title, start_date, end_date, location, description) using proper subsection structure.
        c. Adds a blank line after each role.
    4. Joins the lines with newlines.
    5. Returns the formatted string with a trailing newline.
    6. Returns an empty string if no experience data is present or all is filtered out.
    7. No network, disk, or database access is performed during this function.

---

## function: `serialize_certifications_to_markdown(certifications: UnknownType) -> str`

Serialize certifications information to Markdown format.

Args:
    certifications: Certifications information to serialize, containing a list of certifications.

Returns:
    str: Markdown formatted certifications section.

Notes:
    1. Initializes an empty list of lines and adds a heading.
    2. For each certification in the list:
        a. Adds a subsection header.
        b. Adds each field (name, issuer, id, issued_date, expiry_date) as direct fields if present.
        c. Adds a blank line after each certification.
    3. Joins the lines with newlines.
    4. Returns the formatted string with a trailing newline.
    5. No network, disk, or database access is performed during this function.

---

## function: `update_resume_content_with_structured_data(current_content: str, personal_info: UnknownType, education: UnknownType, certifications: UnknownType, experience: UnknownType) -> str`

Update resume content with structured data by replacing specific sections.

Args:
    current_content (str): Current resume Markdown content to update.
    personal_info: Updated personal information to insert. If None, the existing info is preserved.
    education: Updated education information to insert. If None, the existing info is preserved.
    certifications: Updated certifications information to insert. If None, the existing info is preserved.
    experience: Updated experience information to insert. If None, the existing info is preserved.

Returns:
    str: Updated resume content with new structured data.

Notes:
    1. Extracts existing sections from `current_content` if they are not provided as arguments.
    2. reconstructs the full resume using the combination of new and existing data.

---


===

===
# File: `./resume_editor/app/utils/__init__.py`


===

===
# File: `./resume_editor/app/core/__init__.py`


===

===
# File: `./resume_editor/app/core/config.py`

## function: `get_settings() -> Settings`

Get the global settings instance.

This function returns a singleton instance of the Settings class,
which contains all application configuration values.

Args:
    None: This function does not take any arguments.

Returns:
    Settings: The global settings instance, containing all configuration values.
        The instance is created by loading environment variables and applying defaults.

Raises:
    ValidationError: If required environment variables are missing or invalid.
    ValueError: If the .env file cannot be read or parsed.

Notes:
    1. Reads configuration from environment variables using the .env file.
    2. If environment variables are not set, default values are used.
    3. The Settings class uses Pydantic's validation and configuration features to ensure correct values.
    4. The function returns a cached instance to avoid repeated parsing of the .env file.
    5. This function performs disk access to read the .env file at startup.
    6. If the .env file is missing or cannot be read, a ValidationError may be raised.
    7. The function may raise a ValueError if required environment variables are not provided and no default is available.

---

## `Settings` class

Application settings loaded from environment variables.

This class defines all configuration values used by the application,
including database connection details, security parameters, and API keys.
Values are loaded from environment variables with fallback defaults.

Attributes:
    database_url (PostgresDsn): Database connection URL for PostgreSQL.
        This is used to establish connection to the application's database.
    secret_key (str): Secret key for signing JWT tokens.
        Must be kept secure and changed in production.
    algorithm (str): Algorithm used for JWT token encoding.
        Currently uses HS256 (HMAC-SHA256).
    access_token_expire_minutes (int): Duration in minutes for which access tokens remain valid.
    llm_api_key (str | None): API key for accessing LLM services.
        Optional; used when LLM functionality is needed.
    encryption_key (str): Key used for encrypting sensitive data.

---
## method: `Settings.database_url(self: UnknownType) -> PostgresDsn`

Assembled database URL from components.

Args:
    None: This property does not take any arguments.

Returns:
    PostgresDsn: The fully assembled PostgreSQL connection URL.

Notes:
    1. Constructs the database URL using the components: scheme, username, password, host, port, and path.
    2. The scheme is set to "postgresql".
    3. The username, password, host, port, and database name are retrieved from the instance attributes.
    4. The resulting URL is returned as a PostgresDsn object.
    5. This function performs disk access to read the .env file at startup.

---

===

===
# File: `./resume_editor/app/core/security.py`

## function: `create_access_token(data: dict, settings: Settings, expires_delta: timedelta | None, impersonator: str | None) -> str`

Create a JWT access token.

Args:
    data (dict): The data to encode in the token (e.g., user ID, role).
    settings (Settings): The application settings object.
    expires_delta (Optional[timedelta]): Custom expiration time for the token. If None, uses default value.
    impersonator (str | None): The username of the administrator impersonating the user.

Returns:
    str: The encoded JWT token as a string.

Notes:
    1. Copy the data to avoid modifying the original.
    2. If an impersonator is specified, add it to the token claims.
    3. Set expiration time based on expires_delta or default.
    4. Encode the data with the secret key and algorithm.
    5. No database or network access in this function.

---

## function: `verify_password(plain_password: str, hashed_password: str) -> bool`

Verify a plain password against a hashed password.

Args:
    plain_password (str): The plain text password to verify.
    hashed_password (str): The hashed password to compare against.

Returns:
    bool: True if the password matches, False otherwise.

Notes:
    1. Use bcrypt to verify the password.
    2. No database or network access in this function.

---

## function: `get_password_hash(password: str) -> str`

Hash a plain password.

Args:
    password (str): The plain text password to hash.

Returns:
    str: The hashed password.

Notes:
    1. Use bcrypt to hash the password.
    2. No database or network access in this function.

---

## function: `authenticate_user(db: Session, username: str, password: str) -> Optional['User']`

Authenticate a user by username and password.

Args:
    db (Session): Database session used to query for user records.
    username (str): Username to authenticate.
    password (str): Password to verify.

Returns:
    Optional[User]: The authenticated user if successful, None otherwise.

Notes:
    1. Query the database for a user with the given username.
    2. If user exists and password is correct, return the user.
    3. Otherwise, return None.

---

## function: `encrypt_data(data: str) -> str`

Encrypts data using Fernet symmetric encryption.

Args:
    data (str): The plaintext data to encrypt.

Returns:
    str: The encrypted data, encoded as a string.

Notes:
    1. Use Fernet to encrypt the data.
    2. No database or network access in this function.

---

## function: `decrypt_data(encrypted_data: str) -> str`

Decrypts data using Fernet symmetric encryption.

Args:
    encrypted_data (str): The encrypted data to decrypt.

Returns:
    str: The decrypted plaintext data.

Notes:
    1. Use Fernet to decrypt the data.
    2. No database or network access in this function.

---


===

===
# File: `./resume_editor/app/core/auth.py`

## function: `get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session) -> User`

Retrieve the authenticated user from the provided JWT token.

Args:
    token: JWT token extracted from the request header, used to authenticate the user.
        Type: str
        Purpose: The JWT token that contains the user's identity and is used for authentication.
    db: Database session dependency used to query the database for the user.
        Type: Session
        Purpose: Provides a connection to the database to retrieve the user record by username.

Returns:
    User: The authenticated User object corresponding to the token's subject (username).
        Type: User
        Purpose: Returns the user object if authentication is successful.

Raises:
    HTTPException: Raised when the credentials are invalid or the user is not found.
        Status Code: 401 UNAUTHORIZED
        Detail: "Could not validate credentials"
        Headers: {"WWW-Authenticate": "Bearer"}

Notes:
    1. Initialize an HTTP 401 exception with a generic error message and "Bearer" authentication header.
    2. Decode the JWT token using the secret key and algorithm to extract the subject (username).
    3. If the subject (username) is missing from the token payload, raise the credentials exception.
    4. If the JWT token is invalid or malformed, catch the JWTError and raise the credentials exception.
    5. Query the database using the retrieved username to find the corresponding User record.
    6. If the user is not found in the database, raise the credentials exception.
    7. Return the User object if all authentication checks pass.

Database Access:
    - Queries the User table to retrieve a user record by username.

---

## function: `get_current_admin_user(current_user: Annotated[User, Depends(get_current_user)]) -> User`

Verify that the current user has administrator privileges.

This dependency relies on `get_current_user` to retrieve the authenticated user.
It then checks the user's roles to determine if they are an administrator.

Args:
    current_user (User): The user object obtained from the `get_current_user`
        dependency.

Returns:
    User: The user object if the user has the 'admin' role.

Raises:
    HTTPException: A 403 Forbidden error if the user is not an admin.

Notes:
    1. Retrieves user from `get_current_user` dependency.
    2. Iterates through the user's roles.
    3. If a role with the name 'admin' is found, returns the user object.
    4. If no 'admin' role is found, raises an HTTPException with status 403.

---


===

===
# File: `./resume_editor/app/database/__init__.py`


===

===
# File: `./resume_editor/app/database/database.py`

## function: `get_engine() -> UnknownType`

Get or create the database engine.

Args:
    None

Returns:
    Engine: The SQLAlchemy engine instance used to connect to the database.

Notes:
    1. Create the engine only when first accessed to avoid premature connection.
    2. Reuse the same engine instance on subsequent calls to ensure consistency.
    3. Network access occurs when creating the engine, using the database URL from settings.

---

## function: `get_session_local() -> UnknownType`

Get or create the session local factory.

Args:
    None

Returns:
    sessionmaker: The SQLAlchemy sessionmaker instance used to create database sessions.

Notes:
    1. Create the sessionmaker only when first accessed to avoid premature configuration.
    2. Reuse the same sessionmaker instance on subsequent calls to ensure consistent session behavior.
    3. No network access in this function itself; it uses the previously created engine.

---

## function: `get_db() -> Generator[Session, None, None]`

Dependency to provide database sessions to route handlers.

Args:
    None

Yields:
    Session: A database session for use in route handlers.

Notes:
    1. Create a new database session using the sessionmaker factory.
    2. Yield the session to be used in route handlers.
    3. Ensure the session is closed after use to release resources.
    4. No network access in this function itself; the session is created from the existing engine.

---


===

===
# File: `./resume_editor/app/models/__init__.py`


===

===
# File: `./resume_editor/app/models/user.py`

## `User` class

User model for authentication and session management.

Attributes:
    id (int): Unique identifier for the user.
    username (str): Unique username for the user.
    email (str): Unique email address for the user.
    hashed_password (str): Hashed password for the user.
    is_active (bool): Whether the user account is active.
    attributes (dict): Flexible key-value store for user-specific attributes.
    roles (list[Role]): Roles assigned to the user for authorization.
    resumes (list[Resume]): Resumes associated with the user.
    settings (UserSettings): User-specific settings.

---
## method: `User.__init__(self: UnknownType, username: str, email: str, hashed_password: str, is_active: bool, attributes: dict[str, Any] | None) -> UnknownType`

Initialize a User instance.

Args:
    username (str): Unique username for the user. Must be a non-empty string.
    email (str): Unique email address for the user. Must be a non-empty string.
    hashed_password (str): Hashed password for the user. Must be a non-empty string.
    is_active (bool): Whether the user account is active. Must be a boolean.
    attributes (dict | None): Flexible key-value attributes for the user.

Returns:
    None

Notes:
    1. Validate that username is a non-empty string.
    2. Validate that email is a non-empty string.
    3. Validate that hashed_password is a non-empty string.
    4. Validate that is_active is a boolean.
    5. Validate that attributes is a dict or None.
    6. Assign all values to instance attributes.
    7. Log the initialization of the user with their username.
    8. This operation does not involve network, disk, or database access.

---
## method: `User.validate_username(self: UnknownType, key: UnknownType, username: UnknownType) -> UnknownType`

Validate the username field.

Args:
    key (str): The field name being validated (should be 'username').
    username (str): The username value to validate. Must be a non-empty string.

Returns:
    str: The validated username (stripped of leading/trailing whitespace).

Notes:
    1. Ensure username is a string.
    2. Ensure username is not empty after stripping whitespace.
    3. This operation does not involve network, disk, or database access.

---
## method: `User.validate_email(self: UnknownType, key: UnknownType, email: UnknownType) -> UnknownType`

Validate the email field.

Args:
    key (str): The field name being validated (should be 'email').
    email (str): The email value to validate. Must be a non-empty string.

Returns:
    str: The validated email (stripped of leading/trailing whitespace).

Notes:
    1. Ensure email is a string.
    2. Ensure email is not empty after stripping whitespace.
    3. This operation does not involve network, disk, or database access.

---
## method: `User.validate_hashed_password(self: UnknownType, key: UnknownType, hashed_password: UnknownType) -> UnknownType`

Validate the hashed_password field.

Args:
    key (str): The field name being validated (should be 'hashed_password').
    hashed_password (str): The hashed password value to validate. Must be a non-empty string.

Returns:
    str: The validated hashed password (stripped of leading/trailing whitespace).

Notes:
    1. Ensure hashed_password is a string.
    2. Ensure hashed_password is not empty after stripping whitespace.
    3. This operation does not involve network, disk, or database access.

---
## method: `User.validate_is_active(self: UnknownType, key: UnknownType, is_active: UnknownType) -> UnknownType`

Validate the is_active field.

Args:
    key (str): The field name being validated (should be 'is_active').
    is_active (bool): The is_active value to validate. Must be a boolean.

Returns:
    bool: The validated is_active value.

Notes:
    1. Ensure is_active is a boolean.
    2. This operation does not involve network, disk, or database access.

---
## method: `User.validate_attributes(self: UnknownType, key: UnknownType, attributes: UnknownType) -> UnknownType`

Validate the attributes field.

Args:
    key (str): The field name being validated (should be 'attributes').
    attributes (dict | None): The attributes value to validate. Must be a dictionary or None.

Returns:
    dict | None: The validated attributes.

Notes:
    1. If attributes is not None, ensure it is a dictionary.
    2. This operation does not involve network, disk, or database access.

---

===

===
# File: `./resume_editor/app/models/user_settings.py`

## `UserSettings` class

Stores user-specific settings, such as LLM configurations.

Attributes:
    id (int): Primary key.
    user_id (int): Foreign key to the user.
    llm_endpoint (str | None): Custom LLM API endpoint URL.
    encrypted_api_key (str | None): Encrypted API key for the LLM service.
    user (User): Relationship to the User model.

---
## method: `UserSettings.__init__(self: UnknownType, user_id: int, llm_endpoint: str | None, encrypted_api_key: str | None) -> UnknownType`

Initialize a UserSettings instance.

Args:
    user_id (int): The ID of the user these settings belong to.
    llm_endpoint (str | None): Custom LLM API endpoint URL.
    encrypted_api_key (str | None): Encrypted API key for the LLM service.

Returns:
    None

Notes:
    1. Assign all values to instance attributes.
    2. Log the initialization of the user settings.
    3. This operation does not involve network, disk, or database access.

---

===

===
# File: `./resume_editor/app/models/resume_model.py`

## `Resume` class

Resume model for storing user resumes.

Attributes:
    id (int): Unique identifier for the resume.
    user_id (int): Foreign key to User model, identifying the user who owns the resume.
    name (str): User-assigned descriptive name for the resume, must be non-empty.
    content (str): The Markdown text content of the resume, must be non-empty.
    created_at (datetime): Timestamp when the resume was created.
    updated_at (datetime): Timestamp when the resume was last updated.
    is_active (bool): Whether the resume is currently active.

---
## method: `Resume.__init__(self: UnknownType, user_id: int, name: str, content: str, is_active: bool) -> UnknownType`

Initialize a Resume instance.

Args:
    user_id (int): The unique identifier of the user who owns the resume.
    name (str): A descriptive name assigned by the user for the resume; must be non-empty.
    content (str): The Markdown-formatted text content of the resume; must be non-empty.
    is_active (bool): A flag indicating whether the resume is currently active; defaults to True.

Returns:
    None

Raises:
    ValueError: If user_id is not an integer, name is empty, content is empty, or is_active is not a boolean.

Notes:
    1. Validate that user_id is an integer.
    2. Validate that name is a non-empty string.
    3. Validate that content is a non-empty string.
    4. Validate that is_active is a boolean.
    5. Assign all values to instance attributes.
    6. Log the initialization of the resume with its name.
    7. This function performs no database access.

---

===

===
# File: `./resume_editor/app/models/role.py`


===

===
# File: `./resume_editor/app/models/resume/resume.py`


===

===
# File: `./resume_editor/app/models/resume/education.py`

## `Degree` class

Represents details of a specific academic degree earned.

Attributes:
    school (str): The name of the educational institution.
    degree (str | None): The type of degree (e.g., Bachelor, Master).
    start_date (datetime | None): The start date of the program.
    end_date (datetime | None): The end date of the program.
    major (str | None): The major field of study.
    gpa (str | None): The grade point average.

---
## method: `Degree.validate_school(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the school field.

Args:
    v (str): The school value to validate. Must be a non-empty string.

Returns:
    str: The validated school (stripped of leading/trailing whitespace).

Raises:
    ValueError: If the school is empty or contains only whitespace.

Notes:
    1. Ensure school is a string.
    2. Ensure school is not empty after stripping whitespace.

---
## method: `Degree.validate_degree(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the degree field.

Args:
    v (str | None): The degree value to validate. Must be a non-empty string or None.

Returns:
    str | None: The validated degree (stripped of leading/trailing whitespace) or None.

Raises:
    ValueError: If the degree is empty after stripping whitespace.

Notes:
    1. Ensure degree is a string or None.
    2. Ensure degree is not empty after stripping whitespace.

---
## method: `Degree.validate_major(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the major field.

Args:
    v (str | None): The major value to validate. Must be a non-empty string or None.

Returns:
    str | None: The validated major (stripped of leading/trailing whitespace) or None.

Raises:
    ValueError: If the major is empty after stripping whitespace.

Notes:
    1. Ensure major is a string or None.
    2. Ensure major is not empty after stripping whitespace.

---
## method: `Degree.validate_gpa(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the gpa field.

Args:
    v (str | None): The gpa value to validate. Must be a non-empty string or None.

Returns:
    str | None: The validated gpa (stripped of leading/trailing whitespace) or None.

Raises:
    ValueError: If the gpa is empty after stripping whitespace.

Notes:
    1. Ensure gpa is a string or None.
    2. Ensure gpa is not empty after stripping whitespace.

---
## method: `Degree.validate_end_date(cls: UnknownType, v: UnknownType, info: UnknownType) -> UnknownType`

Validate that start_date is not after end_date.

Args:
    v (datetime | None): The end_date value to validate.
    info (ValidationInfo): Validation info containing data.

Returns:
    datetime | None: The validated end_date.

Raises:
    ValueError: If end_date is before start_date.

Notes:
    1. If both start_date and end_date are provided, ensure start_date is not after end_date.

---
## `Degrees` class

Represents a collection of academic degrees earned.

Attributes:
    degrees (list[Degree]): A list of Degree objects representing educational achievements.

---
## method: `Degrees.__iter__(self: UnknownType) -> UnknownType`

Iterate over the degrees.

Returns:
    Iterator: An iterator over the degrees list.

Notes:
    No external access (network, disk, or database) is performed.

---
## method: `Degrees.__len__(self: UnknownType) -> UnknownType`

Return the number of degrees.

Returns:
    int: The number of degrees in the list.

Notes:
    No external access (network, disk, or database) is performed.

---
## method: `Degrees.__getitem__(self: UnknownType, index: UnknownType) -> UnknownType`

Return the degree at the given index.

Args:
    index (int): The index of the degree to retrieve.

Returns:
    Degree: The Degree object at the specified index.

Notes:
    No external access (network, disk, or database) is performed.

---

===

===
# File: `./resume_editor/app/models/resume/certifications.py`

## `Certification` class

Represents a professional certification.

Attributes:
    name (str): The name of the certification.
    issuer (str | None): The organization that issued the certification.
    issued (datetime | None): The date the certification was issued.
    expires (datetime | None): The date the certification expires.
    certification_id (str | None): An identifier for the certification.

---
## method: `Certification.validate_name(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the name field.

Args:
    v (str): The name value to validate. Must be a non-empty string.

Returns:
    str: The validated name, stripped of leading/trailing whitespace.

Raises:
    ValueError: If the name is not a string or is empty.

Notes:
    1. Ensure name is a string.
    2. Ensure name is not empty.

---
## method: `Certification.validate_optional_strings(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate optional string fields.

Args:
    v (str | None): The field value to validate. Must be a string or None.

Returns:
    str | None: The validated field value.

Raises:
    ValueError: If the field is neither a string nor None.

Notes:
    1. Ensure field is a string or None.

---
## method: `Certification.validate_dates(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the date fields.

Args:
    v (datetime | None): The date value to validate. Must be a datetime object or None.

Returns:
    datetime | None: The validated date.

Raises:
    ValueError: If the date is neither a datetime object nor None.

Notes:
    1. Ensure date is a datetime object or None.

---
## method: `Certification.validate_date_order(self: UnknownType) -> UnknownType`

Validate that issued date is not after expires date.

Returns:
    Certification: The validated model instance.

Raises:
    ValueError: If expires date is before issued date.

Notes:
    1. If both issued and expires dates are provided, ensure issued is not after expires.

---
## `Certifications` class

Represents a collection of professional certifications.

Attributes:
    certifications (list[Certification]): A list of Certification objects.

---
## method: `Certifications.validate_certifications(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the certifications field.

Args:
    v (list[Certification]): The certifications value to validate. Must be a list of Certification objects.

Returns:
    list[Certification]: The validated certifications list.

Raises:
    ValueError: If certifications is not a list or contains non-Certification items.

Notes:
    1. Ensure certifications is a list.
    2. Ensure all items in certifications are instances of Certification.

---
## method: `Certifications.__iter__(self: UnknownType) -> UnknownType`

Iterate over the certifications.

Returns:
    An iterator over the list of certification objects.

Notes:
    1. Return an iterator over the certifications list.

---
## method: `Certifications.__len__(self: UnknownType) -> UnknownType`

Return the number of certifications.

Returns:
    int: The integer count of certifications in the list.

Notes:
    1. Return the length of the certifications list.

---
## method: `Certifications.__getitem__(self: UnknownType, index: UnknownType) -> UnknownType`

Return the certification at the given index.

Args:
    index (int): The index of the certification to retrieve.

Returns:
    Certification: The Certification object at the specified index.

Notes:
    1. Retrieve and return the certification at the given index.

---
## method: `Certifications.list_class(self: UnknownType) -> UnknownType`

Return the type that will be contained in the list.

Returns:
    type: The Certification class.

Notes:
    1. Return the Certification class.

---

===

===
# File: `./resume_editor/app/models/resume/personal.py`

## `ContactInfo` class

Holds personal contact details such as name, email, phone, and location.

Attributes:
    name (str): The full name of the person.
    email (str | None): The email address of the person, or None if not provided.
    phone (str | None): The phone number of the person, or None if not provided.
    location (str | None): The physical location (e.g., city and country) of the person, or None if not provided.

---
## method: `ContactInfo.validate_name(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the name field.

Args:
    v: The name value to validate. Must be a non-empty string.

Returns:
    str: The validated name (stripped of leading/trailing whitespace).

Raises:
    ValueError: If the name is not a string or is empty after stripping whitespace.

Notes:
    1. Ensure name is a string.
    2. Ensure name is not empty after stripping whitespace.

---
## method: `ContactInfo.validate_email(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the email field.

Args:
    v: The email value to validate. Must be a non-empty string or None.

Returns:
    str: The validated email (stripped of leading/trailing whitespace).

Raises:
    ValueError: If the email is not a string or is empty after stripping whitespace.

Notes:
    1. Ensure email is a string or None.
    2. Ensure email is not empty after stripping whitespace.

---
## method: `ContactInfo.validate_phone(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the phone field.

Args:
    v: The phone value to validate. Must be a non-empty string or None.

Returns:
    str: The validated phone (stripped of leading/trailing whitespace).

Raises:
    ValueError: If the phone is not a string or is empty after stripping whitespace.

Notes:
    1. Ensure phone is a string or None.
    2. Ensure phone is not empty after stripping whitespace.

---
## method: `ContactInfo.validate_location(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the location field.

Args:
    v: The location value to validate. Must be a non-empty string or None.

Returns:
    str: The validated location (stripped of leading/trailing whitespace).

Raises:
    ValueError: If the location is not a string or is empty after stripping whitespace.

Notes:
    1. Ensure location is a string or None.
    2. Ensure location is not empty after stripping whitespace.

---
## `Websites` class

Holds personal website and social media links.

Attributes:
    website (str | None): The personal website URL, or None if not provided.
    github (str | None): The GitHub profile URL, or None if not provided.
    linkedin (str | None): The LinkedIn profile URL, or None if not provided.
    twitter (str | None): The Twitter profile URL, or None if not provided.

---
## method: `Websites.validate_website(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the website field.

Args:
    v: The website value to validate. Must be a non-empty string or None.

Returns:
    str: The validated website (stripped of leading/trailing whitespace).

Raises:
    ValueError: If the website is not a string or is empty after stripping whitespace.

Notes:
    1. Ensure website is a string or None.
    2. Ensure website is not empty after stripping whitespace.

---
## method: `Websites.validate_github(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the github field.

Args:
    v: The github value to validate. Must be a non-empty string or None.

Returns:
    str: The validated github (stripped of leading/trailing whitespace).

Raises:
    ValueError: If the github is not a string or is empty after stripping whitespace.

Notes:
    1. Ensure github is a string or None.
    2. Ensure github is not empty after stripping whitespace.

---
## method: `Websites.validate_linkedin(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the linkedin field.

Args:
    v: The linkedin value to validate. Must be a non-empty string or None.

Returns:
    str: The validated linkedin (stripped of leading/trailing whitespace).

Raises:
    ValueError: If the linkedin is not a string or is empty after stripping whitespace.

Notes:
    1. Ensure linkedin is a string or None.
    2. Ensure linkedin is not empty after stripping whitespace.

---
## method: `Websites.validate_twitter(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the twitter field.

Args:
    v: The twitter value to validate. Must be a non-empty string or None.

Returns:
    str: The validated twitter (stripped of leading/trailing whitespace).

Raises:
    ValueError: If the twitter is not a string or is empty after stripping whitespace.

Notes:
    1. Ensure twitter is a string or None.
    2. Ensure twitter is not empty after stripping whitespace.

---
## `VisaStatus` class

Holds information about work authorization and sponsorship requirements.

Attributes:
    work_authorization (str | None): The current work authorization status (e.g., "US Citizen", "H-1B"), or None if not provided.
    require_sponsorship (bool | None): A boolean indicating if sponsorship is required, or None if not provided.

---
## method: `VisaStatus.validate_work_authorization(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the work_authorization field.

Args:
    v: The work_authorization value to validate. Must be a non-empty string or None.

Returns:
    str: The validated work_authorization (stripped of leading/trailing whitespace).

Raises:
    ValueError: If the work_authorization is not a string or is empty after stripping whitespace.

Notes:
    1. Ensure work_authorization is a string or None.
    2. Ensure work_authorization is not empty after stripping whitespace.

---
## method: `VisaStatus.validate_require_sponsorship(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the require_sponsorship field.

Args:
    v: The require_sponsorship value to validate. Must be a boolean, string ("yes"/"no"), or None.

Returns:
    bool: The validated require_sponsorship value.

Raises:
    ValueError: If the require_sponsorship is not a boolean, string, or None, or if the string is not "yes" or "no".

Notes:
    1. Ensure require_sponsorship is a boolean, string ("yes"/"no"), or None.
    2. If require_sponsorship is a string, convert "yes" to True and "no" to False.
    3. If require_sponsorship is not None and not a string, assign it directly.
    4. Otherwise, set require_sponsorship to None.

---
## `Banner` class

Holds a personal banner message with cleaned text content.

Attributes:
    text (str): The cleaned text content of the banner, with leading/trailing and internal blank lines removed.

---
## method: `Banner.validate_text(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the text field and clean it.

Args:
    v: The raw text content of the banner, potentially including leading/trailing or internal blank lines.

Returns:
    str: The cleaned text content of the banner.

Raises:
    ValueError: If the text is not a string.

Notes:
    1. Ensure text is a string.
    2. Split the input text into lines.
    3. Remove leading blank lines.
    4. Remove trailing blank lines.
    5. Filter out any lines that are blank after stripping whitespace.
    6. Join the remaining lines back into a single string.

---
## `Note` class

Holds a personal note with cleaned text content.

Attributes:
    text (str): The cleaned text content of the note, with leading/trailing and internal blank lines removed.

---
## method: `Note.validate_text(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the text field and clean it.

Args:
    v: The raw text content of the note, potentially including leading/trailing or internal blank lines.

Returns:
    str: The cleaned text content of the note.

Raises:
    ValueError: If the text is not a string.

Notes:
    1. Ensure text is a string.
    2. Split the input text into lines.
    3. Remove leading blank lines.
    4. Remove trailing blank lines.
    5. Filter out any lines that are blank after stripping whitespace.
    6. Join the remaining lines back into a single string.

---

===

===
# File: `./resume_editor/app/models/resume/__init__.py`


===

===
# File: `./resume_editor/app/models/resume/experience.py`

## `RoleSkills` class

Represents skills used in a professional role.

Attributes:
    skills (list[str]): A list of non-empty, stripped skill strings.

---
## method: `RoleSkills.validate_skills(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the skills field.

Args:
    v: The skills value to validate. Must be a list of strings.

Returns:
    list[str]: The validated and cleaned skills list.

Notes:
    1. Ensure skills is a list.
    2. Ensure all items in skills are strings.
    3. Strip whitespace from each skill and filter out empty strings.
    4. Raise a ValueError if skills is not a list or if any skill is not a string.
    5. Return the cleaned list of non-empty skills.

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
## method: `RoleSkills.__getitem__(self: UnknownType, index: UnknownType) -> UnknownType`

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
    inclusion_status (InclusionStatus): The inclusion status of the role.

---
## method: `RoleBasics.validate_company(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the company field.

Args:
    v: The company value to validate. Must be a non-empty string.

Returns:
    str: The validated company.

Raises:
    ValueError: If company is not a string or is empty.

Notes:
    1. Ensure company is a string.
    2. Ensure company is not empty.
    3. Strip whitespace from the company name.
    4. Raise a ValueError if company is not a string or is empty.

---
## method: `RoleBasics.validate_title(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the title field.

Args:
    v: The title value to validate. Must be a non-empty string.

Returns:
    str: The validated title.

Raises:
    ValueError: If title is not a string or is empty.

Notes:
    1. Ensure title is a string.
    2. Ensure title is not empty.
    3. Strip whitespace from the title.
    4. Raise a ValueError if title is not a string or is empty.

---
## method: `RoleBasics.validate_end_date(cls: UnknownType, v: UnknownType, info: UnknownType) -> UnknownType`

Validate the end_date field.

Args:
    v: The end_date value to validate. Must be a datetime object or None.
    info: Validation info containing data.

Returns:
    datetime: The validated end_date.

Raises:
    ValueError: If end_date is not a datetime object or None, or if end_date is before start_date.

Notes:
    1. Ensure end_date is a datetime object or None.
    2. If end_date is provided, ensure it is not before start_date.
    3. Raise a ValueError if end_date is not a datetime object or None, or if end_date is before start_date.

---
## `Roles` class

Represents a collection of professional roles.

Attributes:
    roles (list[Role]): A list of Role objects.

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
## method: `Roles.__getitem__(self: UnknownType, index: UnknownType) -> UnknownType`

Return the role at the given index.

Args:
    index (int): The index of the role to return.

Returns:
    Role: The role at the specified index.

---
## method: `Roles.list_class(self: UnknownType) -> UnknownType`

Return the class for the list.

Returns:
    The Role class.

---
## `ProjectSkills` class

Represents skills used in a project.

Attributes:
    skills (list[str]): A list of non-empty, stripped skill strings.

---
## method: `ProjectSkills.validate_skills(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the skills field.

Args:
    v: The skills value to validate. Must be a list of strings.

Returns:
    list[str]: The validated and cleaned skills list.

Raises:
    ValueError: If skills is not a list or if any skill is not a string.

Notes:
    1. Ensure skills is a list.
    2. Ensure all items in skills are strings.
    3. Strip whitespace from each skill and filter out empty strings.
    4. Raise a ValueError if skills is not a list or if any skill is not a string.
    5. Return the cleaned list of non-empty skills.

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
## method: `ProjectSkills.__getitem__(self: UnknownType, index: UnknownType) -> UnknownType`

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
    inclusion_status (InclusionStatus): The inclusion status of the project.

---
## method: `ProjectOverview.validate_title(cls: UnknownType, v: UnknownType) -> UnknownType`

Validate the title field.

Args:
    v: The title value to validate. Must be a non-empty string.

Returns:
    str: The validated title.

Raises:
    ValueError: If title is not a string or is empty.

Notes:
    1. Ensure title is a string.
    2. Ensure title is not empty.
    3. Strip whitespace from the title.
    4. Raise a ValueError if title is not a string or is empty.

---
## method: `ProjectOverview.validate_date_order(cls: UnknownType, v: UnknownType, info: UnknownType) -> UnknownType`

Validate that start_date is not after end_date.

Args:
    v: The end_date value to validate.
    info: Validation info containing data.

Returns:
    datetime: The validated end_date.

Raises:
    ValueError: If end_date is before start_date.

Notes:
    1. If both start_date and end_date are provided, ensure start_date is not after end_date.
    2. Raise a ValueError if end_date is before start_date.

---
## `Projects` class

Represents a collection of projects.

Attributes:
    projects (list[Project]): A list of Project objects.

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
## method: `Projects.__getitem__(self: UnknownType, index: UnknownType) -> UnknownType`

Return the project at the given index.

Args:
    index (int): The index of the project to return.

Returns:
    Project: The project at the specified index.

---
## method: `Projects.list_class(self: UnknownType) -> UnknownType`

Return the class of the list.

Returns:
    The Project class.

---

===

===
# File: `./resume_editor/app/schemas/user.py`


===

===
# File: `./resume_editor/app/schemas/__init__.py`


===

===
# File: `./resume_editor/app/schemas/llm.py`


===

===
# File: `resume_editor/app/__init__.py`


===

===
# File: `resume_editor/app/main.py`

## function: `create_app() -> FastAPI`

Create and configure the FastAPI application.

Args:
    None

Returns:
    FastAPI: The configured FastAPI application instance.

Notes:
    1. Initialize the FastAPI application with the title "Resume Editor API".
    2. Add CORS middleware to allow requests from any origin (for development only).
    3. Include the user router to handle user-related API endpoints.
    4. Include the resume router to handle resume-related API endpoints.
    5. Include the admin router to handle administrative API endpoints.
    6. Define a health check endpoint at "/health" that returns a JSON object with status "ok".
    7. Add static file serving for CSS/JS assets.
    8. Add template rendering for HTML pages.
    9. Define dashboard routes for the HTMX-based interface.
    10. Log a success message indicating the application was created.

---

## function: `initialize_database() -> None`

Initialize the database.

Args:
    None

Returns:
    None

Notes:
    1. Database initialization is now handled by Alembic migrations.
    2. This function is kept for structural consistency but performs no actions.

---


===

===
# File: `resume_editor/app/api/__init__.py`

## function: `get_app() -> FastAPI`

Creates and configures the FastAPI application instance.

This function initializes a FastAPI app with the following features:
- Includes the authentication and resume management routes.
- Configures middleware for logging and error handling.
- Sets up CORS to allow frontend access from different origins.

Args:
    None.

Returns:
    FastAPI: A configured FastAPI application instance.

Raises:
    None.

Notes:
    1. The application is initialized with a title, version, and description.
    2. Routes are included from the main application setup.
    3. CORS is enabled with allow_origins set to allow requests from 'http://localhost:3000'.
    4. The middleware stack includes logging and exception handling.
    5. The database session is provided via dependency injection through the 'get_db' function.
    6. The function performs no disk or network I/O.
    7. The function does not perform any database access.

---


===

===
# File: `resume_editor/app/api/routes/resume.py`

## `UpdateResumeForm` class

Represents the form data for updating a resume.

---
## method: `UpdateResumeForm.__init__(self: UnknownType, name: str, content: str | None, from_editor: str | None, sort_by: ResumeSortBy | None) -> UnknownType`

Initializes the form data.

Args:
    name (str): The new name for the resume.
    content (str | None): The new content for the resume.
    from_editor (str | None): Flag indicating if the update is from the editor.
    sort_by (ResumeSortBy | None): The sorting criteria.

---

===

===
# File: `resume_editor/app/api/routes/user.py`

## function: `get_user_by_username(db: Session, username: str) -> User | None`

Retrieve a user from the database using their username.

Args:
    db: Database session dependency used to query the database.
    username: The unique username to search for in the database.

Returns:
    User | None: The User object if found, otherwise None.

Notes:
    1. Query the database for a user with the given username.
    2. Return the first match or None if no user is found.
    3. Database access: Performs a read operation on the User table.

---

## function: `get_user_by_email(db: Session, email: str) -> User | None`

Retrieve a user from the database using their email address.

Args:
    db: Database session dependency used to query the database.
    email: The unique email address to search for in the database.

Returns:
    User | None: The User object if found, otherwise None.

Notes:
    1. Query the database for a user with the given email.
    2. Return the first match or None if no user is found.
    3. Database access: Performs a read operation on the User table.

---

## function: `create_new_user(db: Session, user_data: UserCreate) -> User`

Create a new user in the database with the provided data.

Args:
    db: Database session dependency used to persist the new user.
    user_data: Data required to create a new user, including username, email, and password.

Returns:
    User: The newly created User object with all fields populated.

Notes:
    1. Hash the provided password using a secure hashing algorithm.
    2. Instantiate a new User object with the username, email, and hashed password.
    3. Add the new user object to the database session.
    4. Commit the transaction to persist the user to the database.
    5. Refresh the object to ensure it contains the latest state from the database.
    6. Database access: Performs a write operation on the User table.

---

## function: `get_users(db: Session) -> list[User]`

Retrieve all users from the database.

Args:
    db (Session): The database session.

Returns:
    list[User]: A list of all user objects.

---

## function: `get_user_by_id(db: Session, user_id: int) -> User | None`

Retrieve a single user by ID.

Args:
    db (Session): The database session.
    user_id (int): The ID of the user to retrieve.

Returns:
    User | None: The user object if found, otherwise None.

---

## function: `delete_user(db: Session, user: User) -> None`

Delete a user from the database.

Args:
    db (Session): The database session.
    user (User): The user object to delete.

Notes:
    1. Remove the user object from the database session.
    2. Commit the transaction to persist the deletion.
    3. Database access: Performs a write operation on the User table.

---

## function: `register_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]) -> UserResponse`

Register a new user with the provided credentials.

Args:
    user: Data containing username, email, and password for the new user.
    db: Database session dependency used to interact with the user database.

Returns:
    UserResponse: The created user's data, excluding the password.

Raises:
    HTTPException: If the username or email is already registered.

Notes:
    1. Check if the provided username already exists in the database.
    2. If the username exists, raise a 400 error.
    3. Check if the provided email already exists in the database.
    4. If the email exists, raise a 400 error.
    5. Create a new user with the provided data and store it in the database.
    6. Return the newly created user's data (without the password).
    7. Database access: Performs read and write operations on the User table.

---

## function: `get_user_settings(db: Annotated[Session, Depends(get_db)], current_user: Annotated[User, Depends(get_current_user)]) -> UserSettingsResponse`

Get the current user's settings.

Args:
    db (Session): The database session.
    current_user (User): The authenticated user.

Returns:
    UserSettingsResponse: The user's settings.

Notes:
    1. Retrieve the user's settings from the database.
    2. If no settings exist, return an empty response.
    3. Database access: Performs a read operation on the UserSettings table.

---

## function: `update_user_settings(settings_data: UserSettingsUpdateRequest, db: Annotated[Session, Depends(get_db)], current_user: Annotated[User, Depends(get_current_user)]) -> UserSettingsResponse`

Update the current user's settings.

Args:
    settings_data (UserSettingsUpdateRequest): The settings data to update.
    db (Session): The database session.
    current_user (User): The authenticated user.

Returns:
    UserSettingsResponse: The updated user's settings.

Notes:
    1. Update the user's settings in the database with the provided data.
    2. Return the updated settings.
    3. Database access: Performs a write operation on the UserSettings table.

---

## function: `change_password(request: Request, form_data: Annotated[ChangePasswordForm, Depends()], db: Annotated[Session, Depends(get_db)], current_user: Annotated[User, Depends(get_current_user_from_cookie)]) -> Response`

Change the current user's password.

This endpoint handles both standard and forced password changes. It also handles
requests from two different forms: the full-page form and the partial form
on the settings page.

It performs content negotiation based on the 'Accept' and 'HX-Target' headers.

Args:
    request (Request): The request object.
    form_data (ChangePasswordForm): The form data with new and current passwords.
    db (Session): The database session.
    current_user (User): The authenticated user.

Returns:
    Response: A response appropriate for a request type (JSON, HTML snippet,
              full page render, or redirect).

---

## function: `get_change_password_page(request: Request, user: Annotated[User, Depends(get_current_user_from_cookie)]) -> HTMLResponse`

Renders the page for changing a password.

This page can be used for both forced and standard password changes. The
template will conditionally render fields based on whether the user is
being forced to change their password.

Args:
    request (Request): The incoming HTTP request.
    user (User): The authenticated user, retrieved from the cookie.

Returns:
    HTMLResponse: The rendered HTML page for changing the password.

Notes:
    1. Render the change_password.html template with the current user context.
    2. The template checks for `user.attributes.force_password_change` to
       determine which version of the form to display.
    3. Return the HTML response to the client.

---

## function: `login_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Annotated[Session, Depends(get_db)], settings: Annotated[Settings, Depends(get_settings)]) -> Token`

Authenticate a user and return an access token.

Args:
    form_data: Form data containing username and password for authentication.
    db: Database session dependency used to verify user credentials.
    settings: Application settings used for token creation and configuration.

Returns:
    Token: An access token for the authenticated user, formatted as a JWT.

Raises:
    HTTPException: If the username or password is incorrect.

Notes:
    1. Attempt to authenticate the user using the provided username and password.
    2. If authentication fails, raise a 401 error.
    3. Update the user's last_login_at timestamp to the current UTC time.
    4. Commit the change to the database.
    5. Generate a JWT access token with a defined expiration time.
    6. Return the access token to the client.
    7. Database access: Performs read and write operations on the User table.

---


===

===
# File: `resume_editor/app/api/routes/route_models.py`

## `RefineForm` class

Form data for refining the experience section of a resume.

---
## method: `RefineForm.__init__(self: UnknownType, job_description: str, limit_refinement_years: str | None) -> None`



---
## `RefinementContext` class

Context data for resume refinement.

---
## method: `RefinementContext.__init__(self: UnknownType, job_description: str | None, introduction: str | None, limit_refinement_years: int | None) -> None`



---
## `SaveAsNewForm` class

Form data for saving a refined resume as a new one.

---
## method: `SaveAsNewForm.__init__(self: UnknownType, refined_content: str, new_resume_name: str | None, context: RefinementContext) -> None`



---
## `ChangePasswordForm` class

Form data for changing a password.

---
## method: `ChangePasswordForm.__init__(self: UnknownType, new_password: str, confirm_new_password: str, current_password: str | None) -> None`



---
## `ProjectUpdateForm` class

Form data for updating projects.

---
## method: `ProjectUpdateForm.__init__(self: UnknownType, title: str, description: str, url: str | None, start_date: str | None, end_date: str | None) -> None`



---
## `CertificationUpdateForm` class

Form data for updating certifications.

---
## method: `CertificationUpdateForm.__init__(self: UnknownType, name: str, issuer: str | None, certification_id: str | None, issued_date: str | None, expiry_date: str | None) -> None`



---
## `ExperienceUpdateForm` class

Form data for updating experience.

---
## method: `ExperienceUpdateForm.__init__(self: UnknownType, company: str, title: str, start_date: str, end_date: str | None, description: str | None) -> None`



---
## `EducationDates` class

Form data for education dates.

---
## method: `EducationDates.__init__(self: UnknownType, start_date: str | None, end_date: str | None) -> None`



---
## `EducationUpdateForm` class

Form data for updating education.

---
## method: `EducationUpdateForm.__init__(self: UnknownType, school: str, degree: str | None, major: str | None, dates: EducationDates, gpa: str | None) -> None`



---

===

===
# File: `resume_editor/app/api/routes/admin.py`

## function: `admin_create_user(user_data: AdminUserCreate, db: Annotated[Session, Depends(get_db)]) -> AdminUserResponse`

Admin endpoint to create a new user.

Args:
    user_data (AdminUserCreate): The data required to create a new user, including username, password, and optional email.
    db (Session): The database session used to interact with the database.

Returns:
    AdminUserResponse: The created user's data, including admin-specific fields.

Notes:
    1. Logs the admin's attempt to create a user.
    2. Calls `admin_crud.create_user_admin` to handle user creation.
    3. The CRUD function hashes the password, commits the new user, and re-fetches it to load relationships.
    4. Logs the completion of user creation.
    5. Database access occurs during user creation.

---

## function: `admin_get_users(db: Annotated[Session, Depends(get_db)]) -> list[AdminUserResponse]`

Admin endpoint to list all users.

Args:
    db (Session): The database session used to interact with the database.

Returns:
    list[AdminUserResponse]: A list of all users' data, including their ID, username, and other public fields.

Notes:
    1. Logs the admin's request to fetch all users.
    2. Retrieves all users from the database using `admin_crud.get_users_admin`.
    3. The response model automatically computes additional fields like resume_count.
    4. Database access occurs during the retrieval of users.

---

## function: `admin_get_user(user_id: int, db: Annotated[Session, Depends(get_db)]) -> AdminUserResponse`

Admin endpoint to get a single user by ID.

Args:
    user_id (int): The unique identifier of the user to retrieve.
    db (Session): The database session used to interact with the database.

Returns:
    AdminUserResponse: The data of the requested user, including their ID, username, and other public fields, as well as admin-specific fields.

Raises:
    HTTPException: If the user with the given ID is not found, raises a 404 error.

Notes:
    1. Logs the admin's request to fetch a user by ID.
    2. Retrieves the user from the database using `admin_crud.get_user_by_id_admin`, which eager-loads resume data.
    3. If the user is not found, raises a 404 HTTPException.
    4. Logs the completion of the fetch operation.
    5. Database access occurs during the user retrieval.

---

## function: `admin_update_user(user_id: int, update_data: AdminUserUpdateRequest, db: Annotated[Session, Depends(get_db)]) -> AdminUserResponse`

Admin endpoint to update a user's attributes.

Args:
    user_id (int): The unique identifier of the user to update.
    update_data (AdminUserUpdateRequest): The data for the update.
    db (Session): The database session.

Returns:
    AdminUserResponse: The updated user's data.

Raises:
    HTTPException: If the user is not found.

Notes:
    1. Retrieves the user by ID using `admin_crud.get_user_by_id_admin`.
    2. If the user is not found, raises a 404 error.
    3. Calls `admin_crud.update_user_admin` to apply attribute updates.
    4. Returns the updated user object.
    5. Database access occurs during user retrieval and update.

---

## function: `admin_delete_user(user_id: int, db: Annotated[Session, Depends(get_db)], admin_user: Annotated[User, Depends(get_current_admin_user)]) -> None`

Admin endpoint to delete a user.

Args:
    user_id (int): The unique identifier of the user to delete.
    db (Session): The database session used to interact with the database.
    admin_user (User): The currently authenticated admin user performing the deletion.

Raises:
    HTTPException: If the user with the given ID is not found, raises a 404 error.

Notes:
    1. Logs the admin's request to delete a user.
    2. Retrieves the user from the database using get_user_by_id_admin.
    3. If the user is not found, raises a 404 HTTPException.
    4. Deletes the user from the database using delete_user_admin.
    5. Commits the deletion to the database.
    6. Logs the completion of the deletion.
    7. Database access occurs during user retrieval, deletion, and commit.

---

## function: `admin_assign_role_to_user(user_id: int, role_name: str, db: Annotated[Session, Depends(get_db)]) -> AdminUserResponse`

Admin endpoint to assign a role to a user.

Args:
    user_id (int): The unique identifier of the user to assign the role to.
    role_name (str): The name of the role to assign.
    db (Session): The database session used to interact with the database.

Returns:
    AdminUserResponse: The updated user data, including the newly assigned role and other admin fields.

Raises:
    HTTPException: If the user or role is not found (404 error), or if the user already has the role (400 error).

Notes:
    1. Logs the admin's attempt to assign a role to a user.
    2. Retrieves the user from the database using get_user_by_id_admin.
    3. If the user is not found, raises a 404 HTTPException.
    4. Retrieves the role from the database using get_role_by_name_admin.
    5. If the role is not found, raises a 404 HTTPException.
    6. Checks if the user already has the role; if so, returns the user without modification.
    7. Appends the role to the user's roles list.
    8. Commits the change to the database.
    9. Refreshes the user object from the database.
    10. Logs the completion of the role assignment.
    11. Database access occurs during user and role retrieval, modification, and commit.

---

## function: `admin_remove_role_from_user(user_id: int, role_name: str, db: Annotated[Session, Depends(get_db)]) -> AdminUserResponse`

Admin endpoint to remove a role from a user.

Args:
    user_id (int): The unique identifier of the user to remove the role from.
    role_name (str): The name of the role to remove.
    db (Session): The database session used to interact with the database.

Returns:
    AdminUserResponse: The updated user data, excluding the removed role, but including other admin fields.

Raises:
    HTTPException: If the user or role is not found (404 error), or if the user does not have the role (400 error).

Notes:
    1. Logs the admin's attempt to remove a role from a user.
    2. Retrieves the user from the database using get_user_by_id_admin.
    3. If the user is not found, raises a 404 HTTPException.
    4. Retrieves the role from the database using get_role_by_name_admin.
    5. If the role is not found, raises a 404 HTTPException.
    6. Checks if the user has the role; if not, raises a 400 HTTPException.
    7. Removes the role from the user's roles list.
    8. Commits the change to the database.
    9. Refreshes the user object from the database.
    10. Logs the completion of the role removal.
    11. Database access occurs during user and role retrieval, modification, and commit.

---

## function: `admin_impersonate_user(username: str, db: Annotated[Session, Depends(get_db)], admin_user: Annotated[User, Depends(get_current_admin_user)], settings: Annotated[Settings, Depends(get_settings)]) -> Token`

Admin endpoint to impersonate a user.

Args:
    username (str): The username of the user to impersonate.
    db (Session): The database session used to interact with the database.
    admin_user (User): The currently authenticated admin user.
    settings (Settings): Application settings used for token creation and configuration.

Returns:
    Token: A JWT access token for the impersonated user, with the admin's username as the impersonator.

Raises:
    HTTPException: If the user to impersonate is not found, raises a 404 error.

Notes:
    1. Logs the admin's attempt to impersonate a user.
    2. Retrieves the target user from the database by username using `admin_crud.get_user_by_username_admin`.
    3. If the target user is not found, raises a 404 HTTPException.
    4. Creates a JWT access token with the admin's username as the impersonator.
    5. Logs the successful creation of the impersonation token.

---


===

===
# File: `resume_editor/app/api/routes/route_logic/resume_crud.py`

## function: `get_resume_by_id_and_user(db: Session, resume_id: int, user_id: int) -> DatabaseResume`

Retrieve a resume by its ID and verify it belongs to the specified user.

Args:
    db (Session): The SQLAlchemy database session used to query the database.
    resume_id (int): The unique identifier for the resume to retrieve.
    user_id (int): The unique identifier for the user who owns the resume.

Returns:
    DatabaseResume: The resume object matching the provided ID and user ID.

Raises:
    HTTPException: If no resume is found with the given ID and user ID, raises a 404 error with detail "Resume not found".

Notes:
    1. Query the DatabaseResume table for a record where the id matches resume_id and the user_id matches user_id.
    2. If no matching record is found, raise an HTTPException with status code 404 and detail "Resume not found".
    3. Return the found DatabaseResume object.
    4. This function performs a single database query to retrieve a resume.

---

## function: `get_user_resumes(db: Session, user_id: int, sort_by: str | None) -> list[DatabaseResume]`

Retrieve all resumes associated with a specific user, with optional sorting.

Args:
    db (Session): The SQLAlchemy database session used to query the database.
    user_id (int): The unique identifier for the user whose resumes are to be retrieved.
    sort_by (str | None): The sorting criterion. Defaults to 'updated_at_desc'.

Returns:
    list[DatabaseResume]: A sorted list of DatabaseResume objects belonging to the specified user.

Notes:
    1. Build a query for records in the DatabaseResume table where the user_id matches.
    2. Determine the sorting column and direction from the `sort_by` parameter.
    3. Default to sorting by `updated_at` in descending order if `sort_by` is not provided.
    4. Apply the sorting to the query.
    5. Execute the query and return the list of matching DatabaseResume objects.
    6. This function performs a single database query.

---

## function: `create_resume(db: Session, params: ResumeCreateParams) -> DatabaseResume`

Create and save a new resume.

Args:
    db (Session): The database session.
    params (ResumeCreateParams): The parameters required to create the resume.

Returns:
    DatabaseResume: The newly created resume object.

Notes:
    1. Create a new DatabaseResume instance with all provided details.
    2. Add the instance to the database session.
    3. Commit the transaction to persist the changes.
    4. Refresh the instance to ensure it has the latest state, including the generated ID.
    5. Return the created resume.
    6. This function performs a database write operation.

---

## function: `update_resume(db: Session, resume: DatabaseResume, params: ResumeUpdateParams) -> DatabaseResume`

Update a resume's name, content, introduction, and/or notes.

Args:
    db (Session): The database session.
    resume (DatabaseResume): The resume to update.
    params (ResumeUpdateParams): The new data for the resume.

Returns:
    DatabaseResume: The updated resume object.

Notes:
    1. If a new name is provided (not None), update the resume's name attribute.
    2. If new content is provided (not None), update the resume's content attribute.
    3. If an introduction is provided (not None), update the resume's introduction attribute.
    4. If new notes are provided (not None), update the resume's notes attribute.
    5. Commit the transaction to save the changes to the database.
    6. Refresh the resume object to ensure it reflects the latest state from the database.
    7. Return the updated resume.
    8. This function performs a database write operation.

---

## function: `delete_resume(db: Session, resume: DatabaseResume) -> None`

Delete a resume.

Args:
    db (Session): The database session.
    resume (DatabaseResume): The resume to delete.

Returns:
    None

Notes:
    1. Delete the resume object from the database session.
    2. Commit the transaction to persist the deletion.
    3. This function performs a database write operation.

---


===

===
# File: `resume_editor/app/api/routes/route_logic/resume_validation.py`

## function: `perform_pre_save_validation(markdown_content: str) -> None`

Perform comprehensive pre-save validation on resume content.

Args:
    markdown_content (str): The updated resume Markdown content to validate.

Returns:
    None: This function does not return any value.

Raises:
    HTTPException: If validation fails with status code 422.

Notes:
    1. Run the updated Markdown through the existing parser to ensure it's still valid.
    2. If any validation fails, raise an HTTPException with detailed error messages.
    3. This function performs validation checks on resume content before saving to ensure data integrity.
    4. Validation includes parsing the Markdown content to verify its structure and format.
    5. The function accesses the resume parsing module to validate the content structure.

---


===

===
# File: `resume_editor/app/api/routes/route_logic/resume_filtering.py`

## function: `_get_date_from_optional_datetime(dt: datetime | None) -> date | None`

Extract the date portion from an optional datetime object.

Args:
    dt (datetime | None): The datetime object to extract the date from, or None.

Returns:
    date | None: The date portion of the datetime object, or None if input is None.

Notes:
    1. If the input dt is None, return None.
    2. Otherwise, extract and return the date portion of the datetime object using the date() method.

---

## function: `_is_in_date_range(item_start_date: date | None, item_end_date: date | None, filter_start_date: date | None, filter_end_date: date | None) -> bool`

Check if an item's date range overlaps with the filter's date range.

Args:
    item_start_date (date | None): The start date of the item being evaluated.
    item_end_date (date | None): The end date of the item (or None if ongoing).
    filter_start_date (date | None): The start date of the filtering period.
    filter_end_date (date | None): The end date of the filtering period.

Returns:
    bool: True if the item overlaps with the filter's date range, False otherwise.

Notes:
    1. If the filter has a start date and the item ends before that date, the item is out of range.
    2. If the filter has an end date and the item starts after that date, the item is out of range.
    3. Otherwise, the item is considered to be in range. This includes ongoing items (those with no end date).

---

## function: `filter_experience_by_date(experience: ExperienceResponse, start_date: date | None, end_date: date | None) -> ExperienceResponse`

Filter roles and projects in an ExperienceResponse based on a date range.

Args:
    experience (ExperienceResponse): The experience data to filter.
    start_date (date | None): The start of the filtering period. If None, no start constraint is applied.
    end_date (date | None): The end of the filtering period. If None, no end constraint is applied.

Returns:
    ExperienceResponse: A new ExperienceResponse object containing only roles and projects that overlap with the specified date range.

Notes:
    1. If both start_date and end_date are None, return the original experience object unmodified.
    2. Iterate through the roles in the experience object and check if each role's date range overlaps with the filter range using _is_in_date_range.
    3. For each role that overlaps, add it to the filtered_roles list.
    4. Iterate through the projects in the experience object and check if each project's date range overlaps with the filter range.
    5. Projects without an end date are treated as ongoing.
    6. For each project that overlaps, add it to the filtered_projects list.
    7. Return a new ExperienceResponse object with the filtered roles and projects.

---


===

===
# File: `resume_editor/app/api/routes/route_logic/resume_llm.py`

## function: `_get_section_content(resume_content: str, section_name: str) -> str`

Extracts the Markdown content for a specific section of the resume.

Args:
    resume_content (str): The full resume content in Markdown.
    section_name (str): The name of the section to extract ("personal", "education", "experience", "certifications", or "full").

Returns:
    str: The Markdown content of the specified section. Returns the full content if "full" is specified.

Raises:
    ValueError: If the section_name is not one of the valid options.

Notes:
    1. If section_name is "full", return the entire resume_content.
    2. Otherwise, map the section_name to a tuple of extractor and serializer functions.
    3. Validate that section_name is in the valid set of keys.
    4. Extract the data using the extractor function.
    5. Serialize the extracted data using the serializer function.
    6. Return the serialized result.

---

## function: `refine_resume_section_with_llm(resume_content: str, job_description: str, target_section: str, llm_endpoint: str | None, api_key: str | None, llm_model_name: str | None) -> str`

Uses an LLM to refine a specific section of a resume based on a job description.

Args:
    resume_content (str): The full Markdown content of the resume.
    job_description (str): The job description to align the resume with.
    target_section (str): The section of the resume to refine (e.g., "experience").
    llm_endpoint (str | None): The custom LLM endpoint URL.
    api_key (str | None): The user's decrypted LLM API key.
    llm_model_name (str | None): The user-specified LLM model name.

Returns:
    str: The refined Markdown content for the target section. Returns an empty string if the target section is empty.

Notes:
    1. Extract the target section content from the resume using _get_section_content.
    2. If the extracted content is empty, return an empty string.
    3. Set up a PydanticOutputParser for structured output based on the RefinedSection model.
    4. Create a PromptTemplate with instructions for the LLM, including format instructions.
    5. Determine the model name, using the provided `llm_model_name` or falling back to a default.
    6. Initialize the ChatOpenAI client. If a custom `llm_endpoint` is set without an `api_key`, a dummy API key is provided to satisfy the OpenAI client library.
    7. Create a chain combining the prompt, LLM, and parser.
    8. Invoke the chain with the job description and resume section content to get a `RefinedSection` object.
    9. Return the `refined_markdown` field from the result.

Network access:
    - This function makes a network request to the LLM endpoint specified by llm_endpoint.

---


===

===
# File: `resume_editor/app/api/routes/route_logic/settings_crud.py`

## function: `get_user_settings(db: Session, user_id: int) -> UserSettings | None`

Retrieves the settings for a given user.

Args:
    db (Session): The database session used to query the database.
    user_id (int): The unique identifier of the user whose settings are being retrieved.

Returns:
    UserSettings | None: The user's settings if found, otherwise None.

Notes:
    1. Queries the database for a UserSettings record where user_id matches the provided user_id.
    2. Returns the first matching record or None if no record is found.
    3. This function performs a single database read operation.

---

## function: `update_user_settings(db: Session, user_id: int, settings_data: 'UserSettingsUpdateRequest') -> UserSettings`

Creates or updates settings for a user.

Args:
    db (Session): The database session used to perform database operations.
    user_id (int): The unique identifier of the user whose settings are being updated.
    settings_data (UserSettingsUpdateRequest): The data containing the updated settings.

Returns:
    UserSettings: The updated or newly created UserSettings object.

Notes:
    1. Attempts to retrieve existing settings for the given user_id using get_user_settings.
    2. If no settings are found, creates a new UserSettings object with the provided user_id and adds it to the session.
    3. Updates the llm_endpoint field if settings_data.llm_endpoint is provided and not None.
    4. Updates the llm_model_name field if settings_data.llm_model_name is provided and not None.
    5. If a non-empty `settings_data.api_key` is provided, encrypts the API key using `encrypt_data` and stores it. An empty or `None` API key in the request will not change a pre-existing key.
    6. Commits the transaction to the database.
    7. Refreshes the session to ensure the returned object has the latest data from the database.
    8. This function performs a database read and possibly a write operation.

---


===

===
# File: `resume_editor/app/api/routes/route_logic/resume_reconstruction.py`

## function: `reconstruct_resume_markdown(personal_info: PersonalInfoResponse | None, education: EducationResponse | None, certifications: CertificationsResponse | None, experience: ExperienceResponse | None) -> str`

Reconstruct a complete resume Markdown document from structured data sections.

Args:
    personal_info (PersonalInfoResponse | None): Personal information data structure. If None, the personal info section is omitted.
    education (EducationResponse | None): Education information data structure. If None, the education section is omitted.
    certifications (CertificationsResponse | None): Certifications information data structure. If None, the certifications section is omitted.
    experience (ExperienceResponse | None): Experience information data structure, containing roles and projects. If None, the experience section is omitted.

Returns:
    str: A complete Markdown formatted resume document with all provided sections joined by double newlines.

Notes:
    1. Initialize an empty list to collect resume sections.
    2. Serialize each provided section using the corresponding serialization function.
    3. Append each serialized section to the sections list if it is not empty.
    4. Filter out any empty strings and strip whitespace from each section.
    5. Join all sections with double newlines to ensure proper spacing.
    6. Return the complete Markdown resume content.
    7. No network, disk, or database access is performed.

---

## function: `build_complete_resume_from_sections(personal_info: PersonalInfoResponse, education: EducationResponse, certifications: CertificationsResponse, experience: ExperienceResponse) -> str`

Build a complete resume Markdown document from all structured sections.

Args:
    personal_info (PersonalInfoResponse): Personal information data structure.
    education (EducationResponse): Education information data structure.
    certifications (CertificationsResponse): Certifications information data structure.
    experience (ExperienceResponse): Experience information data structure.

Returns:
    str: A complete Markdown formatted resume document with all sections in the order: personal, education, certifications, experience.

Notes:
    1. Calls reconstruct_resume_markdown with all sections.
    2. Ensures proper section ordering (personal, education, certifications, experience).
    3. Returns the complete Markdown resume content.
    4. No network, disk, or database access is performed.

---


===

===
# File: `resume_editor/app/api/routes/route_logic/admin_crud.py`

## function: `create_user_admin(db: Session, user_data: AdminUserCreate) -> User`

Create a new user as an administrator.

Args:
    db (Session): The database session used to interact with the database.
    user_data (AdminUserCreate): The data required to create a new user, including username, email, password, and other attributes.

Returns:
    User: The newly created user object with all fields populated, including the generated ID.

Notes:
    1. Hashes the provided password using the `get_password_hash` utility.
    2. Creates a new `User` instance with the provided data and the hashed password.
    3. Adds the new user to the database session.
    4. Commits the transaction to persist the user to the database.
    5. Re-fetches the user to ensure relationships are eagerly loaded, preventing N+1 query issues.
    6. This function performs a database write operation.

---

## function: `create_initial_admin(db: Session, username: str, password: str) -> User`

Create the initial administrator account.

This function creates the first user and assigns them the 'admin' role. It
is intended to be used only during initial application setup when no users
exist in the database.

Args:
    db (Session): The database session.
    username (str): The username for the new admin user.
    password (str): The password for the new admin user.

Returns:
    User: The created admin user object.

Raises:
    RuntimeError: If the 'admin' role is not found in the database.

Notes:
    1. Hashes the provided password.
    2. Creates a placeholder email address.
    3. Creates a new User instance.
    4. Queries for the 'admin' role. Raises RuntimeError if not found.
    5. Appends the 'admin' role to the new user's roles.
    6. Adds the user to the database session.
    7. Commits the transaction.
    8. Re-fetches the user to load relationships.
    9. This function performs database read and write operations.

---

## function: `get_user_by_id_admin(db: Session, user_id: int) -> User | None`

Retrieve a single user by their unique ID as an administrator.

Args:
    db (Session): The database session used to query the database.
    user_id (int): The unique identifier of the user to retrieve.

Returns:
    User | None: The user object if found, otherwise None.

Notes:
    1. Queries the database for a user with the specified ID, eagerly loading their resumes.
    2. This function performs a database read operation.

---

## function: `get_users_admin(db: Session) -> list[User]`

Retrieve all users from the database as an administrator.

Args:
    db (Session): The database session used to query the database.

Returns:
    list[User]: A list of all user objects in the database.

Notes:
    1. Queries the database for all users, eagerly loading their resumes to prevent N+1 issues.
    2. This function performs a database read operation.

---

## function: `get_user_by_username_admin(db: Session, username: str) -> User | None`

Retrieve a single user by their username as an administrator.

Args:
    db (Session): The database session used to query the database.
    username (str): The unique username of the user to retrieve.

Returns:
    User | None: The user object if found, otherwise None.

Notes:
    1. Queries the database for a user with the specified username.
    2. This function performs a database read operation.

---

## function: `delete_user_admin(db: Session, user: User) -> None`

Delete a user from the database as an administrator.

Args:
    db (Session): The database session used to interact with the database.
    user (User): The user object to be deleted.

Returns:
    None

Notes:
    1. Removes the specified user from the database session.
    2. Commits the transaction to permanently delete the user from the database.
    3. This function performs a database write operation.

---

## function: `get_role_by_name_admin(db: Session, name: str) -> Role | None`

Retrieve a role from the database by its unique name.

This function is intended for administrative use to fetch a role before
performing actions like assigning it to or removing it from a user.

Args:
    db (Session): The SQLAlchemy database session.
    name (str): The unique name of the role to retrieve.

Returns:
    Role | None: The `Role` object if found, otherwise `None`.

Notes:
    1. Queries the database for a role with the given name.
    2. This function performs a database read operation.

---

## function: `assign_role_to_user_admin(db: Session, user: User, role: Role) -> User`

Assign a role to a user if they do not already have it.

This administrative function associates a `Role` with a `User`.
It checks for the role's existence on the user before appending to prevent duplicates.
Changes are committed to the database.

Args:
    db (Session): The SQLAlchemy database session.
    user (User): The user object to which the role will be assigned.
    role (Role): The role object to assign.

Returns:
    User: The updated user object, re-fetched from the database with eager-loaded relationships.

Notes:
    1. Checks if the user already has the role.
    2. If not, adds the role, commits, and re-fetches the user to prevent N+1 issues.
    3. This function performs a database write operation if the role is added.

---

## function: `remove_role_from_user_admin(db: Session, user: User, role: Role) -> User`

Remove a role from a user if they have it.

This administrative function disassociates a `Role` from a `User`.
It checks if the user has the role before attempting removal.
Changes are committed to the database.

Args:
    db (Session): The SQLAlchemy database session.
    user (User): The user object from which the role will be removed.
    role (Role): The role object to remove.

Returns:
    User: The updated user object, re-fetched from the database with eager-loaded relationships.

Notes:
    1. Checks if the user has the role.
    2. If so, removes the role, commits, and re-fetches the user to prevent N+1 issues.
    3. This function performs a database write operation if the role is removed.

---

## function: `update_user_admin(db: Session, user: User, update_data: AdminUserUpdateRequest) -> User`

Update a user's attributes as an administrator.

Args:
    db (Session): The database session.
    user (User): The user object to update.
    update_data (AdminUserUpdateRequest): The data containing the updates.

Returns:
    User: The updated user object.

Notes:
    1. Updates the user's attributes dictionary with the force_password_change flag.
    2. Commits the changes to the database.
    3. Re-fetches the user to ensure relationships are eagerly loaded, preventing N+1 issues.
    4. This function performs a database write operation.

---


===

===
# File: `resume_editor/app/api/routes/route_logic/resume_parsing.py`

## function: `parse_resume_to_writer_object(markdown_content: str) -> WriterResume`

Parse Markdown resume content into a resume_writer Resume object.

Args:
    markdown_content (str): The Markdown content to parse, expected to follow a valid resume format.

Returns:
    WriterResume: The parsed resume object from the resume_writer library, containing structured data for personal info, experience, education, certifications, etc.

Raises:
    ValueError: If the parsed content contains no valid resume sections (e.g., no personal, education, experience, or certifications data).

Notes:
    1. Split the input Markdown content into individual lines.
    2. Skip any lines before the first valid top-level section header (i.e., lines starting with "# " but not "##").
    3. Identify valid section headers by checking against the keys in WriterResume.expected_blocks().
    4. If a valid header is found, truncate the lines list to start from that header.
    5. Create a ParseContext object using the processed lines and indentation level 1.
    6. Use the Resume.parse method to parse the content into a WriterResume object.
    7. Check if any of the main resume sections (personal, education, experience, certifications) were successfully parsed.
    8. Raise ValueError if no valid sections were parsed.
    9. Return the fully parsed WriterResume object.

---

## function: `parse_resume(markdown_content: str) -> dict[str, Any]`

Parse Markdown resume content using resume_writer parser and return a dictionary.

Args:
    markdown_content (str): The Markdown content to parse, expected to follow a valid resume format.

Returns:
    dict[str, Any]: A dictionary representation of the parsed resume data, including:
        - personal: Personal information (e.g., name, email, phone).
        - experience: List of work experience entries.
        - education: List of educational qualifications.
        - certifications: List of certifications.
        - Any other sections supported by resume_writer.

Raises:
    HTTPException: If parsing fails due to invalid format or content, with status 422 and a descriptive message.

Notes:
    1. Log the start of the parsing process.
    2. Call a series of extraction functions to get serializable Pydantic models.
    3. Construct a dictionary from these models.
    4. Log successful completion.
    5. Return the dictionary representation.
    6. No disk, network, or database access is performed.

---

## function: `parse_resume_content(markdown_content: str) -> dict[str, Any]`

Parse Markdown resume content and return structured data as a dictionary.

Args:
    markdown_content (str): The Markdown content to parse, expected to follow a valid resume format.

Returns:
    dict: A dictionary containing the structured resume data, including:
        - personal: Personal information (e.g., name, email, phone).
        - experience: List of work experience entries.
        - education: List of educational qualifications.
        - certifications: List of certifications.
        - Any other sections supported by resume_writer.

Raises:
    HTTPException: If parsing fails due to invalid format or content, with status 400 and a descriptive message.

Notes:
    1. Log the start of the parsing process.
    2. Use the parse_resume function to parse the provided markdown_content.
    3. Return the result of parse_resume as a dictionary.
    4. Log successful completion.
    5. No disk, network, or database access is performed.

---

## function: `validate_resume_content(content: str) -> None`

Validate resume Markdown content for proper format.

Args:
    content (str): The Markdown content to validate, expected to be in a format compatible with resume_writer.

Returns:
    None: The function returns nothing if validation passes.

Raises:
    HTTPException: If parsing fails due to invalid format, with status 422 and a descriptive message.

Notes:
    1. Log the start of the validation process.
    2. Attempt to parse the provided content using the parse_resume function.
    3. If parsing fails, raise an HTTPException with a descriptive error message.
    4. Log successful completion if no exception is raised.
    5. No disk, network, or database access is performed.

---


===

===
# File: `resume_editor/app/api/routes/route_logic/resume_serialization.py`

## function: `extract_personal_info(resume_content: str) -> PersonalInfoResponse`

Extract personal information from resume content.

Args:
    resume_content (str): The Markdown content of the resume to parse.

Returns:
    PersonalInfoResponse: Extracted personal information containing name, email, phone, location, and website.

Raises:
    ValueError: If parsing fails due to invalid or malformed resume content.

Notes:
    1. Parses the resume content using `_parse_resume`.
    2. Checks for unparsed content in the "personal" section using `_check_for_unparsed_content`.
    3. If no personal section was parsed, an empty response is returned.
    4. Extracts data from the parsed personal section using `_extract_data_from_personal_section`.
    5. Constructs and returns a `PersonalInfoResponse` with the extracted data.

---

## function: `extract_education_info(resume_content: str) -> EducationResponse`

Extract education information from resume content.

Args:
    resume_content (str): The Markdown content of the resume to parse.

Returns:
    EducationResponse: Extracted education information containing a list of degree entries.

Raises:
    ValueError: If parsing fails due to invalid or malformed resume content.

Notes:
    1. Splits the resume content into lines.
    2. Creates a ParseContext for parsing.
    3. Parses the resume using the resume_writer module.
    4. Retrieves the education section from the parsed resume.
    5. Checks if education data is present; if not, returns an empty response.
    6. Loops through each degree and extracts school, degree, major, start_date, end_date, and gpa.
    7. Maps each degree's fields into a dictionary.
    8. Returns a list of dictionaries wrapped in the EducationResponse model.
    9. If parsing fails, returns an empty response.
    10. No network, disk, or database access is performed during this function.

---

## function: `extract_experience_info(resume_content: str) -> ExperienceResponse`

Extract experience information from resume content.

Args:
    resume_content (str): The Markdown content of the resume to parse.

Returns:
    ExperienceResponse: Extracted experience information containing lists of roles and projects.

Raises:
    ValueError: If parsing fails due to invalid or malformed resume content.

Notes:
    1. Parses the resume content using `_parse_resume`.
    2. Retrieves the experience section. If it's missing but raw content exists, raises ValueError via `_check_for_unparsed_content`.
    3. Loops through each role, converting it to a dictionary via `_convert_writer_role_to_dict`.
    4. Loops through each project, converting it to a dictionary via `_convert_writer_project_to_dict`.
    5. Collects non-empty dictionaries into lists.
    6. Returns an `ExperienceResponse` with the collected lists.

---

## function: `extract_certifications_info(resume_content: str) -> CertificationsResponse`

Extract certifications information from resume content.

Args:
    resume_content (str): The Markdown content of the resume to parse.

Returns:
    CertificationsResponse: Extracted certifications information containing a list of certifications.

Raises:
    ValueError: If parsing fails due to invalid or malformed resume content.

Notes:
    1. Splits the resume content into lines.
    2. Creates a ParseContext for parsing.
    3. Parses the resume using the resume_writer module.
    4. Retrieves the certifications section from the parsed resume.
    5. Checks if certifications data is present; if not, returns an empty response.
    6. Loops through each certification and extracts name, issuer, certification_id, issued, and expires.
    7. Maps the extracted data into a dictionary.
    8. Returns a list of dictionaries wrapped in the CertificationsResponse model.
    9. If parsing fails, returns an empty response.
    10. No network, disk, or database access is performed during this function.

---

## function: `serialize_personal_info_to_markdown(personal_info: PersonalInfoResponse | None) -> str`

Serialize personal information to Markdown format.

    Args:
        personal_info (PersonalInfoResponse | None): Personal information to serialize.

    Returns:
        str: Markdown formatted personal information section.

    Notes:
        1. Returns an empty string if `personal_info` is `None`.
        2. Initializes an empty list `lines`.
        3. Calls helper functions to add contact info, websites, visa status,
           banner, and note sections to `lines`.
        4. If `lines` is not empty, constructs the final string:
            a. Starts with `# Personal

`.
            b. Joins the elements of `lines` with newlines.
            c. Appends a final newline.
        5. Otherwise, returns an empty string.

    

---

## function: `serialize_education_to_markdown(education: EducationResponse | None) -> str`

Serialize education information to Markdown format.

Args:
    education (EducationResponse | None): Education information to serialize, containing a list of degree entries.

Returns:
    str: Markdown formatted education section.

Notes:
    1. Initializes an empty list of lines and adds a heading.
    2. For each degree in the list:
        a. Adds a subsection header.
        b. Adds each field (school, degree, major, start_date, end_date, gpa) as a direct field if present.
        c. Adds a blank line after each degree.
    3. Joins the lines with newlines.
    4. Returns the formatted string with a trailing newline.
    5. No network, disk, or database access is performed during this function.

---

## function: `_serialize_project_to_markdown(project: Project) -> list[str]`

Serialize a single project to markdown lines.

Args:
    project (Project): A project object to serialize.

Returns:
    list[str]: A list of markdown lines representing the project.

Notes:
    1. Gets the overview from the project.
    2. Checks if the inclusion status is OMIT; if so, returns an empty list.
    3. Calls `_add_project_overview_markdown` to add the overview section.
    4. If inclusion status is not `NOT_RELEVANT`, calls `_add_project_description_markdown` and `_add_project_skills_markdown`.
    5. If any content is generated, prepends the `### Project` header.
    6. Returns the full project content as a list of lines.

---

## function: `_serialize_role_to_markdown(role: Role) -> list[str]`

Serialize a single role to markdown lines.

Args:
    role (Role): A role object to serialize.

Returns:
    list[str]: A list of markdown lines representing the role.

Notes:
    1. Gets the `basics` section from the role. If not present, returns an empty list.
    2. Checks the `inclusion_status` on the `basics` object. If `OMIT`, returns an empty list.
    3. Orchestrates calls to helper functions to serialize different parts of the role:
       - `_add_role_basics_markdown` for company, title, dates, etc.
       - `_add_role_summary_markdown` for the summary text.
       - `_add_role_responsibilities_markdown` for responsibilities, handling inclusion status.
       - `_add_role_skills_markdown` for the list of skills.
    4. If any content is generated, prepends the `### Role` header.
    5. Returns the combined list of Markdown lines for the role.

---

## function: `serialize_experience_to_markdown(experience: ExperienceResponse | None) -> str`

Serialize experience information to Markdown format.

Args:
    experience (ExperienceResponse | None): Experience information to serialize, containing lists of roles and projects.

Returns:
    str: Markdown formatted experience section.

Notes:
    1. Checks if the experience object is empty.
    2. Initializes an empty list of lines.
    3. If projects exist, serializes each one using `_serialize_project_to_markdown`.
    4. If roles exist, serializes each one using `_serialize_role_to_markdown`.
    5. If any content was generated, builds the final Markdown string with `# Experience`, `## Projects` (if any), and `## Roles` (if any) headers.
    6. Joins the lines with newlines and returns the formatted string with a trailing newline.
    7. Returns an empty string if no experience data is present or all items are omitted.
    8. No network, disk, or database access is performed during this function.

---

## function: `serialize_certifications_to_markdown(certifications: CertificationsResponse | None) -> str`

Serialize certifications information to Markdown format.

Args:
    certifications (CertificationsResponse | None): Certifications information to serialize, containing a list of certifications.

Returns:
    str: Markdown formatted certifications section.

Notes:
    1. Initializes an empty list of lines and adds a heading.
    2. For each certification in the list:
        a. Adds a subsection header.
        b. Adds each field (name, issuer, id, issued_date, expiry_date) as direct fields if present.
        c. Adds a blank line after each certification.
    3. Joins the lines with newlines.
    4. Returns the formatted string with a trailing newline.
    5. No network, disk, or database access is performed during this function.

---

## function: `update_resume_content_with_structured_data(current_content: str, personal_info: PersonalInfoResponse | None, education: EducationResponse | None, certifications: CertificationsResponse | None, experience: ExperienceResponse | None) -> str`

Update resume content with structured data by replacing specific sections.

Args:
    current_content (str): Current resume Markdown content to update.
    personal_info (PersonalInfoResponse | None): Updated personal information to insert. If None, the existing info is preserved.
    education (EducationResponse | None): Updated education information to insert. If None, the existing info is preserved.
    certifications (CertificationsResponse | None): Updated certifications information to insert. If None, the existing info is preserved.
    experience (ExperienceResponse | None): Updated experience information to insert. If None, the existing info is preserved.

Returns:
    str: Updated resume content with new structured data.

Notes:
    1. Extracts existing sections from `current_content` if they are not provided as arguments.
    2. reconstructs the full resume using the combination of new and existing data.

---


===

===
# File: `resume_editor/app/utils/__init__.py`


===

===
# File: `resume_editor/app/web/__init__.py`


===

===
# File: `resume_editor/app/web/admin.py`


===

===
# File: `resume_editor/app/core/__init__.py`


===

===
# File: `resume_editor/app/core/config.py`

## function: `get_settings() -> Settings`

Get the global settings instance.

This function returns a singleton instance of the Settings class,
which contains all application configuration values.

Args:
    None: This function does not take any arguments.

Returns:
    Settings: The global settings instance, containing all configuration values.
        The instance is created by loading environment variables and applying defaults.

Raises:
    ValidationError: If required environment variables are missing or invalid.
    ValueError: If the .env file cannot be read or parsed.

Notes:
    1. Reads configuration from environment variables using the .env file.
    2. If environment variables are not set, default values are used.
    3. The Settings class uses Pydantic's validation and configuration features to ensure correct values.
    4. The function returns a cached instance to avoid repeated parsing of the .env file.
    5. This function performs disk access to read the .env file at startup.
    6. If the .env file is missing or cannot be read, a ValidationError may be raised.
    7. The function may raise a ValueError if required environment variables are not provided and no default is available.

---

## `Settings` class

Application settings loaded from environment variables.

This class defines all configuration values used by the application,
including database connection details, security parameters, and API keys.
Values are loaded from environment variables with fallback defaults.

Attributes:
    database_url (PostgresDsn): Database connection URL for PostgreSQL.
        This is used to establish connection to the application's database.
    secret_key (str): Secret key for signing JWT tokens.
        Must be kept secure and changed in production.
    algorithm (str): Algorithm used for JWT token encoding.
        Currently uses HS256 (HMAC-SHA256).
    access_token_expire_minutes (int): Duration in minutes for which access tokens remain valid.
    llm_api_key (str | None): API key for accessing LLM services.
        Optional; used when LLM functionality is needed.
    encryption_key (str): Key used for encrypting sensitive data.

---
## method: `Settings.database_url(self: UnknownType) -> PostgresDsn`

Assembled database URL from components.

Args:
    None: This property does not take any arguments.

Returns:
    PostgresDsn: The fully assembled PostgreSQL connection URL.

Notes:
    1. Constructs the database URL using the components: scheme, username, password, host, port, and path.
    2. The scheme is set to "postgresql".
    3. The username, password, host, port, and database name are retrieved from the instance attributes.
    4. The resulting URL is returned as a PostgresDsn object.
    5. This function performs disk access to read the .env file at startup.

---

===

===
# File: `resume_editor/app/core/security.py`

## function: `create_access_token(data: dict, settings: Settings, expires_delta: timedelta | None, impersonator: str | None) -> str`

Create a JWT access token.

Args:
    data (dict): The data to encode in the token (e.g., user ID, role).
    settings (Settings): The application settings object.
    expires_delta (Optional[timedelta]): Custom expiration time for the token. If None, uses default value.
    impersonator (str | None): The username of the administrator impersonating the user.

Returns:
    str: The encoded JWT token as a string.

Notes:
    1. Copy the data to avoid modifying the original.
    2. If an impersonator is specified, add it to the token claims.
    3. Set expiration time based on expires_delta or default.
    4. Encode the data with the secret key and algorithm.
    5. No database or network access in this function.

---

## function: `verify_password(plain_password: str, hashed_password: str) -> bool`

Verify a plain password against a hashed password.

Args:
    plain_password (str): The plain text password to verify.
    hashed_password (str): The hashed password to compare against.

Returns:
    bool: True if the password matches, False otherwise.

Notes:
    1. Use bcrypt to verify the password.
    2. No database or network access in this function.

---

## function: `get_password_hash(password: str) -> str`

Hash a plain password.

Args:
    password (str): The plain text password to hash.

Returns:
    str: The hashed password.

Notes:
    1. Use bcrypt to hash the password.
    2. No database or network access in this function.

---

## function: `authenticate_user(db: Session, username: str, password: str) -> Optional['User']`

Authenticate a user by username and password.

Args:
    db (Session): Database session used to query for user records.
    username (str): Username to authenticate.
    password (str): Password to verify.

Returns:
    Optional[User]: The authenticated user if successful, None otherwise.

Notes:
    1. Query the database for a user with the given username.
    2. If user exists and password is correct, return the user.
    3. Otherwise, return None.

---

## function: `encrypt_data(data: str) -> str`

Encrypts data using Fernet symmetric encryption.

Args:
    data (str): The plaintext data to encrypt.

Returns:
    str: The encrypted data, encoded as a string.

Notes:
    1. Use Fernet to encrypt the data.
    2. No database or network access in this function.

---

## function: `decrypt_data(encrypted_data: str) -> str`

Decrypts data using Fernet symmetric encryption.

Args:
    encrypted_data (str): The encrypted data to decrypt.

Returns:
    str: The decrypted plaintext data.

Notes:
    1. Use Fernet to decrypt the data.
    2. No database or network access in this function.

---


===

===
# File: `resume_editor/app/core/auth.py`

## function: `get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session) -> User`

Retrieve the authenticated user from the provided JWT token.

Args:
    token: JWT token extracted from the request header, used to authenticate the user.
        Type: str
        Purpose: The JWT token that contains the user's identity and is used for authentication.
    db: Database session dependency used to query the database for the user.
        Type: Session
        Purpose: Provides a connection to the database to retrieve the user record by username.

Returns:
    User: The authenticated User object corresponding to the token's subject (username).
        Type: User
        Purpose: Returns the user object if authentication is successful.

Raises:
    HTTPException: Raised when the credentials are invalid or the user is not found.
        Status Code: 401 UNAUTHORIZED
        Detail: "Could not validate credentials"
        Headers: {"WWW-Authenticate": "Bearer"}

Notes:
    1. Initialize an HTTP 401 exception with a generic error message and "Bearer" authentication header.
    2. Decode the JWT token using the secret key and algorithm to extract the subject (username).
    3. If the subject (username) is missing from the token payload, raise the credentials exception.
    4. If the JWT token is invalid or malformed, catch the JWTError and raise the credentials exception.
    5. Query the database using the retrieved username to find the corresponding User record.
    6. If the user is not found in the database, raise the credentials exception.
    7. Return the User object if all authentication checks pass.

Database Access:
    - Queries the User table to retrieve a user record by username.

---

## function: `get_current_user_from_cookie(request: Request, db: Session) -> User`

Retrieve the authenticated user from the JWT token in the request cookie.

For browser-based requests that fail authentication, this function will
raise an HTTPException that results in a redirect to the login page.
For API requests, it will raise a 401 HTTPException.

Args:
    request: The request object, used to access cookies and headers.
    db: Database session dependency.

Returns:
    User: The authenticated User object if the token is valid.

Raises:
    HTTPException: Raised for API requests when the token is missing, invalid, or the user is not found.
        Also raised to redirect users to the login page or to the change password page.

Notes:
    1.  Determine if the request is from a browser by checking the 'Accept' header.
    2.  Attempt to get the 'access_token' from cookies. On failure, redirect
        browser requests to '/login' or raise 401 for API requests.
    3.  Decode the JWT. On failure, redirect or raise 401.
    4.  Verify the username from the JWT payload. On failure, redirect or raise 401.
    5.  Retrieve the user from the database. On failure, redirect or raise 401.
    6.  If the user is successfully authenticated, check for a forced password change.
        If required, redirect the user to the change password page.
    7.  Return the authenticated User object if all checks pass.

Database Access:
    - Queries the User table to retrieve a user record by username.

---

## function: `get_optional_current_user_from_cookie(request: Request, db: Session) -> User | None`

Retrieve an optional authenticated user from the JWT token in the request cookie.

Args:
    request: The request object, used to access cookies.
        Type: Request
        Purpose: Provides access to the HTTP request, including cookies.
    db: Database session dependency.
        Type: Session
        Purpose: Provides a connection to the database to retrieve the user record.

Returns:
    User | None: The authenticated User object if the token is valid, otherwise None.
        Type: User | None
        Purpose: Returns the user object if authentication succeeds, or None if no valid token is present.

Notes:
    1. Attempt to retrieve the authenticated user using `get_current_user_from_cookie`.
    2. If `get_current_user_from_cookie` raises an HTTPException for a forced password change,
       this function propagates that exception.
    3. For any other HTTPException (e.g., login redirect for browsers, 401 for APIs),
       this function returns `None` as the user is not authenticated.
    4. If authentication is successful, the User object is returned.

Database Access:
    - Queries the User table to retrieve a user record by username.

---

## function: `verify_admin_privileges(user: User) -> User`

Verify that a user has admin privileges.

Args:
    user (User): The user object to check for admin privileges.
        Type: User
        Purpose: The user whose roles are checked to determine if they are an admin.

Returns:
    User: The user object if they have admin privileges.
        Type: User
        Purpose: Returns the user object if the check passes.

Raises:
    HTTPException: Raised if the user does not have admin privileges.
        Status Code: 403 FORBIDDEN
        Detail: "The user does not have admin privileges"

Notes:
    1. Iterate through the user's roles.
    2. Check if any role has the name 'admin'.
    3. If no role with the name 'admin' is found, log a warning and raise an HTTPException with status 403.
    4. Return the user object if an 'admin' role is found.

---

## function: `get_current_admin_user(current_user: Annotated[User, Depends(get_current_user)]) -> User`

Verify that the current user has administrator privileges.

This dependency relies on `get_current_user` to retrieve the authenticated user.
It then checks the user's roles to determine if they are an administrator.

Args:
    current_user (User): The user object obtained from the `get_current_user`
        dependency.
        Type: User
        Purpose: The authenticated user whose roles are checked for admin privileges.

Returns:
    User: The user object if the user has the 'admin' role.
        Type: User
        Purpose: Returns the user object if the user is an admin.

Raises:
    HTTPException: A 403 Forbidden error if the user is not an admin.
        Status Code: 403 FORBIDDEN
        Detail: "The user does not have admin privileges"

Notes:
    1. Log a debug message indicating the function has started.
    2. Call `verify_admin_privileges` to check if the user has admin roles.
    3. Log a debug message indicating the function is returning.
    4. Return the user object if the user has admin privileges.

---

## function: `get_current_admin_user_from_cookie(current_user: Annotated[User, Depends(get_current_user_from_cookie)]) -> User`

Verify that the current user (from cookie) has admin privileges.

This dependency relies on `get_current_user_from_cookie` to retrieve the authenticated user.
It then checks the user's roles to determine if they are an administrator.

Args:
    current_user (User): The user object obtained from the `get_current_user_from_cookie`
        dependency.
        Type: User
        Purpose: The authenticated user whose roles are checked for admin privileges.

Returns:
    User: The user object if the user has the 'admin' role.
        Type: User
        Purpose: Returns the user object if the user is an admin.

Raises:
    HTTPException: A 403 Forbidden error if the user is not an admin.
        Status Code: 403 FORBIDDEN
        Detail: "The user does not have admin privileges"

Notes:
    1. Log a debug message indicating the function has started.
    2. Call `verify_admin_privileges` to check if the user has admin roles.
    3. Log a debug message indicating the function is returning.
    4. Return the user object if the user has admin privileges.

---


===

===
# File: `resume_editor/app/database/__init__.py`


===

===
# File: `resume_editor/app/database/database.py`

## function: `get_engine() -> Engine`

Get or create the database engine.

Args:
    None

Returns:
    Engine: The SQLAlchemy engine instance used to connect to the database.

Notes:
    1. Create the engine only when first accessed to avoid premature connection.
    2. Reuse the same engine instance on subsequent calls to ensure consistency.
    3. Network access occurs when creating the engine, using the database URL from settings.

---

## function: `get_session_local() -> sessionmaker[Session]`

Get or create the session local factory.

Args:
    None

Returns:
    sessionmaker: The SQLAlchemy sessionmaker instance used to create database sessions.

Notes:
    1. Create the sessionmaker only when first accessed to avoid premature configuration.
    2. Reuse the same sessionmaker instance on subsequent calls to ensure consistent session behavior.
    3. No network access in this function itself; it uses the previously created engine.

---

## function: `get_db() -> Generator[Session, None, None]`

Dependency to provide database sessions to route handlers.

Args:
    None

Yields:
    Session: A database session for use in route handlers.

Notes:
    1. Create a new database session using the sessionmaker factory.
    2. Yield the session to be used in route handlers.
    3. Ensure the session is closed after use to release resources.
    4. No network access in this function itself; the session is created from the existing engine.

---


===

===
# File: `resume_editor/app/models/__init__.py`


===

===
# File: `resume_editor/app/models/user.py`

## `User` class

User model for authentication and session management.

Attributes:
    id (int): Unique identifier for the user.
    username (str): Unique username for the user.
    email (str): Unique email address for the user.
    hashed_password (str): Hashed password for the user.
    is_active (bool): Whether the user account is active.
    last_login_at (datetime): Timestamp of the last successful login.
    force_password_change (bool): If true, user must change password on next login.
    attributes (dict): Flexible key-value store for user-specific attributes.
    roles (list[Role]): Roles assigned to the user for authorization.
    resumes (list[Resume]): Resumes associated with the user.
    settings (UserSettings): User-specific settings.

---
## method: `User.__init__(self: UnknownType, data: UserData) -> UnknownType`

Initialize a User instance.

Args:
    data (UserData): An object containing all initialization data for the user.

Returns:
    None

Notes:
    1. Validate that username is a non-empty string.
    2. Validate that email is a non-empty string.
    3. Validate that hashed_password is a non-empty string.
    4. Validate that is_active is a boolean.
    5. Validate that attributes is a dict or None.
    6. Assign all values to instance attributes.
    7. Log the initialization of the user with their username.
    8. This operation does not involve network, disk, or database access.

---
## method: `User.validate_username(self: UnknownType, _key: str, username: str) -> str`

Validate the username field.

Args:
    _key (str): The field name being validated (should be 'username').
    username (str): The username value to validate. Must be a non-empty string.

Returns:
    str: The validated username (stripped of leading/trailing whitespace).

Notes:
    1. Ensure username is a string.
    2. Ensure username is not empty after stripping whitespace.
    3. This operation does not involve network, disk, or database access.

---
## method: `User.validate_email(self: UnknownType, _key: str, email: str) -> str`

Validate the email field.

Args:
    _key (str): The field name being validated (should be 'email').
    email (str): The email value to validate. Must be a non-empty string.

Returns:
    str: The validated email (stripped of leading/trailing whitespace).

Notes:
    1. Ensure email is a string.
    2. Ensure email is not empty after stripping whitespace.
    3. This operation does not involve network, disk, or database access.

---
## method: `User.validate_hashed_password(self: UnknownType, _key: str, hashed_password: str) -> str`

Validate the hashed_password field.

Args:
    _key (str): The field name being validated (should be 'hashed_password').
    hashed_password (str): The hashed password value to validate. Must be a non-empty string.

Returns:
    str: The validated hashed password (stripped of leading/trailing whitespace).

Notes:
    1. Ensure hashed_password is a string.
    2. Ensure hashed_password is not empty after stripping whitespace.
    3. This operation does not involve network, disk, or database access.

---
## method: `User.validate_is_active(self: UnknownType, _key: str, is_active: bool) -> bool`

Validate the is_active field.

Args:
    _key (str): The field name being validated (should be 'is_active').
    is_active (bool): The is_active value to validate. Must be a boolean.

Returns:
    bool: The validated is_active value.

Notes:
    1. Ensure is_active is a boolean.
    2. This operation does not involve network, disk, or database access.

---
## method: `User.validate_attributes(self: UnknownType, _key: str, attributes: dict[str, Any] | None) -> dict[str, Any] | None`

Validate the attributes field.

Args:
    _key (str): The field name being validated (should be 'attributes').
    attributes (dict | None): The attributes value to validate. Must be a dictionary or None.

Returns:
    dict | None: The validated attributes.

Notes:
    1. If attributes is not None, ensure it is a dictionary.
    2. This operation does not involve network, disk, or database access.

---

===

===
# File: `resume_editor/app/models/user_settings.py`

## `UserSettings` class

Stores user-specific settings, such as LLM configurations.

Attributes:
    id (int): Primary key.
    user_id (int): Foreign key to the user.
    llm_endpoint (str | None): Custom LLM API endpoint URL.
    llm_model_name (str | None): The user-specified LLM model name.
    encrypted_api_key (str | None): Encrypted API key for the LLM service.
    user (User): Relationship to the User model.

---
## method: `UserSettings.__init__(self: UnknownType, user_id: int, llm_endpoint: str | None, llm_model_name: str | None, encrypted_api_key: str | None) -> UnknownType`

Initialize a UserSettings instance.

Args:
    user_id (int): The ID of the user these settings belong to.
    llm_endpoint (str | None): Custom LLM API endpoint URL.
    llm_model_name (str | None): The user-specified LLM model name.
    encrypted_api_key (str | None): Encrypted API key for the LLM service.

Returns:
    None

Notes:
    1. Assign all values to instance attributes.
    2. Log the initialization of the user settings.
    3. This operation does not involve network, disk, or database access.

---

===

===
# File: `resume_editor/app/models/resume_model.py`

## `Resume` class

Resume model for storing user resumes.

Attributes:
    id (int): Unique identifier for the resume.
    user_id (int): Foreign key to User model, identifying the user who owns the resume.
    name (str): User-assigned descriptive name for the resume, must be non-empty.
    content (str): The Markdown text content of the resume, must be non-empty.
    created_at (datetime): Timestamp when the resume was created.
    updated_at (datetime): Timestamp when the resume was last updated.
    is_active (bool): Whether the resume is currently active.
    is_base (bool): True if this is a base resume, False if it is a refined version.
    job_description (str | None): The job description associated with a refined resume.
    parent_id (int | None): A self-referencing foreign key to link a refined resume to its base resume.
    parent (Resume): The parent resume relationship.
    children (list[Resume]): The child resumes relationship.
    notes (str | None): User-provided notes for the resume.
    introduction (str | None): AI-generated introduction for the resume.

---
## method: `Resume.__init__(self: UnknownType, data: ResumeData) -> UnknownType`

Initialize a Resume instance.

Args:
    data (ResumeData): An object containing the data for the new resume.

Returns:
    None

Notes:
    1. Assigns attributes from the `data` object to the `Resume` instance.
    2. This constructor does not perform validation. It assumes `data` is a valid `ResumeData` object.
    3. Logs the initialization of the resume.
    4. This function does not perform disk, network, or database access.

---

===

===
# File: `resume_editor/app/models/role.py`


===

===
# File: `resume_editor/app/models/resume/resume.py`


===

===
# File: `resume_editor/app/models/resume/education.py`

## `Degree` class

Represents details of a specific academic degree earned.

Attributes:
    school (str): The name of the educational institution.
    degree (str | None): The type of degree (e.g., Bachelor, Master).
    start_date (datetime | None): The start date of the program.
    end_date (datetime | None): The end date of the program.
    major (str | None): The major field of study.
    gpa (str | None): The grade point average.

---
## method: `Degree.validate_school(cls: UnknownType, v: str) -> UnknownType`

Validate the school field.

Args:
    v (str): The school value to validate. Must be a non-empty string.

Returns:
    str: The validated school (stripped of leading/trailing whitespace).

Raises:
    ValueError: If the school is empty or contains only whitespace.

Notes:
    1. Ensure school is a string.
    2. Ensure school is not empty after stripping whitespace.

---
## method: `Degree.validate_degree(cls: UnknownType, v: str | None) -> UnknownType`

Validate the degree field.

Args:
    v (str | None): The degree value to validate. Must be a non-empty string or None.

Returns:
    str | None: The validated degree (stripped of leading/trailing whitespace) or None.

Raises:
    ValueError: If the degree is empty after stripping whitespace.

Notes:
    1. Ensure degree is a string or None.
    2. Ensure degree is not empty after stripping whitespace.

---
## method: `Degree.validate_major(cls: UnknownType, v: str | None) -> UnknownType`

Validate the major field.

Args:
    v (str | None): The major value to validate. Must be a non-empty string or None.

Returns:
    str | None: The validated major (stripped of leading/trailing whitespace) or None.

Raises:
    ValueError: If the major is empty after stripping whitespace.

Notes:
    1. Ensure major is a string or None.
    2. Ensure major is not empty after stripping whitespace.

---
## method: `Degree.validate_gpa(cls: UnknownType, v: str | None) -> UnknownType`

Validate the gpa field.

Args:
    v (str | None): The gpa value to validate. Must be a non-empty string or None.

Returns:
    str | None: The validated gpa (stripped of leading/trailing whitespace) or None.

Raises:
    ValueError: If the gpa is empty after stripping whitespace.

Notes:
    1. Ensure gpa is a string or None.
    2. Ensure gpa is not empty after stripping whitespace.

---
## method: `Degree.validate_end_date(cls: UnknownType, v: datetime | None, info: ValidationInfo) -> UnknownType`

Validate that start_date is not after end_date.

Args:
    v (datetime | None): The end_date value to validate.
    info (ValidationInfo): Validation info containing data.

Returns:
    datetime | None: The validated end_date.

Raises:
    ValueError: If end_date is before start_date.

Notes:
    1. If both start_date and end_date are provided, ensure start_date is not after end_date.

---
## `Degrees` class

Represents a collection of academic degrees earned.

Attributes:
    degrees (list[Degree]): A list of Degree objects representing educational achievements.

---
## method: `Degrees.__iter__(self: UnknownType) -> UnknownType`

Iterate over the degrees.

Returns:
    Iterator: An iterator over the degrees list.

Notes:
    No external access (network, disk, or database) is performed.

---
## method: `Degrees.__len__(self: UnknownType) -> UnknownType`

Return the number of degrees.

Returns:
    int: The number of degrees in the list.

Notes:
    No external access (network, disk, or database) is performed.

---
## method: `Degrees.__getitem__(self: UnknownType, index: int) -> UnknownType`

Return the degree at the given index.

Args:
    index (int): The index of the degree to retrieve.

Returns:
    Degree: The Degree object at the specified index.

Notes:
    No external access (network, disk, or database) is performed.

---

===

===
# File: `resume_editor/app/models/resume/certifications.py`

## `Certification` class

Represents a professional certification.

Attributes:
    name (str): The name of the certification.
    issuer (str | None): The organization that issued the certification.
    issued (datetime | None): The date the certification was issued.
    expires (datetime | None): The date the certification expires.
    certification_id (str | None): An identifier for the certification.

---
## method: `Certification.validate_name(cls: UnknownType, v: str) -> UnknownType`

Validate the name field.

Args:
    v (str): The name value to validate. Must be a non-empty string.

Returns:
    str: The validated name, stripped of leading/trailing whitespace.

Raises:
    ValueError: If the name is not a string or is empty.

Notes:
    1. Ensure name is a string.
    2. Ensure name is not empty.

---
## method: `Certification.validate_optional_strings(cls: UnknownType, v: str | None) -> UnknownType`

Validate optional string fields.

Args:
    v (str | None): The field value to validate. Must be a string or None.

Returns:
    str | None: The validated field value.

Raises:
    ValueError: If the field is neither a string nor None.

Notes:
    1. Ensure field is a string or None.

---
## method: `Certification.validate_dates(cls: UnknownType, v: datetime | None) -> UnknownType`

Validate the date fields.

Args:
    v (datetime | None): The date value to validate. Must be a datetime object or None.

Returns:
    datetime | None: The validated date.

Raises:
    ValueError: If the date is neither a datetime object nor None.

Notes:
    1. Ensure date is a datetime object or None.

---
## method: `Certification.validate_date_order(self: UnknownType) -> Self`

Validate that issued date is not after expires date.

Returns:
    Certification: The validated model instance.

Raises:
    ValueError: If expires date is before issued date.

Notes:
    1. If both issued and expires dates are provided, ensure issued is not after expires.

---
## `Certifications` class

Represents a collection of professional certifications.

Attributes:
    certifications (list[Certification]): A list of Certification objects.

---
## method: `Certifications.validate_certifications(cls: UnknownType, v: list['Certification']) -> UnknownType`

Validate the certifications field.

Args:
    v (list[Certification]): The certifications value to validate. Must be a list of Certification objects.

Returns:
    list[Certification]: The validated certifications list.

Raises:
    ValueError: If certifications is not a list or contains non-Certification items.

Notes:
    1. Ensure certifications is a list.
    2. Ensure all items in certifications are instances of Certification.

---
## method: `Certifications.__iter__(self: UnknownType) -> UnknownType`

Iterate over the certifications.

Returns:
    An iterator over the list of certification objects.

Notes:
    1. Return an iterator over the certifications list.

---
## method: `Certifications.__len__(self: UnknownType) -> UnknownType`

Return the number of certifications.

Returns:
    int: The integer count of certifications in the list.

Notes:
    1. Return the length of the certifications list.

---
## method: `Certifications.__getitem__(self: UnknownType, index: int) -> UnknownType`

Return the certification at the given index.

Args:
    index (int): The index of the certification to retrieve.

Returns:
    Certification: The Certification object at the specified index.

Notes:
    1. Retrieve and return the certification at the given index.

---
## method: `Certifications.list_class(self: UnknownType) -> type['Certification']`

Return the type that will be contained in the list.

Returns:
    type: The Certification class.

Notes:
    1. Return the Certification class.

---

===

===
# File: `resume_editor/app/models/resume/personal.py`

## `ContactInfo` class

Holds personal contact details such as name, email, phone, and location.

Attributes:
    name (str): The full name of the person.
    email (str | None): The email address of the person, or None if not provided.
    phone (str | None): The phone number of the person, or None if not provided.
    location (str | None): The physical location (e.g., city and country) of the person, or None if not provided.

---
## method: `ContactInfo.validate_name(cls: UnknownType, v: str) -> UnknownType`

Validate the name field.

Args:
    v: The name value to validate. Must be a non-empty string.

Returns:
    str: The validated name (stripped of leading/trailing whitespace).

Raises:
    ValueError: If the name is not a string or is empty after stripping whitespace.

Notes:
    1. Ensure name is a string.
    2. Ensure name is not empty after stripping whitespace.

---
## method: `ContactInfo.validate_email(cls: UnknownType, v: str | None) -> UnknownType`

Validate the email field.

Args:
    v: The email value to validate. Must be a non-empty string or None.

Returns:
    str: The validated email (stripped of leading/trailing whitespace).

Raises:
    ValueError: If the email is not a string or is empty after stripping whitespace.

Notes:
    1. Ensure email is a string or None.
    2. Ensure email is not empty after stripping whitespace.

---
## method: `ContactInfo.validate_phone(cls: UnknownType, v: str | None) -> UnknownType`

Validate the phone field.

Args:
    v: The phone value to validate. Must be a non-empty string or None.

Returns:
    str: The validated phone (stripped of leading/trailing whitespace).

Raises:
    ValueError: If the phone is not a string or is empty after stripping whitespace.

Notes:
    1. Ensure phone is a string or None.
    2. Ensure phone is not empty after stripping whitespace.

---
## method: `ContactInfo.validate_location(cls: UnknownType, v: str | None) -> UnknownType`

Validate the location field.

Args:
    v: The location value to validate. Must be a non-empty string or None.

Returns:
    str: The validated location (stripped of leading/trailing whitespace).

Raises:
    ValueError: If the location is not a string or is empty after stripping whitespace.

Notes:
    1. Ensure location is a string or None.
    2. Ensure location is not empty after stripping whitespace.

---
## `Websites` class

Holds personal website and social media links.

Attributes:
    website (str | None): The personal website URL, or None if not provided.
    github (str | None): The GitHub profile URL, or None if not provided.
    linkedin (str | None): The LinkedIn profile URL, or None if not provided.
    twitter (str | None): The Twitter profile URL, or None if not provided.

---
## method: `Websites.validate_website(cls: UnknownType, v: str | None) -> UnknownType`

Validate the website field.

Args:
    v: The website value to validate. Must be a non-empty string or None.

Returns:
    str: The validated website (stripped of leading/trailing whitespace).

Raises:
    ValueError: If the website is not a string or is empty after stripping whitespace.

Notes:
    1. Ensure website is a string or None.
    2. Ensure website is not empty after stripping whitespace.

---
## method: `Websites.validate_github(cls: UnknownType, v: str | None) -> UnknownType`

Validate the github field.

Args:
    v: The github value to validate. Must be a non-empty string or None.

Returns:
    str: The validated github (stripped of leading/trailing whitespace).

Raises:
    ValueError: If the github is not a string or is empty after stripping whitespace.

Notes:
    1. Ensure github is a string or None.
    2. Ensure github is not empty after stripping whitespace.

---
## method: `Websites.validate_linkedin(cls: UnknownType, v: str | None) -> UnknownType`

Validate the linkedin field.

Args:
    v: The linkedin value to validate. Must be a non-empty string or None.

Returns:
    str: The validated linkedin (stripped of leading/trailing whitespace).

Raises:
    ValueError: If the linkedin is not a string or is empty after stripping whitespace.

Notes:
    1. Ensure linkedin is a string or None.
    2. Ensure linkedin is not empty after stripping whitespace.

---
## method: `Websites.validate_twitter(cls: UnknownType, v: str | None) -> UnknownType`

Validate the twitter field.

Args:
    v: The twitter value to validate. Must be a non-empty string or None.

Returns:
    str: The validated twitter (stripped of leading/trailing whitespace).

Raises:
    ValueError: If the twitter is not a string or is empty after stripping whitespace.

Notes:
    1. Ensure twitter is a string or None.
    2. Ensure twitter is not empty after stripping whitespace.

---
## `VisaStatus` class

Holds information about work authorization and sponsorship requirements.

Attributes:
    work_authorization (str | None): The current work authorization status (e.g., "US Citizen", "H-1B"), or None if not provided.
    require_sponsorship (bool | None): A boolean indicating if sponsorship is required, or None if not provided.

---
## method: `VisaStatus.validate_work_authorization(cls: UnknownType, v: str | None) -> UnknownType`

Validate the work_authorization field.

Args:
    v: The work_authorization value to validate. Must be a non-empty string or None.

Returns:
    str: The validated work_authorization (stripped of leading/trailing whitespace).

Raises:
    ValueError: If the work_authorization is not a string or is empty after stripping whitespace.

Notes:
    1. Ensure work_authorization is a string or None.
    2. Ensure work_authorization is not empty after stripping whitespace.

---
## method: `VisaStatus.validate_require_sponsorship(cls: UnknownType, v: bool | str | None) -> UnknownType`

Validate the require_sponsorship field.

Args:
    v: The require_sponsorship value to validate. Must be a boolean, string ("yes"/"no"), or None.

Returns:
    bool: The validated require_sponsorship value.

Raises:
    ValueError: If the require_sponsorship is not a boolean, string, or None, or if the string is not "yes" or "no".

Notes:
    1. Ensure require_sponsorship is a boolean, string ("yes"/"no"), or None.
    2. If require_sponsorship is a string, convert "yes" to True and "no" to False.
    3. If require_sponsorship is not None and not a string, assign it directly.
    4. Otherwise, set require_sponsorship to None.

---
## `Banner` class

Holds a personal banner message with cleaned text content.

Attributes:
    text (str): The cleaned text content of the banner. Internal blank lines are preserved,
        while surrounding whitespace is removed.

---
## method: `Banner.validate_text(cls: UnknownType, v: str) -> UnknownType`

Validate the text field and clean it.

Args:
    v: The raw text content of the banner, potentially including leading/trailing or internal blank lines.

Returns:
    str: The cleaned text content of the banner.

Raises:
    ValueError: If the text is not a string.

Notes:
    1. Ensure text is a string.
    2. Preserves internal newlines and blank lines.
    3. Only removes surrounding whitespace from the text block.

---
## `Note` class

Holds a personal note with cleaned text content.

Attributes:
    text (str): The cleaned text content of the note. Internal blank lines are preserved,
        while surrounding whitespace is removed.

---
## method: `Note.validate_text(cls: UnknownType, v: str) -> UnknownType`

Validate the text field and clean it.

Args:
    v: The raw text content of the note, potentially including leading/trailing or internal blank lines.

Returns:
    str: The cleaned text content of the note.

Raises:
    ValueError: If the text is not a string.

Notes:
    1. Ensure text is a string.
    2. Preserves internal newlines and blank lines.
    3. Only removes surrounding whitespace from the text block.

---

===

===
# File: `resume_editor/app/models/resume/__init__.py`


===

===
# File: `resume_editor/app/models/resume/experience.py`

## `RoleSkills` class

Represents skills used in a professional role.

Attributes:
    skills (list[str]): A list of non-empty, stripped skill strings.

---
## method: `RoleSkills.validate_skills(cls: UnknownType, v: list[str]) -> UnknownType`

Validate the skills field.

Args:
    v: The skills value to validate. Must be a list of strings.

Returns:
    list[str]: The validated and cleaned skills list.

Notes:
    1. Ensure skills is a list.
    2. Ensure all items in skills are strings.
    3. Strip whitespace from each skill and filter out empty strings.
    4. Raise a ValueError if skills is not a list or if any skill is not a string.
    5. Return the cleaned list of non-empty skills.

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
    inclusion_status (InclusionStatus): The inclusion status of the role.

---
## method: `RoleBasics.validate_company(cls: UnknownType, v: str) -> UnknownType`

Validate the company field.

Args:
    v: The company value to validate. Must be a non-empty string.

Returns:
    str: The validated company.

Raises:
    ValueError: If company is not a string or is empty.

Notes:
    1. Ensure company is a string.
    2. Ensure company is not empty.
    3. Strip whitespace from the company name.
    4. Raise a ValueError if company is not a string or is empty.

---
## method: `RoleBasics.validate_title(cls: UnknownType, v: str) -> UnknownType`

Validate the title field.

Args:
    v: The title value to validate. Must be a non-empty string.

Returns:
    str: The validated title.

Raises:
    ValueError: If title is not a string or is empty.

Notes:
    1. Ensure title is a string.
    2. Ensure title is not empty.
    3. Strip whitespace from the title.
    4. Raise a ValueError if title is not a string or is empty.

---
## method: `RoleBasics.validate_end_date(cls: UnknownType, v: datetime | None, info: ValidationInfo) -> UnknownType`

Validate the end_date field.

Args:
    v: The end_date value to validate. Must be a datetime object or None.
    info: Validation info containing data.

Returns:
    datetime: The validated end_date.

Raises:
    ValueError: If end_date is not a datetime object or None, or if end_date is before start_date.

Notes:
    1. Ensure end_date is a datetime object or None.
    2. If end_date is provided, ensure it is not before start_date.
    3. Raise a ValueError if end_date is not a datetime object or None, or if end_date is before start_date.

---
## `Roles` class

Represents a collection of professional roles.

Attributes:
    roles (list[Role]): A list of Role objects.

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
## method: `Roles.list_class(self: UnknownType) -> type[Role]`

Return the class for the list.

Returns:
    The Role class.

---
## `ProjectSkills` class

Represents skills used in a project.

Attributes:
    skills (list[str]): A list of non-empty, stripped skill strings.

---
## method: `ProjectSkills.validate_skills(cls: UnknownType, v: list[str]) -> UnknownType`

Validate the skills field.

Args:
    v: The skills value to validate. Must be a list of strings.

Returns:
    list[str]: The validated and cleaned skills list.

Raises:
    ValueError: If skills is not a list or if any skill is not a string.

Notes:
    1. Ensure skills is a list.
    2. Ensure all items in skills are strings.
    3. Strip whitespace from each skill and filter out empty strings.
    4. Raise a ValueError if skills is not a list or if any skill is not a string.
    5. Return the cleaned list of non-empty skills.

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
    inclusion_status (InclusionStatus): The inclusion status of the project.

---
## method: `ProjectOverview.validate_title(cls: UnknownType, v: str) -> UnknownType`

Validate the title field.

Args:
    v: The title value to validate. Must be a non-empty string.

Returns:
    str: The validated title.

Raises:
    ValueError: If title is not a string or is empty.

Notes:
    1. Ensure title is a string.
    2. Ensure title is not empty.
    3. Strip whitespace from the title.
    4. Raise a ValueError if title is not a string or is empty.

---
## method: `ProjectOverview.validate_date_order(cls: UnknownType, v: datetime | None, info: ValidationInfo) -> UnknownType`

Validate that start_date is not after end_date.

Args:
    v: The end_date value to validate.
    info: Validation info containing data.

Returns:
    datetime: The validated end_date.

Raises:
    ValueError: If end_date is before start_date.

Notes:
    1. If both start_date and end_date are provided, ensure start_date is not after end_date.
    2. Raise a ValueError if end_date is before start_date.

---
## `Projects` class

Represents a collection of projects.

Attributes:
    projects (list[Project]): A list of Project objects.

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
## method: `Projects.list_class(self: UnknownType) -> type[Project]`

Return the class of the list.

Returns:
    The Project class.

---

===

===
# File: `resume_editor/app/schemas/user.py`

## `AdminUserResponse` class

Detailed user response schema for administrators.

Extends the standard UserResponse to include additional administrative fields.

Args:
    id (int): Unique identifier assigned to the user in the database.
    username (str): Unique username for the user.
    email (EmailStr): Unique email address for the user.
    is_active (bool): Indicates if the user account is active.
    roles (list[RoleResponse]): List of roles assigned to the user.
    attributes (dict[str, Any] | None): Flexible key-value attributes for the user.
    last_login_at (datetime | None): Timestamp of the last successful login.

Attributes:
    last_login_at (datetime | None): Timestamp of the last successful login.
    force_password_change (bool): Flag indicating if the user must change their password.
    resume_count (int): The number of resumes associated with the user.

Notes:
    1. This model is for administrative use only.
    2. It provides a more detailed view of user data.
    3. `resume_count` and `force_password_change` are computed fields.

---
## method: `AdminUserResponse.resume_count(self: UnknownType) -> int`

Computes the number of resumes for the user.

---
## method: `AdminUserResponse.force_password_change(self: UnknownType) -> bool`

Checks if the user must change their password.

---

===

===
# File: `resume_editor/app/schemas/__init__.py`


===

===
# File: `resume_editor/app/schemas/llm.py`


===

===
# File: `resume_editor/app/api/routes/route_logic/user.py`

## function: `change_password(db: Session, user: User, new_password: str, current_password: str | None) -> None`

Change a user's password and unset the force_password_change flag.

Args:
    db (Session): The database session used to persist changes to the user record.
    user (User): The user object whose password is being changed.
    new_password (str): The new password to set for the user.
    current_password (str | None): The user's current password, used for verification. Required for standard changes, optional for forced changes.

Returns:
    None: This function does not return a value.

Raises:
    HTTPException: For a standard password change, if the current password is not provided or is incorrect, a 400 Bad Request error is raised.

Notes:
    1. Determine if it's a forced password change by checking the user's attributes.
    2. For a standard password change (when `force_password_change` is False), verify that `current_password` is provided and correct. If not, raise an HTTPException.
    3. For a forced password change, the current password check is bypassed.
    4. Hash the new password using get_password_hash.
    5. Update the user's hashed_password attribute with the new hash.
    6. Ensure the user's attributes are initialized as a dictionary if they are None.
    7. Set the 'force_password_change' key in attributes to False.
    8. Mark the attributes as modified to ensure SQLAlchemy tracks changes.
    9. Commit the transaction to persist changes to the database.
    10. Database access: The function performs a write operation to update the user's password and attributes in the database.

---


===

===
# File: `resume_editor/app/web/admin_forms.py`


===

===
# File: `resume_editor/app/api/routes/pages/setup.py`


===

===
# File: `resume_editor/app/api/routes/route_logic/user_crud.py`

## function: `user_count(db: Session) -> int`

Counts the total number of users in the database.

Args:
    db (Session): The database session.

Returns:
    int: The total number of users.

Notes:
    1. Queries the User model to get a count of all records.
    2. Returns the count as an integer.
    3. This function performs a database read operation.

---


===

===
# File: `resume_editor/tests/app/models/test_user_settings.py`

## function: `test_user_settings_initialization() -> UnknownType`

Test UserSettings initialization.

Args:
    None

Returns:
    None

Notes:
    1. Create a UserSettings instance with all parameters.
    2. Assert that all attributes are set correctly.

---

## function: `test_user_settings_initialization_with_defaults() -> UnknownType`

Test UserSettings initialization with default values.

Args:
    None

Returns:
    None

Notes:
    1. Create a UserSettings instance with only required parameters.
    2. Assert that attributes with defaults are None.

---


===

===
# File: `resume_editor/app/llm/__init__.py`


===

===
# File: `resume_editor/app/llm/orchestration.py`

## function: `_initialize_llm_client(llm_config: LLMConfig) -> ChatOpenAI`

Initializes the ChatOpenAI client from configuration.

Args:
    llm_config (LLMConfig): Configuration for the LLM client.

Returns:
    ChatOpenAI: An initialized ChatOpenAI client instance.

Notes:
    1.  Determines the model name, using the provided `llm_model_name` or falling back to a default.
    2.  Sets up LLM parameters for temperature, endpoint, and headers (if OpenRouter is used).
    3.  Sets the API key if provided, or uses a dummy key if a custom endpoint is specified without a key.
    4.  Returns an initialized `ChatOpenAI` client.

---

## function: `_invoke_chain_and_parse(chain: Any, pydantic_model: Any) -> Any`

Invokes a LangChain chain, gets content, parses JSON, and validates with Pydantic.

Args:
    chain (Any): The LangChain runnable chain to invoke.
    pydantic_model (Any): The Pydantic model to validate the parsed JSON against.
    **kwargs (Any): Keyword arguments to pass to the chain's invoke method.

Returns:
    Any: An instance of the `pydantic_model` populated with the parsed data.

Raises:
    json.JSONDecodeError: If the LLM's response content is not valid JSON.
    ValidationError: If the parsed JSON does not conform to the `pydantic_model`.

Notes:
    1. Invokes the provided LangChain `chain` with the given `kwargs`.
    2. Extracts the content string from the result.
    3. Parses the content string as JSON using `parse_json_markdown`.
    4. Validates the parsed JSON against the `pydantic_model`.
    5. Returns the validated Pydantic model instance.
    6. No network, disk, or database access is performed.

---

## function: `_generate_introduction_from_analysis(job_analysis_json: str, resume_content: str, llm: ChatOpenAI) -> str`

Orchestrates the resume analysis and introduction synthesis steps.

Args:
    job_analysis_json (str): A JSON string representing the pre-analyzed job requirements,
                             conforming to the `JobKeyRequirements` model.
    resume_content (str): The full Markdown content of the resume.
    llm (ChatOpenAI): An initialized ChatOpenAI client instance.

Returns:
    str: The generated introduction as a Markdown-formatted bulleted list,
         or an empty string if generation fails.

Notes:
    1.  **Step 1: Resume Analysis**: Creates a chain with `INTRO_ANALYZE_RESUME_PROMPT` and a parser for `CandidateAnalysis`.
        It invokes this chain with the `resume_content` and the `job_analysis_json`.
    2.  **Step 2: Introduction Synthesis**: Creates a chain with `INTRO_SYNTHESIZE_INTRODUCTION_PROMPT` and a parser for `GeneratedIntroduction`.
        It invokes this chain with the JSON output from the resume analysis step.
    3.  Extracts the `strengths` list from the final Pydantic object and formats it as a Markdown bulleted list.
    4.  Handles JSON decoding and Pydantic validation errors by logging and returning an empty string.
    5.  This function performs multiple network requests to the configured LLM endpoint.

---

## function: `generate_introduction_from_resume(resume_content: str, job_description: str, llm_config: LLMConfig) -> str`

Generates a resume introduction using a multi-step LLM chain.

Args:
    resume_content (str): The full Markdown content of the resume.
    job_description (str): The job description to align the introduction with.
    llm_config (LLMConfig): Configuration for the LLM client.

Returns:
    str: The generated introduction, or an empty string if generation fails.

Notes:
    1.  Initializes a ChatOpenAI client using the provided `llm_config`.
    2.  **Step 1: Job Analysis**: Creates a chain with `INTRO_ANALYZE_JOB_PROMPT` to extract key skills and priorities from the job description.
    3.  Calls `_generate_introduction_from_analysis` with the job analysis result to perform the subsequent resume analysis and synthesis steps.
    4.  Handles exceptions during the job analysis step and returns an empty string on failure.
    5.  This function performs multiple network requests to the configured LLM endpoint.

---


===

===
# File: `resume_editor/app/llm/models.py`


===

===
# File: `resume_editor/app/llm/prompts.py`


===

===
# File: `resume_editor/app/api/dependencies.py`


===

===
# File: `resume_editor/app/api/routes/resume_edit.py`


===

===
# File: `resume_editor/app/api/routes/resume_export.py`

## function: `_parse_date_range(start_date: str | None, end_date: str | None) -> tuple[date | None, date | None]`

Parses start and end date strings into date objects.

---

## function: `_get_filtered_resume_content(resume_content: str, start_date: date | None, end_date: date | None) -> str`

Filters resume content by date range if dates are provided.

---

## `ResumeExportSettingsForm` class

Form data for resume export settings.

---
## method: `ResumeExportSettingsForm.__init__(self: UnknownType, include_projects: bool, render_projects_first: bool, include_education: bool) -> UnknownType`



---
## `DownloadParams` class

Parameters for downloading a rendered resume.

---
## method: `DownloadParams.__init__(self: UnknownType, render_format: RenderFormat, settings_name: RenderSettingsName, start_date: Annotated[str | None, Query()], end_date: Annotated[str | None, Query()]) -> UnknownType`



---

===

===
# File: `resume_editor/app/api/routes/html_fragments.py`

## function: `_date_format_filter(value: datetime | None, format_string: str) -> str`

Jinja2 filter to format a datetime object as a string.

---

## function: `_generate_resume_list_html(base_resumes: list[DatabaseResume], refined_resumes: list[DatabaseResume], selected_resume_id: int | None, sort_by: str | None, wrap_in_div: bool) -> str`

Generates HTML for a list of resumes, optionally marking one as selected.

Args:
    base_resumes (list[DatabaseResume]): The list of base resumes to display.
    refined_resumes (list[DatabaseResume]): The list of refined resumes to display.
    selected_resume_id (int | None): The ID of the resume to mark as selected.
    sort_by (str | None): The current sorting key applied to the resume list, if any.
    wrap_in_div (bool): If True, wrap the generated HTML in a div with id 'resume-list'.

Returns:
    str: HTML string for the resume list.

Notes:
    1. Renders the `partials/resume/_resume_list.html` template.

---

## function: `_generate_resume_detail_html(resume: DatabaseResume) -> str`

Generate the HTML for the resume detail view.

Args:
    resume (DatabaseResume): The resume object to generate HTML for.

Returns:
    str: HTML string for the resume detail view.

Notes:
    1. Renders the `partials/resume/_resume_detail.html` template.

---

## function: `_create_refine_result_html(params: RefineResultParams) -> str`

Creates the HTML for the refinement result container with controls.

Args:
    params (RefineResultParams): Parameters for rendering the template.

Returns:
    str: An HTML snippet containing a form with the refined content
         in a textarea and buttons to accept, reject, or save as new.

Notes:
    1. Renders the `partials/resume/_refine_result.html` template.

---


===

===
# File: `resume_editor/app/api/routes/resume_ai.py`

## function: `get_refine_stream_query(job_description: Annotated[str, Query(...)], limit_refinement_years: Annotated[str | None, Query()]) -> RefineStreamQueryParams`

Dependency to collect and validate refine/stream query parameters.

Args:
    job_description (str): The job description to align the resume with.
    limit_refinement_years (str | None): Year limit for filtering experience, if provided.

Returns:
    RefineStreamQueryParams: Aggregated query parameters object.

Notes:
    1. Performs only basic typing via FastAPI's Query parameters.
    2. No disk, network, or database access is performed.

---

## function: `_make_early_error_stream_response(message: str) -> StreamingResponse`

Create a short SSE stream response that sends an error and closes.

Args:
    message (str): The error message to send.

Returns:
    StreamingResponse: A streaming response that emits an error and close event.

Notes:
    1. Builds a minimal async generator to emit two SSE events.
    2. No disk, network, or database access is performed.

---

## function: `_parse_limit_years_for_stream(limit_refinement_years: str | None) -> tuple[int | None, StreamingResponse | None]`

Parse and validate the limit_refinement_years value for streaming endpoints.

Args:
    limit_refinement_years (str | None): The user-supplied string for years.

Returns:
    tuple[int | None, StreamingResponse | None]: The parsed positive integer years (or None),
        and an optional early StreamingResponse if validation fails.

Notes:
    1. Accepts None and returns (None, None) to indicate no limit.
    2. Returns an early error StreamingResponse when invalid, to be returned directly by the route.

---

## function: `_build_filtered_content_if_needed(resume_content: str, limit_years: int | None) -> str`

Optionally filter experience by a date window and rebuild resume content.

Args:
    resume_content (str): The original full resume content.
    limit_years (int | None): The positive number of years to include, or None.

Returns:
    str: The content to refine (filtered if a limit was supplied).

Notes:
    1. If limit_years is None, returns the original content unchanged.
    2. Otherwise:
        a. Computes a start_date of (today - limit_years years).
        b. Extracts all sections from the original content.
        c. Filters experience by date range.
        d. Rebuilds a complete resume from the sections.
    3. This function may raise exceptions from extract/serialize helpers.

---

## function: `_validate_and_parse_limit_for_post(original_limit_str: str | None) -> tuple[int | None, StreamingResponse | None]`

Validate and parse the limit years for POST refine stream.

Args:
    original_limit_str (str | None): The original user-supplied string, possibly None.

Returns:
    tuple[int | None, StreamingResponse | None]: Parsed integer years (or None) and
        an optional early StreamingResponse when numeric validation fails.

Notes:
    1. Non-numeric values are treated as None (no limit, no early error).
    2. Numeric values are validated via _parse_limit_years_for_stream.

---


===

===
# File: `resume_editor/app/middleware.py`


===

===
# File: `resume_editor/app/core/rendering_settings.py`

## function: `get_render_settings(name: str) -> dict`

get_render_settings gets the render settings

Args:
    name (str): name of the settings to get

Raises:
    ValueError: if the name is unknown

Returns:
    dict: the settings

---


===

===
# File: `resume_editor/tests/app/core/test_rendering_settings.py`

## function: `test_get_render_settings_general() -> UnknownType`

Test get_render_settings for 'general' settings.

---

## function: `test_get_render_settings_exec_summary() -> UnknownType`

Test get_render_settings for 'executive_summary' settings.

---

## function: `test_get_render_settings_invalid_name() -> UnknownType`

Test that get_render_settings raises ValueError for an invalid name.

---


===

===
# File: `resume_editor/app/api/routes/route_logic/resume_export.py`

## function: `render_resume_to_docx_stream(resume_content: str, render_format: str, settings_dict: dict) -> io.BytesIO`

Renders a resume's markdown content to a DOCX file stream.

This function parses resume markdown, applies render settings, and uses the
appropriate renderer to generate a DOCX file into an in-memory buffer.

Args:
    resume_content (str): The markdown content of the resume.
    render_format (str): The rendering format, either "plain" or "ats".
    settings_dict (dict): A dictionary of settings to apply to the render.

Returns:
    io.BytesIO: An in-memory buffer containing the generated DOCX file.

Raises:
    ValueError: If an unknown render_format is provided.

Notes:
    1. Parse the `resume_content` into a `resume_writer` `Resume` object.
    2. Instantiate `ResumeRenderSettings` and update it with `settings_dict`.
    3. Create an in-memory `io.BytesIO` buffer.
    4. Create a `docx.Document` object.
    5. Based on `render_format`, instantiate `AtsRenderResume` or `PlainRenderResume`.
    6. Invoke the renderer's `render()` method.
    7. Save the generated document to the buffer.
    8. Reset the buffer's position to the start.
    9. Return the buffer.

---


===

===
# File: `resume_editor/tests/app/api/routes/route_logic/test_resume_export.py`

## function: `test_render_resume_to_docx_stream_ats_format(mock_parse: UnknownType, mock_docx_document: UnknownType, mock_ats_renderer: UnknownType) -> UnknownType`

Test render_resume_to_docx_stream with 'ats' format.

---

## function: `test_render_resume_to_docx_stream_plain_based_formats(mock_parse: UnknownType, mock_docx_document: UnknownType, mock_plain_renderer: UnknownType, render_format: UnknownType) -> UnknownType`

Test render_resume_to_docx_stream with plain-based formats.

---

## function: `test_render_resume_to_docx_stream_invalid_format(mock_parse: UnknownType) -> UnknownType`

Test render_resume_to_docx_stream raises ValueError for invalid format.

---


===

===
# File: `resume_editor/app/api/routes/route_logic/resume_serialization_helpers.py`

## function: `_parse_resume(resume_content: str) -> WriterResume`

Parse resume content using resume_writer.

Args:
    resume_content (str): The Markdown content of the resume to parse.

Returns:
    WriterResume: The parsed resume object.

Raises:
    ValueError: If parsing fails.

Notes:
    1. Splits content into lines.
    2. Creates a ParseContext.
    3. Attempts to parse the resume using WriterResume.parse.
    4. On any exception, logs and raises a ValueError.

---

## function: `_check_for_unparsed_content(resume_content: str, section_name: str, parsed_section: any) -> None`

Check for unparsed content in a resume section.

Args:
    resume_content (str): The raw resume content.
    section_name (str): The name of the section to check (e.g., "personal").
    parsed_section (any): The result from the parser for this section.

Raises:
    ValueError: If the section was not parsed but raw content exists.

Notes:
    1. If 'parsed_section' is not empty, return.
    2. Iterate through 'resume_content' lines to find the section header.
    3. Once inside the section, check for any non-empty lines before the next top-level section.
    4. If any content is found, log a warning and raise a ValueError.

---

## function: `_extract_data_from_personal_section(personal: any) -> dict`

Extract data from a parsed personal section into a dictionary.
Args:
    personal (any): The parsed personal section from resume_writer.
Returns:
    dict: A dictionary of personal information.
Notes:
    1. If `personal` is None, returns an empty dictionary.
    2. Extracts contact info: name, email, phone, location.
    3. Extracts websites: website, github, linkedin, twitter.
    4. Extracts visa status: work_authorization, require_sponsorship.
    5. Extracts banner text.
    6. Extracts note text.
    7. Returns a dictionary containing all extracted data.

---

## function: `_convert_writer_role_to_dict(role: any) -> dict`

Convert a resume_writer Role object to a dictionary.
Args:
    role (any): The parsed role object from resume_writer.
Returns:
    dict: A dictionary of role information.
Notes:
    1. Extracts basics: company, title, dates, etc.
    2. Extracts summary text.
    3. Extracts responsibilities text.
    4. Extracts skills list.
    5. Returns a dictionary containing all extracted data.

---

## function: `_convert_writer_project_to_dict(project: any) -> dict`

Convert a resume_writer Project object to a dictionary.
Args:
    project (any): The parsed project object from resume_writer.
Returns:
    dict: A dictionary of project information.
Notes:
    1. Extracts overview: title, url, dates, inclusion_status, etc.
    2. Extracts description text.
    3. Extracts skills list.
    4. Returns a dictionary containing all extracted data.

---

## function: `_add_contact_info_markdown(personal_info: PersonalInfoResponse, lines: list[str]) -> None`

Adds contact info Markdown to a list of lines.
Args:
    personal_info (PersonalInfoResponse): The personal info data.
    lines (list[str]): The list of lines to append to.
Notes:
    1. Checks for name, email, phone, location.
    2. If any exist, adds a "Contact Information" section header.
    3. Appends each non-empty field.
    4. Adds a trailing blank line to the section.

---

## function: `_add_websites_markdown(personal_info: PersonalInfoResponse, lines: list[str]) -> None`

Adds websites Markdown to a list of lines.
Args:
    personal_info (PersonalInfoResponse): The personal info data.
    lines (list[str]): The list of lines to append to.
Notes:
    1. Checks for github, linkedin, website, twitter.
    2. If any exist, adds a "Websites" section header.
    3. Appends each non-empty field.
    4. Adds a trailing blank line to the section.

---

## function: `_add_visa_status_markdown(personal_info: PersonalInfoResponse, lines: list[str]) -> None`

Adds visa status Markdown to a list of lines.
Args:
    personal_info (PersonalInfoResponse): The personal info data.
    lines (list[str]): The list of lines to append to.
Notes:
    1. Checks for work_authorization or require_sponsorship.
    2. If any exist, adds a "Visa Status" section header.
    3. Appends each field if it has a value.
    4. Adds a trailing blank line to the section.

---

## function: `_add_banner_markdown(personal_info: PersonalInfoResponse, lines: list[str]) -> None`

Adds banner Markdown to a list of lines.
Args:
    personal_info (PersonalInfoResponse): The personal info data.
    lines (list[str]): The list of lines to append to.
Notes:
    1. Checks if `personal_info.banner` has content.
    2. If the content is a string, it is used directly.
    3. If the content is a `Banner` object, the value of its `text` attribute is used.
    4. Any other type of content is ignored.
    5. If valid text is found, it adds a "Banner" section header and the text, followed by a blank line.

---

## function: `_add_note_markdown(personal_info: PersonalInfoResponse, lines: list[str]) -> None`

Adds note Markdown to a list of lines.
Args:
    personal_info (PersonalInfoResponse): The personal info data.
    lines (list[str]): The list of lines to append to.
Notes:
    1. Checks if `personal_info.note` has content.
    2. If the content is a string, it is used directly.
    3. If the content is a `Note` object, the value of its `text` attribute is used.
    4. Any other type of content is ignored.
    5. If valid text is found, it adds a "Note" section header and the text, followed by a blank line.

---

## function: `_add_project_overview_markdown(overview: any, lines: list[str]) -> None`

Adds project overview Markdown to a list of lines.
Args:
    overview (any): The parsed project overview from resume_writer.
    lines (list[str]): The list of lines to append to.
Notes:
    1. Checks for title, url, url_description, start_date, end_date.
    2. If any exist, adds an "Overview" section header.
    3. Appends each non-empty field.
    4. Adds a trailing blank line to the section.

---

## function: `_add_project_description_markdown(description: any, lines: list[str]) -> None`

Adds project description Markdown to a list of lines.
Args:
    description (any): The parsed project description from resume_writer.
    lines (list[str]): The list of lines to append to.
Notes:
    1. Checks for description text.
    2. If it exists, adds a "Description" section header and the text.
    3. Adds a trailing blank line to the section.

---

## function: `_add_project_skills_markdown(skills: any, lines: list[str]) -> None`

Adds project skills Markdown to a list of lines.
Args:
    skills (any): The parsed project skills from resume_writer.
    lines (list[str]): The list of lines to append to.
Notes:
    1. Checks for a list of skills.
    2. If it exists, adds a "Skills" section header and the skills as a bulleted list.
    3. Adds a trailing blank line to the section.

---

## function: `_add_role_basics_markdown(basics: any, lines: list[str]) -> None`

Adds role basics Markdown to a list of lines.
Args:
    basics (any): The parsed role basics from resume_writer.
    lines (list[str]): The list of lines to append to.
Notes:
    1. Defines mappings for string and date fields to their labels.
    2. Iterates through the field mappings to collect basics info.
    3. Formats date fields to 'MM/YYYY'.
    4. If any data is collected, adds a "Basics" section header.
    5. Appends each non-empty field.
    6. Adds a trailing blank line.

---

## function: `_add_role_summary_markdown(summary: any, lines: list[str]) -> None`

Adds role summary Markdown to a list of lines.
Args:
    summary (any): The parsed role summary from resume_writer.
    lines (list[str]): The list of lines to append to.
Notes:
    1. Checks for summary text.
    2. If present, adds a "Summary" section header and the text.
    3. Adds a trailing blank line.

---

## function: `_add_role_responsibilities_markdown(responsibilities: any, inclusion_status: InclusionStatus, lines: list[str]) -> None`

Adds role responsibilities Markdown to a list of lines.
Args:
    responsibilities (any): The parsed role responsibilities from resume_writer.
    inclusion_status (InclusionStatus): The inclusion status of the role.
    lines (list[str]): The list of lines to append to.
Notes:
    1. If inclusion_status is `NOT_RELEVANT`, appends a placeholder.
    2. If inclusion_status is `INCLUDE` and responsibilities text exists, appends the text.
    3. Adds section header and trailing blank line as appropriate.

---

## function: `_add_role_skills_markdown(skills: any, lines: list[str]) -> None`

Adds role skills Markdown to a list of lines.
Args:
    skills (any): The parsed role skills from resume_writer.
    lines (list[str]): The list of lines to append to.
Notes:
    1. Checks for a list of skills.
    2. If it exists and is not empty, adds a "Skills" section header.
    3. Appends the skills as a bulleted list.
    4. Adds a trailing blank line.

---


===

===
# File: `resume_editor/app/api/routes/route_logic/resume_ai_logic.py`

## function: `reconstruct_resume_with_new_introduction(resume_content: str, introduction: str | None) -> str`

Reconstructs resume content with a new introduction banner.

This function parses a resume's Markdown content, replaces the banner
text in the personal information section with the provided introduction,
and then reconstructs and returns the full Markdown content.

Args:
    resume_content (str): The original Markdown content of the resume.
    introduction (str | None): The new introduction text to be placed in
        the banner. If None or an empty/whitespace string, the original
        `resume_content` is returned unchanged.

Returns:
    str: The updated resume content as a Markdown string, or the
         original content if `introduction` is empty.

Raises:
    ValueError: If the resume content is malformed and cannot be parsed.

Notes:
    1.  Check if `introduction` is `None` or an empty/whitespace string. If so, return `resume_content` immediately.
    2.  Extract raw sections for Personal, Education, Certifications, and Experience.
    3.  Update the banner in the raw Personal section using `_update_banner_in_raw_personal`.
    4.  Concatenate the sections to form the updated resume content.
    5.  Return the newly reconstructed Markdown string.

---

## function: `_replace_resume_banner(resume_content: str, introduction: str | None) -> str`

Parse a resume, replace its banner, and reconstruct it.

This function is a wrapper that calls `reconstruct_resume_with_new_introduction`
to update the banner section of a resume with a new introduction.

Args:
    resume_content (str): The full markdown content of the resume.
    introduction (str | None): The new introduction text for the banner.
        If None or whitespace-only, the original content is returned unchanged.

Returns:
    str: The reconstructed markdown string with the updated banner.

Notes:
    1. This function delegates its logic to `reconstruct_resume_with_new_introduction`.

---

## function: `get_llm_config(db: Session, user_id: int) -> tuple[str | None, str | None, str | None]`

Retrieves LLM configuration for a user.

Fetches user settings, decrypts the API key, and returns the LLM endpoint,
model name, and API key.

Args:
    db (Session): The database session.
    user_id (int): The ID of the user.

Returns:
    tuple[str | None, str | None, str | None]: A tuple containing the
        llm_endpoint, llm_model_name, and decrypted api_key.

Raises:
    InvalidToken: If the API key decryption fails.

---

## function: `create_sse_message(event: str, data: str) -> str`

Formats a message for Server-Sent Events (SSE).

Args:
    event (str): The event name.
    data (str): The data to send. Can be multi-line.

Returns:
    str: The formatted SSE message string.

---

## function: `create_sse_progress_message(message: str) -> str`

Creates an SSE 'progress' message.

Args:
    message (str): The progress message content.

Returns:
    str: The formatted SSE 'progress' message.

---

## function: `create_sse_introduction_message(introduction: str) -> str`

Creates an SSE 'introduction_generated' message.

Args:
    introduction (str): The introduction text.

Returns:
    str: The formatted SSE 'introduction_generated' message.

---

## function: `create_sse_error_message(message: str, is_warning: bool) -> str`

Creates an SSE 'error' message.

Args:
    message (str): The error or warning message.
    is_warning (bool): If True, formats as a warning (yellow). Defaults to False (red).

Returns:
    str: The formatted SSE 'error' message.

---

## function: `create_sse_done_message(html_content: str) -> str`

Creates an SSE 'done' message.

Args:
    html_content (str): The final HTML content to be sent.

Returns:
    str: The formatted SSE 'done' message.

---

## function: `_extract_raw_section(resume_content: str, section_name: str) -> str`

Extract the raw text of a section from the resume content.

---

## function: `_update_banner_in_raw_personal(raw_personal: str, introduction: str | None) -> str`

Update the Banner subsection in a raw Personal section string.

If `introduction` is None or empty, return `raw_personal` unchanged.
It parses the `raw_personal` string to find the `## Banner` subsection.
If found, it replaces the content of the Banner subsection with the new `introduction`.
If not found, it appends a new `## Banner` section with the `introduction` at the end of the Personal section.
It preserves all other lines in the Personal section exactly as they are.

Notes:
    1. It carefully handles newlines, ensuring there is a blank line between
       the '## Banner' header and its content for correct paragraph and
       list rendering in Markdown.

---

## function: `create_sse_close_message() -> str`

Creates an SSE 'close' message.

Returns:
    str: The formatted SSE 'close' message.

---

## function: `process_refined_experience_result(params: ProcessExperienceResultParams) -> str`

Processes refined experience roles and reconstructs the full resume.

This function takes the refined roles from the LLM, combines them with the
original projects, and reconstructs the entire resume. It then generates
the final HTML result to be sent in the 'done' SSE event.

Args:
    params (ProcessExperienceResultParams): An object containing all parameters
        needed for processing the result.

Returns:
    str: The complete HTML content for the body of the `done` event.

Notes:
    1.  Extracts raw sections for Personal, Education, and Certifications to preserve them exactly.
    2.  Updates the banner in the raw Personal section if an introduction is provided.
    3.  Extracts projects from `original_resume_content` and roles from `resume_content_to_refine`.
    4.  Updates the roles list with the `refined_roles` data from the LLM.
    5.  Creates a new `ExperienceResponse` with the refined roles and original projects.
    6.  Reconstructs the resume using updated raw personal, raw education/certifications, and serialized experience.
    7.  The final, complete markdown is passed to `_create_refine_result_html` to generate the HTML for the UI.

---

## function: `_process_refined_role_event(event: dict, refined_roles: dict) -> str | None`

Processes a 'role_refined' event and returns a progress message.

---

## function: `_process_sse_event(event: dict, refined_roles: dict) -> tuple[str | None, str | None]`

Processes a single SSE event from the experience refinement stream.

This helper function updates the state of refined roles and determines
what message, if any, should be yielded to the client.

Args:
    event (dict): The event data from the async generator.
    refined_roles (dict): A dictionary to be updated with refined role data.

Returns:
    tuple[str | None, str | None]: A tuple containing an optional SSE message
                                   to yield and optional new introduction text.

Notes:
    1.  Gets the 'status' from the event dictionary.
    2.  If status is 'in_progress', creates a progress message.
    3.  If status is 'introduction_generated', creates a progress message
        confirming generation and extracts the introduction text.
    4.  If status is 'role_refined', processes the role data and creates a
        progress message.
    5.  Returns a tuple with the SSE message and the introduction text (if any).

---

## function: `_handle_sse_exception(e: Exception, resume_id: int) -> str`

Handles exceptions during an SSE stream and formats an error message.

Args:
    e (Exception): The exception that was raised.
    resume_id (int): The ID of the resume being processed.

Returns:
    str: A formatted SSE error message string.

---

## function: `handle_save_as_new_refinement(params: SaveAsNewParams) -> DatabaseResume`

Orchestrates saving a refined resume as a new resume.

This function takes the full refined resume content, validates it, and
creates a new resume record in the database. The introduction is taken
directly from the refinement context and persisted to its dedicated field.

Args:
    params (SaveAsNewParams): The parameters for saving the new resume.

Returns:
    DatabaseResume: The newly created resume object.

Raises:
    HTTPException: If validation fails.

Notes:
    1. The `refined_content` from the form is assumed to be the full, final resume content.
    2. The introduction is taken from the form context and passed directly to the database.
    3. No resume reconstruction or on-the-fly introduction generation occurs here.

---


===

===
# File: `resume_editor/app/web/pages.py`


===

===
# File: `resume_editor/tests/app/api/routes/route_logic/test_resume_ai_logic.py`

## function: `test_replace_resume_banner_none_introduction() -> None`

Test _replace_resume_banner returns original content when introduction is None.

---

## function: `test_replace_resume_banner_whitespace_introduction() -> None`

Test _replace_resume_banner returns original content when introduction is whitespace.

---

## function: `test_replace_resume_banner_success(mock_extract_personal: MagicMock, mock_extract_education: MagicMock, mock_extract_experience: MagicMock, mock_extract_certifications: MagicMock, mock_reconstruct: MagicMock) -> None`

Test _replace_resume_banner successfully replaces banner when introduction is provided.

---

## function: `test_replace_resume_banner_malformed_content(mock_extract_personal: MagicMock) -> None`

Test _replace_resume_banner handles malformed resume content.

---

## function: `test_replace_resume_banner_personal_info_none(mock_extract_personal: MagicMock, mock_extract_education: MagicMock, mock_extract_experience: MagicMock, mock_extract_certifications: MagicMock, mock_reconstruct: MagicMock) -> None`

Test branch where personal_info is None to cover the False path of the condition.

---

## function: `test_replace_resume_banner_reconstruct_failure(mock_extract_personal: MagicMock, mock_extract_education: MagicMock, mock_extract_experience: MagicMock, mock_extract_certifications: MagicMock, mock_reconstruct: MagicMock) -> None`

Test exception handling path when reconstruction fails.

---

## function: `test_handle_save_as_new_refinement_uses_banner_replacement_with_intro(mock_validate: MagicMock, mock_reconstruct: MagicMock, mock_replace_banner: MagicMock, mock_create_resume: MagicMock) -> None`

Verify handle_save_as_new_refinement integrates banner replacement when introduction is provided.

---

## function: `test_handle_save_as_new_refinement_uses_banner_replacement_with_none_intro(mock_validate: MagicMock, mock_reconstruct: MagicMock, mock_replace_banner: MagicMock, mock_create_resume: MagicMock) -> None`

Verify handle_save_as_new_refinement calls banner replacement with None introduction.

---


===

