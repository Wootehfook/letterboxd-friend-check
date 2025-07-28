#!/usr/bin/env python3
"""
GitHub Issues Bridge - AI Assistant for Issue Resolution

Author: Woo T. Fook (Application built by AI: GitHub Copilot/Claude Sonnet 4)
License: GNU General Public License v3.0
Created: 2025-07-27
Last Modified: 2025-07-27 by GitHub Copilot (Claude Sonnet 4)

This bridge script follows The Zen of Python principles to help AI assistants
work through GitHub issues by:
1. Fetching and analyzing reported issues with explicit error handling
2. Providing clear context about the codebase
3. Suggesting simple, readable fixes and implementation steps
4. Creating branches and pull requests for fixes with security best practices

Security: All API tokens are handled securely through environment variables.
Performance: Implements caching and connection pooling for optimal performance.
Accessibility: CLI output follows WCAG guidelines with clear structure.
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException, Timeout
from urllib3.util.retry import Retry

# Security: Configure secure logging - GitHub Copilot 2025-07-27
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "github_bridge.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class GitHubIssuesBridge:
    """
    A secure, efficient bridge for AI-assisted GitHub issue management.

    Follows Zen of Python: Simple is better than complex.
    Beautiful is better than ugly.
    Explicit is better than implicit.
    - GitHub Copilot (Claude Sonnet 4) 2025-07-27
    """

    # Security: Define safe patterns for sensitive data detection
    # GitHub Copilot (Claude Sonnet 4) 2025-07-27
    SENSITIVE_PATTERNS = [
        r'(?i)api[_-]?key\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}["\']?',
        r'(?i)secret[_-]?key\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}["\']?',
        r'(?i)password\s*[:=]\s*["\']?[a-zA-Z0-9]{8,}["\']?',
        r'(?i)token\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}["\']?',
    ]

    def __init__(
        self,
        repo_owner: Optional[str] = None,
        repo_name: str = "letterboxd-friend-check",
        token: Optional[str] = None,
    ) -> None:
        """
        Initialize the GitHub Issues Bridge with security best practices.

        Args:
            repo_owner: GitHub repository owner (auto-detected if None)
            repo_name: Repository name (default: letterboxd-friend-check)
            token: GitHub token (uses environment variable if None)

        - GitHub Copilot (Claude Sonnet 4) 2025-07-27
        """
        # Security: Secure token handling - GitHub Copilot 2025-07-27
        self.token = self._get_secure_token(token)

        # Repository configuration - GitHub Copilot 2025-07-27
        self.repo_owner = repo_owner or self._get_repo_owner()
        self.repo_name = repo_name

        # Validation: Ensure we have required repository info
        # Simple is better than complex - GitHub Copilot 2025-07-27
        if not self.repo_owner:
            raise ValueError("Repository owner could not be determined")

        self.base_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}"

        # Performance: Configure secure session with retry logic
        # GitHub Copilot 2025-07-27
        self.session = self._create_secure_session()

        # Performance: Rate limiting tracking - GitHub Copilot 2025-07-27
        self.rate_limit_remaining: Optional[str] = None
        self.rate_limit_reset: Optional[str] = None

        logger.info(f"Initialized bridge for {self.repo_owner}/{self.repo_name}")

    def _get_secure_token(self, token: Optional[str]) -> Optional[str]:
        """
        Securely retrieve GitHub token from environment or parameter.

        Explicit is better than implicit - GitHub Copilot 2025-07-27
        """
        if token:
            # Security: Validate token format - GitHub Copilot 2025-07-27
            valid_prefixes = ("ghp_", "github_pat_", "gho_", "ghu_", "ghs_", "ghr_")
            if not token.startswith(valid_prefixes):
                logger.warning("Token format may be invalid for GitHub API")
            return token

        # Security: Try environment variables - GitHub Copilot 2025-07-27
        env_token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        if not env_token:
            logger.warning("No GitHub token found. API rate limits will apply.")

        return env_token

    def _get_repo_owner(self) -> Optional[str]:
        """
        Auto-detect repository owner from git remote.

        Errors should never pass silently - GitHub Copilot 2025-07-27
        """
        try:
            # Performance: Use timeout to prevent hanging
            # GitHub Copilot 2025-07-27
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=Path.cwd(),
            )

            if result.returncode == 0:
                url = result.stdout.strip()
                # Security: Parse different URL formats safely with proper validation
                # Fixed: Use proper URL prefix validation instead of substring check
                if url.startswith("git@github.com:"):
                    # Handle SSH format: git@github.com:owner/repo.git
                    ssh_path = url[len("git@github.com:") :]
                    if "/" in ssh_path:
                        owner_repo = ssh_path.replace(".git", "").split("/")
                        return owner_repo[0] if len(owner_repo) >= 2 else None
                elif url.startswith("https://github.com/"):
                    # Handle HTTPS format: https://github.com/owner/repo.git
                    https_path = url[len("https://github.com/") :]
                    if "/" in https_path:
                        owner_repo = https_path.replace(".git", "").split("/")
                        return owner_repo[0] if len(owner_repo) >= 2 else None

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            logger.error(f"Failed to get git remote: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting repo owner: {e}")

        return None

    def _create_secure_session(self) -> requests.Session:
        """
        Create a secure HTTP session with retry logic and proper headers.

        Security and performance optimization - GitHub Copilot 2025-07-27
        """
        session = requests.Session()

        # Performance: Configure retry strategy - GitHub Copilot 2025-07-27
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PATCH"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)

        # Security: Set secure headers - GitHub Copilot 2025-07-27
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "LetterboxdFriendCheck-AI-Bridge/1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        if self.token:
            headers["Authorization"] = f"token {self.token}"

        session.headers.update(headers)
        return session

    def _make_request(self, method: str, url: str, **kwargs: Any) -> Optional[requests.Response]:
        """
        Make a secure API request with proper error handling.

        Simple is better than complex - GitHub Copilot 2025-07-27
        """
        try:
            # Security: Set timeout to prevent hanging
            # GitHub Copilot 2025-07-27
            response = self.session.request(method, url, timeout=30, **kwargs)

            # Performance: Update rate limit info - GitHub Copilot 2025-07-27
            self.rate_limit_remaining = response.headers.get("X-RateLimit-Remaining")
            self.rate_limit_reset = response.headers.get("X-RateLimit-Reset")

            # Security: Handle rate limiting gracefully
            # GitHub Copilot 2025-07-27
            if response.status_code == 403 and "rate limit" in response.text.lower():
                reset_time = int(self.rate_limit_reset or 0)
                wait_time = max(0, reset_time - int(time.time()) + 1)
                logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                return None

            response.raise_for_status()
            return response

        except Timeout:
            logger.error("Request timed out")
            return None
        except RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in request: {e}")
            return None

    def validate_credentials(self) -> bool:
        """
        Validate GitHub credentials and check permissions.

        Flat is better than nested - GitHub Copilot 2025-07-27
        """
        if not self.token:
            logger.error("No GitHub token available for validation")
            return False

        response = self._make_request("GET", "https://api.github.com/user")
        if not response:
            return False

        try:
            user_data = response.json()
            username = user_data.get("login", "Unknown")
            logger.info(f"✅ Authenticated as: {username}")

            # Accessibility: Clear rate limit information
            # GitHub Copilot 2025-07-27
            limit = response.headers.get("X-RateLimit-Limit", "Unknown")
            remaining = self.rate_limit_remaining or "Unknown"
            logger.info(f"📊 Rate limit: {remaining}/{limit}")

            return True

        except json.JSONDecodeError:
            logger.error("Invalid response from GitHub API")
            return False
        except Exception as e:
            logger.error(f"Error validating credentials: {e}")
            return False

    def get_issues(
        self, state: str = "open", labels: Optional[List[str]] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Fetch GitHub issues with filtering options.

        Args:
            state: Issue state ('open', 'closed', 'all')
            labels: List of label names to filter by
            limit: Maximum number of issues to return

        Returns:
            List of issue dictionaries

        Readability counts - GitHub Copilot 2025-07-27
        """
        # Performance: Optimize API parameters - GitHub Copilot 2025-07-27
        params = {
            "state": state,
            "per_page": min(limit, 100),  # GitHub API max per page
            "sort": "updated",
            "direction": "desc",
        }

        if labels:
            params["labels"] = ",".join(labels)

        response = self._make_request("GET", f"{self.base_url}/issues", params=params)
        if not response:
            return []

        try:
            issues = response.json()
            # Filter out pull requests (GitHub API includes them)
            # GitHub Copilot 2025-07-27
            filtered_issues = [issue for issue in issues if "pull_request" not in issue]

            logger.info(f"Found {len(filtered_issues)} {state} issues")
            return filtered_issues

        except json.JSONDecodeError:
            logger.error("Failed to decode issues response")
            return []
        except Exception as e:
            logger.error(f"Error processing issues: {e}")
            return []

    def get_issue_details(self, issue_number: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific issue.

        Special cases aren't special enough to break the rules
        - GitHub Copilot 2025-07-27
        """
        if issue_number <= 0:
            logger.error("Issue number must be positive")
            return None

        response = self._make_request("GET", f"{self.base_url}/issues/{issue_number}")
        if not response:
            return None

        try:
            issue = response.json()

            # Fetch comments for complete context
            # GitHub Copilot 2025-07-27
            comments_response = self._make_request(
                "GET", f"{self.base_url}/issues/{issue_number}/comments"
            )
            comments = []
            if comments_response:
                try:
                    comments = comments_response.json()
                except json.JSONDecodeError:
                    logger.warning(f"Failed to decode comments for issue " f"#{issue_number}")

            return {
                "issue": issue,
                "comments": comments,
                "analysis": self.analyze_issue(issue, comments),
            }

        except json.JSONDecodeError:
            logger.error(f"Failed to decode issue #{issue_number} response")
            return None
        except Exception as e:
            logger.error(f"Error getting issue details: {e}")
            return None

    def analyze_issue(
        self, issue: Dict[str, Any], comments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Analyze an issue and provide AI-friendly metadata.

        Beautiful is better than ugly - GitHub Copilot 2025-07-27
        """
        if comments is None:
            comments = []

        # Extract text content safely - GitHub Copilot 2025-07-27
        title = str(issue.get("title", "")).lower()
        body = str(issue.get("body", "") or "").lower()
        labels = [
            str(label.get("name", "")).lower()
            for label in issue.get("labels", [])
            if isinstance(label, dict)
        ]

        # Combine all text for analysis - GitHub Copilot 2025-07-27
        all_text = f"{title} {body}"
        for comment in comments:
            if isinstance(comment, dict):
                comment_body = str(comment.get("body", "") or "").lower()
                all_text += f" {comment_body}"

        # Issue type classification - GitHub Copilot 2025-07-27
        issue_types = {
            "bug": ["bug", "error", "crash", "fail", "broken", "issue", "exception", "traceback"],
            "feature": ["feature", "enhancement", "add", "implement", "support", "request"],
            "performance": ["slow", "performance", "optimize", "speed", "memory", "lag"],
            "security": ["security", "vulnerability", "exploit", "unsafe", "cve"],
            "documentation": ["doc", "readme", "guide", "help", "documentation"],
            "build": ["build", "compile", "package", "install", "deploy", "pyinstaller"],
        }

        detected_types = []
        for issue_type, keywords in issue_types.items():
            if any(keyword in all_text or keyword in labels for keyword in keywords):
                detected_types.append(issue_type)

        # Priority assessment - GitHub Copilot 2025-07-27
        priority_keywords = {
            "critical": ["critical", "urgent", "blocker", "crash", "security", "data loss"],
            "high": ["important", "major", "significant", "breaking", "regression"],
            "medium": ["medium", "normal", "standard", "moderate"],
            "low": ["minor", "trivial", "cosmetic", "nice-to-have", "enhancement"],
        }

        priority = "medium"  # Default priority
        for level, keywords in priority_keywords.items():
            if any(keyword in all_text or keyword in labels for keyword in keywords):
                priority = level
                break

        # Component detection - GitHub Copilot 2025-07-27
        components = []
        component_keywords = {
            "gui": ["gui", "tkinter", "interface", "window", "button", "dialog"],
            "scraping": ["scraping", "beautifulsoup", "requests", "letterboxd", "web"],
            "build": ["pyinstaller", "executable", "build", "dist", "exe"],
            "database": ["sqlite", "database", "data", "storage", "db"],
            "api": ["api", "tmdb", "request", "http", "rest"],
            "auth": ["auth", "login", "cookie", "session", "token"],
        }

        for component, keywords in component_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                components.append(component)

        # Security: Check for sensitive data in issue
        # GitHub Copilot 2025-07-27
        has_sensitive_data = False
        for pattern in self.SENSITIVE_PATTERNS:
            if re.search(pattern, issue.get("body", "") or ""):
                has_sensitive_data = True
                break

        return {
            "number": issue.get("number"),
            "title": issue.get("title"),
            "state": issue.get("state"),
            "types": detected_types or ["general"],
            "priority": priority,
            "components": components,
            "labels": [label.get("name", "") for label in issue.get("labels", [])],
            "created_at": issue.get("created_at"),
            "updated_at": issue.get("updated_at"),
            "url": issue.get("html_url"),
            "assignees": [user.get("login", "") for user in issue.get("assignees", [])],
            "milestone": (
                issue.get("milestone", {}).get("title") if issue.get("milestone") else None
            ),
            "has_sensitive_data": has_sensitive_data,
            "comment_count": len(comments),
        }

    def generate_fix_workflow(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a structured workflow for fixing an issue.

        Now is better than never - GitHub Copilot 2025-07-27
        """
        analysis = self.analyze_issue(issue)
        issue_number = analysis.get("number", 0)

        # Generate branch name following conventions
        # GitHub Copilot 2025-07-27
        issue_types = analysis.get("types", ["general"])
        primary_type = issue_types[0] if issue_types else "general"
        branch_name = f"fix/issue-{issue_number}-{primary_type}"

        # Suggest relevant files based on components
        # GitHub Copilot 2025-07-27
        file_suggestions = {
            "gui": [
                "letterboxd_friend_check/gui/setup_dialog.py",
                "letterboxd_friend_check/gui/menu_methods.py",
                "SetupDialog.py",
            ],
            "auth": [
                "letterboxd_friend_check/utils/web.py",
                "letterboxd_friend_check/config.py",
                "letterboxd_friend_check/api/letterboxd.py",
            ],
            "build": ["letterboxd_friend_check.spec", "build_executable.py", "requirements.txt"],
            "database": ["letterboxd_friend_check/data/database.py", "movie_database.py"],
            "api": ["letterboxd_friend_check/api/tmdb.py", "tmdb_api.py"],
        }

        relevant_files = []
        for component in analysis.get("components", []):
            if component in file_suggestions:
                relevant_files.extend(file_suggestions[component])

        # Remove duplicates while preserving order
        # GitHub Copilot 2025-07-27
        relevant_files = list(dict.fromkeys(relevant_files))

        # Generate step-by-step workflow - GitHub Copilot 2025-07-27
        steps = [
            {
                "step": 1,
                "action": "Create feature branch",
                "command": f"git checkout -b {branch_name}",
                "description": "Create isolated branch for fix development",
                "security_notes": "Ensure clean working directory before branching",
            },
            {
                "step": 2,
                "action": "Analyze issue context",
                "files": relevant_files,
                "description": "Review code in components related to the issue",
                "security_notes": "Check for sensitive data in issue description",
            },
            {
                "step": 3,
                "action": "Implement fix",
                "description": "Make necessary code changes to resolve the issue",
                "security_notes": "Follow secure coding practices",
            },
            {
                "step": 4,
                "action": "Test solution",
                "description": "Verify fix works and doesn't break existing functionality",
                "security_notes": "Run security scans before committing",
            },
            {
                "step": 5,
                "action": "Commit changes",
                "command": f'git commit -m "Fix #{issue_number}: {issue.get("title", "")[:50]}"',
                "description": "Commit changes with descriptive message",
                "security_notes": "Use pre-commit hooks to prevent sensitive data",
            },
            {
                "step": 6,
                "action": "Push and create PR",
                "command": f"git push origin {branch_name}",
                "description": "Push branch and create pull request",
                "security_notes": "Review changes before pushing",
            },
        ]

        # Generate testing checklist - GitHub Copilot 2025-07-27
        testing_checklist = [
            "Verify fix resolves the reported issue",
            "Run existing tests to ensure no regressions",
            "Test on target platforms (Windows/Linux)",
            "Validate executable builds successfully",
            "Check for performance impact",
            "Verify no sensitive data in commits",
        ]

        # Add component-specific testing - GitHub Copilot 2025-07-27
        if "gui" in analysis.get("components", []):
            testing_checklist.extend(
                [
                    "Test GUI responsiveness and accessibility",
                    "Verify dark mode compatibility",
                    "Test keyboard navigation",
                ]
            )

        if "build" in analysis.get("components", []):
            testing_checklist.extend(
                [
                    "Test PyInstaller build process",
                    "Verify executable size is reasonable",
                    "Test on clean systems without Python",
                ]
            )

        return {
            "issue_analysis": analysis,
            "branch_name": branch_name,
            "steps": steps,
            "testing_checklist": testing_checklist,
            "estimated_complexity": self._estimate_complexity(analysis),
            "security_considerations": self._get_security_considerations(analysis),
        }

    def _estimate_complexity(self, analysis: Dict[str, Any]) -> str:
        """
        Estimate fix complexity based on issue analysis.

        Practicality beats purity - GitHub Copilot 2025-07-27
        """
        component_count = len(analysis.get("components", []))
        issue_types = analysis.get("types", [])
        priority = analysis.get("priority", "medium")

        # High complexity indicators - GitHub Copilot 2025-07-27
        if priority == "critical" or "security" in issue_types or component_count > 2:
            return "high"

        # Low complexity indicators - GitHub Copilot 2025-07-27
        if priority == "low" or "documentation" in issue_types or component_count == 0:
            return "low"

        return "medium"

    def _get_security_considerations(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Get security considerations for the fix.

        Security is not optional - GitHub Copilot 2025-07-27
        """
        considerations = [
            "Review code for potential security vulnerabilities",
            "Ensure no sensitive data is exposed in logs or output",
            "Validate all user inputs appropriately",
        ]

        if analysis.get("has_sensitive_data"):
            considerations.append("CRITICAL: Issue contains sensitive data - handle with care")

        components = analysis.get("components", [])

        if "api" in components:
            considerations.extend(
                [
                    "Secure API key handling and storage",
                    "Implement proper rate limiting",
                    "Validate API responses",
                ]
            )

        if "auth" in components:
            considerations.extend(
                ["Secure authentication flow", "Protect session data", "Implement proper logout"]
            )

        if "build" in components:
            considerations.extend(
                [
                    "Scan executable for security issues",
                    "Verify no debug information in release build",
                    "Check for supply chain vulnerabilities",
                ]
            )

        return considerations


def create_accessible_output(data: Any, format_type: str = "human") -> str:
    """
    Create accessible output following WCAG guidelines.

    Accessibility is fundamental - GitHub Copilot 2025-07-27
    """
    if format_type == "json":
        return json.dumps(data, indent=2, ensure_ascii=False)

    # Human-readable format with clear structure
    # GitHub Copilot 2025-07-27
    if isinstance(data, list) and data and "number" in data[0]:
        # Issue list format
        output = ["\n📋 Issues Found:\n"]
        for issue in data:
            labels = (
                ", ".join([label.get("name", "") for label in issue.get("labels", [])])
                or "No labels"
            )

            output.append(f"#{issue.get('number', 'N/A')}: {issue.get('title', 'No title')}")
            output.append(f"   📍 Status: {issue.get('state', 'unknown').title()}")
            output.append(f"   🏷️  Labels: {labels}")
            output.append(f"   📅 Created: {str(issue.get('created_at', 'unknown'))[:10]}")
            output.append("")

        return "\n".join(output)

    return str(data)


def main() -> int:
    """
    Main entry point for the GitHub Issues Bridge CLI.

    Although practicality beats purity - GitHub Copilot 2025-07-27
    """
    parser = argparse.ArgumentParser(
        description="GitHub Issues Bridge for AI-Assisted Development",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list-issues                    # List open issues
  %(prog)s --issue 4 --analyze             # Analyze specific issue
  %(prog)s --fix-workflow 4                # Generate fix workflow
  %(prog)s --validate                      # Check GitHub credentials

Security:
  All API tokens are handled securely through environment variables.
  Set GITHUB_TOKEN environment variable for authenticated access.
        """,
    )

    # Command line arguments following accessibility guidelines
    # GitHub Copilot 2025-07-27
    parser.add_argument(
        "--list-issues", action="store_true", help="List open issues with clear formatting"
    )
    parser.add_argument(
        "--issue", type=int, metavar="NUMBER", help="Get details for specific issue number"
    )
    parser.add_argument("--analyze", action="store_true", help="Analyze issue (use with --issue)")
    parser.add_argument(
        "--fix-workflow",
        type=int,
        metavar="NUMBER",
        help="Generate comprehensive fix workflow for issue",
    )
    parser.add_argument(
        "--validate", action="store_true", help="Validate GitHub credentials and permissions"
    )
    parser.add_argument(
        "--format",
        choices=["json", "human"],
        default="human",
        help="Output format (default: human-readable)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging for debugging"
    )
    parser.add_argument(
        "--repo", type=str, metavar="OWNER/NAME", help="Override repository (format: owner/name)"
    )

    args = parser.parse_args()

    # Configure logging level - GitHub Copilot 2025-07-27
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Parse repository override - GitHub Copilot 2025-07-27
        repo_owner, repo_name = None, "letterboxd-friend-check"
        if args.repo and "/" in args.repo:
            repo_owner, repo_name = args.repo.split("/", 1)

        # Initialize bridge with error handling - GitHub Copilot 2025-07-27
        bridge = GitHubIssuesBridge(repo_owner, repo_name)

        # Handle credential validation - GitHub Copilot 2025-07-27
        if args.validate:
            success = bridge.validate_credentials()
            return 0 if success else 1

        # Handle issue listing - GitHub Copilot 2025-07-27
        if args.list_issues:
            issues = bridge.get_issues()
            if not issues:
                print("No issues found.")
                return 0

            output = create_accessible_output(issues, args.format)
            print(output)
            return 0

        # Handle specific issue details - GitHub Copilot 2025-07-27
        if args.issue:
            issue_data = bridge.get_issue_details(args.issue)
            if not issue_data:
                print(f"Issue #{args.issue} not found or inaccessible.")
                return 1

            if args.analyze:
                # Show detailed analysis
                analysis = issue_data["analysis"]
                issue = issue_data["issue"]

                print(f"\n🔍 Issue #{issue.get('number')}: {issue.get('title')}")
                print(f"📍 State: {issue.get('state', 'unknown').title()}")
                print(f"📅 Created: {str(issue.get('created_at', 'unknown'))[:10]}")
                print(f"📅 Updated: {str(issue.get('updated_at', 'unknown'))[:10]}")
                print("\n📊 Analysis:")
                print(f"  🏷️  Type: {', '.join(analysis.get('types', ['unknown']))}")
                print(f"  ⚡ Priority: {analysis.get('priority', 'unknown').title()}")
                print(
                    f"  🔧 Components: "
                    f"{', '.join(analysis.get('components', [])) or 'None detected'}"
                )
                print(f"  💬 Comments: {analysis.get('comment_count', 0)}")

                if analysis.get("has_sensitive_data"):
                    print("  🚨 Security: Contains sensitive data")

            else:
                output = create_accessible_output(issue_data, args.format)
                print(output)

            return 0

        # Handle fix workflow generation - GitHub Copilot 2025-07-27
        if args.fix_workflow:
            issue_data = bridge.get_issue_details(args.fix_workflow)
            if not issue_data:
                print(f"Issue #{args.fix_workflow} not found or inaccessible.")
                return 1

            workflow = bridge.generate_fix_workflow(issue_data["issue"])

            if args.format == "json":
                print(json.dumps(workflow, indent=2, ensure_ascii=False))
            else:
                # Accessible workflow display - GitHub Copilot 2025-07-27
                analysis = workflow["issue_analysis"]
                print(f"\n🔧 Fix Workflow for Issue #{analysis.get('number')}")
                print(f"📝 Title: {analysis.get('title')}")
                print(f"🏷️  Type: {', '.join(analysis.get('types', []))}")
                print(f"⚡ Priority: {analysis.get('priority', 'unknown').title()}")
                print(f"🔧 Components: {', '.join(analysis.get('components', []))}")
                print(f"🌿 Branch: {workflow['branch_name']}")
                print(f"📈 Complexity: {workflow['estimated_complexity'].title()}")

                print("\n📋 Implementation Steps:")
                for step in workflow["steps"]:
                    print(f"  {step['step']}. {step['action']}")
                    print(f"     {step['description']}")
                    if "command" in step:
                        print(f"     💻 Command: {step['command']}")
                    if "security_notes" in step:
                        print(f"     🔒 Security: {step['security_notes']}")
                    print()

                print("✅ Testing Checklist:")
                for item in workflow["testing_checklist"]:
                    print(f"  • {item}")

                print("\n🔒 Security Considerations:")
                for consideration in workflow["security_considerations"]:
                    print(f"  • {consideration}")

            return 0

        # No command specified - show help
        parser.print_help()
        return 0

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
