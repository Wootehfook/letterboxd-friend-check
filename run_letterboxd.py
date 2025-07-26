#!/usr/bin/env python
"""
Launcher script for Letterboxd Friend Check application
This helps diagnose issues with launching the main application

Author: Woo T. Fook
Note: This application was built with assistance from AI

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import sys
import traceback
import os
import logging
from datetime import datetime

# Add the current directory to Python's path to ensure modules can be found
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Make sure logs directory exists
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

print("Letterboxd Friend Check Launcher")
print("-------------------------------")
print("Author: Woo T. Fook (Built with AI)")
print("Licensed under GNU GPL v3")
print(f"Launch date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

# Ensure we have the right directories
os.makedirs("letterboxd_friend_check/data", exist_ok=True)

# Handle config files - both config.json and Cookie.json
for config_file in ["config.json", "Cookie.json"]:
    source_path = os.path.join(current_dir, config_file)
    target_path = os.path.join(current_dir, "letterboxd_friend_check", "data", config_file)

    if os.path.exists(source_path):
        if not os.path.exists(target_path):
            print(f"Copying {config_file} to the package data directory...")
            try:
                import shutil

                shutil.copy(source_path, target_path)
                print(f"{config_file} copied successfully")
            except Exception as e:
                print(f"Error copying {config_file}: {e}")
        else:
            # Check if the root config file is newer than the one in the data directory
            source_mtime = os.path.getmtime(source_path)
            target_mtime = os.path.getmtime(target_path)

            if source_mtime > target_mtime:
                print(f"Updating {config_file} in the package data directory with newer version...")
                try:
                    import shutil

                    shutil.copy(source_path, target_path)
                    print(f"{config_file} updated successfully")
                except Exception as e:
                    print(f"Error updating {config_file}: {e}")
    else:
        print(f"Warning: {config_file} not found in the root directory")

try:
    print("\nAttempting to import and run the application...")
    logger.info("Starting Letterboxd Friend Check application")

    # Try importing required modules first to provide better error messages
    try:
        import tmdb_api  # noqa: F401

        logger.info("tmdb_api module imported successfully")
    except ImportError as e:
        logger.error(f"Failed to import tmdb_api: {e}")
        print(f"ERROR: Failed to import tmdb_api: {e}")
        raise

    try:
        logger.info("movie_database module imported successfully")
    except ImportError:
        raise

    # First, try importing from package structure
    try:
        from letterboxd_friend_check.app import main

        logger.info("Successfully imported from package structure")
    except ImportError:
        # If that fails, try to import directly from LBoxFriendCheck module
        print("Could not import from package, trying direct import...")
        logger.info("Attempting direct import from LBoxFriendCheck...")

        # Make sure the main file is in the path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)

        # Import the main GUI class directly and create a main function
        try:
            from LBoxFriendCheck import LetterboxdGUI

            def main():
                """Create and run the main application"""
                app = LetterboxdGUI()
                app.mainloop()

            logger.info("Successfully imported LBoxFriendCheck module")
        except ImportError as e:
            logger.error(f"Failed to import LBoxFriendCheck: {e}")
            raise

    print("\nStarting the application...")
    main()
    print("Application closed normally.")

except ImportError as e:
    error_msg = f"Failed to import application module: {e}"
    print(f"\nERROR: {error_msg}")
    logger.error(error_msg)
    print("Make sure you're running this script from the correct directory.")
    print("\nTrying to fix common issues...")

    # Create necessary directories if they don't exist
    os.makedirs("letterboxd_friend_check/data", exist_ok=True)

    # Check if the main Python file exists
    if not os.path.exists("LBoxFriendCheck.py"):
        print("ERROR: LBoxFriendCheck.py not found in the current directory.")
    else:
        print("LBoxFriendCheck.py found, but there might be import issues.")

    # Check for missing modules
    if not os.path.exists("tmdb_api.py"):
        print("ERROR: tmdb_api.py not found - this module is required!")

    if not os.path.exists("movie_database.py"):
        print("ERROR: movie_database.py not found - this module is required!")

    logger.error(traceback.format_exc())
    traceback.print_exc()

except Exception as e:
    error_msg = f"An exception occurred: {e}"
    print(f"\nERROR: {error_msg}")
    logger.error(error_msg)
    print("\nDetailed traceback:")
    logger.error(traceback.format_exc())
    traceback.print_exc()

print("\n" + "-" * 60)
print("If you encountered errors, please check:")
print("1. Python has all required packages installed (run 'pip install -r requirements.txt')")
print("2. config.json and Cookie.json files exist and are valid")
print("3. The application directory structure is intact")
print("\nOptional: For enhanced movie details from TMDB:")
print("4. Add your TMDB API key to config.json (see config_template.json for instructions)")
print("   - Sign up at https://www.themoviedb.org/")
print("   - Get API key from https://www.themoviedb.org/settings/api")
print('   - Update "tmdb_api_key": "your_key_here" in config.json')
print("-" * 60)
try:
    input("\nPress Enter to exit...")  # nosec B601 # Safe exit prompt
except (EOFError, KeyboardInterrupt):
    pass  # Allow graceful exit
