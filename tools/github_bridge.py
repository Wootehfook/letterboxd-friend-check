#!/usr/bin/env python
"""
GitHub Bridge - Enhanced project context provider for AI assistance
-----------------------------------------------------------------
A bridge between your local project and GitHub's API to provide comprehensive
context for AI development assistants.

This script helps gather repository data, issues, PRs, and local project
information to give AI tools better context when working on your projects.

Author: GitHub Copilot & Team
License: MIT
"""

import functools
import hashlib
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("github_bridge")


def cached_request(cache_ttl=None):
    """Decorator for caching API responses"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            cache_key = self._cache_key(func.__name__, *args, **kwargs)

            # Check cache
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                ttl = cache_ttl or self._cache_ttl
                if datetime.now().timestamp() - timestamp < ttl:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_data

            # Make request
            result = func(self, *args, **kwargs)
            if result:
                self._cache[cache_key] = (result, datetime.now().timestamp())
            return result

        return wrapper

    return decorator


class GitHubBridge:
    """GitHub API bridge for project analysis and issue management"""

    def __init__(self, repo_owner=None, repo_name=None, token=None):
        """Initialize the GitHub bridge with repository information"""
        # Environment detection
        self.is_codespace = "CODESPACES" in os.environ
        self.is_github_action = "GITHUB_ACTIONS" in os.environ

        # Repository info
        self.repo_owner = repo_owner or self._get_repo_owner()
        repo_name_default = "letterboxd-friend-check"
        self.repo_name = repo_name or self._get_repo_name() or repo_name_default

        # Authentication
        if self.is_github_action:
            self.token = os.getenv("GITHUB_TOKEN")  # Automatic in Actions
        elif self.is_codespace:
            # Try codespace token
            codespace_token = os.getenv("CODESPACE_TOKEN")
            self.token = token or os.getenv("GITHUB_TOKEN") or codespace_token
        else:
            self.token = token or os.getenv("GITHUB_TOKEN")

        # API configuration
        repo_path = f"{self.repo_owner}/{self.repo_name}"
        self.base_url = f"https://api.github.com/repos/{repo_path}"
        self.headers = {}
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

        # Set up session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(self.headers)

        # Rate limiting tracking
        self._rate_limit_remaining = None
        self._rate_limit_reset = None

        # Caching
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes default

        logger.info(f"Initialized GitHubBridge for {self.repo_owner}/" f"{self.repo_name}")
        if self.is_codespace:
            logger.info("Running in GitHub Codespace environment")
        elif self.is_github_action:
            logger.info("Running in GitHub Actions environment")

    def validate_credentials(self) -> bool:
        """Validate GitHub credentials"""
        if not self.token:
            logger.warning("No GitHub token provided")
            return False

        response = self._make_request("GET", "https://api.github.com/user")
        if response and response.status_code == 200:
            user_data = response.json()
            logger.info(f"Authenticated as: {user_data.get('login')}")
            return True

        logger.error("GitHub authentication failed")
        return False

    # === UTILITY METHODS ===
    def _get_repo_owner(self):
        """Extract repo owner from git remote"""
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"], capture_output=True, text=True, check=False
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

            return None
        except Exception as e:
            logger.warning(f"Could not determine repo owner: {e}")
            return None

    def _get_repo_name(self):
        """Extract repo name from git remote"""
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"], capture_output=True, text=True, check=False
            )
            url = result.stdout.strip()

            # Securely parse GitHub URLs with proper validation
            repo_name = None
            if url.startswith("git@github.com:"):
                # Handle SSH format: git@github.com:owner/repo.git
                ssh_path = url[len("git@github.com:") :]
                if "/" in ssh_path:
                    repo_name = ssh_path.split("/")[1]
            elif url.startswith("https://github.com/"):
                # Handle HTTPS format: https://github.com/owner/repo.git
                https_path = url[len("https://github.com/") :]
                if "/" in https_path:
                    repo_name = https_path.split("/")[1]

            # Remove .git extension if present
            if repo_name and repo_name.endswith(".git"):
                repo_name = repo_name[:-4]

            return repo_name
        except Exception as e:
            logger.warning(f"Could not determine repo name: {e}")
            return None

    def _make_request(self, method, url, **kwargs):
        """Centralized request handler with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.request(method, url, **kwargs)

                # Update rate limit info
                if "X-RateLimit-Remaining" in response.headers:
                    remaining = response.headers.get("X-RateLimit-Remaining")
                    self._rate_limit_remaining = remaining
                    self._rate_limit_reset = response.headers.get("X-RateLimit-Reset")

                # Handle rate limiting
                if response.status_code == 403 and "rate limit" in response.text.lower():
                    if self._rate_limit_reset:
                        reset_time = int(self._rate_limit_reset)
                        current_time = int(datetime.now().timestamp())
                        wait_time = max(1, reset_time - current_time)
                        logger.warning(f"Rate limited. Waiting {wait_time} " f"seconds...")
                        time.sleep(wait_time + 1)
                        continue

                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    logger.error(f"Error after {max_retries} attempts: {e}")
                    return None
                wait_time = 2**attempt  # Exponential backoff
                logger.warning(f"Request failed, retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
        return None

    def _cache_key(self, method, *args, **kwargs):
        """Generate cache key from method and arguments"""
        key_str = f"{method}:{args}:{sorted(kwargs.items())}"
        # Use SHA256 for cache key generation for better security
        return hashlib.sha256(key_str.encode()).hexdigest()[:16]

    # === ISSUE MANAGEMENT ===
    @cached_request()
    def get_issues(self, state="open", labels=None, limit=30) -> List[Dict]:
        """Get repository issues"""
        params = {"state": state, "per_page": limit}
        if labels:
            params["labels"] = ",".join(labels)

        response = self._make_request("GET", f"{self.base_url}/issues", params=params)
        if response:
            return response.json()
        return []

    def create_issue(
        self, title: str, body: str = "", labels: Optional[List[str]] = None
    ) -> Optional[Dict]:
        """Create a new issue"""
        data = {"title": title, "body": body}
        if labels:
            data["labels"] = labels

        response = self._make_request("POST", f"{self.base_url}/issues", json=data)
        if response:
            issue = response.json()
            logger.info(f"Created issue #{issue['number']}: {title}")
            return issue
        return None

    def update_issue(
        self,
        issue_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None,
    ) -> Optional[Dict]:
        """Update an existing issue"""
        data = {}
        if title:
            data["title"] = title
        if body:
            data["body"] = body
        if state:
            data["state"] = state

        url = f"{self.base_url}/issues/{issue_number}"
        response = self._make_request("PATCH", url, json=data)
        if response:
            return response.json()
        return None

    # === PULL REQUEST MANAGEMENT ===
    @cached_request()
    def get_pull_requests(self, state="open", limit=30) -> List[Dict]:
        """Get repository pull requests"""
        response = self._make_request(
            "GET", f"{self.base_url}/pulls", params={"state": state, "per_page": limit}
        )
        if response:
            return response.json()
        return []

    def get_pull_request(self, pr_number: int) -> Optional[Dict]:
        """Get a specific pull request"""
        response = self._make_request("GET", f"{self.base_url}/pulls/{pr_number}")
        if response:
            return response.json()
        return None

    # === PROJECT ANALYSIS ===
    def analyze_project(self, project_path: str = ".") -> Dict:
        """Analyze local project structure and provide context"""
        project_root = Path(project_path).resolve()

        analysis = {
            "project_root": str(project_root),
            "last_analysis": datetime.now().isoformat(),
            "git_info": self._analyze_git(project_root),
            "project_structure": self._analyze_structure(project_root),
            "dependencies": self._analyze_dependencies(project_root),
            "code_stats": self._analyze_code(project_root),
            "recent_activity": self._analyze_recent_activity(project_root),
        }

        return analysis

    def _analyze_git(self, project_root: Path) -> Dict:
        """Analyze git repository information"""
        git_info = {}
        try:
            # Get current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=False,
            )
            git_info["current_branch"] = result.stdout.strip()

            # Get recent commits
            result = subprocess.run(
                ["git", "log", "--oneline", "-10"],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=False,
            )
            git_info["recent_commits"] = result.stdout.strip().split("\n")

            # Get status
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=False,
            )
            git_info["status"] = result.stdout.strip()

        except Exception as e:
            logger.warning(f"Error analyzing git: {e}")

        return git_info

    def _analyze_structure(self, project_root: Path) -> Dict:
        """Analyze project file structure"""
        structure = {
            "total_files": 0,
            "directories": [],
            "key_files": [],
            "config_files": [],
            "languages": set(),
        }

        # Count files and identify structure
        for item in project_root.rglob("*"):
            if item.is_file():
                structure["total_files"] += 1

                # Identify key files
                if item.name in [
                    "README.md",
                    "requirements.txt",
                    "setup.py",
                    "pyproject.toml",
                    "package.json",
                    "Dockerfile",
                ]:
                    structure["key_files"].append(str(item.relative_to(project_root)))

                # Identify config files
                config_patterns = ["*.json", "*.yaml", "*.yml", "*.toml", "*.ini", "*.cfg"]
                if any(item.match(pattern) for pattern in config_patterns):
                    structure["config_files"].append(str(item.relative_to(project_root)))

                # Identify languages
                suffix = item.suffix
                if suffix:
                    structure["languages"].add(suffix)
            elif item.is_dir() and not item.name.startswith("."):
                structure["directories"].append(str(item.relative_to(project_root)))

        structure["languages"] = list(structure["languages"])
        return structure

    def _analyze_dependencies(self, project_root: Path) -> Dict:
        """Analyze project dependencies"""
        deps = {}

        # Python dependencies
        req_file = project_root / "requirements.txt"
        if req_file.exists():
            deps["python_requirements"] = req_file.read_text().strip().split("\n")

        # Python project file
        pyproject_file = project_root / "pyproject.toml"
        if pyproject_file.exists():
            deps["pyproject_exists"] = True

        # Node.js dependencies
        package_file = project_root / "package.json"
        if package_file.exists():
            try:
                package_data = json.loads(package_file.read_text())
                deps["npm_dependencies"] = list(package_data.get("dependencies", {}).keys())
                deps["npm_dev_dependencies"] = list(package_data.get("devDependencies", {}).keys())
            except json.JSONDecodeError:
                logger.warning("Could not parse package.json")

        return deps

    def _analyze_code(self, project_root: Path) -> Dict:
        """Analyze code statistics"""
        stats = {"total_lines": 0, "files_by_type": {}}

        code_extensions = [".py", ".js", ".ts", ".java", ".cpp", ".c", ".css", ".html", ".md"]

        for ext in code_extensions:
            files = list(project_root.rglob(f"*{ext}"))
            if files:
                line_count = 0
                for file_path in files:
                    try:
                        lines = len(file_path.read_text().splitlines())
                        line_count += lines
                    except Exception:
                        continue

                stats["files_by_type"][ext] = {"count": len(files), "lines": line_count}
                stats["total_lines"] += line_count

        return stats

    def _analyze_recent_activity(self, project_root: Path) -> Dict:
        """Analyze recent file activity"""
        activity = {"recently_modified": []}

        try:
            # Get files modified in last 7 days
            result = subprocess.run(
                [
                    "find",
                    str(project_root),
                    "-name",
                    "*.py",
                    "-o",
                    "-name",
                    "*.js",
                    "-o",
                    "-name",
                    "*.md",
                    "-mtime",
                    "-7",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.stdout:
                files = result.stdout.strip().split("\n")
                activity["recently_modified"] = [
                    str(Path(f).relative_to(project_root)) for f in files if f and Path(f).is_file()
                ]
        except Exception as e:
            logger.warning(f"Error analyzing recent activity: {e}")

        return activity

    # === UTILITY FUNCTIONS ===
    def get_rate_limit_status(self) -> Dict:
        """Get current rate limit status"""
        response = self._make_request("GET", "https://api.github.com/rate_limit")
        if response:
            return response.json()
        return {}

    def search_code(self, query: str, language: Optional[str] = None) -> List[Dict]:
        """Search code in the repository"""
        params = {"q": f"repo:{self.repo_owner}/{self.repo_name} {query}"}
        if language:
            params["q"] += f" language:{language}"

        response = self._make_request("GET", "https://api.github.com/search/code", params=params)
        if response:
            return response.json().get("items", [])
        return []


def main():
    """Main function for command-line usage"""
    import argparse

    parser = argparse.ArgumentParser(description="GitHub Bridge Tool")
    parser.add_argument("--analyze", action="store_true", help="Analyze current project")
    parser.add_argument("--issues", action="store_true", help="List open issues")
    parser.add_argument("--prs", action="store_true", help="List open pull requests")
    parser.add_argument(
        "--create-issue", nargs=2, metavar=("TITLE", "BODY"), help="Create a new issue"
    )
    parser.add_argument("--token", help="GitHub token")
    parser.add_argument("--repo", help="Repository (owner/name)")

    args = parser.parse_args()

    # Parse repository
    repo_owner = repo_name = None
    if args.repo:
        if "/" in args.repo:
            repo_owner, repo_name = args.repo.split("/", 1)
        else:
            repo_name = args.repo

    # Initialize bridge
    bridge = GitHubBridge(repo_owner=repo_owner, repo_name=repo_name, token=args.token)

    if not bridge.validate_credentials():
        logger.error("GitHub authentication failed")
        sys.exit(1)

    if args.analyze:
        analysis = bridge.analyze_project()
        print(json.dumps(analysis, indent=2))

    if args.issues:
        issues = bridge.get_issues()
        print(f"\n📋 Open Issues ({len(issues)}):")
        for issue in issues:
            print(f"  #{issue['number']}: {issue['title']}")

    if args.prs:
        prs = bridge.get_pull_requests()
        print(f"\n🔀 Open Pull Requests ({len(prs)}):")
        for pr in prs:
            print(f"  #{pr['number']}: {pr['title']}")

    if args.create_issue:
        title, body = args.create_issue
        issue = bridge.create_issue(title, body)
        if issue:
            print(f"✅ Created issue #{issue['number']}: {title}")


if __name__ == "__main__":
    main()
