#!/usr/bin/env python3
"""
Git Safe - Pre-commit Safety Check
=================================
Quick safety wrapper for git operations to prevent accidental commits.

Usage:
    python git_safe.py add .
    python git_safe.py commit -m "message"
    python git_safe.py push

This script runs pre-commit checks before executing git commands.
"""

import sys
import subprocess


def run_pre_commit_check(fix_mode: bool = False) -> bool:
    """Run pre-commit checks and return True if safe to proceed."""
    print("🛡️  Running pre-commit safety checks...")

    try:
        # Run the pre-commit checker
        cmd = [sys.executable, "pre_commit_check.py"]
        if fix_mode:
            cmd.append("--fix")

        result = subprocess.run(cmd, capture_output=False)

        if result.returncode == 0:
            print("✅ Pre-commit checks passed - proceeding with git operation")
            return True
        elif result.returncode == 1:
            response = input("\n⚠️  Warnings found. Continue anyway? (y/N): ")
            return response.lower() in ["y", "yes"]
        else:
            print("\n❌ Critical issues found. Aborting git operation.")
            print("Run 'python pre_commit_check.py --fix' to auto-fix issues")
            return False

    except FileNotFoundError:
        print("❌ pre_commit_check.py not found in current directory")
        return False
    except Exception as e:
        print(f"❌ Error running pre-commit checks: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python git_safe.py <git-command> [args...]")
        print("Examples:")
        print("  python git_safe.py add .")
        print("  python git_safe.py commit -m 'message'")
        print("  python git_safe.py push")
        sys.exit(1)

    git_command = sys.argv[1]
    git_args = sys.argv[2:]

    # Commands that should trigger pre-commit checks
    check_commands = ["add", "commit", "push"]

    if git_command in check_commands:
        # Special handling for 'add .' - offer to fix issues automatically
        fix_mode = git_command == "add" and "." in git_args

        if not run_pre_commit_check(fix_mode=fix_mode):
            print(f"🛑 Aborting 'git {git_command}'")
            sys.exit(1)

    # Execute the git command
    cmd = ["git", git_command] + git_args
    print(f"🔧 Executing: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Error executing git command: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
