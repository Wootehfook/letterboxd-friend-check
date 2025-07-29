#!/usr/bin/env python3
"""
Documentation Maintenance Automation
Automatically updates project summary files with current information

Created by: GitHub Copilot (Claude Sonnet 4) - 2025-07-28
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class DocumentationMaintainer:
    """Maintains project documentation with current metadata."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.project_files = self._discover_project_files()

    def _discover_project_files(self) -> Dict[str, List[str]]:
        """Discover current project structure."""
        structure = {
            "core_files": [],
            "package_files": [],
            "script_files": [],
            "tool_files": [],
            "test_files": [],
            "doc_files": [],
        }

        # Core application files
        for pattern in ["*.py"]:
            for file in self.repo_path.glob(pattern):
                if file.is_file() and not file.name.startswith("."):
                    structure["core_files"].append(str(file.name))

        # Package structure
        package_dir = self.repo_path / "letterboxd_friend_check"
        if package_dir.exists():
            for file in package_dir.rglob("*.py"):
                rel_path = file.relative_to(self.repo_path)
                structure["package_files"].append(str(rel_path))

        # Scripts
        scripts_dir = self.repo_path / "scripts"
        if scripts_dir.exists():
            for file in scripts_dir.rglob("*.py"):
                rel_path = file.relative_to(self.repo_path)
                structure["script_files"].append(str(rel_path))

        # Tools
        tools_dir = self.repo_path / "tools"
        if tools_dir.exists():
            for file in tools_dir.rglob("*.py"):
                rel_path = file.relative_to(self.repo_path)
                structure["tool_files"].append(str(rel_path))

        # Tests
        tests_dir = self.repo_path / "tests"
        if tests_dir.exists():
            for file in tests_dir.rglob("*.py"):
                rel_path = file.relative_to(self.repo_path)
                structure["test_files"].append(str(rel_path))

        # Documentation
        for pattern in ["*.md", "*.rst", "*.txt"]:
            for file in self.repo_path.glob(pattern):
                if file.is_file():
                    structure["doc_files"].append(str(file.name))

        return structure

    def _get_git_info(self) -> Dict[str, Any]:
        """Get current git repository information."""
        try:
            # Get current branch
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            current_branch = branch_result.stdout.strip()

            # Get recent commits
            log_result = subprocess.run(
                ["git", "log", "--oneline", "-5"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            recent_commits = log_result.stdout.strip().split("\n") if log_result.stdout else []

            # Get remote URL
            remote_result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            remote_url = remote_result.stdout.strip()

            return {
                "current_branch": current_branch,
                "recent_commits": recent_commits,
                "remote_url": remote_url,
                "last_updated": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"error": str(e), "last_updated": datetime.now().isoformat()}

    def _count_lines_of_code(self) -> Dict[str, int]:
        """Count lines of code by file type (project files only)."""
        extensions = {".py": 0, ".js": 0, ".md": 0, ".json": 0, ".yaml": 0, ".yml": 0}
        
        # Exclude directories that contain external dependencies or generated files
        excluded_dirs = {
            "__pycache__", ".git", "node_modules", "venv", ".venv",
            "env", ".env", "build", "dist", ".pytest_cache", ".mypy_cache",
            "site-packages", ".tox", "htmlcov", ".coverage"
        }

        for ext in extensions.keys():
            for file in self.repo_path.rglob(f"*{ext}"):
                # Skip files in excluded directories
                if any(excluded_dir in file.parts for excluded_dir in excluded_dirs):
                    continue
                
                # Only count files in the project structure
                relative_path = file.relative_to(self.repo_path)
                if file.is_file() and relative_path.parts[0] not in excluded_dirs:
                    try:
                        with open(file, "r", encoding="utf-8", errors="ignore") as f:
                            extensions[ext] += len(f.readlines())
                    except Exception:
                        continue

        return extensions

    def update_ai_summary(self) -> bool:
        """Update PROJECT_SUMMARY_AI.json with current information."""
        ai_summary_path = self.repo_path / "PROJECT_SUMMARY_AI.json"

        try:
            # Load existing summary
            if ai_summary_path.exists():
                with open(ai_summary_path, "r") as f:
                    summary = json.load(f)
            else:
                summary = {}

            # Ensure project_metadata exists - Fix for issues #8, #9, #10
            if "project_metadata" not in summary:
                summary["project_metadata"] = {}

            # Update metadata
            summary["project_metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")

            # Update git information
            git_info = self._get_git_info()
            summary["git_status"] = git_info

            # Update file structure
            summary["current_structure"] = self.project_files

            # Update code statistics
            summary["code_statistics"] = self._count_lines_of_code()

            # Write back
            with open(ai_summary_path, "w") as f:
                json.dump(summary, f, indent=2)

            print(f"✅ Updated {ai_summary_path}")
            return True

        except Exception as e:
            print(f"❌ Error updating AI summary: {e}")
            return False

    def update_ai_context(self) -> bool:
        """Update .ai-context.yaml with current information."""
        context_path = self.repo_path / ".ai-context.yaml"

        try:
            # Read existing content
            if context_path.exists():
                with open(context_path, "r") as f:
                    content = f.read()
            else:
                content = ""

            # Update last_updated timestamp
            current_date = datetime.now().strftime("%Y-%m-%d")

            if "last_updated:" in content:
                # Replace existing timestamp
                import re

                content = re.sub(r"last_updated:.*", f"last_updated: {current_date}", content)
            else:
                # Add timestamp to project section
                content = content.replace("project:", f"project:\n  last_updated: {current_date}")

            # Write back
            with open(context_path, "w") as f:
                f.write(content)

            print(f"✅ Updated {context_path}")
            return True

        except Exception as e:
            print(f"❌ Error updating AI context: {e}")
            return False

    def update_human_summary(self) -> bool:
        """Update PROJECT_SUMMARY.md with current date."""
        summary_path = self.repo_path / "PROJECT_SUMMARY.md"

        try:
            if summary_path.exists():
                with open(summary_path, "r") as f:
                    content = f.read()

                # Update the last updated date using regex for robustness
                import re
                current_date = datetime.now().strftime("%B %d, %Y")
                
                # Match any date in "Last Updated: <date>" format
                content = re.sub(
                    r"\*Last Updated: .*?\*",
                    f"*Last Updated: {current_date}*",
                    content
                )

                with open(summary_path, "w") as f:
                    f.write(content)

                print(f"✅ Updated {summary_path}")
                return True
            else:
                print(f"⚠️ {summary_path} not found")
                return False

        except Exception as e:
            print(f"❌ Error updating human summary: {e}")
            return False

    def run_maintenance(self) -> bool:
        """Run complete documentation maintenance."""
        print("🔄 Running Documentation Maintenance...")
        print("=" * 50)

        success = True
        success &= self.update_ai_summary()
        success &= self.update_ai_context()
        success &= self.update_human_summary()

        if success:
            print("\n🎉 Documentation maintenance completed successfully!")
        else:
            print("\n⚠️ Some maintenance tasks failed. Check output above.")

        return success


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Maintain project documentation")
    parser.add_argument("--check", action="store_true", help="Check if updates are needed")
    parser.add_argument("--auto", action="store_true", help="Run automatically (for git hooks)")

    args = parser.parse_args()

    maintainer = DocumentationMaintainer()

    if args.check:
        # Just report current status
        print("📊 Documentation Status Check")
        print("=" * 30)
        git_info = maintainer._get_git_info()
        print(f"Current branch: {git_info.get('current_branch', 'unknown')}")
        print(f"Last updated: {git_info.get('last_updated', 'unknown')}")
        return 0

    # Run maintenance
    success = maintainer.run_maintenance()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
