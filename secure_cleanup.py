#!/usr/bin/env python3
"""
Secure File Cleanup Utility
Safely removes files containing sensitive data patterns without exposing the data itself.
Uses pattern matching instead of hardcoded sensitive values.
"""

import re
from pathlib import Path
from typing import List, Dict, Any
import argparse


class SecureCleanup:
    """Secure cleanup utility that uses patterns instead of hardcoded sensitive data."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()

        # Safe file patterns to automatically remove
        self.safe_to_remove_patterns = [
            r"backup_dev_state_.*",
            r"security_report.*\.txt",
            r"SECURITY_ALERT_.*\.md",  # Any security alert files
            r"trufflehog-.*\.json",
            r".*-security-report\..*",
        ]

        # Files that need manual review before deletion
        self.requires_review_patterns = [
            r"SECURITY\.md",
            r"create_clean_repo\.py",
            r".*\.py.*",  # Any Python files need review
        ]

        # Sensitive data patterns to detect (no actual secrets)
        self.sensitive_patterns = [
            r"[a-f0-9]{32}",  # 32-char hex (API key format)
            r'"api_key":\s*"[^"]{20,}"',  # API key in JSON
            r'"tmdb_api_key":\s*"[^"]{20,}"',  # TMDB API key in JSON
            r"api_key.*=.*[a-zA-Z0-9]{20,}",  # API key assignments
        ]

    def scan_for_sensitive_files(self) -> Dict[str, List[str]]:
        """Scan for files containing sensitive data patterns."""
        results = {"safe_to_remove": [], "requires_review": [], "clean_files": []}

        print("🔍 Scanning repository for files with sensitive data patterns...")

        for file_path in self.repo_path.rglob("*"):
            if not file_path.is_file() or file_path.name.startswith("."):
                continue

            try:
                # Check if file contains sensitive patterns
                if self._file_contains_sensitive_data(file_path):
                    relative_path = str(file_path.relative_to(self.repo_path))

                    # Categorize the file
                    if self._matches_safe_patterns(relative_path):
                        results["safe_to_remove"].append(relative_path)
                    elif self._matches_review_patterns(relative_path):
                        results["requires_review"].append(relative_path)
                    else:
                        results["requires_review"].append(relative_path)  # Default to review
                else:
                    relative_path = str(file_path.relative_to(self.repo_path))
                    results["clean_files"].append(relative_path)

            except Exception:
                # Skip files we can't read
                continue

        return results

    def _file_contains_sensitive_data(self, file_path: Path) -> bool:
        """Check if file contains any sensitive data patterns."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            for pattern in self.sensitive_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return True

            return False

        except Exception:
            return False

    def _matches_safe_patterns(self, file_path: str) -> bool:
        """Check if file matches safe-to-remove patterns."""
        for pattern in self.safe_to_remove_patterns:
            if re.search(pattern, file_path, re.IGNORECASE):
                return True
        return False

    def _matches_review_patterns(self, file_path: str) -> bool:
        """Check if file matches requires-review patterns."""
        for pattern in self.requires_review_patterns:
            if re.search(pattern, file_path, re.IGNORECASE):
                return True
        return False

    def cleanup_safe_files(self, dry_run: bool = True) -> Dict[str, Any]:
        """Remove files that are safe to delete automatically."""
        results = self.scan_for_sensitive_files()
        cleanup_results = {
            "deleted_files": [],
            "errors": [],
            "skipped_for_review": results["requires_review"],
        }

        print("\n📋 Summary:")
        print(f"   🗑️  Safe to remove: {len(results['safe_to_remove'])} files")
        print(f"   ⚠️  Requires review: {len(results['requires_review'])} files")
        print(f"   ✅ Clean files: {len(results['clean_files'])} files")

        if not results["safe_to_remove"]:
            print("\n✅ No files need automatic cleanup!")
            return cleanup_results

        print(f"\n{'🧹 DRY RUN - Would delete:' if dry_run else '🗑️ Deleting:'}")

        for file_path in results["safe_to_remove"]:
            full_path = self.repo_path / file_path

            try:
                if not dry_run:
                    full_path.unlink()
                    cleanup_results["deleted_files"].append(file_path)
                    print(f"   ✅ Deleted: {file_path}")
                else:
                    print(f"   🔍 Would delete: {file_path}")

            except Exception as e:
                error_msg = f"Failed to delete {file_path}: {str(e)}"
                cleanup_results["errors"].append(error_msg)
                print(f"   ❌ {error_msg}")

        if results["requires_review"]:
            print("\n⚠️  Files requiring manual review:")
            for file_path in results["requires_review"]:
                print(f"   📄 {file_path}")
            print("\n💡 These files contain sensitive data but need manual review before deletion.")

        return cleanup_results

    def generate_report(self) -> str:
        """Generate a cleanup report."""
        results = self.scan_for_sensitive_files()

        report = []
        report.append("🛡️  SECURE CLEANUP REPORT")
        report.append("=" * 50)
        report.append(f"📊 Repository: {self.repo_path}")
        report.append(
            f"🔍 Total files scanned: {len(results['safe_to_remove']) + len(results['requires_review']) + len(results['clean_files'])}"
        )
        report.append("")

        if results["safe_to_remove"]:
            report.append(f"🗑️  Files safe to remove ({len(results['safe_to_remove'])}):")
            for file_path in results["safe_to_remove"]:
                report.append(f"   - {file_path}")
            report.append("")

        if results["requires_review"]:
            report.append(f"⚠️  Files requiring manual review ({len(results['requires_review'])}):")
            for file_path in results["requires_review"]:
                report.append(f"   - {file_path}")
            report.append("")

        report.append(f"✅ Clean files: {len(results['clean_files'])}")

        return "\n".join(report)


def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(description="Secure cleanup utility for sensitive files")
    parser.add_argument("--scan", action="store_true", help="Scan for sensitive files (default)")
    parser.add_argument(
        "--cleanup", action="store_true", help="Actually delete safe files (not dry run)"
    )
    parser.add_argument("--path", default=".", help="Repository path to clean")

    args = parser.parse_args()

    cleanup = SecureCleanup(args.path)

    if args.cleanup:
        print("🚨 LIVE CLEANUP MODE - Files will be permanently deleted!")

        # Secure input validation for destructive operation
        while True:
            try:
                # nosec B601 # Safe confirmation for file deletion with strict validation
                confirm = input("Are you sure? Type 'yes' to continue: ")
                if confirm.lower() == "yes":
                    break
                elif confirm.lower() in ["no", "n", ""]:
                    print("❌ Cleanup cancelled.")
                    return
                else:
                    print("❌ You must type exactly 'yes' to proceed with deletion")
            except (EOFError, KeyboardInterrupt):
                print("\n❌ Cleanup cancelled by user")
                return

        results = cleanup.cleanup_safe_files(dry_run=False)
        print(f"\n✅ Cleanup complete! Deleted {len(results['deleted_files'])} files.")

    else:
        print("🔍 SCAN MODE - No files will be deleted")
        results = cleanup.cleanup_safe_files(dry_run=True)

        print("\n" + cleanup.generate_report())
        print("\n💡 To actually delete files, run with --cleanup flag")


if __name__ == "__main__":
    main()
