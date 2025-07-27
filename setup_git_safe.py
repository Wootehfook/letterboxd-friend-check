#!/usr/bin/env python3
"""
Setup Git Safe Aliases
======================
Creates convenient aliases for safe git operations.

This script sets up git aliases and shell functions to automatically
run pre-commit checks before git operations.
"""

import sys
import subprocess
from pathlib import Path


def setup_git_aliases():
    """Setup git aliases for safe operations."""
    aliases = {
        "safe-add": "!python git_safe.py add",
        "safe-commit": "!python git_safe.py commit",
        "safe-push": "!python git_safe.py push",
        "safe-check": "!python pre_commit_check.py",
    }

    print("🔧 Setting up git aliases...")

    for alias, command in aliases.items():
        try:
            subprocess.run(["git", "config", "--global", f"alias.{alias}", command], check=True)
            print(f"✅ Created alias: git {alias}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create alias {alias}: {e}")

    print("\n📝 Available aliases:")
    print("  git safe-add .        # Safe git add with checks")
    print("  git safe-commit -m '' # Safe git commit with checks")
    print("  git safe-push         # Safe git push with checks")
    print("  git safe-check        # Run pre-commit checks only")


def create_shell_functions():
    """Create shell function for convenient usage."""

    bash_function = """
# Git Safe Functions
# Add to your ~/.bashrc or ~/.zshrc

gadd() {
    python git_safe.py add "$@"
}

gcommit() {
    python git_safe.py commit "$@"
}

gpush() {
    python git_safe.py push "$@"
}

gcheck() {
    python pre_commit_check.py "$@"
}
"""

    powershell_function = """
# Git Safe Functions  
# Add to your PowerShell profile ($PROFILE)

function gadd { python git_safe.py add $args }
function gcommit { python git_safe.py commit $args }
function gpush { python git_safe.py push $args }
function gcheck { python pre_commit_check.py $args }
"""

    # Write to files
    with open("git_safe_functions.sh", "w") as f:
        f.write(bash_function)

    with open("git_safe_functions.ps1", "w") as f:
        f.write(powershell_function)

    print("\n📄 Shell function files created:")
    print("  git_safe_functions.sh  (for Bash/Zsh)")
    print("  git_safe_functions.ps1 (for PowerShell)")


def create_makefile_targets():
    """Create Makefile targets for easy usage."""
    makefile_content = """# Git Safe Targets
# Add to your existing Makefile

.PHONY: git-check git-add git-commit git-push

git-check:
    python pre_commit_check.py

git-add:
    python git_safe.py add .

git-commit:
    python git_safe.py commit

git-push:
    python git_safe.py push

# Combined targets
git-safe-commit: git-check
    @echo "Checks passed, ready to commit"

git-safe-push: git-check
    python git_safe.py push
"""

    with open("Makefile.git-safe", "w") as f:
        f.write(makefile_content)

    print("\n📄 Makefile targets created: Makefile.git-safe")
    print("  make git-check     # Run pre-commit checks")
    print("  make git-add       # Safe git add")
    print("  make git-push      # Safe git push")


def main():
    print("🚀 Setting up Git Safe automation...")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("pre_commit_check.py").exists():
        print("❌ pre_commit_check.py not found in current directory")
        print("Run this script from the repository root")
        sys.exit(1)

    setup_git_aliases()
    create_shell_functions()
    create_makefile_targets()

    print("\n" + "=" * 50)
    print("🎉 Git Safe setup complete!")
    print("\n📖 Usage options:")
    print("1. Direct scripts:")
    print("   python git_safe.py add .")
    print("   python pre_commit_check.py --fix")
    print()
    print("2. PowerShell wrapper:")
    print("   .\\git-safe.ps1 add .")
    print("   .\\git-safe.ps1 push")
    print()
    print("3. Git aliases (global):")
    print("   git safe-add .")
    print("   git safe-push")
    print()
    print("4. Shell functions (add to profile):")
    print("   gadd .    # Safe git add")
    print("   gpush     # Safe git push")
    print("   gcheck    # Run checks only")
    print()
    print("5. Make targets:")
    print("   make git-check")
    print("   make git-push")


if __name__ == "__main__":
    main()
