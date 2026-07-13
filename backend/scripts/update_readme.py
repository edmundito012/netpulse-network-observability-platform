from __future__ import annotations

import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

README_PATH = PROJECT_ROOT / "README.md"
SCREENSHOTS_DIR = PROJECT_ROOT / "docs" / "screenshots"
TEST_RESULTS_PATH = (
    PROJECT_ROOT
    / "docs"
    / "evidence"
    / "latest-tests.txt"
)

START_MARKER = "<!-- NETPULSE:AUTO:START -->"
END_MARKER = "<!-- NETPULSE:AUTO:END -->"

MAX_COMMITS = 10


def run_git_command(arguments: list[str]) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        return ""

    return result.stdout.strip()


def get_test_summary() -> tuple[int | None, int | None]:
    if not TEST_RESULTS_PATH.exists():
        return None, None

    content = TEST_RESULTS_PATH.read_text(
        encoding="utf-8",
        errors="replace",
    )

    passed_match = re.search(
        r"(\d+)\s+passed",
        content,
    )

    warnings_match = re.search(
        r"(\d+)\s+warnings?",
        content,
    )

    passed = (
        int(passed_match.group(1))
        if passed_match
        else None
    )

    warnings = (
        int(warnings_match.group(1))
        if warnings_match
        else 0
    )

    return passed, warnings


def get_recent_commits() -> list[str]:
    output = run_git_command(
        [
            "log",
            f"-{MAX_COMMITS}",
            "--pretty=format:%s",
        ]
    )

    if not output:
        return []

    accepted_prefixes = (
        "feat(",
        "fix(",
        "refactor(",
        "test(",
        "perf(",
        "chore(",
        "docs(",
    )

    commits = []

    for line in output.splitlines():
        clean_line = line.strip()

        if clean_line.startswith(accepted_prefixes):
            commits.append(clean_line)

    return commits


def format_commit(commit: str) -> str:
    match = re.match(
        r"(?P<type>[a-z]+)"
        r"\((?P<scope>[^)]+)\): "
        r"(?P<message>.+)",
        commit,
    )

    if not match:
        return commit

    commit_type = match.group("type")
    scope = match.group("scope")
    message = match.group("message")

    icons = {
        "feat": "✨",
        "fix": "🐛",
        "refactor": "♻️",
        "test": "🧪",
        "perf": "⚡",
        "chore": "🔧",
        "docs": "📝",
    }

    icon = icons.get(commit_type, "•")

    return (
        f"{icon} **{scope}** — {message}"
    )


def get_screenshots() -> list[Path]:
    if not SCREENSHOTS_DIR.exists():
        return []

    extensions = {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
    }

    return sorted(
        path
        for path in SCREENSHOTS_DIR.iterdir()
        if (
            path.is_file()
            and path.suffix.lower() in extensions
        )
    )


def build_test_section() -> list[str]:
    passed, warnings = get_test_summary()

    lines = [
        "### ✅ Automated Quality",
        "",
    ]

    if passed is None:
        lines.append(
            "Test results are not available yet."
        )

        return lines

    lines.append(
        f"- **Tests:** {passed} passed"
    )

    lines.append(
        f"- **Warnings:** {warnings or 0}"
    )

    lines.extend(
        [
            "- **CI:** GitHub Actions",
            "- **Security:** CodeQL",
            "- **Workflow:** Feature branch → Pull Request → CI → Merge",
        ]
    )

    return lines


def build_feature_section() -> list[str]:
    commits = get_recent_commits()

    lines = [
        "### 🧠 Recent Engineering Milestones",
        "",
    ]

    if not commits:
        lines.append(
            "No recent conventional commits were found."
        )

        return lines

    for commit in commits:
        lines.append(
            f"- {format_commit(commit)}"
        )

    return lines


def build_screenshot_section() -> list[str]:
    screenshots = get_screenshots()

    lines = [
        "### 📸 Automated Screenshots",
        "",
    ]

    if not screenshots:
        lines.append(
            "Screenshots will appear after the visual workflow runs."
        )

        return lines

    for screenshot in screenshots:
        relative_path = screenshot.relative_to(
            PROJECT_ROOT
        )

        display_name = (
            screenshot.stem
            .replace("-", " ")
            .replace("_", " ")
            .title()
        )

        markdown_path = relative_path.as_posix()

        lines.extend(
            [
                f"#### {display_name}",
                "",
                f"![{display_name}]({markdown_path})",
                "",
            ]
        )

    return lines


def build_generated_content() -> str:
    updated_at = datetime.now(UTC).strftime(
        "%Y-%m-%d %H:%M UTC"
    )

    sections = [
        "Generated automatically from tests, commits, and screenshots.",
        "",
        f"_Last automation run: {updated_at}_",
        "",
        *build_test_section(),
        "",
        *build_feature_section(),
        "",
        *build_screenshot_section(),
    ]

    return "\n".join(sections).strip()


def update_readme() -> None:
    if not README_PATH.exists():
        raise FileNotFoundError(
            f"README not found: {README_PATH}"
        )

    readme = read_text_with_fallback(
        README_PATH
    )

    if (
        START_MARKER not in readme
        or END_MARKER not in readme
    ):
        raise RuntimeError(
            "README markers were not found. Add "
            f"{START_MARKER} and {END_MARKER}."
        )

    generated_content = build_generated_content()

    replacement = (
        f"{START_MARKER}\n\n"
        f"{generated_content}\n\n"
        f"{END_MARKER}"
    )

    pattern = re.compile(
        rf"{re.escape(START_MARKER)}"
        rf".*?"
        rf"{re.escape(END_MARKER)}",
        flags=re.DOTALL,
    )

    updated_readme = pattern.sub(
        replacement,
        readme,
        count=1,
    )

    README_PATH.write_text(
        updated_readme,
        encoding="utf-8",
    )

    print(
        f"README updated successfully: {README_PATH}"
    )


def read_text_with_fallback(
    path: Path,
) -> str:
    encodings = (
        "utf-8-sig",
        "utf-16",
        "utf-16-le",
        "utf-16-be",
        "cp1252",
    )

    for encoding in encodings:
        try:
            return path.read_text(
                encoding=encoding,
            )
        except UnicodeDecodeError:
            continue

    raise RuntimeError(
        f"Unable to decode file: {path}"
    )

if __name__ == "__main__":
    update_readme()