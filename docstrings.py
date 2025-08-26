"""Docstring extraction and updating tool."""

import ast
import json
import os
from time import sleep
from typing import Any

import click
import dotenv
from aider.coders import Coder
from aider.io import InputOutput
from aider.models import Model

dotenv.load_dotenv(dotenv_path=".env")

# Configuration
DOCSTRINGS_JSON_FILE = "docstrings.json"
DOCSTRINGS_MD_FILE = "DOCSTRINGS.md"
DEFAULT_DELAY = 30  # seconds


class DocstringProcessor:
    """Main class for processing Python files and managing docstrings."""

    def __init__(self, delay: int = DEFAULT_DELAY):
        """Initialize the docstring processor.

        Args:
            delay: Delay in seconds between LLM API calls

        """
        self.delay = delay
        self.model = Model("openrouter/qwen/qwen3-30b-a3b-instruct-2507")

    def create_docstring_prompt(self) -> str:
        """Create the prompt for updating docstrings.

        Returns:
            str: The prompt for updating docstrings

        """
        return """Your job is to update function docstrings with details about functions and methods.

* Classes should be documented.
    - Class purpose, if known
    - Members should be listed, with their type if known.
    - Functions should have a docstring as part of the function.


* Every function should have a docstring.
* The docstring should include
    - an `Args:` section, which includes the name, type, and purpose of the function argument.
    - a `Returns:` section, which includes the type and purpose of all possible return values
    - a `Notes:` section, which should include a numbered step-by-step description of the function internals.
        - The numbered steps should exclude logging statements.
        - The "Notes:" should mention any network, disk, or database access.
        - Any exceptions potentially raised

IMPORTANT!
==========
* **Only** update the docstrings, do **NOT** change, delete, or edit code.
* **Only document existing code**.
* **Ignore** placeholder functions and docstrings.
* **Preserve** existing code, functions, class members and methods
* Files **must** be processed one at a time.
* **NEVER add more files**, update **ONLY** the one file.

Example:
--------
The input is:
class ResumeResponse(BaseModel):
    \"\"\"Response model for a resume.\"\"\"

    id: int
    name: str

The expected output is:
class ResumeResponse(BaseModel):
    \"\"\"Response model for a resume.

    Attributes:
        id (int): The unique identifier for the resume.
        name (str): The name of the resume.
    \"\"\"
    
    id: int
    name: str
--------
        """

    def create_coder(self, filepath: str) -> Coder:
        """Create a coder instance for processing the file.

        Args:
            filepath: Path to the file to process

        Returns:
            Coder: Configured coder instance

        """
        io = InputOutput(yes=True)
        fnames = [filepath]
        return Coder.create(
            main_model=self.model,
            fnames=fnames,
            io=io,
            auto_commits=False,
        )

    def update_docstrings(self, filepath: str) -> None:
        """Update docstrings in the specified file using an LLM.

        Args:
            filepath: Path to the file to process

        Returns:
            None

        """
        prompt = self.create_docstring_prompt()
        coder = self.create_coder(filepath)
        coder.run(prompt)
        print(f"Sleeping for {self.delay} seconds")
        sleep(self.delay)

    def parse_function_node(self, node: ast.FunctionDef) -> tuple[str, str]:
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
        signature = f"{func_name}({', '.join(f'{a}: {t}' for a, t in zip(args, arg_types))}) -> {return_type}"
        docstring = ast.get_docstring(node) or ""
        return signature, docstring

    def parse_class_node(
        self,
        node: ast.ClassDef,
    ) -> tuple[str, str, list[tuple[str, str]]]:
        """Parse a class node to extract class info and methods.

        Args:
            node: AST class node to parse

        Returns:
            Tuple[str, str, List[Tuple[str, str]]]: Class name, docstring, and list of method signatures/docstrings

        """
        class_name = node.name
        class_docstring = ast.get_docstring(node) or ""
        class_methods = []

        # Only process methods directly defined in this class
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                signature, docstring = self.parse_function_node(item)
                class_methods.append((signature, docstring))

        return class_name, class_docstring, class_methods

    def extract_docstrings_from_file(self, filepath: str) -> dict[str, Any]:
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

        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                signature, docstring = self.parse_function_node(node)
                functions.append((signature, docstring))
            elif isinstance(node, ast.ClassDef):
                class_name, class_docstring, class_methods = self.parse_class_node(node)
                if class_methods:
                    classes[class_name] = (class_docstring, class_methods)

        return {
            "filepath": filepath,
            "filename": os.path.basename(filepath),
            "functions": functions,
            "classes": classes,
        }

    def load_existing_docstrings(self) -> dict[str, Any]:
        """Load existing docstrings from the JSON file.

        Returns:
            Dict[str, Any]: Dictionary containing existing docstrings

        """
        if os.path.exists(DOCSTRINGS_JSON_FILE):
            with open(DOCSTRINGS_JSON_FILE) as f:
                return json.load(f)
        return {}

    def save_docstrings(self, docstrings: dict[str, Any]) -> None:
        """Save docstrings to the JSON file.

        Args:
            docstrings: Dictionary containing docstrings to save

        Returns:
            None

        """
        with open(DOCSTRINGS_JSON_FILE, "w") as f:
            json.dump(docstrings, f, indent=2)

    def generate_markdown_from_docstrings(self, docstrings: dict[str, Any]) -> None:
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
                for class_name, (class_docstring, class_methods) in data[
                    "classes"
                ].items():
                    output_file.write(f"## `{class_name}` class\n\n")
                    if class_docstring:
                        output_file.write(f"{class_docstring}\n")
                        output_file.write("\n---\n")
                    for signature, docstring in class_methods:
                        output_file.write(f"## method: `{class_name}.{signature}`\n\n")
                        output_file.write(f"{docstring}\n")
                        output_file.write("\n---\n")
                output_file.write("\n===\n\n")

    def process_file(self, filepath: str, use_llm: bool = True) -> None:
        """Process a single Python file for docstring extraction.

        Args:
            filepath: Path to the Python file to process
            use_llm: Whether to use LLM to update docstrings

        Returns:
            None

        """
        try:
            if use_llm:
                print(f"Updating docstrings for {filepath}")
                self.update_docstrings(filepath)

            # Extract docstrings from the file
            docstring_data = self.extract_docstrings_from_file(filepath)

            # Load existing docstrings
            all_docstrings = self.load_existing_docstrings()

            # Update the specific file's docstrings
            all_docstrings[filepath] = docstring_data

            # Save updated docstrings
            self.save_docstrings(all_docstrings)

            # Generate markdown
            self.generate_markdown_from_docstrings(all_docstrings)

        except Exception as e:
            print(f"Error processing {filepath}: {e}")

    def clean_and_rebuild(self, project_root: str) -> None:
        """Clean existing docstrings file and rebuild from scratch.

        Args:
            project_root: Root directory to search for Python files

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

        # Process all Python files in project directory
        filepaths = []
        for root, _, files in os.walk(project_root):
            for file in files:
                if file.endswith(".py"):
                    filepaths.append(os.path.join(root, file))

        for filepath in filepaths:
            self.process_file(filepath, use_llm=True)


@click.command()
@click.option("--filepath", "-f", multiple=True, help="Process specific file(s)")
@click.option(
    "--project-root",
    "-r",
    default="resume_writer/models",
    help="Project root directory",
)
@click.option(
    "--delay",
    "-d",
    default=DEFAULT_DELAY,
    help="Delay between API calls in seconds",
)
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
    help="Regenerate DOCSTRINGS.md from existing data",
)
def main(
    filepath: tuple[str],
    project_root: str,
    delay: int,
    clean: bool,
    no_llm: bool,
    markdown_only: bool,
) -> None:
    """Generates or updates docstrings for functions and classes.
    Writes results to DOCSTRINGS.md
    """
    # Check for incompatible combinations
    if clean and (filepath or no_llm or markdown_only):
        print("Error: --clean cannot be combined with other options.")
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit(1)

    if markdown_only and no_llm:
        print("Error: --markdown-only and --no-llm cannot be combined.")
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit(1)

    processor = DocstringProcessor(delay=delay)

    if clean:
        processor.clean_and_rebuild(project_root)
    elif markdown_only:
        docstrings = processor.load_existing_docstrings()
        if not docstrings:
            print("No docstrings found. Run with --clean or process files first.")
            return
        processor.generate_markdown_from_docstrings(docstrings)
        print(f"Regenerated {DOCSTRINGS_MD_FILE} from {DOCSTRINGS_JSON_FILE}")
    elif filepath:
        # Process each specified file
        for fp in filepath:
            processor.process_file(fp, use_llm=not no_llm)
    elif no_llm:
        # Process all files without LLM
        filepaths = []
        for root, _, files in os.walk(project_root):
            for file in files:
                if file.endswith(".py"):
                    filepaths.append(os.path.join(root, file))
        for fp in filepaths:
            processor.process_file(fp, use_llm=False)
    else:
        # Default behavior - show help
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit()


if __name__ == "__main__":
    main()
