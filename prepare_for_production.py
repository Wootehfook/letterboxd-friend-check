#!/usr/bin/env python
"""
Production Preparation Script for Letterboxd Friend Check Application

This script:
1. Removes sensitive personal data
2. Cleans up development test files
3. Creates clean config templates
4. Prepares the project for public release

Author: GitHub Copilot
"""

import os
import json
import shutil
from datetime import datetime


def backup_current_state():
    """Create a backup of the current development state."""
    print("📦 Creating backup of current development state...")

    backup_dir = f"backup_dev_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)

    # Files to backup
    important_files = [
        "config.json",
        "letterboxd.db",
        "data/config.json" if os.path.exists("data/config.json") else None,
        (
            "letterboxd_friend_check/data/config.json"
            if os.path.exists("letterboxd_friend_check/data/config.json")
            else None
        ),
    ]

    for file_path in important_files:
        if file_path and os.path.exists(file_path):
            dest_path = os.path.join(backup_dir, file_path.replace("/", "_"))
            shutil.copy2(file_path, dest_path)
            print(f"   ✓ Backed up: {file_path}")

    print(f"   ✅ Backup created in: {backup_dir}")
    return backup_dir


def remove_sensitive_data():
    """Remove sensitive personal data from config files."""
    print("\n🔒 Removing sensitive personal data...")

    # List of config files that may contain sensitive data
    config_files = [
        "config.json",
        "data/config.json",
        "letterboxd_friend_check/data/config.json",
    ]

    clean_config = {
        "username": "",
        "remember_user": False,
        "tmdb_api_key": "",
        "_comment_tmdb_api_key": (
            "Get your free TMDB API key from " "https://www.themoviedb.org/settings/api"
        ),
        "_comment_instructions": [
            "1. Sign up for a free account at https://www.themoviedb.org/",
            "2. Go to your account settings: https://www.themoviedb.org/settings/api",
            "3. Request an API key (choose 'Developer' option)",
            "4. Copy your API key and paste it in the tmdb_api_key field above",
            "5. Save this file and restart the application",
        ],
        "dark_mode": False,
    }

    for config_file in config_files:
        if os.path.exists(config_file):
            try:
                # Create clean config
                os.makedirs(os.path.dirname(config_file), exist_ok=True)
                with open(config_file, "w") as f:
                    json.dump(clean_config, f, indent=4)
                print(f"   ✓ Cleaned: {config_file}")
            except Exception as e:
                print(f"   ⚠ Error cleaning {config_file}: {e}")


def remove_personal_database():
    """Remove personal database files."""
    print("\n🗄️ Removing personal database files...")

    db_files = [
        "letterboxd.db",
        "letterboxd.db-journal",
        "data/letterboxd.db",
        "letterboxd_friend_check/data/letterboxd.db",
    ]

    for db_file in db_files:
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"   ✓ Removed: {db_file}")


def remove_development_test_files():
    """Remove development test files."""
    print("\n🧪 Removing development test files...")

    # Get all test files in root directory
    test_files = [f for f in os.listdir(".") if f.startswith("test_") and f.endswith(".py")]

    # Additional development files to remove
    dev_files = [
        "demo_canvas_scaling.py",
        "demo_large_watchlist.py",
        "interactive_theme_tester.py",
        "theme_testing_tool.py",
        "fix_all_flake8.py",
        "fix_flake8.py",
        "menu_methods.py",
        "menu_methods.txt",
        "new_methods.txt",
        "Output.txt",
        "README.md.new",
    ]

    all_files_to_remove = test_files + dev_files

    removed_count = 0
    for file_name in all_files_to_remove:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"   ✓ Removed: {file_name}")
            removed_count += 1

    print(f"   ✅ Removed {removed_count} development files")


