#!/usr/bin/env python
"""
GitHub Repository Setup Script for Letterboxd Friend Check

This script helps you prepare the project for GitHub and create a professional repository.

Usage:
    python setup_github_repo.py

What it does:
1. Initializes git repository
2. Creates .gitignore (if needed)
3. Creates release notes
4. Provides git commands for setup
"""

import os
import json
import subprocess


def check_git_installed():
    """Check if git is installed and available."""
    print("🔍 Checking git installation...")
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✓ {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        print("   ❌ Git not found. Please install Git from https://git-scm.com/")
        return False
    return False


def initialize_git_repo():
    """Initialize git repository if not already done."""
    print("\n📁 Initializing git repository...")

    if os.path.exists(".git"):
        print("   ✓ Git repository already exists")
        return True

    try:
        subprocess.run(["git", "init"], check=True, capture_output=True)
        print("   ✓ Git repository initialized")

        # Set main as default branch
        subprocess.run(["git", "branch", "-M", "main"], check=True, capture_output=True)
        print("   ✓ Set main as default branch")

        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error initializing git: {e}")
        return False


def create_release_notes():
    """Create release notes for v1.0.0."""
    print("\n📝 Creating release notes...")

    release_notes = """# Letterboxd Friend Check v1.0.0 🎬

Welcome to the first official release of Letterboxd Friend Check! This desktop application
helps you discover movies you and your friends both want to watch by comparing your
Letterboxd watchlists.

## ✨ Features

### Core Functionality
- 🎭 **Compare Watchlists**: Find movies you and your friends both want to watch
- 👥 **Friends Management**: Select specific friends to sync with
- 💾 **Data Persistence**: Your data is saved locally between sessions
- 🔗 **Direct Links**: Click to open movies on Letterboxd

### User Interface
- 🎨 **Modern GUI**: Professional interface with light and dark themes
- ♿ **Accessibility**: WCAG AA compliant for all users
- 🖱️ **Smooth Scrolling**: Mouse wheel support throughout the application
- 📱 **Responsive Design**: Adapts to window resizing

### Advanced Features
- 🎭 **TMDB Integration**: Optional movie posters, ratings, and details
- ⚡ **Background Sync**: Non-blocking operations with cancel support
- 📊 **Large Watchlist Support**: Handles 500+ movie watchlists efficiently
- 🛡️ **Privacy Focused**: No login required, only public data accessed

## 🚀 Quick Start

### Windows Users (Recommended)
1. Download `LetterboxdFriendCheck.exe` from the releases
2. Double-click to run (no Python installation needed!)
3. Enter your Letterboxd username
4. Click "Fetch Friends" and select friends to compare with
5. Click "Sync Watchlists" to find common movies

### Python Users
1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python run_letterboxd.py`

## 🎭 Optional TMDB Integration

For enhanced movie details (posters, ratings, genres):
1. Sign up at [TMDB](https://www.themoviedb.org/) (free)
2. Get your API key from [Account Settings](https://www.themoviedb.org/settings/api)
3. Enter it in the Setup tab

## 📋 System Requirements

- **Windows**: Windows 10 or later (executable)
- **Python**: Python 3.8+ (if running from source)
- **Internet**: Required for accessing Letterboxd data
- **Profile**: Public Letterboxd profile

## 🔒 Privacy & Security

- ✅ Only accesses **public** Letterboxd data
- ✅ No login or authentication required
- ✅ All data stored **locally** on your computer
- ✅ Respects Letterboxd's rate limits
- ✅ No personal data transmitted

## 🐛 Known Issues

- Windows Defender may show a warning (executable is unsigned)
- Some antivirus software may flag the executable
- Large friend lists (100+) may take time to load

## 📞 Support

Having issues? Check out:
- [Installation Guide](INSTALL.md) (included with executable)
- [GitHub Issues](https://github.com/yourusername/letterboxd-friend-check/issues)
- [README Documentation](README.md)

## 🙏 Credits

- Built with ❤️ using Python, tkinter, and AI assistance
- Movie data powered by [TMDB](https://www.themoviedb.org/)
- Letterboxd integration via web scraping
- Licensed under GNU GPL v3.0

## 🔄 What's Next?

We're working on:
- Additional movie metadata
- Export functionality
- Performance improvements
- Cross-platform installers

---

**Download the executable below and start discovering movies with your friends! 🍿**

*Note: This application is not affiliated with Letterboxd or TMDB.*"""

    with open("RELEASE_NOTES.md", "w", encoding="utf-8") as f:
        f.write(release_notes)

    print("   ✓ Created RELEASE_NOTES.md")


def create_github_instructions():
    """Create step-by-step GitHub setup instructions."""
    print("\n📋 Creating GitHub setup instructions...")

    instructions = """# 🚀 GitHub Repository Setup Instructions

Generated automatically for repository setup.

## Step 1: Create GitHub Repository

1. Go to [GitHub](https://github.com) and log in
2. Click the "+" icon → "New repository"
3. Repository name: `letterboxd-friend-check`
4. Description: `A Python desktop app to compare Letterboxd watchlists with friends`
5. Set as **Public** repository
6. **DO NOT** initialize with README (we have one)
7. Click "Create repository"

## Step 2: Connect Local Repository

Open a terminal in this directory and run these commands:

```bash
# Add all files to git
git add .

# Create initial commit
git commit -m "Initial release - Letterboxd Friend Check v1.0.0"

# Add your GitHub repository as remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/letterboxd-friend-check.git

# Push to GitHub
git push -u origin main
```

## Step 3: Create GitHub Release

1. Go to your repository on GitHub
2. Click "Releases" → "Create a new release"
3. **Tag version**: `v1.0.0`
4. **Release title**: `Letterboxd Friend Check v1.0.0`
5. **Description**: Copy content from `RELEASE_NOTES.md`
6. **Attach files**: Upload `distribution/LetterboxdFriendCheck.exe`
7. Click "Publish release"

## Step 4: Repository Settings (Recommended)

### About Section
- Description: "A Python desktop app to compare Letterboxd watchlists with friends"
- Website: (leave blank initially)
- Topics: `letterboxd`, `python`, `desktop-app`, `movies`, `watchlist`, `tkinter`

### README Badge (Optional)
Add this to your README.md:
```markdown
![GitHub release](https://img.shields.io/github/v/release/YOUR_USERNAME/letterboxd-friend-check)
![GitHub downloads](https://img.shields.io/github/downloads/YOUR_USERNAME/letterboxd-friend-check/total)
```

### Enable Issues
- Go to Settings → General
- Check "Issues" under Features

## Step 5: Post-Release Tasks

1. **Test the release**: Download and test your own executable
2. **Share it**: Post on social media, Reddit, etc.
3. **Monitor**: Watch for issues and user feedback
4. **Update**: Plan future releases based on feedback

## Quick Command Reference

```bash
# Check git status
git status

# Stage all changes
git add .

# Commit changes
git commit -m "Your commit message"

# Push to GitHub
git push

# Check git log
git log --oneline

# Create new branch for features
git checkout -b feature-name

# Switch back to main
git checkout main
```

## 🎉 You're Ready!

Your Letterboxd Friend Check application is now ready for the world! 

Remember to:
- ✅ Test the executable on different machines
- ✅ Respond to user issues promptly
- ✅ Keep the README updated
- ✅ Plan future enhancements

**Congratulations on creating and deploying a professional desktop application! 🏆**"""

    with open("GITHUB_SETUP.md", "w", encoding="utf-8") as f:
        f.write(instructions)

    print("   ✓ Created GITHUB_SETUP.md")


def check_files_ready():
    """Check that all necessary files are ready for GitHub."""
    print("\n✅ Checking files for GitHub readiness...")

    essential_files = [
        "README.md",
        "LICENSE",
        "config_template.json",
        "requirements.txt",
        ".gitignore",
        "LBoxFriendCheck.py",
        "run_letterboxd.py",
        "distribution/LetterboxdFriendCheck.exe",
    ]

    missing_files = []
    for file in essential_files:
        if os.path.exists(file):
            print(f"   ✓ {file}")
        else:
            print(f"   ❌ {file}")
            missing_files.append(file)

    if missing_files:
        print(f"\n⚠️  Missing files: {missing_files}")
        return False
    else:
        print("\n🎉 All essential files ready for GitHub!")
        return True


def main():
    """Main setup workflow."""
    print("🚀 Letterboxd Friend Check - GitHub Setup")
    print("=" * 50)

    # Check prerequisites
    if not check_git_installed():
        return 1

    # Initialize git repository
    if not initialize_git_repo():
        return 1

    # Create release documentation
    create_release_notes()
    create_github_instructions()

    # Verify readiness
    if not check_files_ready():
        print("\n❌ Please ensure all files are present before proceeding.")
        return 1

    print("\n🎯 Next Steps:")
    print("1. Review the files created:")
    print("   - RELEASE_NOTES.md (copy this to GitHub release)")
    print("   - GITHUB_SETUP.md (follow these instructions)")
    print("\n2. Create your GitHub repository")
    print("3. Follow the instructions in GITHUB_SETUP.md")
    print("4. Upload your executable to the release")

    print("\n🎉 Your application is ready for GitHub! 🚀")

    return 0


if __name__ == "__main__":
    exit(main())
