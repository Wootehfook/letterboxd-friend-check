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

import os
import sys
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('letterboxd_bridge')

class LetterboxdBridge:
    """A simplified bridge for the Letterboxd project"""
    
    def __init__(self):
        """Initialize the bridge"""
        logger.info("Initializing Letterboxd Bridge...")
        self.workspace_path = Path("/workspaces/letterboxd-friend-check")
    
    def check_executable_status(self):
        """Check status of built executables"""
        logger.info("Checking executable status...")
        executables = {
            'windows': 'download/LetterboxdFriendCheck.exe',
            'linux': 'download/LetterboxdFriendCheck-Linux'
        }
        
        status = {}
        for platform, path in executables.items():
            full_path = self.workspace_path / path
            if full_path.exists():
                stat = os.stat(full_path)
                status[platform] = {
                    'exists': True,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'executable': os.access(full_path, os.X_OK)
                }
                logger.info(f"Found {platform} executable: {status[platform]['size_mb']} MB")
            else:
                status[platform] = {'exists': False}
                logger.warning(f"Executable for {platform} not found at {full_path}")
        
        return status
    
    def get_project_structure(self):
        """Analyze the project structure"""
        logger.info("Analyzing project structure...")
        result = {
            'files': {},
            'executables': self.check_executable_status(),
            'timestamp': datetime.now().isoformat()
        }
        
        # Count file types
        extensions = {}
        for ext in ['.py', '.json', '.md', '.txt', '.spec', '.exe']:
            files = list(self.workspace_path.glob(f"**/*{ext}"))
            extensions[ext] = len(files)
            
        result['files']['extensions'] = extensions
        
        # Check key files
        key_files = [
            'LBoxFriendCheck.py',
            'run_letterboxd.py', 
            'tmdb_api.py',
            'requirements.txt',
            'README.md'
        ]
        
        result['files']['key_files'] = {}
        for file in key_files:
            path = self.workspace_path / file
            if path.exists():
                result['files']['key_files'][file] = {
                    'exists': True,
                    'size_kb': round(path.stat().st_size / 1024, 2)
                }
            else:
                result['files']['key_files'][file] = {'exists': False}
        
        return result

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Letterboxd Project Bridge')
    parser.add_argument('--exes', action='store_true', help='Check executables')
    parser.add_argument('--structure', action='store_true', help='Analyze project structure')
    parser.add_argument('--format', choices=['json', 'pretty'], default='pretty', 
                       help='Output format (default: pretty)')
    
    args = parser.parse_args()
    
    bridge = LetterboxdBridge()
    
    if args.exes:
        result = bridge.check_executable_status()
    elif args.structure:
        result = bridge.get_project_structure()
    else:
        parser.print_help()
        return
    
    # Output results
    if args.format == 'json':
        print(json.dumps(result, indent=2, default=str))
    else:
        # Pretty print
        if args.exes:
            print("\n📊 Executable Status:")
            for platform, info in result.items():
                if info['exists']:
                    print(f"✅ {platform}: {info['size_mb']} MB")
                    print(f"   - Modified: {info['modified']}")
                    print(f"   - Executable: {info['executable']}")
                else:
                    print(f"❌ {platform}: Not found")
        elif args.structure:
            print("\n📁 Project Structure:")
            print(f"Timestamp: {result['timestamp']}")
            
            print("\n📄 File Extensions:")
            for ext, count in result['files']['extensions'].items():
                print(f"  {ext}: {count} files")
            
            print("\n🔑 Key Files:")
            for file, info in result['files']['key_files'].items():
                if info['exists']:
                    print(f"  ✅ {file} ({info['size_kb']} KB)")
                else:
                    print(f"  ❌ {file} (not found)")
            
            print("\n⚙️ Executables:")
            for platform, info in result['executables'].items():
                if info['exists']:
                    print(f"  ✅ {platform}: {info['size_mb']} MB")
                else:
                    print(f"  ❌ {platform}: Not found")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