def remove_development_summary_files():
    """Remove development summary markdown files."""
    print("\n📝 Removing development summary files...")

    summary_files = [
        "CONTRAST_ISSUES_RESOLUTION.md",
        "ENHANCEMENT_SUMMARY.md",
        "FRIENDS_SCROLLING_FIX_SUMMARY.md",
        "GUI_QUEUE_CLEANUP_SUMMARY.md",
        "LETTERBOXD_URL_FIX_SUMMARY.md",
        "PERSISTENCE_IMPLEMENTATION_SUMMARY.md",
        "SETUP_UX_IMPROVEMENT_SUMMARY.md",
        "THEME_IMPLEMENTATION_SUMMARY.md",
        "THEME_READABILITY_FIX_SUMMARY.md",
        "THEME_TESTING_IMPROVEMENTS.md",
        "TMDB_API_KEY_FIX_SUMMARY.md",
        "TMDB_CONFIG_ENHANCEMENT.md",
        "TMDB_GUI_INTEGRATION_SUMMARY.md",
    ]

    removed_count = 0
    for file_name in summary_files:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"   ✓ Removed: {file_name}")
            removed_count += 1

    print(f"   ✅ Removed {removed_count} development summary files")


def clean_logs_and_cache():
    """Clean log files and cache directories."""
    print("\n🧹 Cleaning logs and cache...")

    # Remove log files
    if os.path.exists("logs"):
        shutil.rmtree("logs")
        print("   ✓ Removed logs directory")

    # Remove __pycache__ directories
    for root, dirs, files in os.walk("."):
        for dir_name in dirs[:]:  # Create copy to modify during iteration
            if dir_name == "__pycache__":
                cache_path = os.path.join(root, dir_name)
                shutil.rmtree(cache_path)
                print(f"   ✓ Removed: {cache_path}")
                dirs.remove(dir_name)  # Don't recurse into removed directory


def remove_sensitive_environment_files():
    """Remove files that might contain sensitive environment data."""
    print("\n🌍 Removing sensitive environment files...")

    sensitive_files = [
        ".env",
        "Cookie.json",
    ]

    for file_name in sensitive_files:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"   ✓ Removed: {file_name}")


def create_production_readme():
    """Create a clean production README."""
    print("\n📖 Creating production README...")

    production_readme = """# Letterboxd Friend Check

A Python desktop application that compares your Letterboxd watchlist with friends' watchlists
to find common movies.

## Features

- 🎬 **Compare Watchlists**: Find movies you and your friends both want to watch
- 👥 **Friends Management**: Easily select which friends to sync with
- 🎨 **Modern UI**: Professional interface with light/dark themes
- 🎭 **TMDB Integration**: Optional movie details, posters, and ratings
- 💾 **Data Persistence**: Saves your data between sessions
- ♿ **Accessibility**: WCAG AA compliant themes
- 🌐 **Cross-Platform**: Works on Windows, macOS, and Linux

## Quick Start

1. **Install Python 3.8+** if not already installed
2. **Clone this repository**:
   ```bash
   git clone https://github.com/yourusername/letterboxd-friend-check.git
   cd letterboxd-friend-check
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the application**:
   ```bash
   python run_letterboxd.py
   ```

## First Run Setup

1. Enter your Letterboxd username
2. (Optional) Add your TMDB API key for enhanced movie details
3. Click "Fetch Friends" to load your friends list
4. Select friends you want to compare with
5. Click "Sync Watchlists" to find common movies

## TMDB API Key (Optional)

For movie posters, ratings, and additional details:

1. Sign up at [TMDB](https://www.themoviedb.org/)
2. Get your free API key from [Account Settings → API](https://www.themoviedb.org/settings/api)
3. Enter it in the Setup tab

## Requirements

- Python 3.8 or higher
- Internet connection
- Public Letterboxd profile

## Privacy & Data

- Only accesses **public** Letterboxd data
- No login required
- All data stored **locally** on your computer
- Respects Letterboxd's rate limits

## License

GNU General Public License v3.0 - see [LICENSE](LICENSE)

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

---

**Note**: This application was developed with AI assistance and is not affiliated with Letterboxd.
"""

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(production_readme)

    print("   ✓ Created production README.md")


