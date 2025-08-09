"""Runs each file through the LLM to update the docstrings with important details."""

import ast
import json
import os
from time import sleep
from typing import Any

import click
import dotenv
from aider.coders import Coder  # type: ignore
from aider.io import InputOutput  # type: ignore
from aider.models import Model  # type: ignore
from rich.pretty import pprint as pp

dotenv.load_dotenv(dotenv_path=".env")

# JSON file to store docstrings
DOCSTRINGS_JSON_FILE = "docstrings.json"
DOCSTRINGS_MD_FILE = "DOCSTRINGS.md"

PROJECT_ROOT = "resume_writer/models"


def _create_docstring_prompt() -> str:
    """Create the prompt for updating docstrings.

    Returns:
        str: The prompt for updating docstrings

    """
    return """Your job is to update function docstrings with details about functions and methods.


* Classes should be documented.
    - Class purpose, if known
    - Members should be listed, with their type if known.

* Every function should have a docstring.
* The purpose of the docstring is to act as a specification for the function
* You will be asked to update functions using the docstring as a specification
* The docstring should include
    - an `Args:` section, which includes the name, type, and purpose of the function argument.
    - a `Returns:` section, which includes the type and purpose of all possible return values
    - a `Notes:` section, which should include a numbered step-by-step description of the function internals.
        - The numbered steps should exclude logging statements.
        - The "Notes:" should mention any network, disk, or database access.

    Ensure all functions meet this specification.

IMPORTANT!
==========
* Update **ONLY** the docstrings, do **NOT** edit code.
* Files **must** be processed one at a time.
* **NEVER add more files**, update **ONLY** the one file.
    """


def _create_coder(filepath: str) -> Coder:
    """Create a coder instance for processing the file.

    Args:
        filepath: Path to the file to process

    Returns:
        Coder: Configured coder instance

    """
    io = InputOutput(yes=True)
    fnames = [filepath]
    model = Model("openrouter/qwen/qwen3-30b-a3b-instruct-2507")
    return Coder.create(main_model=model, fnames=fnames, io=io)


def update_docstrings(filepath: str) -> None:
    """Update docstrings in the specified file using an LLM.

    Args:
        filepath: Path to the file to process

    Returns:
        None

    """
    prompt = _create_docstring_prompt()
    coder = _create_coder(filepath)
    coder.run(prompt)


def _parse_function_node(node: ast.FunctionDef) -> tuple[str, str]:
    """Parse a function node to extract signature and docstring.

    Args:
        node: AST function node to parse

    Returns:
        Tuple[str, str]: Function signature and docstring

    """
    func_name = node.name
    args = [arg.arg for arg in node.args.args]
    arg_types = [
        ast.unparse(arg.annotation) if arg.annotation else "UnknownType"
        for arg in node.args.args
    ]
    return_type = ast.unparse(node.returns) if node.returns else "UnknownType"
    signature = f"{func_name}({', '.join(f'{a}: {t}' for a, t in zip(args, arg_types, strict=False))}) -> {return_type}"
    docstring = ast.get_docstring(node) or ""
    return signature, docstring


def _parse_class_node(node: ast.ClassDef) -> tuple[str, str, list[tuple[str, str]]]:
    """Parse a class node to extract class info and methods.

    Args:
        node: AST class node to parse

    Returns:
        Tuple[str, str, List[Tuple[str, str]]]: Class name, docstring, and list of method signatures/docstrings

    """
    class_name = node.name
    class_docstring = ast.get_docstring(node) or ""
    class_functions = []

    for class_node in ast.walk(node):
        if isinstance(class_node, ast.FunctionDef):
            signature, docstring = _parse_function_node(class_node)
            class_functions.append((signature, docstring))

    return class_name, class_docstring, class_functions


