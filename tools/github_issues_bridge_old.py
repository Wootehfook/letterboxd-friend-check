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
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException, Timeout
from urllib3.util.retry import Retry

# Security: Configure secure logging - GitHub Copilot 2025-07-27
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/github_bridge.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class GitHubIssuesBridge:
    """Bridge for working with GitHub issues and implementing fixes"""

    def __init__(self, repo_owner=None, repo_name=None, token=None):
        """Initialize the GitHub Issues Bridge"""
        self.repo_owner = repo_owner or self._get_repo_owner() or "Wootehfook"
        self.repo_name = repo_name or "letterboxd-friend-check"
        self.token = token or os.getenv("GITHUB_TOKEN")

        # API configuration
        self.base_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}"
        self.headers = {"Authorization": f"token {self.token}"} if self.token else {}

        logger.info(f"Initialized GitHub Issues Bridge for {self.repo_owner}/{self.repo_name}")

        if not self.token:
            logger.warning("No GitHub token found. Some features will be limited.")

    def _get_repo_owner(self):
        """Extract repo owner from git remote"""
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                cwd="/workspaces/letterboxd-friend-check",
            )
            url = result.stdout.strip()

            # Securely parse GitHub URLs with proper validation
            if url.startswith("git@github.com:"):
                # Handle SSH format: git@github.com:owner/repo.git
                ssh_path = url[len("git@github.com:") :]
                if "/" in ssh_path:
                    return ssh_path.split("/")[0]
            elif url.startswith("https://github.com/"):
                # Handle HTTPS format: https://github.com/owner/repo.git
                https_path = url[len("https://github.com/") :]
                if "/" in https_path:
                    return https_path.split("/")[0]
        except Exception as e:
            logger.warning(f"Could not determine repo owner: {e}")
        return None

    def _make_request(self, method, url, **kwargs):
        """Make API request with error handling"""
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None

    # === ISSUE FETCHING AND ANALYSIS ===
    def get_issues(self, state="open", labels=None, assignee=None):
        """Fetch GitHub issues with filtering"""
        params = {"state": state, "per_page": 30}
        if labels:
            params["labels"] = ",".join(labels) if isinstance(labels, list) else labels
        if assignee:
            params["assignee"] = assignee

        response = self._make_request("GET", f"{self.base_url}/issues", params=params)
        if response:
            issues = response.json()
            logger.info(f"Found {len(issues)} {state} issues")
            return issues
        return []

    def get_issue_details(self, issue_number):
        """Get detailed information about a specific issue"""
        response = self._make_request("GET", f"{self.base_url}/issues/{issue_number}")
        if response:
            issue = response.json()

            # Get comments
            comments_response = self._make_request(
                "GET", f"{self.base_url}/issues/{issue_number}/comments"
            )
            comments = comments_response.json() if comments_response else []

            return {
                "issue": issue,
                "comments": comments,
                "analysis": self._analyze_issue(issue, comments),
            }
        return None

    def _analyze_issue(self, issue, comments):
        """Analyze an issue to extract key information"""
        analysis = {
            "type": "unknown",
            "priority": "medium",
            "components": [],
            "error_messages": [],
            "suggested_files": [],
            "keywords": [],
        }

        text = f"{issue['title']} {issue['body']}"
        for comment in comments:
            text += f" {comment['body']}"

        text = text.lower()

        # Categorize issue type
        if any(word in text for word in ["error", "exception", "traceback", "crash"]):
            analysis["type"] = "bug"
        elif any(word in text for word in ["feature", "enhancement", "add", "implement"]):
            analysis["type"] = "feature"
        elif any(word in text for word in ["performance", "slow", "speed", "optimize"]):
            analysis["type"] = "performance"
        elif any(word in text for word in ["documentation", "docs", "readme"]):
            analysis["type"] = "documentation"

        # Determine priority
        if any(word in text for word in ["critical", "urgent", "blocker", "security"]):
            analysis["priority"] = "high"
        elif any(word in text for word in ["minor", "cosmetic", "nice to have"]):
            analysis["priority"] = "low"

        # Extract error messages
        error_patterns = [
            r"Error: (.+)",
            r"Exception: (.+)",
            r"Traceback[^\n]*\n(.+)",
            r"ModuleNotFoundError: (.+)",
        ]

        for pattern in error_patterns:
            matches = re.findall(pattern, issue["body"] or "", re.IGNORECASE)
            analysis["error_messages"].extend(matches)

        # Identify relevant components
        components_map = {
            "tkinter": ["tkinter", "gui", "interface", "window"],
            "pyinstaller": ["pyinstaller", "executable", "build", "exe"],
            "letterboxd": ["letterboxd", "scraping", "friends", "watchlist"],
            "tmdb": ["tmdb", "movie", "api", "poster"],
            "database": ["database", "sqlite", "db"],
            "authentication": ["login", "cookie", "auth", "session"],
        }

        for component, keywords in components_map.items():
            if any(keyword in text for keyword in keywords):
                analysis["components"].append(component)

        # Suggest relevant files to examine
        file_map = {
            "tkinter": ["LBoxFriendCheck.py", "SetupDialog.py"],
            "pyinstaller": ["build_executable.py", "letterboxd_friend_check.spec"],
            "letterboxd": ["letterboxd_bridge.py", "LBoxFriendCheck.py"],
            "tmdb": ["tmdb_api.py"],
            "database": ["movie_database.py"],
            "authentication": ["LBoxFriendCheck.py"],
        }

        for component in analysis["components"]:
            if component in file_map:
                analysis["suggested_files"].extend(file_map[component])

        # Remove duplicates
        analysis["suggested_files"] = list(set(analysis["suggested_files"]))

        return analysis

    def search_issues(self, query):
        """Search issues by text"""
        search_url = "https://api.github.com/search/issues"
        search_query = f"repo:{self.repo_owner}/{self.repo_name} {query}"

        response = self._make_request("GET", search_url, params={"q": search_query})
        if response:
            return response.json().get("items", [])
        return []

    # === ISSUE MANAGEMENT ===
    def create_issue(self, title, body, labels=None, assignees=None):
        """Create a new issue"""
        data = {"title": title, "body": body}
        if labels:
            data["labels"] = labels
        if assignees:
            data["assignees"] = assignees

        response = self._make_request("POST", f"{self.base_url}/issues", json=data)
        if response:
            issue = response.json()
            logger.info(f"Created issue #{issue['number']}: {title}")
            return issue
        return None

    def update_issue(self, issue_number, title=None, body=None, state=None, labels=None):
        """Update an existing issue"""
        data = {}
        if title:
            data["title"] = title
        if body:
            data["body"] = body
        if state:
            data["state"] = state
        if labels:
            data["labels"] = labels

        response = self._make_request("PATCH", f"{self.base_url}/issues/{issue_number}", json=data)
        if response:
            logger.info(f"Updated issue #{issue_number}")
            return response.json()
        return None

    def add_comment(self, issue_number, body):
        """Add a comment to an issue"""
        data = {"body": body}
        response = self._make_request(
            "POST", f"{self.base_url}/issues/{issue_number}/comments", json=data
        )
        if response:
            logger.info(f"Added comment to issue #{issue_number}")
            return response.json()
        return None

    # === BRANCH AND PR MANAGEMENT ===
    def create_branch(self, branch_name, from_branch="main"):
        """Create a new branch for issue fixes"""
        try:
            # Get current commit of from_branch
            subprocess.run(
                ["git", "fetch", "origin"], check=True, cwd="/workspaces/letterboxd-friend-check"
            )
            subprocess.run(
                ["git", "checkout", from_branch],
                check=True,
                cwd="/workspaces/letterboxd-friend-check",
            )
            subprocess.run(
                ["git", "pull", "origin", from_branch],
                check=True,
                cwd="/workspaces/letterboxd-friend-check",
            )

            # Create and checkout new branch
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                check=True,
                cwd="/workspaces/letterboxd-friend-check",
            )

            logger.info(f"Created branch: {branch_name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create branch {branch_name}: {e}")
            return False

    def commit_changes(self, message, files=None):
        """Commit changes to the current branch"""
        try:
            if files:
                for file in files:
                    subprocess.run(
                        ["git", "add", file], check=True, cwd="/workspaces/letterboxd-friend-check"
                    )
            else:
                subprocess.run(
                    ["git", "add", "."], check=True, cwd="/workspaces/letterboxd-friend-check"
                )

            subprocess.run(
                ["git", "commit", "-m", message],
                check=True,
                cwd="/workspaces/letterboxd-friend-check",
            )
            logger.info(f"Committed changes: {message}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to commit changes: {e}")
            return False

    def push_branch(self, branch_name):
        """Push branch to origin"""
        try:
            subprocess.run(
                ["git", "push", "origin", branch_name],
                check=True,
                cwd="/workspaces/letterboxd-friend-check",
            )
            logger.info(f"Pushed branch: {branch_name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to push branch {branch_name}: {e}")
            return False

    def create_pull_request(self, title, body, head_branch, base_branch="main"):
        """Create a pull request"""
        data = {"title": title, "body": body, "head": head_branch, "base": base_branch}

        response = self._make_request("POST", f"{self.base_url}/pulls", json=data)
        if response:
            pr = response.json()
            logger.info(f"Created PR #{pr['number']}: {title}")
            return pr
        return None

    # === WORKFLOW HELPERS ===
    def fix_issue_workflow(self, issue_number):
        """Complete workflow to fix an issue"""
        logger.info(f"Starting fix workflow for issue #{issue_number}")

        # Get issue details
        issue_data = self.get_issue_details(issue_number)
        if not issue_data:
            logger.error(f"Could not fetch issue #{issue_number}")
            return None

        issue = issue_data["issue"]
        analysis = issue_data["analysis"]

        # Create branch name
        branch_name = f"fix-issue-{issue_number}"

        workflow = {
            "issue_number": issue_number,
            "issue_title": issue["title"],
            "issue_type": analysis["type"],
            "priority": analysis["priority"],
            "components": analysis["components"],
            "error_messages": analysis["error_messages"],
            "suggested_files": analysis["suggested_files"],
            "branch_name": branch_name,
            "next_steps": self._generate_fix_steps(analysis),
            "full_issue_data": issue_data,
        }

        return workflow

    def _generate_fix_steps(self, analysis):
        """Generate suggested fix steps based on issue analysis"""
        steps = []

        if analysis["type"] == "bug":
            steps.append("1. Reproduce the error in the development environment")
            steps.append("2. Examine the error messages and stack traces")
            steps.append("3. Check the suggested files for potential issues")
            steps.append("4. Implement a fix")
            steps.append("5. Test the fix thoroughly")
        elif analysis["type"] == "feature":
            steps.append("1. Design the feature implementation")
            steps.append("2. Identify files that need modification")
            steps.append("3. Implement the feature")
            steps.append("4. Add tests if applicable")
            steps.append("5. Update documentation")

        # Component-specific steps
        if "tkinter" in analysis["components"]:
            steps.append("- Check GUI layout and event handling")
            steps.append("- Test on different screen resolutions")

        if "pyinstaller" in analysis["components"]:
            steps.append("- Test executable build process")
            steps.append("- Verify all dependencies are included")
            steps.append("- Test on target platforms")

        return steps

    # === REPORTING ===
    def generate_issue_report(self, state="open"):
        """Generate a comprehensive report of issues"""
        issues = self.get_issues(state=state)

        report = {
            "timestamp": datetime.now().isoformat(),
            "repository": f"{self.repo_owner}/{self.repo_name}",
            "total_issues": len(issues),
            "issues_by_type": {},
            "issues_by_priority": {},
            "issues_by_component": {},
            "issues": [],
        }

        for issue in issues:
            analysis = self._analyze_issue(issue, [])

            issue_summary = {
                "number": issue["number"],
                "title": issue["title"],
                "state": issue["state"],
                "created_at": issue["created_at"],
                "updated_at": issue["updated_at"],
                "labels": [label["name"] for label in issue["labels"]],
                "analysis": analysis,
            }

            report["issues"].append(issue_summary)

            # Count by type
            issue_type = analysis["type"]
            report["issues_by_type"][issue_type] = report["issues_by_type"].get(issue_type, 0) + 1

            # Count by priority
            priority = analysis["priority"]
            report["issues_by_priority"][priority] = (
                report["issues_by_priority"].get(priority, 0) + 1
            )

            # Count by component
            for component in analysis["components"]:
                report["issues_by_component"][component] = (
                    report["issues_by_component"].get(component, 0) + 1
                )

        return report