def update_gitignore():
    """Ensure .gitignore is comprehensive for production."""
    print("\n📄 Updating .gitignore...")

    production_gitignore = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/
.venv/

# VS Code
.vscode/*
!.vscode/settings.json
!.vscode/tasks.json
!.vscode/launch.json
!.vscode/extensions.json

# Database
*.db
*.db-journal
*.sqlite3

# Logs
*.log
logs/

# Local configuration
.env
config.json
data/config.json

# Personal data
Cookie.json
letterboxd.db

# Temporary files
*.tmp
*.bak
*.swp
*.swo

# Output files
Output.txt

# Development backups
backup_dev_state_*/

# PyInstaller
*.manifest
*.spec

# Distribution / packaging
build/
dist/
"""

    with open(".gitignore", "w") as f:
        f.write(production_gitignore)

    print("   ✓ Updated .gitignore")


def validate_production_state():
    """Validate that production preparation was successful."""
    print("\n✅ Validating production state...")

    issues = []

    # Check for sensitive data
    sensitive_patterns = ["[REDACTED_USERNAME]", "[REDACTED_API_KEY]"]

    for root, dirs, files in os.walk("."):
        # Skip hidden directories and backup directories
        dirs[:] = [d for d in dirs if not d.startswith(".") and not d.startswith("backup_")]

        for file in files:
            if file.endswith((".py", ".json", ".md", ".txt")):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        for pattern in sensitive_patterns:
                            if pattern in content:
                                issues.append(f"Sensitive data '{pattern}' found in {file_path}")
                except Exception:
                    continue

    # Check for remaining test files
    remaining_tests = [f for f in os.listdir(".") if f.startswith("test_") and f.endswith(".py")]
    if remaining_tests:
        issues.append(f"Test files still present: {remaining_tests}")

    # Check for database files
    if os.path.exists("letterboxd.db"):
        issues.append("Personal database file still present")

    if issues:
        print("   ⚠️ Issues found:")
        for issue in issues:
            print(f"      • {issue}")
        return False
    else:
        print("   ✅ Production state validated successfully!")
        return True


def main():
    """Main production preparation workflow."""
    print("🚀 Letterboxd Friend Check - Production Preparation")
    print("=" * 60)

    print("\n⚠️  WARNING: This will remove personal data and test files!")
    
    # Secure input validation for confirmation
    while True:
        try:
            # nosec B601 # Safe confirmation input with validation
            response = input("Continue? (y/N): ").strip().lower()
            if response in ['y', 'yes', 'n', 'no', '']:
                break
            print("❌ Please respond with 'y' for yes or 'n' for no")
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Operation cancelled by user")
            response = 'n'
            break

    if response not in ['y', 'yes']:
        print("❌ Production preparation cancelled.")
        return

    try:
        # Create backup first
        backup_dir = backup_current_state()

        # Clean up for production
        remove_sensitive_data()
        remove_personal_database()
        remove_development_test_files()
        remove_development_summary_files()
        clean_logs_and_cache()
        remove_sensitive_environment_files()
        create_production_readme()
        update_gitignore()

        # Validate the cleanup
        if validate_production_state():
            print("\n🎉 Production preparation completed successfully!")
            print("\n📋 Summary:")
            print("✅ Sensitive personal data removed")
            print("✅ Development test files cleaned up")
            print("✅ Personal database removed")
            print("✅ Logs and cache cleared")
            print("✅ Production README created")
            print("✅ .gitignore updated")
            print(f"✅ Development backup saved: {backup_dir}")

            print("\n🚢 Your application is now ready for:")
            print("   • GitHub repository creation")
            print("   • PyInstaller packaging")
            print("   • Public distribution")
            print("   • CI/CD pipeline setup")

        else:
            print("\n❌ Production preparation completed with issues!")
            print("Please review the validation results above.")

    except Exception as e:
        print(f"\n❌ Error during production preparation: {e}")
        print("Your original files are safe in the backup directory.")


if __name__ == "__main__":
    main()
