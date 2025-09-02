# General
* Imports **always** should be at the top of the file, **never** inline
* The main files are in a subdirectory directory named `./resume_editor`.
* The root folder is for project configuration files, only.
* `uv` is used for dependency management
    * `python` related commands are prefixed with `uv run`, for example `uv run pytest tests`
    * New dependencies are added with `uv add <package>`
* Functions **must** be short, and serve a single purpose. Avoid long functions, create new functions as needed.
* Functions **must** be easily mocked, avoid complexity.
* All text output for questions and answers **must** be in Markdown format
* All assigned variables should be used. 
    * If a variable is unused, remove the variable.

# Preferred libraries

* `click` for command line parsing.
* `langchain` and related libraries for LLM processing.
* `pathlib` for file operations
* `pytest` for unit testing
* `httpx` for web-related calls, unless a specific library is offered
* `langchain_community.retrievers.WikipediaRetriever` for Wikipedia searches
* `htmx` for web page rendering
    
# LLM calls
* All calls to an LLM **must** use a `PydanticOutputParser` object
* All messages formatted for the LLM **must** include the `format_instructions` parameter
* All messages received from the LLM **must** use `langchain_core.utils.json.parse_json_markdown`
* The API key for LLM calls is in the environment variable `LLM_API_KEY`

# Variable conventions

* **always** use type-hints for all arguments and return values
* Correct type-hints are **critical**
* Use named arguments when calling functions when possible.

# General formatting
* use double-quotes for strings
* all functions should have a docstring describing:
    * what it does
    * what arguments it takes ("Args:\n")
    * what it returns ("Returns:\n)
* Multi-line docstrings should start at the first line, with no line break.
    * For example: `"""The line should start like this`
* Blank lines **must** be blank, with no unnecessary spaces or tabs.

# Defensive coding
* arguments to functions should check for valid inputs using `assert`
* returned values from called functions should check for validity using `assert`
* call functions using named arguments
* Code should be written to be easily mocked and tested
* No secret keys should be in code, not even defaults. **Always** get secrets from an external source.

# Exceptions
* `try` blocks should not `return` from within the `try`
* `try` blocks should use `else` to `return`
* Exceptions should have an error log before being raised.
* General exceptions on FastAPI routes will be handled by FastAPI.

# Logging
* Every source file must have logging setup using the following in it's header:
    ```
    import logging

    log = logging.getLogger(__name__)
    ```
* functions should `log.debug` at the start of the function with a message including the function name and "starting".
* functions should `log.debug` before returning with a message including the function name and "returning".
* Logging should never use f-string or `%s` formatting. Format the message into its own variable, and pass the variable to the log statment.

    For example, this is correct:
    ```
    _msg = f"{component_name} completed processing"
    log.info(_msg)
    ```

    ```
    These are incorrect:
    ```
    log.info(f"{component_name} completed processing")
    log.info("%s completed processing", component_name)
    ```
* When logging from an exception, use `log.exception`

# Deprecated usage
* `typing.List` is deprecated, use `list` instead
* `datetime.datetime.utcnow()` is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: `datetime.datetime.now(datetime.UTC)`
* IMPORTANT: DeprecationWarning: The `name` is not the first parameter anymore. The first parameter should be the `Request` instance.
  Replace `TemplateResponse(name, {"request": request})` by `TemplateResponse(request, name)`.

# Docstrings
* Every function should have a docstring.
* The purpose of the docstring is to act as a specification for the function
* You will be asked to update functions using the docstring as a specification
* Classes should be documented.
    - Class purpose, if known
    - Members should be listed, with their type if known.
* The docstring should include
    - an `Args:` section, which includes the name, type, and purpose of the function argument.
    - a `Returns:` section, which includes the type and purpose of all possible return values
    - an optional "Raises:" section, which includes any potential exceptions raised
    - a `Notes:` section, which should include a numbered step-by-step description of the function internals.
        - The numbered steps should exclude logging statements.
        - The "Notes:" should mention any network, disk, or database access.
    - Include a blank line after the last section. For example:
    ```
    Notes:
        <some notes>

    ```

# Unit tests
* Unit tests are run with `pytest`.
* Tests are located in `./tests` and its subdirectories.
* Tests should be written as functions, do **not** use test classes.
* Each `*.py` file should have its own test file.
* Unit tests should be run with a logging level of DEBUG
* Unit tests should be written before the code, and they should fail if the code is incorrect.
* IMPORTANT: Do not use duplicate file names for tests, even in separate paths. This causes errors.
    * All test files **must** have unique filenames

# HTML considerations
* Prefer putting HTML into templates
* Putting HTML into Python code is discouraged
* Template and HTML are kept in `resume_editor/app/templates`

# Context management
It is **important** to keep the size of individual files manageable.

* Try to keep individual files under 1000 lines
* Create new files and libraries as necessary

# Special considerations for FastAPI route dependency injection

To successfully mock FastAPI route calls with dependency injection, `app.dependency_overrides` **must** be used.

For example, for a route like this:
```

```
@router.get("", response_model=list[str])
async def some_function(
    request: Request,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user),
):

```
# Note that we import `get_db` so we can override it
from resume_editor.app.api.routes.resume import get_db

@patch("resume_editor.app.api.routes.resume.get_current_user")
@patch("resume_editor.app.api.routes.resume.get_db")
def test_something():
    app = create_app()
    client = TestClient(app)

    mock_db = Mock()

    # mock the return value
    mock_db.query.return_value.filter.return_value.<first/all>.return_value = <correct answer>

    # These next lines are **very** important
    def get_mock_db():
        yield mock_db

    # note that we are overriding `get_db` here
    app.dependency_overrides[get_db] = get_mock_db

    # perform tests and assertions

    # clear the overrides
    app.dependency_overrides.clear()
```

# Test file name exception

There are several cases where test files may not be named exactly the same as the python file. For example, the tests for `app/api/routes/user.py` are in `tests/app/api/routes/test_user_route.py`, not in `tests/app/api/routes/test_user.py`. This is to prevent a naming collision which causes errors during test collection. 

* Known mappings are found in `code_test_mappings.md`. 
* Update `code_test_mappings.md` as new mappings are discovered or created.