def extract_docstrings_from_file(filepath: str) -> dict[str, Any]:
    """Extract docstrings from a Python file.

    Args:
        filepath: Path to the Python file to process

    Returns:
        Dict[str, Any]: Dictionary containing extracted docstrings

    """
    with open(filepath, encoding="utf-8") as file:
        tree = ast.parse(file.read(), filename=filepath)

    functions = []
    classes = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            signature, docstring = _parse_function_node(node)
            functions.append((signature, docstring))

        elif isinstance(node, ast.ClassDef):
            class_name, class_docstring, class_functions = _parse_class_node(node)

            if class_functions:
                classes[class_name] = (class_docstring, class_functions)

    return {
        "filepath": filepath,
        "filename": os.path.basename(filepath),
        "functions": functions,
        "classes": classes,
    }


def load_existing_docstrings() -> dict[str, Any]:
    """Load existing docstrings from the JSON file.

    Returns:
        Dict[str, Any]: Dictionary containing existing docstrings

    """
    if os.path.exists(DOCSTRINGS_JSON_FILE):
        with open(DOCSTRINGS_JSON_FILE) as f:
            return json.load(f)
    return {}


def save_docstrings(docstrings: dict[str, Any]) -> None:
    """Save docstrings to the JSON file.

    Args:
        docstrings: Dictionary containing docstrings to save

    Returns:
        None

    """
    with open(DOCSTRINGS_JSON_FILE, "w") as f:
        json.dump(docstrings, f, indent=2)


def generate_markdown_from_docstrings(docstrings: dict[str, Any]) -> None:
    """Generate DOCSTRINGS.md from the docstrings data.

    Args:
        docstrings: Dictionary containing docstrings data

    Returns:
        None

    """
    with open(DOCSTRINGS_MD_FILE, "w") as output_file:
        output_file.write("# Docstrings Reference\n\n")

        for filepath, data in docstrings.items():
            output_file.write(f"===\n# File: `{data['filename']}`\n\n")

            # Write functions
            for signature, docstring in data["functions"]:
                output_file.write(f"## function: `{signature}`\n\n")
                output_file.write(f"{docstring}\n")
                output_file.write("\n---\n\n")

            # Write classes
            for class_name, (class_docstring, class_functions) in data[
                "classes"
            ].items():
                output_file.write(f"## `{class_name}` class\n\n")
                if class_docstring:
                    output_file.write(f"{class_docstring}\n")
                    output_file.write("\n---\n")
                for signature, docstring in class_functions:
                    output_file.write(f"## method: `{class_name}.{signature}`\n\n")
                    output_file.write(f"{docstring}\n")
                    output_file.write("\n---\n")
            output_file.write("\n===\n\n")


def process_file(filepath: str, use_llm: bool = True) -> None:
    """Process a single Python file for docstring extraction.

    Args:
        filepath: Path to the Python file to process
        use_llm: Whether to use LLM to update docstrings

    Returns:
        None

    """
    try:
        if use_llm:
            update_docstrings(filepath=filepath)
            print("Sleeping so we aren't rate limited")
            sleep(60)

        # Extract docstrings from the file
        docstring_data = extract_docstrings_from_file(filepath)

        # Load existing docstrings
        all_docstrings = load_existing_docstrings()

        # Update the specific file's docstrings
        all_docstrings[filepath] = docstring_data

        # Save updated docstrings
        save_docstrings(all_docstrings)

        # Generate markdown
        generate_markdown_from_docstrings(all_docstrings)

    except Exception as e:
        print(f"Error processing {filepath}: {e}")


def process_files(filepaths: list[str], use_llm: bool = True) -> None:
    """Process multiple Python files for docstring extraction.

    Args:
        filepaths: List of file paths to process
        use_llm: Whether to use LLM to update docstrings

    Returns:
        None

    """
    # Load existing docstrings
    all_docstrings = load_existing_docstrings()

    # Process each file
    for filepath in filepaths:
        try:
            if use_llm:
                update_docstrings(filepath=filepath)
                print("Sleeping so we aren't rate limited")
                sleep(60)

            # Extract docstrings from the file
            docstring_data = extract_docstrings_from_file(filepath)
            all_docstrings[filepath] = docstring_data

        except Exception as e:
            print(f"Error processing {filepath}: {e}")

    # Save updated docstrings
    save_docstrings(all_docstrings)

    # Generate markdown
    generate_markdown_from_docstrings(all_docstrings)