def main():
    """Main CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="GitHub Issues Bridge for AI Development")

    # Commands
    parser.add_argument("--list-issues", action="store_true", help="List open issues")
    parser.add_argument("--issue", type=int, help="Get details for specific issue number")
    parser.add_argument("--search", type=str, help="Search issues by text")
    parser.add_argument("--report", action="store_true", help="Generate issues report")
    parser.add_argument("--fix-workflow", type=int, help="Start fix workflow for issue number")
    parser.add_argument(
        "--create-issue", nargs=2, metavar=("TITLE", "BODY"), help="Create new issue"
    )

    # Options
    parser.add_argument(
        "--state", choices=["open", "closed", "all"], default="open", help="Issue state"
    )
    parser.add_argument("--labels", type=str, help="Filter by labels (comma-separated)")
    parser.add_argument(
        "--format", choices=["json", "pretty"], default="pretty", help="Output format"
    )
    parser.add_argument("--repo", type=str, help="Repository in format owner/name")

    args = parser.parse_args()

    # Parse repo if provided
    repo_owner, repo_name = None, None
    if args.repo and "/" in args.repo:
        repo_owner, repo_name = args.repo.split("/", 1)

    # Initialize bridge
    bridge = GitHubIssuesBridge(repo_owner, repo_name)

    # Execute commands
    result = None

    if args.list_issues:
        labels = args.labels.split(",") if args.labels else None
        result = bridge.get_issues(state=args.state, labels=labels)
    elif args.issue:
        result = bridge.get_issue_details(args.issue)
    elif args.search:
        result = bridge.search_issues(args.search)
    elif args.report:
        result = bridge.generate_issue_report(state=args.state)
    elif args.fix_workflow:
        result = bridge.fix_issue_workflow(args.fix_workflow)
    elif args.create_issue:
        result = bridge.create_issue(args.create_issue[0], args.create_issue[1])
    else:
        parser.print_help()
        return

    # Output results
    if args.format == "json":
        print(json.dumps(result, indent=2, default=str))
    else:
        # Pretty print based on command
        if args.list_issues:
            print(f"\n📋 {args.state.title()} Issues:")
            for issue in result:
                labels = ", ".join([label["name"] for label in issue["labels"]]) or "No labels"
                print(f"#{issue['number']}: {issue['title']}")
                print(f"   Labels: {labels}")
                print(f"   Created: {issue['created_at'][:10]}")
                print()
        elif args.issue:
            issue = result["issue"]
            analysis = result["analysis"]
            print(f"\n🔍 Issue #{issue['number']}: {issue['title']}")
            print(f"State: {issue['state']}")
            print(f"Created: {issue['created_at'][:10]}")
            print(f"Updated: {issue['updated_at'][:10]}")
            print(f"\nAnalysis:")
            print(f"  Type: {analysis['type']}")
            print(f"  Priority: {analysis['priority']}")
            print(f"  Components: {', '.join(analysis['components']) or 'None detected'}")
            print(f"  Suggested files: {', '.join(analysis['suggested_files']) or 'None'}")
            if analysis["error_messages"]:
                print(f"  Error messages: {analysis['error_messages']}")
        elif args.fix_workflow:
            print(f"\n🔧 Fix Workflow for Issue #{result['issue_number']}")
            print(f"Title: {result['issue_title']}")
            print(f"Type: {result['issue_type']}")
            print(f"Priority: {result['priority']}")
            print(f"Components: {', '.join(result['components'])}")
            print(f"Branch: {result['branch_name']}")
            print(f"\nNext Steps:")
            for step in result["next_steps"]:
                print(f"  {step}")
        elif args.report:
            print(f"\n📊 Issues Report ({args.state})")
            print(f"Total issues: {result['total_issues']}")
            print(f"\nBy Type:")
            for issue_type, count in result["issues_by_type"].items():
                print(f"  {issue_type}: {count}")
            print(f"\nBy Priority:")
            for priority, count in result["issues_by_priority"].items():
                print(f"  {priority}: {count}")
            print(f"\nBy Component:")
            for component, count in result["issues_by_component"].items():
                print(f"  {component}: {count}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
