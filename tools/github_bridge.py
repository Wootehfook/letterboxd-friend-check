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

import requests
import json
import os
import subprocess
import sys
import time
import hashlib
import functools
import logging
import concurrent.futures
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('github_bridge')

class GitHubBridge:
    def __init__(self, repo_owner=None, repo_name=None, token=None):
        """Initialize the GitHub bridge with repository information"""
        # Environment detection
        self.is_codespace = 'CODESPACES' in os.environ
        self.is_github_action = 'GITHUB_ACTIONS' in os.environ
        
        # Repository info
        self.repo_owner = repo_owner or self._get_repo_owner()
        self.repo_name = repo_name or self._get_repo_name() or "letterboxd-friend-check"
        
        # Authentication
        if self.is_github_action:
            self.token = os.getenv('GITHUB_TOKEN')  # Automatic in Actions
        elif self.is_codespace:
            # Try codespace token
            self.token = token or os.getenv('GITHUB_TOKEN') or os.getenv('CODESPACE_TOKEN')
        else:
            self.token = token or os.getenv('GITHUB_TOKEN')
        
        # API configuration
        self.base_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}"
        self.headers = {'Authorization': f'token {self.token}'} if self.token else {}
        
        # Set up session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Rate limiting tracking
        self._rate_limit_remaining = None
        self._rate_limit_reset = None
        
        # Caching
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes default
        
        logger.info(f"Initialized GitHubBridge for {self.repo_owner}/{self.repo_name}")
        if self.is_codespace:
            logger.info("Running in GitHub Codespace environment")
        elif self.is_github_action:
            logger.info("Running in GitHub Actions environment")

    # === UTILITY METHODS ===
    def _get_repo_owner(self):
        """Extract repo owner from git remote"""
        try:
            result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                                  capture_output=True, text=True)
            url = result.stdout.strip()
            # Parse github.com/owner/repo format
            if 'github.com' in url:
                parts = url.split('/')
                if ':' in parts[-2]:  # Handle git@github.com:owner/repo.git format
                    return parts[-2].split(':')[-1]
                return parts[-2]
            return None
        except Exception as e:
            logger.warning(f"Could not determine repo owner: {e}")
            return None
    
    def _get_repo_name(self):
        """Extract repo name from git remote"""
        try:
            result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                                  capture_output=True, text=True)
            url = result.stdout.strip()
            # Parse github.com/owner/repo format
            if 'github.com' in url:
                parts = url.split('/')
                # Handle .git extension
                repo = parts[-1]
                if repo.endswith('.git'):
                    repo = repo[:-4]
                return repo
            return None
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
                if 'X-RateLimit-Remaining' in response.headers:
                    self._rate_limit_remaining = response.headers.get('X-RateLimit-Remaining')
                    self._rate_limit_reset = response.headers.get('X-RateLimit-Reset')
                
                # Handle rate limiting
                if response.status_code == 403 and 'rate limit' in response.text.lower():
                    wait_time = int(self._rate_limit_reset) - int(datetime.now().timestamp())
                    wait_time = max(1, wait_time)  # Ensure positive wait time
                    logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time + 1)
                    continue
                    
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    logger.error(f"Error after {max_retries} attempts: {e}")
                    return None
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Request failed, retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
        return None

    def _cache_key(self, method, *args, **kwargs):
        """Generate cache key from method and arguments"""
        key_str = f"{method}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