def process_single_file_only(filepath: str, use_llm: bool = True) -> None:
    """Process a single Python file and update only that file's entry in _docstrings.json.

    Args:
        filepath: Path to the Python file to process
        use_llm: Whether to use LLM to update docstrings

    Returns:
        None

    """
    try:
        if use_llm:
            update_docstrings(filepath=filepath)
            print("Sleeping so we aren't rate limited")
            sleep(30)

        # Extract docstrings from the file
        docstring_data = extract_docstrings_from_file(filepath)

        # Load existing docstrings
        all_docstrings = load_existing_docstrings()

        # Update only this specific file's docstrings
        all_docstrings[filepath] = docstring_data

        # Save updated docstrings
        save_docstrings(all_docstrings)

        # Generate markdown
        generate_markdown_from_docstrings(all_docstrings)

    except Exception as e:
        print(f"Error processing {filepath}: {e}")


def clean_and_rebuild() -> None:
    """Clean existing docstrings file and rebuild from scratch.

    Args:
        None

    Returns:
        None

    """
    # Confirmation prompt
    response = input(
        "This will delete the existing docstrings file and rebuild it. Continue? (y/N): ",
    )
    if response.lower() != "y":
        print("Operation cancelled.")
        return

    # Remove existing files
    if os.path.exists(DOCSTRINGS_JSON_FILE):
        os.remove(DOCSTRINGS_JSON_FILE)
    if os.path.exists(DOCSTRINGS_MD_FILE):
        os.remove(DOCSTRINGS_MD_FILE)

    # Process all Python files in msa directory
    filepaths = []
    for root, _, files in os.walk(PROJECT_ROOT):
        for file in files:
            if file.endswith(".py"):
                filepaths.append(os.path.join(root, file))

    process_files(filepaths, use_llm=True)


def regenerate_markdown_only() -> None:
    """Regenerate DOCSTRINGS.md from _docstrings.json without processing files.

    Args:
        None

    Returns:
        None

    """
    docstrings = load_existing_docstrings()
    if not docstrings:
        print("No docstrings found. Run with --clean or process files first.")
        return
    generate_markdown_from_docstrings(docstrings)
    print(f"Regenerated {DOCSTRINGS_MD_FILE} from {DOCSTRINGS_JSON_FILE}")


@click.command()
@click.option("--filename", "-f", multiple=True, help="Process specific file(s)")
@click.option("--clean", "-c", is_flag=True, help="Clean and rebuild all docstrings")
@click.option(
    "--no-llm",
    "-n",
    is_flag=True,
    help="Skip LLM processing, only parse files",
)
@click.option(
    "--markdown-only",
    "-m",
    is_flag=True,
    help="Regenerate DOCSTRINGS.md from _docstrings.json",
)
def main(filename: tuple[str], clean: bool, no_llm: bool, markdown_only: bool) -> None:
    """Main function to run the docstring extraction process.

    Args:
        filename: Tuple of filenames to process
        clean: Whether to clean and rebuild all docstrings
        no_llm: Whether to skip LLM processing
        markdown_only: Whether to only regenerate markdown from existing JSON

    Returns:
        None

    """
    # Check for incompatible combinations
    if clean and (filename or no_llm or markdown_only):
        print("Error: --clean cannot be combined with other options.")
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit(1)

    if markdown_only and no_llm:
        print("Error: --markdown-only and --no-llm cannot be combined.")
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit(1)

    # Check if no options are specified
    if not any([clean, filename, no_llm, markdown_only]):
        # Default behavior - show help
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit()

    if clean:
        clean_and_rebuild()
    elif markdown_only:
        regenerate_markdown_only()
    elif filename:
        # Process each specified file individually
        for filepath in filename:
            process_single_file_only(filepath, use_llm=not no_llm)
    elif no_llm:
        # Process all files without LLM
        filepaths = []
        for root, _, files in os.walk(PROJECT_ROOT):
            pp("Walking tree...")
            for file in files:
                pp(f"file: {file}")
                if file.endswith(".py"):
                    filepaths.append(os.path.join(root, file))
        process_files(filepaths, use_llm=False)


if __name__ == "__main__":
    main()
