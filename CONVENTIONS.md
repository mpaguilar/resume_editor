# General
* Imports **always** should be at the top of the file, **never** inline
* The main files are in a directory named `./msa`.
* The root folder is for project configuration files, only.
* `uv` is used for dependency management
    * `python` related commands are prefixed with `uv run`, for example `uv run pytest tests`
    * New dependencies are added with `uv add <package>`
* Functions **must** be short, and serve a single purpose. Avoid long functions, create new functions as needed.
* All text output for questions and answers **must** be in Markdown format

# Preferred libraries

* `click` for command line parsing.
* `langchain` and related libraries for LLM processing.
* `pathlib` for file operations
* `pytest` for unit testing
* `httpx` for web-related calls, unless a specific library is offered
* `langchain_community.retrievers.WikipediaRetriever` for Wikipedia searches
* `serpapi.GoogleSearch` for web searches
    * `SERPER_API_KEY` will be passed as an environment variable
    

# Directory layout
* The root directory is used **only** for project configuration and utilities, e.g. `pyproject.toml`, etc.
* The project root is `./msa`. Any code, application configuration, etc., is created there
* Tests are in kept in the `./tests` directory
* LLM memory, temp files, etc., are kept in the `./msa/llm_memory` directory

# LLM calls
* All calls to an LLM **must** use a `PydanticOutputParser` object
* All messages formatted for the LLM **must** include the `format_instructions` parameter
* All messages received from the LLM **must** use `langchain_core.utils.json.parse_json_markdown`
* The API key for LLM calls is in the environment variable `LLM_API_KEY`

# Variable conventions

* **always** use type-hints for all arguments and return values
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

# Exceptions
* `try` blocks should not `return` from within the `try`
* `try` blocks should use `else` to `return`

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

# Docstrings
* Every function should have a docstring.
* The purpose of the docstring is to act as a specification for the function
* You will be asked to update functions using the docstring as a specification
* The docstring should include
    - an `Args:` section, which includes the name, type, and purpose of the function argument.
    - a `Returns:` section, which includes the type and purpose of all possible return values
    - a `Notes:` section, which should include a numbered step-by-step description of the function internals.
        - The numbered steps should exclude logging statements.
        - The "Notes:" should mention any network, disk, or database access.
    - Include a blank line after the last section. For example:
    ```
    Notes:
        <some notes>
    ```

# Configuration
* Application configuration is kept in `./msa/app_config.yml`
* LLM configuration is in `./msa/llm_config.yml`

# Unit tests
* Unit tests are run with `pytest`.
* Tests are located in `./tests` and its subdirectories.
* Tests should be written as functions, do **not** use test classes.
* Each `*.py` file should have its own test file. For example `example.py` should have a test file named `test_example.py`
* Unit tests should be run with a logging level of DEBUG
* Unit tests should be written before the code, and they should fail if the code is incorrect.
