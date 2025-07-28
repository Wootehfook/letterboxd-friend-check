#!/usr/bin/env python
"""
Quick Commit - Simple wrapper for smart git automation

Usage:
    python quick_commit.py          # Safe automatic commit
    python quick_commit.py --check  # Preview what would be committed
    python quick_commit.py --ask    # Ask before committing

Author: GitHub Copilot
"""

import subprocess
import sys
import argparse


def main():
    parser = argparse.ArgumentParser(description="Quick commit with safety checks")
    parser.add_argument("--check", action="store_true", help="Preview mode (dry run)")
    parser.add_argument("--ask", action="store_true", help="Interactive mode")
    parser.add_argument("message", nargs="?", help="Custom commit message")

    args = parser.parse_args()

    # Build command for smart_git_automation.py
    cmd = [sys.executable, "scripts/git/smart_git_automation.py"]

    if args.check:
        cmd.append("--dry-run")
        cmd.append("--interactive")
    elif args.ask:
        cmd.append("--interactive")

    print("🚀 Quick Commit - Letterboxd Friend Check")
    print("=" * 40)

    # Run the smart automation
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
