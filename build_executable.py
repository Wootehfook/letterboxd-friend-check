#!/usr/bin/env python
"""
Build Script for Letterboxd Friend Check Application

This script creates standalone executables using PyInstaller for distribution.

Usage:
    python build_executable.py

Output:
    - Creates dist/ directory with executable
    - Creates build/ directory with temporary files
    - Generates .spec file for PyInstaller configuration
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")

    try:
        import PyInstaller

        print(f"   ✓ PyInstaller {PyInstaller.__version__} found")
    except ImportError:
        print("   ❌ PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("   ✓ PyInstaller installed")

    # Check main application files
    required_files = [
        "LBoxFriendCheck.py",
        "run_letterboxd.py",
        "tmdb_api.py",
        "movie_database.py",
        "requirements.txt",
    ]

    for file in required_files:
        if os.path.exists(file):
            print(f"   ✓ {file} found")
        else:
            print(f"   ❌ {file} missing")
            return False

    return True


def clean_previous_builds():
    """Clean up previous build artifacts."""
    print("\n🧹 Cleaning previous builds...")

    dirs_to_clean = ["build", "dist", "__pycache__"]
    files_to_clean = ["*.spec"]

    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"   ✓ Removed {dir_name}/")

    # Remove .spec files
    for spec_file in Path(".").glob("*.spec"):
        spec_file.unlink()
        print(f"   ✓ Removed {spec_file}")


def create_pyinstaller_spec():
    """Create PyInstaller spec file for the application."""
    print("\n📄 Creating PyInstaller spec file...")

    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Data files to include
datas = [
    ('config_template.json', '.'),
    ('LICENSE', '.'),
    ('README.md', '.'),
]

# Hidden imports that PyInstaller might miss
hiddenimports = [
    'tkinter',
    'tkinter.ttk',
    'requests',
    'beautifulsoup4',
    'bs4',
    'sqlite3',
    'json',
    'threading',
    'queue',
    'webbrowser',
    'urllib.parse',
    'datetime',
    'tmdbsimple',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'io',
    'base64'
]

a = Analysis(
    ['run_letterboxd.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LetterboxdFriendCheck',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None  # Add icon path here if you have one
)
"""

    with open("letterboxd_friend_check.spec", "w") as f:
        f.write(spec_content)

    print("   ✓ Created letterboxd_friend_check.spec")


def build_executable():
    """Build the executable using PyInstaller."""
    print("\n🔨 Building executable...")

    try:
        # Build using the spec file
        cmd = [
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            "--noconfirm",
            "letterboxd_friend_check.spec",
        ]

        print(f"   Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("   ✅ Build completed successfully!")
            return True
        else:
            print("   ❌ Build failed!")
            print(f"   Error: {result.stderr}")
            return False

    except Exception as e:
        print(f"   ❌ Build error: {e}")
        return False


def create_distribution_package():
    """Create a clean distribution package."""
    print("\n📦 Creating distribution package...")

    if not os.path.exists("dist/LetterboxdFriendCheck.exe"):
        print("   ❌ Executable not found in dist/")
        return False

    # Create distribution directory
    dist_dir = "distribution"
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir)

    # Copy executable
    shutil.copy2("dist/LetterboxdFriendCheck.exe", f"{dist_dir}/LetterboxdFriendCheck.exe")
    print("   ✓ Copied executable")

    # Copy essential files
    essential_files = ["README.md", "LICENSE", "requirements.txt", "config_template.json"]

    for file in essential_files:
        if os.path.exists(file):
            shutil.copy2(file, f"{dist_dir}/{file}")
            print(f"   ✓ Copied {file}")

    # Create installation instructions
    install_instructions = """# Letterboxd Friend Check - Installation Instructions

## Windows Installation

1. **Run the Application**
   - Double-click `LetterboxdFriendCheck.exe` to start
   - No Python installation required!

2. **First Run Setup**
   - Enter your Letterboxd username
   - (Optional) Add TMDB API key for enhanced features
   - The application will create a config file automatically

3. **TMDB API Key (Optional)**
   - Sign up at https://www.themoviedb.org/
   - Get free API key from https://www.themoviedb.org/settings/api
   - Enter it in the Setup tab for movie posters and details

## Troubleshooting

- **Windows Defender Warning**: The executable is unsigned. Click "More info" then "Run anyway"
- **Antivirus Warning**: Add the executable to your antivirus whitelist
- **Application Won't Start**: Ensure you have internet connection for Letterboxd access

## Files Included

- `LetterboxdFriendCheck.exe` - Main application
- `README.md` - Full documentation
- `LICENSE` - Software license
- `config_template.json` - Configuration reference

## Support

For issues, please check the README.md file or visit the project repository.
"""

    with open(f"{dist_dir}/INSTALL.md", "w", encoding="utf-8") as f:
        f.write(install_instructions)
    print("   ✓ Created INSTALL.md")

    # Get file sizes
    exe_size = os.path.getsize(f"{dist_dir}/LetterboxdFriendCheck.exe")
    exe_size_mb = exe_size / (1024 * 1024)

    print(f"\n📊 Distribution Summary:")
    print(f"   • Executable size: {exe_size_mb:.1f} MB")
    print(f"   • Distribution directory: {dist_dir}/")
    print(f"   • Ready for distribution!")

    return True


def main():
    """Main build process."""
    print("🚀 Letterboxd Friend Check - Build Script")
    print("=" * 50)

    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed!")
        return 1

    # Clean previous builds
    clean_previous_builds()

    # Create spec file
    create_pyinstaller_spec()

    # Build executable
    if not build_executable():
        print("\n❌ Build failed!")
        return 1

    # Create distribution package
    if not create_distribution_package():
        print("\n❌ Distribution package creation failed!")
        return 1

    print("\n🎉 Build completed successfully!")
    print("\n📋 Next Steps:")
    print("   1. Test the executable in distribution/")
    print("   2. Create installer (optional)")
    print("   3. Upload to GitHub releases")
    print("   4. Create release notes")

    return 0


if __name__ == "__main__":
    sys.exit(main())
