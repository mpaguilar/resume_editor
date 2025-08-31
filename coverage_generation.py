import ast
import logging
import subprocess
import textwrap
from pathlib import Path
from typing import Any

import click

# Setting up basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
log = logging.getLogger(__name__)

TEMPLATE = """
--------------------------------------------------------------------------------
File: {filename}
Coverage: {coverage}%

Missed Code Blocks:
{missed_lines_details}
--------------------------------------------------------------------------------"""


class FunctionFinder(ast.NodeVisitor):
    """AST visitor to find all functions and their line ranges."""

    def __init__(self):
        self.functions: list[dict[str, Any]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._add_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._add_function(node)
        self.generic_visit(node)

    def _add_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        """Helper to add function details to the list."""
        # end_lineno is available on Python 3.8+
        end_lineno = getattr(
            node,
            "end_lineno",
            max(l.lineno for l in ast.walk(node) if hasattr(l, "lineno")),
        )
        self.functions.append(
            {"name": node.name, "start": node.lineno, "end": end_lineno},
        )


def run_pytest_coverage(source_dir: str) -> str:
    """Runs pytest with coverage and returns the output."""
    command = [
        "pytest",
        "--cov-report",
        "term-missing",
        f"--cov=./{source_dir}",
        "--cov-branch",
    ]
    log.info(f"Running command: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    # pytest returns 5 if no tests are found, which is not an error for us.
    if result.returncode not in [0, 5]:
        log.error("Pytest run failed.")
        log.error(f"STDOUT:\n{result.stdout}")
        log.error(f"STDERR:\n{result.stderr}")
        raise click.ClickException("Pytest command failed.")
    return result.stdout


def parse_line_ranges(range_str: str) -> list[dict[str, Any]]:
    """Parses a string of line number ranges into a list of dictionaries."""
    ranges = []
    parts = range_str.split(",")
    for part in parts:
        part = part.strip()
        if "->" in part:  # This indicates branch coverage.
            start_str, end_str = part.split("->")
            try:
                # Regular branch coverage like "23->25"
                line1 = int(start_str)
                line2 = int(end_str)
                ranges.append(
                    {
                        "start": min(line1, line2),
                        "end": max(line1, line2),
                        "display": part,
                    },
                )
            except ValueError:
                # For branches like "23->exit" or "->23"
                if end_str == "exit" and start_str.isdigit():
                    line_num = int(start_str)
                    ranges.append(
                        {
                            "start": line_num,
                            "end": line_num,
                            "display": part,
                            "to_exit": True,
                        },
                    )
                else:
                    line_num = None
                    if start_str.isdigit():
                        line_num = int(start_str)
                    elif end_str.isdigit():
                        line_num = int(end_str)

                    if line_num is not None:
                        ranges.append(
                            {"start": line_num, "end": line_num, "display": part},
                        )
                    else:
                        log.warning(f"Could not parse branch coverage entry: {part}")
        elif "-" in part:
            try:
                start, end = map(int, part.split("-"))
                ranges.append({"start": start, "end": end, "display": part})
            except ValueError:
                log.warning(f"Could not parse range coverage entry: {part}")
        elif part.isdigit():
            line = int(part)
            ranges.append({"start": line, "end": line, "display": part})
        elif part:
            log.warning(f"Could not parse coverage entry: {part}")
    return ranges


def parse_coverage_report(report: str) -> list[dict[str, Any]]:
    """Parses the pytest coverage report to find files with less than 100% coverage."""
    log.info("Parsing coverage report.")
    files_with_missed_lines = []

    lines = report.splitlines()
    header_index = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("Name") and "Stmts" in line and "Cover" in line:
            header_index = i
            break

    if header_index == -1:
        log.warning("Could not find coverage report header.")
        return []

    header = lines[header_index]
    col_stmts_start = header.find("Stmts")
    col_cover_start = header.find("Cover")
    col_missing_start = header.find("Missing")

    if -1 in [col_stmts_start, col_cover_start, col_missing_start]:
        log.error("Could not parse coverage report header columns.")
        return []

    # Data starts 2 lines after header (skip header and '---' line)
    for line in lines[header_index + 2 :]:
        if line.startswith("---") or not line.strip() or line.startswith("TOTAL"):
            continue

        name = line[:col_stmts_start].strip()
        if not name.endswith(".py"):
            continue

        cover_str = line[col_cover_start:col_missing_start].strip()

        try:
            coverage = int(cover_str.rstrip("%"))
        except (ValueError, AttributeError):
            log.warning(
                f"Could not parse coverage percentage for {name}: '{cover_str}'",
            )
            continue

        if coverage < 100:
            missing = line[col_missing_start:].strip()
            if missing:
                log.info(f"Found file with < 100% coverage: {name} ({coverage}%)")
                files_with_missed_lines.append(
                    {
                        "filename": name,
                        "coverage": coverage,
                        "line_ranges": parse_line_ranges(missing),
                    },
                )

    return files_with_missed_lines


def get_function_for_line(
    line_num: int,
    functions: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Finds the function containing a given line number."""
    containing_functions = [f for f in functions if f["start"] <= line_num <= f["end"]]
    if not containing_functions:
        return None
    # Return the innermost function (the one with the latest start line)
    return max(containing_functions, key=lambda f: f["start"])


def get_missed_code_details(file_info: dict[str, Any]) -> dict[str, Any]:
    """Reads a file and extracts details about missed code."""
    filename = file_info["filename"]
    log.info(f"Analyzing {filename} for missed code details.")

    try:
        source_path = Path(filename)
        source_code = source_path.read_text()
        source_lines = source_code.splitlines()
    except FileNotFoundError:
        log.error(f"File not found: {filename}")
        file_info["lines"] = []
        return file_info

    try:
        tree = ast.parse(source_code)
        finder = FunctionFinder()
        finder.visit(tree)
        functions = finder.functions
    except SyntaxError as e:
        log.error(f"Could not parse AST for {filename}: {e}")
        functions = []

    missed_lines_details = []
    for range_info in file_info["line_ranges"]:
        start = range_info["start"]
        end = range_info["end"]

        function = get_function_for_line(start, functions)

        if range_info.get("to_exit") and function:
            end = function["end"]

        function_name = function["name"] if function else "<module>"

        code_lines = source_lines[start - 1 : end]
        missed_code = "\n".join(code_lines)

        missed_lines_details.append(
            {
                "line_display": range_info["display"],
                "function_name": function_name,
                "missed_code": missed_code,
            },
        )

    file_info["lines"] = missed_lines_details
    if "line_ranges" in file_info:
        del file_info["line_ranges"]
    return file_info


@click.command()
@click.argument(
    "source_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
)
def main(source_dir: str):
    """
    Generates a detailed code coverage report from PyTest output.

    SOURCE_DIR: The directory containing the source code to be analyzed.
    """
    log.info(f"Starting coverage analysis for directory: {source_dir}")

    try:
        pytest_output = run_pytest_coverage(source_dir)
    except click.ClickException:
        return  # Error already logged

    files_to_analyze = parse_coverage_report(pytest_output)

    if not files_to_analyze:
        log.info("Congratulations! All files have 100% coverage.")
        return

    detailed_reports = [get_missed_code_details(f) for f in files_to_analyze]

    log.info("Generating final report.")
    print("\n\n======== Detailed Coverage Report ========")
    for report_data in detailed_reports:
        missed_lines_str = []
        if "lines" not in report_data:
            continue

        for line_info in report_data["lines"]:
            display = line_info["line_display"]
            if "->" in display or "-" in display:
                line_text = f"Lines: {display}"
            else:
                line_text = f"Line: {display}"
            details = (
                f"  Function: {line_info['function_name']}()\n"
                f"  {line_text} \n"
                "  Code:\n"
                f"{textwrap.indent(line_info['missed_code'], '    ')}"
            )
            missed_lines_str.append(details)

        formatted_report = TEMPLATE.format(
            filename=report_data["filename"],
            coverage=report_data["coverage"],
            missed_lines_details="\n\n".join(missed_lines_str),
        )
        print(formatted_report)


if __name__ == "__main__":
    main()
