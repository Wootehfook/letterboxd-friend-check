#!/usr/bin/env python3
"""
Pre-commit Check Script
======================
Automated validation to ensure clean git commits by checking for:
- Unwanted temporary files
- Large files that shouldn't be committed
- Files that should be in .gitignore
- Cosmetic-only changes vs. functional changes

Usage:
    python pre_commit_check.py [--fix] [--verbose]

Options:
    --fix       Automatically fix issues where possible
    --verbose   Show detailed output

Exit codes:
    0: Clean - safe to commit
    1: Issues found - review before committing
    2: Critical issues - do not commit
"""

import sys
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Tuple


class PreCommitChecker:
    def __init__(self, fix_mode: bool = False, verbose: bool = False):
        self.fix_mode = fix_mode
        self.verbose = verbose
        self.issues = []
        self.warnings = []
        self.fixes_applied = []

        # Files that should never be committed
        self.forbidden_patterns = [
            "*.tmp",
            "*.log",
            "*.cache",
            "*.swp",
            "*.swo",
            "bandit-*.json",
            "safety-*.json",
            "trufflehog-*.json",
            "*-security-report.*",
            "security_report*.txt",
            "*.pyc",
            "__pycache__/*",
            ".pytest_cache/*",
            ".coverage",
            "coverage.xml",
            "htmlcov/*",
            "*.orig",
            "*.rej",
        ]

        # Files that are cosmetic-only (formatting, style)
        self.cosmetic_indicators = [
            "single quotes to double quotes",
            "trailing whitespace",
            "line too long",
            "blank line",
            "indentation",
            "import order",
        ]

    def log(self, message: str, level: str = "INFO"):
        """Log message with appropriate formatting."""
        if level == "ERROR":
            print(f"❌ {message}")
            self.issues.append(message)
        elif level == "WARNING":
            print(f"⚠️  {message}")
            self.warnings.append(message)
        elif level == "SUCCESS":
            print(f"✅ {message}")
        elif level == "FIX":
            print(f"🔧 {message}")
            self.fixes_applied.append(message)
        elif self.verbose or level == "INFO":
            print(f"ℹ️  {message}")

    def run_git_command(self, cmd: List[str]) -> Tuple[str, int]:
        """Run git command and return output and return code."""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            return result.stdout.strip(), result.returncode
        except Exception as e:
            self.log(f"Git command failed: {e}", "ERROR")
            return "", 1

    def get_modified_files(self) -> Dict[str, str]:
        """Get list of modified files and their status."""
        output, _ = self.run_git_command(["git", "status", "--porcelain"])

        files = {}
        for line in output.split("\n"):
            if line.strip():
                status = line[:2]
                filename = line[3:]
                files[filename] = status

        return files

    def get_staged_files(self) -> List[str]:
        """Get list of staged files."""
        output, _ = self.run_git_command(["git", "diff", "--cached", "--name-only"])
        return [f for f in output.split("\n") if f.strip()]

    def check_forbidden_files(self, files: Dict[str, str]) -> None:
        """Check for files that should never be committed."""
        self.log("Checking for forbidden files...", "INFO")

        forbidden_found = []
        for filename in files.keys():
            file_path = Path(filename)

            # Check against forbidden patterns
            for pattern in self.forbidden_patterns:
                if file_path.match(pattern) or pattern.replace("*", "") in filename:
                    forbidden_found.append(filename)
                    break

            # Check file size (>10MB is suspicious)
            if file_path.exists() and file_path.stat().st_size > 10 * 1024 * 1024:
                size_mb = file_path.stat().st_size / 1024 / 1024
                self.log(f"Large file detected: {filename} ({size_mb:.1f}MB)", "WARNING")

        if forbidden_found:
            self.log(f"Forbidden files found: {forbidden_found}", "ERROR")
            if self.fix_mode:
                self.remove_forbidden_files(forbidden_found)
        else:
            self.log("No forbidden files found", "SUCCESS")

    def remove_forbidden_files(self, files: List[str]) -> None:
        """Remove forbidden files from git tracking."""
        for filename in files:
            # Remove from git if tracked
            output, code = self.run_git_command(["git", "rm", "--cached", filename])
            if code == 0:
                self.log(f"Removed from git: {filename}", "FIX")

            # Add to .gitignore if not already there
            self.ensure_in_gitignore(filename)

    def ensure_in_gitignore(self, filename: str) -> None:
        """Ensure pattern is in .gitignore."""
        gitignore_path = Path(".gitignore")

        if not gitignore_path.exists():
            return

        # Determine appropriate pattern
        if filename.startswith("bandit-"):
            pattern = "bandit-*.json"
        elif filename.startswith("safety-"):
            pattern = "safety-*.json"
        elif filename.endswith(".json") and any(x in filename for x in ["security", "report"]):
            pattern = "*-security-report.*"
        else:
            pattern = filename

        # Check if already in .gitignore
        content = gitignore_path.read_text()
        if pattern not in content:
            with open(gitignore_path, "a") as f:
                f.write(f"\n{pattern}\n")
            self.log(f"Added to .gitignore: {pattern}", "FIX")

    def analyze_changes(self, files: Dict[str, str]) -> None:
        """Analyze the nature of changes in modified files."""
        self.log("Analyzing change types...", "INFO")

        cosmetic_files = []
        functional_files = []

        for filename in files.keys():
            if not filename.endswith((".py", ".js", ".ts", ".yml", ".yaml")):
                continue

            # Get diff for the file
            output, _ = self.run_git_command(["git", "diff", filename])

            if not output:
                continue

            # Analyze diff content
            is_cosmetic = self.is_cosmetic_change(output)

            if is_cosmetic:
                cosmetic_files.append(filename)
            else:
                functional_files.append(filename)

        if cosmetic_files:
            self.log(f"Cosmetic-only changes detected in: {cosmetic_files}", "WARNING")
            self.log("Consider reviewing if these should be committed", "WARNING")

        if functional_files:
            self.log(f"Functional changes detected in: {functional_files}", "INFO")

    def is_cosmetic_change(self, diff_content: str) -> bool:
        """Determine if changes are purely cosmetic."""
        lines = diff_content.split("\n")

        functional_changes = 0
        cosmetic_changes = 0

        for line in lines:
            if line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
                # Skip pure whitespace changes
                stripped = line[1:].strip()
                original_line = line[1:]

                if not stripped:  # Empty line change
                    cosmetic_changes += 1
                elif any(indicator in line.lower() for indicator in self.cosmetic_indicators):
                    cosmetic_changes += 1
                elif original_line != original_line.strip():  # Whitespace only
                    cosmetic_changes += 1
                elif "'" in line and '"' in line:  # Quote changes
                    # Check if it's just quote style change
                    single_to_double = line.replace('"', "'") in diff_content
                    double_to_single = line.replace("'", '"') in diff_content
                    if single_to_double or double_to_single:
                        cosmetic_changes += 1
                    else:
                        functional_changes += 1
                else:
                    functional_changes += 1

        # If >80% cosmetic, consider it cosmetic-only
        total_changes = functional_changes + cosmetic_changes
        if total_changes == 0:
            return False

        return (cosmetic_changes / total_changes) > 0.8

    def check_commit_readiness(self) -> None:
        """Check if repository is ready for commit."""
        self.log("Checking commit readiness...", "INFO")

        # Check for staged vs unstaged changes
        staged = self.get_staged_files()
        modified = self.get_modified_files()

        if not staged and not modified:
            self.log("No changes to commit", "INFO")
            return

        if modified and not staged:
            self.log("Changes detected but nothing staged", "WARNING")
            self.log("Run 'git add <files>' to stage changes", "INFO")

        # Check for mixed staged/unstaged in same files
        staged_set = set(staged)
        modified_set = set(modified.keys())
        overlap = staged_set.intersection(modified_set)

        if overlap:
            self.log(f"Files with both staged and unstaged changes: {list(overlap)}", "WARNING")

    def generate_commit_suggestion(self, files: Dict[str, str]) -> None:
        """Generate commit message suggestions based on changes."""
        if not files:
            return

        categories = {
            "security": [],
            "fix": [],
            "feature": [],
            "style": [],
            "docs": [],
            "test": [],
            "config": [],
        }

        for filename in files.keys():
            if any(x in filename.lower() for x in ["security", "bandit", "safety"]):
                categories["security"].append(filename)
            elif filename.startswith("test_") or "/test" in filename:
                categories["test"].append(filename)
            elif filename.endswith((".md", ".txt", ".rst")):
                categories["docs"].append(filename)
            elif filename.endswith((".yml", ".yaml", ".json", ".toml", ".ini")):
                categories["config"].append(filename)
            elif self.is_cosmetic_change(self.run_git_command(["git", "diff", filename])[0]):
                categories["style"].append(filename)
            else:
                categories["feature"].append(filename)

        # Generate suggestion
        parts = []
        if categories["security"]:
            parts.append("🔒 Security fixes")
        if categories["fix"]:
            parts.append("🐛 Bug fixes")
        if categories["feature"]:
            parts.append("✨ New features")
        if categories["config"]:
            parts.append("⚙️ Configuration updates")
        if categories["style"]:
            parts.append("🎨 Code formatting")
        if categories["test"]:
            parts.append("🧪 Test updates")
        if categories["docs"]:
            parts.append("📚 Documentation")

        if parts:
            self.log(f"Suggested commit prefix: {', '.join(parts)}", "INFO")

    def run_checks(self) -> int:
        """Run all pre-commit checks."""
        print("🚀 Running pre-commit checks...")
        print("=" * 50)

        # Get current file status
        modified_files = self.get_modified_files()

        if not modified_files:
            self.log("No modified files found", "SUCCESS")
            return 0

        self.log(f"Found {len(modified_files)} modified files", "INFO")

        # Run checks
        self.check_forbidden_files(modified_files)
        self.analyze_changes(modified_files)
        self.check_commit_readiness()
        self.generate_commit_suggestion(modified_files)

        # Summary
        print("\n" + "=" * 50)
        print("📊 PRE-COMMIT CHECK SUMMARY")
        print("=" * 50)

        if self.fixes_applied:
            print(f"🔧 Fixes applied: {len(self.fixes_applied)}")
            for fix in self.fixes_applied:
                print(f"   • {fix}")

        if self.warnings:
            print(f"⚠️  Warnings: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"   • {warning}")

        if self.issues:
            print(f"❌ Issues found: {len(self.issues)}")
            for issue in self.issues:
                print(f"   • {issue}")
            print("\n🛑 CRITICAL: Do not commit until issues are resolved!")
            return 2
        elif self.warnings:
            print("\n⚠️  CAUTION: Review warnings before committing")
            return 1
        else:
            print("\n✅ SUCCESS: Repository ready for commit!")
            return 0


def main():
    parser = argparse.ArgumentParser(description="Pre-commit validation checks")
    parser.add_argument(
        "--fix", action="store_true", help="Automatically fix issues where possible"
    )
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")

    args = parser.parse_args()

    checker = PreCommitChecker(fix_mode=args.fix, verbose=args.verbose)
    exit_code = checker.run_checks()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
