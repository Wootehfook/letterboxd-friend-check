#!/usr/bin/env python
"""
Smart Git Automation Script for Letterboxd Friend Check

This script intelligently reviews changes and automatically handles:
1. File classification (production vs development)
2. Sensitive data detection
3. Automatic staging of appropriate files
4. Smart commit messages
5. Safe push to GitHub

Usage:
    python smart_git_automation.py [--dry-run] [--interactive]

Author: GitHub Copilot
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import List, Dict


class SmartGitAutomation:
    """Intelligent Git automation for safe repository management."""

    def __init__(self, dry_run: bool = False, interactive: bool = False):
        self.dry_run = dry_run
        self.interactive = interactive
        self.repo_root = Path.cwd()

        # File classification rules
        self.production_files = {
            # Core application
            "LBoxFriendCheck.py",
            "run_letterboxd.py",
            "tmdb_api.py",
            "movie_database.py",
            # Package structure
            "letterboxd_friend_check/__init__.py",
            "letterboxd_friend_check/app.py",
            "letterboxd_friend_check/cli.py",
            "letterboxd_friend_check/config.py",
            "letterboxd_friend_check/new_methods.py",
            "letterboxd_friend_check/api/__init__.py",
            "letterboxd_friend_check/api/tmdb.py",
            "letterboxd_friend_check/data/__init__.py",
            "letterboxd_friend_check/data/database.py",
            "letterboxd_friend_check/gui/__init__.py",
            "letterboxd_friend_check/gui/menu_methods.py",
            "letterboxd_friend_check/gui/setup_dialog.py",
            "letterboxd_friend_check/utils/__init__.py",
            "letterboxd_friend_check/utils/logging.py",
            "letterboxd_friend_check/utils/web.py",
            # User documentation
            "README.md",
            "LICENSE",
            "CONTRIBUTING.md",
            "download/README.md",
            "download/INSTALL.md",
            # Configuration templates
            "config_template.json",
            "download/config_template.json",
            "requirements.txt",
            "pyproject.toml",
            "setup.py",
            ".env.example",
            # Build and deployment
            "build_executable.py",
            "prepare_for_production.py",
            "setup_github_repo.py",
            "SetupDialog.py",
            # Git automation system
            "smart_git_automation.py",
            "quick_commit.py",
            "commit.ps1",
            "GIT_AUTOMATION_GUIDE.md",
            # VS Code workspace (selective)
            ".vscode/tasks.json",
            ".vscode/launch.json",
            ".vscode/extensions.json",
            # Git configuration
            ".gitignore",
            # Tests
            "tests/__init__.py",
            "tests/test_letterboxd.py",
            "pytest.ini",
            "mypy.ini",
        }

        # Files that should NEVER be committed
        self.forbidden_files = {
            # Personal data
            "config.json",
            "data/config.json",
            "letterboxd_friend_check/data/config.json",
            "*.db",
            "*.db-journal",
            "*.sqlite3",
            "Cookie.json",
            ".env",
            # Development documentation
            "*_ENABLED.md",
            "*_SUCCESS.md",
            "*_COMPLETE.md",
            "*_READY.md",
            "DEPLOYMENT_*.md",
            "GITHUB_SETUP.md",
            "PRIVATE_REPO_GUIDE.md",
            "RELEASE_NOTES.md",
            "GITLENS_ENABLED.md",
            # Development files
            "test_*.py",
            "demo_*.py",
            "interactive_*.py",
            "*_testing_*.py",
            "fix_*.py",
            "Output.txt",
            "*.log",
            # Build artifacts
            "build/",
            "dist/",
            "*.spec",
            "*.exe",
            "distribution/",
            "download/LetterboxdFriendCheck.exe",
            # Backups and temporary
            "backup_*/",
            "*.tmp",
            "*.bak",
            "*.swp",
            # Cache
            "__pycache__/",
            "*.pyc",
            "*.pyo",
            # Personal VS Code settings
            ".vscode/settings.json",
        }

        # Sensitive data patterns - GENERIC (no personal data in code)
        self.sensitive_patterns = [
            r'"username":\s*"[^"\s]+"',  # Any non-empty username
            r'"tmdb_api_key":\s*"[a-zA-Z0-9]{20,}"',  # Any filled API key (20+ chars)
            r'"friends_list":\s*\[[^\]]*[^\s\]]+[^\]]*\]',  # Non-empty friends list
            r"Cookie\.json",  # Cookie file references
            r"letterboxd\.db",  # Database files
            # Pattern-based detection instead of hardcoded values
            r"[a-z0-9]{32}",  # 32-char hex strings (likely API keys)
            r'"[a-zA-Z][a-zA-Z0-9_]{2,19}"\s*:\s*"[^"]+@[^"]+"',  # Email patterns
        ]

        # Security report file patterns (should never be committed)
        self.security_report_patterns = [
            r"security_report.*\.txt",
            r"trufflehog-.*\.json",
            r".*-security-report\..*",
            r"bandit-report\.json",
            r"safety-report\.json",
        ]

    def run(self) -> bool:
        """Main automation workflow."""
        print("🤖 Smart Git Automation - Letterboxd Friend Check")
        print("=" * 60)

        try:
            # 1. Check git status
            changes = self.get_git_changes()
            if not changes["modified"] and not changes["untracked"] and not changes["deleted"]:
                print("✅ No changes detected. Repository is up to date!")
                return True

            # 2. Classify and review files
            review_result = self.review_changes(changes)

            # 3. Display review summary
            self.display_review_summary(review_result)

            # 4. Get user confirmation (if interactive)
            if self.interactive and not self.confirm_changes(review_result):
                print("❌ Operation cancelled by user.")
                return False

            # 5. Execute Git operations
            if not self.dry_run:
                return self.execute_git_operations(review_result)
            else:
                print("🔍 DRY RUN: Would execute the operations above.")
                return True

        except Exception as e:
            print(f"❌ Error during automation: {e}")
            return False

    def get_git_changes(self) -> Dict[str, List[str]]:
        """Get current git status and categorize changes."""
        print("📋 Scanning repository for changes...")

        try:
            # Get git status
            result = subprocess.run(
                ["git", "status", "--porcelain"], capture_output=True, text=True, check=True
            )

            changes = {"modified": [], "untracked": [], "deleted": [], "renamed": []}

            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                status = line[:2]
                filename = line[3:]

                if status.startswith("M") or status.startswith(" M"):
                    changes["modified"].append(filename)
                elif status.startswith("A") or status.startswith("??"):
                    changes["untracked"].append(filename)
                elif status.startswith("D"):
                    changes["deleted"].append(filename)
                elif status.startswith("R"):
                    changes["renamed"].append(filename)

            total_changes = sum(len(files) for files in changes.values())
            print(f"   📊 Found {total_changes} changes")

            return changes

        except subprocess.CalledProcessError:
            print("❌ Error: Not a git repository or git not available")
            raise

    def review_changes(self, changes: Dict[str, List[str]]) -> Dict:
        """Review and classify all changes."""
        print("\n🔍 Reviewing changes for safety...")

        review_result = {
            "safe_to_commit": [],
            "forbidden": [],
            "sensitive_content": [],
            "requires_review": [],
            "commit_message": "",
            "warnings": [],
        }

        all_files = []
        for file_list in changes.values():
            all_files.extend(file_list)

        for filename in all_files:
            classification = self.classify_file(filename)

            if classification == "forbidden":
                review_result["forbidden"].append(filename)
                review_result["warnings"].append(f"🚫 {filename} - Excluded by rules")

            elif classification == "sensitive":
                review_result["sensitive_content"].append(filename)
                review_result["warnings"].append(f"⚠️  {filename} - Contains sensitive data")

            elif classification == "production":
                review_result["safe_to_commit"].append(filename)

            else:  # 'needs_review'
                review_result["requires_review"].append(filename)
                review_result["warnings"].append(f"❓ {filename} - Needs manual review")

        # Generate smart commit message
        safe_files = review_result["safe_to_commit"]
        review_result["commit_message"] = self.generate_commit_message(safe_files)

        return review_result

    def classify_file(self, filename: str) -> str:
        """Classify a single file for commit eligibility."""
        filepath = Path(filename)

        # Check if it's a security report (highest priority - always forbidden)
        if self.is_security_report(filename):
            return "forbidden"

        # Check if explicitly forbidden
        if self.matches_pattern_list(filename, self.forbidden_files):
            return "forbidden"

        # Check for sensitive content in text files
        if filepath.suffix in [".py", ".json", ".md", ".txt", ".yml", ".yaml"]:
            if self.has_sensitive_content(filename):
                return "sensitive"

        # Check if it's a production file
        if filename in self.production_files or self.matches_pattern_list(
            filename, self.production_files
        ):
            return "production"

        # Default: needs review
        return "needs_review"

    def matches_pattern_list(self, filename: str, pattern_collection) -> bool:
        """Check if filename matches any pattern in the given collection."""
        if isinstance(pattern_collection, set):
            patterns = pattern_collection
        elif isinstance(pattern_collection, dict):
            patterns = set()
            for key, value in pattern_collection.items():
                if isinstance(value, list):
                    patterns.update(value)
                else:
                    patterns.add(key)
        else:
            patterns = pattern_collection

        for pattern in patterns:
            if self.matches_glob_pattern(filename, pattern):
                return True
        return False

    def matches_glob_pattern(self, filename: str, pattern: str) -> bool:
        """Check if filename matches a glob-style pattern."""
        import fnmatch

        # Handle directory patterns
        if pattern.endswith("/"):
            return filename.startswith(pattern[:-1] + "/")

        # Handle recursive patterns (**)
        if "**" in pattern:
            parts = pattern.split("**")
            if len(parts) == 2:
                prefix, suffix = parts
                return filename.startswith(prefix) and filename.endswith(suffix)

        # Standard glob matching
        return fnmatch.fnmatch(filename, pattern)

    def has_sensitive_content(self, filename: str) -> bool:
        """Check if file contains sensitive data patterns."""
        try:
            # Skip automation files - they may contain example patterns
            automation_files = [
                "smart_git_automation.py",
                "quick_commit.py",
                "GIT_AUTOMATION_GUIDE.md",
            ]
            if filename in automation_files:
                return False

            with open(filename, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            for pattern in self.sensitive_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return True

            return False

        except (IOError, UnicodeDecodeError):
            # If we can't read the file, be conservative
            return True

    def is_security_report(self, filename: str) -> bool:
        """Check if file is a security report that should never be committed."""
        try:
            for pattern in self.security_report_patterns:
                if re.search(pattern, filename, re.IGNORECASE):
                    return True
            return False
        except Exception:
            return False

    def generate_commit_message(self, safe_files: List[str]) -> str:
        """Generate an intelligent commit message based on changed files."""
        if not safe_files:
            return "Update repository configuration"

        # Categorize changes
        categories = {
            "core": [],
            "docs": [],
            "config": [],
            "build": [],
            "package": [],
            "automation": [],
        }

        core_files = ["LBoxFriendCheck.py", "run_letterboxd.py", "tmdb_api.py", "movie_database.py"]

        for filename in safe_files:
            if filename in core_files:
                categories["core"].append(filename)
            elif filename.endswith(".md") or "README" in filename:
                categories["docs"].append(filename)
            elif "config" in filename.lower() or filename in ["requirements.txt", "pyproject.toml"]:
                categories["config"].append(filename)
            elif filename in ["build_executable.py", "prepare_for_production.py"]:
                categories["build"].append(filename)
            elif filename.startswith("letterboxd_friend_check/"):
                categories["package"].append(filename)
            elif "automation" in filename.lower() or "commit" in filename.lower():
                categories["automation"].append(filename)

        # Generate message based on primary category
        if categories["automation"]:
            return "Add smart Git automation system"
        elif categories["core"]:
            return f"Update core application ({len(categories['core'])} files)"
        elif categories["docs"]:
            return f"Update documentation ({len(categories['docs'])} files)"
        elif categories["config"]:
            return "Update configuration and dependencies"
        elif categories["build"]:
            return "Update build and deployment scripts"
        elif categories["package"]:
            return f"Update package structure ({len(categories['package'])} files)"
        else:
            return f"Update project files ({len(safe_files)} files)"

    def display_review_summary(self, review_result: Dict):
        """Display a comprehensive review summary."""
        print("\n📊 Review Summary:")
        print("=" * 50)

        if review_result["safe_to_commit"]:
            print(f"✅ Ready to commit ({len(review_result['safe_to_commit'])} files):")
            for file in review_result["safe_to_commit"][:10]:  # Show first 10
                print(f"   📄 {file}")
            if len(review_result["safe_to_commit"]) > 10:
                print(f"   ... and {len(review_result['safe_to_commit']) - 10} more files")

        if review_result["forbidden"]:
            print(f"\n🚫 Excluded files ({len(review_result['forbidden'])} files):")
            for file in review_result["forbidden"][:5]:
                print(f"   ❌ {file}")
            if len(review_result["forbidden"]) > 5:
                print(f"   ... and {len(review_result['forbidden']) - 5} more")

        if review_result["sensitive_content"]:
            sensitive_count = len(review_result["sensitive_content"])
            print(f"\n⚠️  Files with sensitive content ({sensitive_count} files):")
            for file in review_result["sensitive_content"]:
                print(f"   🔒 {file}")

        if review_result["requires_review"]:
            print(f"\n❓ Requires manual review ({len(review_result['requires_review'])} files):")
            for file in review_result["requires_review"]:
                print(f"   🤔 {file}")

        if review_result["warnings"]:
            print("\n⚠️  Warnings:")
            for warning in review_result["warnings"][:5]:
                print(f"   {warning}")

        print("\n📝 Proposed commit message:")
        print(f"   '{review_result['commit_message']}'")

    def confirm_changes(self, review_result: Dict) -> bool:
        """Get user confirmation for the proposed changes."""
        if not review_result["safe_to_commit"]:
            print("\n❌ No files ready for commit.")
            return False

        print(f"\n❓ Ready to commit {len(review_result['safe_to_commit'])} files?")

        if review_result["forbidden"] or review_result["sensitive_content"]:
            print("⚠️  Note: Some files will be excluded for safety.")

        while True:
            response = input("\nProceed? (y/n/details): ").strip().lower()

            if response in ["y", "yes"]:
                return True
            elif response in ["n", "no"]:
                return False
            elif response in ["d", "details"]:
                self.show_detailed_review(review_result)
            else:
                print("Please enter 'y' for yes, 'n' for no, or 'd' for details.")

    def show_detailed_review(self, review_result: Dict):
        """Show detailed file-by-file review."""
        print("\n📋 Detailed Review:")
        print("-" * 30)

        print("✅ Files to commit:")
        for file in review_result["safe_to_commit"]:
            print(f"   {file}")

        if review_result["forbidden"]:
            print("\n🚫 Excluded files:")
            for file in review_result["forbidden"]:
                print(f"   {file}")

        if review_result["sensitive_content"]:
            print("\n🔒 Sensitive content detected:")
            for file in review_result["sensitive_content"]:
                print(f"   {file}")

    def execute_git_operations(self, review_result: Dict) -> bool:
        """Execute the git operations safely."""
        if not review_result["safe_to_commit"]:
            print("✅ No changes to commit.")
            return True

        print("\n🚀 Executing Git operations...")

        try:
            # Stage only the safe files
            print("📋 Staging files...")
            for filename in review_result["safe_to_commit"]:
                subprocess.run(["git", "add", filename], check=True)
                print(f"   ✓ Staged: {filename}")

            # Commit with generated message
            print("💾 Committing changes...")
            commit_msg = review_result["commit_message"]
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)
            print(f"   ✓ Committed: '{commit_msg}'")

            # Push to remote
            print("🌐 Pushing to GitHub...")
            result = subprocess.run(["git", "push"], capture_output=True, text=True)

            if result.returncode == 0:
                print("   ✅ Successfully pushed to GitHub!")
                return True
            else:
                print(f"   ⚠️  Push failed: {result.stderr}")
                print("   💡 You may need to run 'git pull' first or check your credentials.")
                return False

        except subprocess.CalledProcessError as e:
            print(f"❌ Git operation failed: {e}")
            return False


def main():
    """Main entry point with command line argument parsing."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Smart Git Automation for Letterboxd Friend Check",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python smart_git_automation.py                # Run with defaults
  python smart_git_automation.py --dry-run      # Preview actions only  
  python smart_git_automation.py --interactive  # Ask for confirmation
  python smart_git_automation.py --dry-run --interactive  # Preview with interaction
        """,
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Preview actions without making changes"
    )
    parser.add_argument(
        "--interactive", action="store_true", help="Ask for confirmation before committing"
    )
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")

    args = parser.parse_args()

    # Create and run automation
    automation = SmartGitAutomation(dry_run=args.dry_run, interactive=args.interactive)

    success = automation.run()

    if success:
        print("\n🎉 Git automation completed successfully!")
        if not args.dry_run:
            print("✅ Your changes are now safely on GitHub!")
        sys.exit(0)
    else:
        print("\n❌ Git automation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
