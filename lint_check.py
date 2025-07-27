#!/usr/bin/env python3
"""
Quick lint checker for common Python issues.
Helps identify potential pylint problems without full pylint installation.
"""

import os
import re


def check_f_strings(file_path):
    """Check for f-strings without placeholders."""
    issues = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for i, line in enumerate(lines, 1):
            # Look for f-strings without {} placeholders
            if re.search(r'f["\'][^"\']*["\']', line) and "{" not in line:
                issues.append(f"Line {i}: f-string without placeholders: {line.strip()}")
    except Exception as e:
        issues.append(f"Error reading file: {e}")

    return issues


def check_line_length(file_path, max_length=100):
    """Check for lines exceeding max length."""
    issues = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for i, line in enumerate(lines, 1):
            if len(line.rstrip()) > max_length:
                issues.append(f"Line {i}: Line too long ({len(line.rstrip())} > {max_length})")
    except Exception as e:
        issues.append(f"Error reading file: {e}")

    return issues


def check_trailing_whitespace(file_path):
    """Check for trailing whitespace."""
    issues = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for i, line in enumerate(lines, 1):
            if line.rstrip() != line.rstrip("\n"):
                issues.append(f"Line {i}: Trailing whitespace")
    except Exception as e:
        issues.append(f"Error reading file: {e}")

    return issues


def main():
    """Run lint checks on Python files."""
    print("🔍 Running quick lint checks...")

    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk("."):
        # Skip virtual environments and build directories
        dirs[:] = [d for d in dirs if d not in [".venv", "__pycache__", "build", "dist", ".git"]]

        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    total_issues = 0

    for file_path in python_files:
        print(f"\n📄 Checking {file_path}...")

        issues = []
        issues.extend(check_f_strings(file_path))
        issues.extend(check_line_length(file_path))
        issues.extend(check_trailing_whitespace(file_path))

        if issues:
            print(f"   ⚠️  Found {len(issues)} issues:")
            for issue in issues[:5]:  # Show first 5 issues
                print(f"      {issue}")
            if len(issues) > 5:
                print(f"      ... and {len(issues) - 5} more")
            total_issues += len(issues)
        else:
            print("   ✅ No issues found")

    print(f"\n📊 Summary: {total_issues} total issues found across {len(python_files)} files")

    if total_issues > 0:
        print("\n💡 Focus on files with the most issues for maximum impact!")


if __name__ == "__main__":
    main()
