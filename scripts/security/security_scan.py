#!/usr/bin/env python3
"""
Comprehensive Security Scanner for Letterboxd Friend Check
Scans for secrets, API keys, and sensitive data across the repository.
"""

import os
import re
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import time
import atexit


class SecurityScanner:
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.findings = []
        self.report_file = None
        self.temp_files = []

        # Register cleanup function to run on exit
        atexit.register(self.cleanup_on_exit)

        # Enhanced patterns for detecting secrets
        self.secret_patterns = [
            # API Keys and Tokens
            (r'["\']?api[_-]?key["\']?\s*[:=]\s*["\']([a-zA-Z0-9]{20,})["\']', "API Key"),
            (r'["\']?token["\']?\s*[:=]\s*["\']([a-zA-Z0-9]{20,})["\']', "Token"),
            (r'["\']?secret["\']?\s*[:=]\s*["\']([a-zA-Z0-9]{20,})["\']', "Secret"),
            (r'["\']?password["\']?\s*[:=]\s*["\']([^"\']{8,})["\']', "Password"),
            # TMDB API Key (32 chars)
            (r"[a-f0-9]{32}", "TMDB API Key (32-char hex)"),
            # Email addresses
            (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "Email Address"),
            # Personal usernames in config
            (r'"username"\s*:\s*"([^"]{3,})"', "Username in Config"),
            # Database connection strings
            (r'(mongodb|mysql|postgres|redis)://[^\s"\']+', "Database Connection"),
            # Private keys
            (r"-----BEGIN [A-Z ]+PRIVATE KEY-----", "Private Key"),
            # GitHub tokens
            (r"gh[ps]_[a-zA-Z0-9]{36}", "GitHub Token"),
            # AWS keys
            (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
        ]

    def scan_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Scan a single file for secrets."""
        findings = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            for line_num, line in enumerate(content.split("\n"), 1):
                for pattern, secret_type in self.secret_patterns:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        # Skip certain safe patterns
                        if self._is_safe_match(match.group(0), str(file_path)):
                            continue

                        findings.append(
                            {
                                "file": str(file_path.relative_to(self.repo_path)),
                                "line": line_num,
                                "type": secret_type,
                                "match": (
                                    match.group(0)[:50] + "..."
                                    if len(match.group(0)) > 50
                                    else match.group(0)
                                ),
                                "severity": self._get_severity(secret_type),
                                "context": line.strip()[:100],
                            }
                        )
        except Exception as e:
            print(f"Error scanning {file_path}: {e}")

        return findings

    def _is_safe_match(self, match: str, file_path: str) -> bool:
        """Check if a match is a false positive."""
        safe_patterns = [
            # Empty values
            r'^["\']?\s*["\']?$',
            # Template placeholders
            r"your[_-]?key[_-]?here",
            r"enter[_-]?your",
            r"paste[_-]?your",
            r"example",
            r"placeholder",
            r"template",
            # Common non-secrets
            r'^["\']?test["\']?$',
            r'^["\']?debug["\']?$',
            r'^["\']?localhost["\']?$',
            # Documentation
            r"README|INSTALL|LICENSE",
        ]

        # Check if in documentation or template files
        doc_files = ["readme", "install", "license", "template", "example"]
        if any(doc in file_path.lower() for doc in doc_files):
            return True

        # Check against safe patterns
        for safe_pattern in safe_patterns:
            if re.search(safe_pattern, match, re.IGNORECASE):
                return True

        return False

    def _get_severity(self, secret_type: str) -> str:
        """Determine the severity of a finding."""
        high_severity = [
            "API Key",
            "Token",
            "Secret",
            "Password",
            "Private Key",
            "Database Connection",
        ]
        medium_severity = ["Email Address", "GitHub Token", "AWS Access Key"]

        if secret_type in high_severity:
            return "HIGH"
        elif secret_type in medium_severity:
            return "MEDIUM"
        else:
            return "LOW"

    def scan_repository(self) -> Dict[str, Any]:
        """Scan the entire repository."""
        print("🔍 Starting comprehensive security scan...")

        # Files to scan
        scan_extensions = {".py", ".json", ".md", ".txt", ".yml", ".yaml", ".env", ".cfg", ".ini"}
        exclude_dirs = {".git", ".venv", "__pycache__", "node_modules", "build", "dist"}

        scanned_files = 0
        total_findings = []

        for file_path in self.repo_path.rglob("*"):
            # Skip directories and excluded paths
            if file_path.is_dir():
                continue
            if any(excluded in file_path.parts for excluded in exclude_dirs):
                continue
            if file_path.suffix not in scan_extensions:
                continue
            # Skip security scanner output files to prevent recursive scanning
            if file_path.name in [
                "security_report.txt",
                "trufflehog-git-results.json",
                "trufflehog-fs-results.json",
                "safety-report.json",
                "bandit-report.json",
            ]:
                continue

            findings = self.scan_file(file_path)
            total_findings.extend(findings)
            scanned_files += 1

            if findings:
                relative_path = file_path.relative_to(self.repo_path)
                print(f"   ⚠️  Found {len(findings)} potential issues in {relative_path}")

        return {
            "scanned_files": scanned_files,
            "total_findings": len(total_findings),
            "findings": total_findings,
            "summary": self._generate_summary(total_findings),
        }

    def _generate_summary(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of findings."""
        severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        type_counts = {}

        for finding in findings:
            severity_counts[finding["severity"]] += 1
            finding_type = finding["type"]
            type_counts[finding_type] = type_counts.get(finding_type, 0) + 1

        return {
            "by_severity": severity_counts,
            "by_type": type_counts,
            "risk_level": (
                "HIGH"
                if severity_counts["HIGH"] > 0
                else "MEDIUM" if severity_counts["MEDIUM"] > 0 else "LOW"
            ),
        }

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a detailed security report."""
        report = []
        report.append("🛡️  SECURITY SCAN REPORT")
        report.append("=" * 50)
        report.append(f"📊 Scanned {results['scanned_files']} files")
        report.append(f"🔍 Found {results['total_findings']} potential issues")
        report.append(f"⚠️  Risk Level: {results['summary']['risk_level']}")
        report.append("")

        # Summary by severity
        report.append("📈 Findings by Severity:")
        for severity, count in results["summary"]["by_severity"].items():
            if count > 0:
                icon = "🚨" if severity == "HIGH" else "⚠️" if severity == "MEDIUM" else "ℹ️"
                report.append(f"   {icon} {severity}: {count}")
        report.append("")

        # Summary by type
        if results["summary"]["by_type"]:
            report.append("📋 Findings by Type:")
            for finding_type, count in results["summary"]["by_type"].items():
                report.append(f"   • {finding_type}: {count}")
            report.append("")

        # Detailed findings
        if results["findings"]:
            report.append("🔍 Detailed Findings:")
            report.append("-" * 30)

            # Group by severity
            for severity in ["HIGH", "MEDIUM", "LOW"]:
                severity_findings = [f for f in results["findings"] if f["severity"] == severity]
                if severity_findings:
                    icon = "🚨" if severity == "HIGH" else "⚠️" if severity == "MEDIUM" else "ℹ️"
                    report.append(f"\n{icon} {severity} SEVERITY:")

                    for finding in severity_findings:
                        report.append(f"   📁 File: {finding['file']}")
                        report.append(f"   📍 Line: {finding['line']}")
                        report.append(f"   🏷️  Type: {finding['type']}")
                        report.append(f"   🔍 Match: {finding['match']}")
                        report.append(f"   📝 Context: {finding['context']}")
                        report.append("")
        else:
            report.append("✅ No security issues found!")

        return "\n".join(report)

    def cleanup_on_exit(self):
        """Clean up temporary files and security reports on exit."""
        try:
            # Clean up any security reports that may contain sensitive data
            report_patterns = ["security_report*.txt", "trufflehog-*.json", "*-security-report.*"]

            for pattern in report_patterns:
                for file_path in self.repo_path.glob(pattern):
                    try:
                        file_path.unlink()
                        print(f"🧹 Cleaned up security report: {file_path.name}")
                    except Exception:
                        pass  # Ignore cleanup errors

            # Clean up temp files tracked by this instance
            for temp_file in self.temp_files:
                try:
                    if temp_file.exists():
                        temp_file.unlink()
                except Exception:
                    pass

        except Exception:
            pass  # Silent cleanup - don't interfere with main execution

    def generate_timestamped_report_name(self) -> str:
        """Generate a timestamped report filename."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"security_report_{timestamp}.txt"

    def save_report_with_auto_cleanup(self, report_content: str, cleanup_delay: int = 30) -> str:
        """Save report and schedule automatic cleanup."""
        report_name = self.generate_timestamped_report_name()
        report_path = self.repo_path / report_name

        # Save the report
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        # Track for cleanup
        self.temp_files.append(report_path)
        self.report_file = report_path

        # Schedule cleanup in a separate thread
        import threading

        def delayed_cleanup():
            time.sleep(cleanup_delay)
            try:
                if report_path.exists():
                    report_path.unlink()
                    print(f"\n🧹 Auto-cleaned security report after {cleanup_delay}s")
            except Exception:
                pass

        cleanup_thread = threading.Thread(target=delayed_cleanup, daemon=True)
        cleanup_thread.start()

        return str(report_path)


def main():
    """Run the security scan."""
    scanner = SecurityScanner()
    results = scanner.scan_repository()
    report = scanner.generate_report(results)

    print("\n" + report)

    # Save report with auto-cleanup (will be deleted in 30 seconds)
    report_path = scanner.save_report_with_auto_cleanup(report, cleanup_delay=30)
    print(f"\n📄 Temporary report saved to: {Path(report_path).name}")
    print("⏰ Report will auto-delete in 30 seconds to prevent accidental commits")

    # Return exit code based on findings
    if results["summary"]["risk_level"] == "HIGH":
        print("\n🚨 HIGH RISK findings detected!")
        return 1
    elif results["summary"]["risk_level"] == "MEDIUM":
        print("\n⚠️  MEDIUM RISK findings detected.")
        return 0
    else:
        print("\n✅ Repository appears secure!")
        return 0


if __name__ == "__main__":
    exit(main())
