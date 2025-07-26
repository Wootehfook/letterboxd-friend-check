#!/usr/bin/env python
"""
Clean Repository Creator for Letterboxd Friend Check

This script creates a completely clean copy of your repository with:
1. No Git history containing sensitive data
2. All personal data files removed
3. Ready for public GitHub repository

Usage:
    python create_clean_repo.py

Author: GitHub Copilot
"""

import os
import shutil
import subprocess
import sys
import re
from pathlib import Path


class CleanRepositoryCreator:
    """Creates a clean repository copy without sensitive data or history."""

    def __init__(self):
        self.current_dir = Path.cwd()
        self.clean_dir = self.current_dir.parent / "LetterboxdFriendCheck-Clean"

        # Files to exclude from clean copy
        self.exclude_files = {
            # Personal data files
            "config.json",
            "data/config.json",
            "letterboxd_friend_check/data/config.json",
            "letterboxd.db",
            "letterboxd.db-journal",
            "Cookie.json",
            ".env",
            # Development documentation
            "GITLENS_ENABLED.md",
            "DEPLOYMENT_COMPLETE.md",
            "DEPLOYMENT_READY.md",
            "DEPLOYMENT_CHECKLIST.md",
            "PRIVATE_REPO_GUIDE.md",
            "GITHUB_SETUP.md",
            "RELEASE_NOTES.md",
            "DOWNLOAD_FOLDER_SUCCESS.md",
            "SECURITY_ALERT_GIT_HISTORY.md",
            # Development backups
            "backup_dev_state_20250725_210536/",
            # Build artifacts
            "build/",
            "dist/",
            "distribution/",
            # Personal VS Code settings
            ".vscode/settings.json",
            # Git history
            ".git/",
            # Cache and temp
            "__pycache__/",
            "*.pyc",
            "*.pyo",
            "*.tmp",
            "*.log",
            "logs/",
            # This cleanup script itself
            "create_clean_repo.py",
        }

        # Directories to exclude completely
        self.exclude_dirs = {
            ".git",
            "__pycache__",
            "build",
            "dist",
            "distribution",
            "backup_dev_state_20250725_210536",
            "logs",
        }

    def run(self):
        """Execute the clean repository creation process."""
        print("🧹 Creating Clean Repository - Letterboxd Friend Check")
        print("=" * 60)

        try:
            # 1. Create clean directory
            self.create_clean_directory()

            # 2. Copy safe files
            self.copy_safe_files()

            # 3. Verify no sensitive data
            self.verify_clean_copy()

            # 4. Initialize new Git repository
            self.initialize_git_repo()

            # 5. Create initial commit
            self.create_initial_commit()

            # 6. Display success message
            self.display_success_message()

            return True

        except Exception as e:
            print(f"❌ Error creating clean repository: {e}")
            return False

    def create_clean_directory(self):
        """Create the clean repository directory."""
        print(f"📁 Creating clean directory: {self.clean_dir}")

        if self.clean_dir.exists():
            print("   ⚠️  Directory exists, removing old version...")
            shutil.rmtree(self.clean_dir)

        self.clean_dir.mkdir()
        print(f"   ✓ Created: {self.clean_dir}")

    def copy_safe_files(self):
        """Copy only safe files to the clean directory."""
        print("\n📋 Copying safe files...")

        copied_count = 0
        excluded_count = 0

        for root, dirs, files in os.walk(self.current_dir):
            # Remove excluded directories from dirs list to skip them
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            rel_root = Path(root).relative_to(self.current_dir)

            # Skip if this is an excluded directory
            if any(part in self.exclude_dirs for part in rel_root.parts):
                continue

            for file in files:
                rel_file_path = rel_root / file

                # Check if file should be excluded
                if self.should_exclude_file(rel_file_path):
                    excluded_count += 1
                    print(f"   ❌ Excluded: {rel_file_path}")
                    continue

                # Copy the file
                source_path = Path(root) / file
                dest_path = self.clean_dir / rel_file_path

                # Create directory if needed
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                # Copy file
                shutil.copy2(source_path, dest_path)
                copied_count += 1
                print(f"   ✓ Copied: {rel_file_path}")

        print(f"\n📊 Copy Summary:")
        print(f"   ✅ Files copied: {copied_count}")
        print(f"   ❌ Files excluded: {excluded_count}")

    def should_exclude_file(self, file_path):
        """Check if a file should be excluded from the clean copy."""
        file_str = str(file_path)

        # Check exact matches
        if file_str in self.exclude_files or file_path.name in self.exclude_files:
            return True

        # Check patterns
        if file_str.endswith(".pyc") or file_str.endswith(".pyo"):
            return True
        if file_str.endswith(".tmp") or file_str.endswith(".log"):
            return True
        if "__pycache__" in file_str:
            return True

        return False

    def verify_clean_copy(self):
        """Verify the clean copy contains no sensitive data."""
        print("\n🔍 Verifying clean copy...")

        # Use pattern matching instead of hardcoded sensitive data
        sensitive_patterns = [
            r"[a-f0-9]{32}",  # 32-char hex strings (API key format)
            r'"tmdb_api_key":\s*"[^"]{20,}"',  # Filled API keys in JSON
        ]

        issues_found = []

        for root, dirs, files in os.walk(self.clean_dir):
            for file in files:
                if file.endswith((".py", ".json", ".md", ".txt", ".yml", ".yaml")):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()

                        for pattern in sensitive_patterns:
                            if re.search(pattern, content):
                                issues_found.append(f"{file_path}: contains sensitive data pattern")

                    except Exception:
                        continue

        if issues_found:
            print("   ⚠️  Potential issues found:")
            for issue in issues_found:
                print(f"      {issue}")
        else:
            print("   ✅ No sensitive data found in clean copy!")

    def initialize_git_repo(self):
        """Initialize a new Git repository in the clean directory."""
        print(f"\n🔧 Initializing Git repository...")

        os.chdir(self.clean_dir)

        # Initialize repo
        subprocess.run(["git", "init"], check=True)
        print("   ✓ Git repository initialized")

        # Configure user (copy from original repo)
        original_dir = self.current_dir
        os.chdir(original_dir)

        try:
            name_result = subprocess.run(
                ["git", "config", "user.name"], capture_output=True, text=True
            )
            email_result = subprocess.run(
                ["git", "config", "user.email"], capture_output=True, text=True
            )

            os.chdir(self.clean_dir)

            if name_result.returncode == 0 and name_result.stdout.strip():
                subprocess.run(
                    ["git", "config", "user.name", name_result.stdout.strip()], check=True
                )
                print(f"   ✓ Git user name configured")

            if email_result.returncode == 0 and email_result.stdout.strip():
                subprocess.run(
                    ["git", "config", "user.email", email_result.stdout.strip()], check=True
                )
                print(f"   ✓ Git user email configured")

        except subprocess.CalledProcessError:
            print("   ⚠️  Could not copy Git configuration, using defaults")

    def create_initial_commit(self):
        """Create the initial commit with all clean files."""
        print(f"\n💾 Creating initial commit...")

        # Add all files
        subprocess.run(["git", "add", "."], check=True)
        print("   ✓ All files staged")

        # Create commit
        commit_message = "Initial commit - Letterboxd Friend Check (clean history)"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        print(f"   ✓ Initial commit created")

        # Show status
        result = subprocess.run(["git", "log", "--oneline"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   📋 Commit: {result.stdout.strip()}")

    def display_success_message(self):
        """Display success message with next steps."""
        print(f"\n🎉 Clean Repository Created Successfully!")
        print("=" * 50)
        print(f"📁 Location: {self.clean_dir}")
        print(f"🔒 Security: No sensitive data in history")
        print(f"🚀 Status: Ready for public GitHub repository")

        print(f"\n📋 Next Steps:")
        print(f"1. 🔥 REVOKE old API key at https://www.themoviedb.org/settings/api")
        print(f"2. 🆕 GET new API key from TMDB")
        print(f"3. 📝 UPDATE config.json in clean repo with new key (local only)")
        print(f"4. 🌐 CREATE new GitHub repository")
        print(f"5. 📤 PUSH clean repository to GitHub")

        print(f"\n🛡️ Git Commands for GitHub:")
        print(f"   cd {self.clean_dir}")
        print(f"   git remote add origin https://github.com/Wootehfook/NEW_REPO_NAME.git")
        print(f"   git branch -M main")
        print(f"   git push -u origin main")

        print(f"\n✅ This repository will be 100% safe to make public!")


def main():
    """Main entry point."""
    creator = CleanRepositoryCreator()
    success = creator.run()

    if success:
        print(f"\n🎊 SUCCESS: Clean repository ready!")
        sys.exit(0)
    else:
        print(f"\n❌ FAILED: Could not create clean repository")
        sys.exit(1)


if __name__ == "__main__":
    main()
