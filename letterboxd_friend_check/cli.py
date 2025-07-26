#!/usr/bin/env python
"""
Command-line interface for the Letterboxd Friend Check application
"""
import sys
import os
import traceback
from datetime import datetime


def main():
    """Main entry point for the Letterboxd Friend Check application"""
    print("Letterboxd Friend Check")
    print("---------------------")
    print(f"Launch date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")

    try:
        # Import the main application module
        from letterboxd_friend_check.app import main as app_main

        print("\nStarting the application...")
        app_main()
        print("Application closed normally.")
    except ImportError as e:
        print(f"\nERROR: Failed to import application module: {e}")
        print("Make sure the package is correctly installed.")
        traceback.print_exc()
    except Exception as e:
        print(f"\nERROR: An exception occurred: {e}")
        print("\nDetailed traceback:")
        traceback.print_exc()


if __name__ == "__main__":
    main()