def cached_request(cache_ttl=None):
    """Decorator for caching API responses"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            cache_key = self._cache_key(func.__name__, *args, **kwargs)
            
            # Check cache
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if datetime.now().timestamp() - timestamp < (cache_ttl or self._cache_ttl):
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_data
            
            # Make request
            result = func(self, *args, **kwargs)
            if result:
                self._cache[cache_key] = (result, datetime.now().timestamp())
            return result
        return wrapper
    return decorator

    def validate_credentials(self):
        """Validate GitHub token and permissions"""
        response = self._make_request('GET', 'https://api.github.com/user')
        if response and response.status_code == 200:
            user_data = response.json()
            logger.info(f"✅ Authenticated as: {user_data.get('login')}")
            
            # Check rate limits
            logger.info(f"📊 Rate limit: {self._rate_limit_remaining}/{response.headers.get('X-RateLimit-Limit')}")
            return True
        else:
            logger.error("❌ Authentication failed. Set GITHUB_TOKEN environment variable.")
            return False

    # === ISSUE MANAGEMENT ===
    @cached_request()
    def get_issues(self, state='open', labels=None, limit=30):
        """Fetch GitHub issues with filtering"""
        params = {'state': state, 'per_page': limit}
        if labels:
            params['labels'] = ','.join(labels)
        
        response = self._make_request('GET', f"{self.base_url}/issues", params=params)
        return response.json() if response and response.status_code == 200 else []

    def create_issue(self, title, body, labels=None):
        """Create a new GitHub issue"""
        data = {'title': title, 'body': body}
        if labels:
            data['labels'] = labels
        
        response = self._make_request('POST', f"{self.base_url}/issues", json=data)
        if response and response.status_code == 201:
            result = response.json()
            logger.info(f"Created issue #{result['number']}: {title}")
            return result
        logger.error(f"Failed to create issue: {title}")
        return None

    def update_issue(self, issue_number, title=None, body=None, state=None):
        """Update an existing issue"""
        data = {}
        if title: data['title'] = title
        if body: data['body'] = body
        if state: data['state'] = state
        
        response = self._make_request('PATCH', f"{self.base_url}/issues/{issue_number}", json=data)
        if response and response.status_code == 200:
            logger.info(f"Updated issue #{issue_number}")
            return response.json()
        logger.error(f"Failed to update issue #{issue_number}")
        return None

    # === PULL REQUEST MANAGEMENT ===
    @cached_request()
    def get_pull_requests(self, state='open', limit=10):
        """Fetch pull requests"""
        response = self._make_request('GET', f"{self.base_url}/pulls", 
                              params={'state': state, 'per_page': limit})
        return response.json() if response and response.status_code == 200 else []

    def create_pull_request(self, title, body, head, base='main'):
        """Create a pull request"""
        data = {
            'title': title,
            'body': body,
            'head': head,
            'base': base
        }
        response = self._make_request('POST', f"{self.base_url}/pulls", json=data)
        if response and response.status_code == 201:
            result = response.json()
            logger.info(f"Created PR #{result['number']}: {title}")
            return result
        logger.error(f"Failed to create PR: {title}")
        return None

    # === REPOSITORY INFO ===
    @cached_request()
    def get_repo_info(self):
        """Get repository information"""
        response = self._make_request('GET', self.base_url)
        return response.json() if response and response.status_code == 200 else None

    @cached_request()
    def get_branches(self):
        """Get all branches"""
        response = self._make_request('GET', f"{self.base_url}/branches")
        return response.json() if response and response.status_code == 200 else []

    @cached_request()
    def get_releases(self):
        """Get releases"""
        response = self._make_request('GET', f"{self.base_url}/releases")
        return response.json() if response and response.status_code == 200 else []

    # === BUILD & CI STATUS ===
    @cached_request()
    def get_workflows(self):
        """Get GitHub Actions workflows"""
        response = self._make_request('GET', f"{self.base_url}/actions/workflows")
        return response.json() if response and response.status_code == 200 else {}

    @cached_request()
    def get_workflow_runs(self, workflow_id=None):
        """Get workflow run history"""
        url = f"{self.base_url}/actions/runs"
        if workflow_id:
            url = f"{self.base_url}/actions/workflows/{workflow_id}/runs"
        
        response = self._make_request('GET', url)
        return response.json() if response and response.status_code == 200 else {}

    # === LOCAL PROJECT ANALYSIS ===
    def analyze_project_structure(self):
        """Analyze local project structure"""
        project_root = Path(".")
        structure = {
            'python_files': list(project_root.glob("**/*.py")),
            'requirements': list(project_root.glob("**/requirements*.txt")),
            'config_files': list(project_root.glob("**/*.json")) + list(project_root.glob("**/*.yaml")),
            'docs': list(project_root.glob("**/*.md")),
            'tests': list(project_root.glob("**/test_*.py")) + list(project_root.glob("**/*_test.py")),
            'build_files': list(project_root.glob("**/*.spec")) + list(project_root.glob("**/Dockerfile")),
        }
        # Convert Path objects to strings and limit to first 30 of each type
        return {k: [str(f) for f in v][:30] for k, v in structure.items()}

    def get_git_status(self):
        """Get current git status"""
        try:
            # Current branch
            branch_result = subprocess.run(['git', 'branch', '--show-current'], 
                                         capture_output=True, text=True)
            current_branch = branch_result.stdout.strip()
            
            # Git status
            status_result = subprocess.run(['git', 'status', '--porcelain'], 
                                         capture_output=True, text=True)
            
            # Recent commits
            log_result = subprocess.run(['git', 'log', '--oneline', '-5'], 
                                      capture_output=True, text=True)
            
            # Commit count
            count_result = subprocess.run(['git', 'rev-list', '--count', 'HEAD'], 
                                      capture_output=True, text=True)
            
            return {
                'current_branch': current_branch,
                'status': status_result.stdout.strip().split('\n') if status_result.stdout.strip() else [],
                'recent_commits': log_result.stdout.strip().split('\n') if log_result.stdout.strip() else [],
                'commit_count': count_result.stdout.strip() if count_result.stdout.strip() else "0"
            }
        except Exception as e:
            logger.error(f"Git status error: {e}")
            return {'error': 'Git not available or not in git repository'}

    # === CODE ANALYSIS ===
    @cached_request()
    def search_code(self, query, file_extension=None):
        """Search code in repository"""
        search_query = f"repo:{self.repo_owner}/{self.repo_name} {query}"
        if file_extension:
            search_query += f" extension:{file_extension}"
        
        response = self._make_request('GET', "https://api.github.com/search/code", 
                              params={'q': search_query})
        return response.json() if response and response.status_code == 200 else {}

    def get_project_dependencies(self):
        """Analyze project dependencies"""
        deps = {}
        
        # Python requirements
        req_files = ['requirements.txt', 'requirements-dev.txt', 'pyproject.toml']
        for req_file in req_files:
            if os.path.exists(req_file):
                try:
                    with open(req_file, 'r') as f:
                        deps[req_file] = f.read().splitlines()
                except Exception as e:
                    logger.warning(f"Error reading {req_file}: {e}")
        
        # Package.json if exists
        if os.path.exists('package.json'):
            try:
                with open('package.json', 'r') as f:
                    package_data = json.load(f)
                    deps['npm_dependencies'] = package_data.get('dependencies', {})
                    deps['npm_dev_dependencies'] = package_data.get('devDependencies', {})
            except Exception as e:
                logger.warning(f"Error reading package.json: {e}")
        
        return deps
    
    def analyze_python_quality(self):
        """Analyze Python code quality specific to this project"""
        try:
            issues = {
                'missing_docstrings': [],
                'long_lines': [],
                'complex_functions': [],
                'todo_comments': []
            }
            
            # Check for pylint
            pylint_available = False
            try:
                pylint_version = subprocess.run(['pylint', '--version'], 
                                              capture_output=True, text=True)
                pylint_available = pylint_version.returncode == 0
            except:
                pylint_available = False
                
            # Run pylint if available
            pylint_result = None
            if pylint_available:
                try:
                    pylint_result = subprocess.run(['pylint', '*.py', '--output-format=json'], 
                                                 capture_output=True, text=True, timeout=10)
                except:
                    pylint_result = None
            
            # Check Python files
            for py_file in Path('.').glob('**/*.py'):
                # Skip virtual environments
                if '.venv/' in str(py_file) or 'venv/' in str(py_file):
                    continue
                    
                try:
                    with open(py_file, 'r') as f:
                        content = f.read()
                        lines = content.splitlines()
                        
                        # Check for long lines
                        for i, line in enumerate(lines):
                            if len(line) > 100:
                                issues['long_lines'].append(f"{py_file}:{i+1}: {line[:50]}...")
                            
                            # Check for TODOs
                            if 'TODO' in line or 'FIXME' in line:
                                issues['todo_comments'].append(f"{py_file}:{i+1}: {line.strip()}")
                        
                        # Check for missing docstrings in functions and classes
                        if not content.strip().startswith('"""') and not content.strip().startswith("'''"):
                            issues['missing_docstrings'].append(f"{py_file}: Missing module docstring")
                except Exception as e:
                    logger.warning(f"Error analyzing {py_file}: {e}")
            
            # Limit the number of issues reported
            for key in issues:
                issues[key] = issues[key][:20]  # Only report first 20 issues of each type
            
            return {
                'pylint_available': pylint_available,
                'pylint_result': pylint_result.stdout if pylint_result and pylint_result.returncode == 0 else None,
                'issues': issues
            }
        except Exception as e:
            logger.error(f"Code analysis error: {e}")
            return {'error': 'Code analysis failed'}
            
    def check_executable_status(self):
        """Check status of built executables"""
        executables = {
            'windows': 'download/LetterboxdFriendCheck.exe',
            'linux': 'download/LetterboxdFriendCheck-Linux'
        }
        
        status = {}
        for platform, path in executables.items():
            if os.path.exists(path):
                stat = os.stat(path)
                status[platform] = {
                    'exists': True,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'executable': os.access(path, os.X_OK)
                }
            else:
                status[platform] = {'exists': False}
        
        return status

    # === COMPREHENSIVE REPORT ===
    def generate_project_report(self, use_parallel=False):
        """Generate comprehensive project report for AI analysis"""
        if use_parallel:
            return self.generate_project_report_parallel()
            
        report = {
            'timestamp': datetime.now().isoformat(),
            'repository': {
                'owner': self.repo_owner,
                'name': self.repo_name,
                'info': self.get_repo_info()
            },
            'issues': {
                'open': self.get_issues('open'),
                'closed_recent': self.get_issues('closed', limit=5)  # Last 5 closed
            },
            'pull_requests': {
                'open': self.get_pull_requests('open'),
                'closed_recent': self.get_pull_requests('closed', limit=3)
            },
            'builds': {
                'workflows': self.get_workflows(),
                'recent_runs': self.get_workflow_runs()
            },
            'local_analysis': {
                'project_structure': self.analyze_project_structure(),
                'git_status': self.get_git_status(),
                'dependencies': self.get_project_dependencies(),
                'executable_status': self.check_executable_status(),
                'code_quality': self.analyze_python_quality()
            },
            'releases': self.get_releases()[:3]  # Last 3 releases
        }
        return report
        
    def generate_project_report_parallel(self):
        """Generate report with parallel API calls"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all tasks
            futures = {
                'repo_info': executor.submit(self.get_repo_info),
                'open_issues': executor.submit(self.get_issues, 'open'),
                'closed_issues': executor.submit(self.get_issues, 'closed', None, 5),
                'open_prs': executor.submit(self.get_pull_requests, 'open'),
                'closed_prs': executor.submit(self.get_pull_requests, 'closed', 3),
                'workflows': executor.submit(self.get_workflows),
                'workflow_runs': executor.submit(self.get_workflow_runs),
                'releases': executor.submit(self.get_releases),
            }
            
            # Gather results
            report = {
                'timestamp': datetime.now().isoformat(),
                'repository': {
                    'owner': self.repo_owner,
                    'name': self.repo_name,
                }
            }
            
            for key, future in futures.items():
                try:
                    report[key] = future.result(timeout=30)
                except Exception as e:
                    logger.error(f"Error in parallel task {key}: {e}")
                    report[key] = {'error': str(e)}
            
            # Structure the results nicely
            structured_report = {
                'timestamp': report['timestamp'],
                'repository': {
                    'owner': self.repo_owner,
                    'name': self.repo_name,
                    'info': report.get('repo_info')
                },
                'issues': {
                    'open': report.get('open_issues', []),
                    'closed_recent': report.get('closed_issues', [])
                },
                'pull_requests': {
                    'open': report.get('open_prs', []),
                    'closed_recent': report.get('closed_prs', [])
                },
                'builds': {
                    'workflows': report.get('workflows', {}),
                    'recent_runs': report.get('workflow_runs', {})
                },
                'releases': report.get('releases', [])[:3]
            }
            
            # Add local analysis (not API dependent)
            structured_report['local_analysis'] = {
                'project_structure': self.analyze_project_structure(),
                'git_status': self.get_git_status(),
                'dependencies': self.get_project_dependencies(),
                'executable_status': self.check_executable_status(),
                'code_quality': self.analyze_python_quality()
            }
            
            return structured_report
            
    def format_output(self, data, format_type='json'):
        """Format output in different styles"""
        if format_type == 'json':
            return json.dumps(data, indent=2, default=str)
        elif format_type == 'markdown':
            # Convert to markdown for easy reading
            md = ["# GitHub Bridge Report\n"]
            md.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            if isinstance(data, dict) and 'repository' in data:
                md.append(f"## Repository: {data['repository'].get('owner')}/{data['repository'].get('name')}\n")
            
            if isinstance(data, dict) and 'issues' in data and 'open' in data['issues']:
                md.append("## Open Issues\n")
                for issue in data['issues']['open']:
                    md.append(f"- [ ] #{issue['number']}: {issue['title']}")
            
            if isinstance(data, dict) and 'local_analysis' in data and 'executable_status' in data['local_analysis']:
                md.append("\n## Executable Status\n")
                for platform, status in data['local_analysis']['executable_status'].items():
                    if status.get('exists'):
                        md.append(f"- {platform}: ✅ {status.get('size_mb')}MB (Modified: {status.get('modified', 'unknown')})")
                    else:
                        md.append(f"- {platform}: ❌ Not found")
            
            return '\n'.join(md)
        elif format_type == 'summary':
            # Brief summary for quick review
            summary = {}
            
            if isinstance(data, dict):
                if 'issues' in data and 'open' in data['issues']:
                    summary['open_issues'] = len(data['issues']['open'])
                
                if 'pull_requests' in data and 'open' in data['pull_requests']:
                    summary['open_prs'] = len(data['pull_requests']['open'])
                
                if 'releases' in data and data['releases']:
                    summary['last_release'] = data['releases'][0].get('tag_name', 'None') if data['releases'] else 'None'
                
                if 'local_analysis' in data and 'executable_status' in data['local_analysis']:
                    summary['executable_status'] = data['local_analysis']['executable_status']
                
                if 'local_analysis' in data and 'git_status' in data['local_analysis']:
                    git_status = data['local_analysis']['git_status']
                    summary['git'] = {
                        'branch': git_status.get('current_branch', 'unknown'),
                        'commits': git_status.get('commit_count', '0'),
                        'uncommitted_changes': len(git_status.get('status', []))
                    }
            else:
                summary = {'error': 'Invalid data format for summary'}
                
            return json.dumps(summary, indent=2)
        else:
            return json.dumps(data, indent=2, default=str)


# === CLI INTERFACE ===
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='GitHub Bridge for AI Development')
    
    # Main commands
    parser.add_argument('--issues', action='store_true', help='Get open issues')
    parser.add_argument('--prs', action='store_true', help='Get open pull requests')
    parser.add_argument('--status', action='store_true', help='Get git status')
    parser.add_argument('--report', action='store_true', help='Generate full project report')
    parser.add_argument('--search', type=str, help='Search code in repository')
    parser.add_argument('--create-issue', nargs=2, metavar=('TITLE', 'BODY'), 
                       help='Create new issue')
    parser.add_argument('--quality', action='store_true', help='Run code quality analysis')
    parser.add_argument('--exes', action='store_true', help='Check executable status')
    parser.add_argument('--validate', action='store_true', help='Validate GitHub credentials')
    
    # Configuration options
    parser.add_argument('--format', choices=['json', 'markdown', 'summary'], 
                       default='json', help='Output format')
    parser.add_argument('--output', '-o', type=str, help='Output file (default: stdout)')
    parser.add_argument('--cache-ttl', type=int, default=300, help='Cache TTL in seconds')
    parser.add_argument('--parallel', action='store_true', help='Use parallel API requests')
    parser.add_argument('--repo', type=str, help='Repository in format owner/name')
    
    args = parser.parse_args()
    
    # Parse repo argument if provided
    repo_owner, repo_name = None, None
    if args.repo and '/' in args.repo:
        repo_owner, repo_name = args.repo.split('/', 1)
    
    # Initialize the bridge
    bridge = GitHubBridge(repo_owner, repo_name)
    bridge._cache_ttl = args.cache_ttl
    
    # Execute requested command
    result = None
    
    if args.validate:
        result = {"authenticated": bridge.validate_credentials()}
    elif args.issues:
        result = bridge.get_issues()
    elif args.prs:
        result = bridge.get_pull_requests()
    elif args.status:
        result = bridge.get_git_status()
    elif args.report:
        result = bridge.generate_project_report(args.parallel)
    elif args.search:
        result = bridge.search_code(args.search, 'py')
    elif args.create_issue:
        result = bridge.create_issue(args.create_issue[0], args.create_issue[1])
    elif args.quality:
        result = bridge.analyze_python_quality()
    elif args.exes:
        result = bridge.check_executable_status()
    else:
        parser.print_help()
        return
    
    # Format output
    output = bridge.format_output(result, args.format)
    
    # Save or print output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Output saved to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        sys.exit(1)
