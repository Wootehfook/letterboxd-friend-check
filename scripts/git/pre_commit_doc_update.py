#!/usr/bin/env python3
"""
Pre-commit hook to automatically update documentation
Runs before each commit to ensure documentation is current

Usage: Copy to .git/hooks/pre-commit and make executable
Created by: GitHub Copilot (Claude Sonnet 4) - 2025-07-28
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Pre-commit hook main function."""
    repo_root = Path(__file__).parent.parent.parent
    maintainer_script = repo_root / "tools" / "documentation_maintainer.py"

    if not maintainer_script.exists():
        print("⚠️ Documentation maintainer not found, skipping auto-update")
        return 0

    print("🔄 Auto-updating documentation...")

    try:
        # Run documentation maintenance
        result = subprocess.run(
            [sys.executable, str(maintainer_script), "--auto"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ Documentation updated successfully")

            # Check if any documentation files were modified - Fix for issue #11
            git_status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repo_root,
                capture_output=True,
                text=True,
            )

            modified_files = [
                line.split()[-1]
                for line in git_status.stdout.strip().splitlines()
                if line.split()[-1].endswith((".md", ".json", ".yaml"))
            ]

            if modified_files:
                print("📝 Documentation files were updated, adding to commit...")
                # Add updated documentation files to the commit
                files_to_add = ["PROJECT_SUMMARY.md", "PROJECT_SUMMARY_AI.json", ".ai-context.yaml"]
                subprocess.run(["git", "add"] + files_to_add, cwd=repo_root)
                print("✅ Updated documentation files added to commit")

        else:
            print("⚠️ Documentation update had issues (continuing with commit)")
            print(result.stderr)

    except Exception as e:
        print(f"⚠️ Error running documentation maintenance: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
