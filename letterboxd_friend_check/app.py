"""
Main application module for Letterboxd Friend Check App

This module provides both TMDB API integration and the main application entry point.
"""

import logging
import requests
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# TMDB API base URL and endpoints
TMDB_BASE_URL = "https://api.themoviedb.org/3"
SEARCH_MOVIE_URL = f"{TMDB_BASE_URL}/search/movie"
MOVIE_DETAILS_URL = f"{TMDB_BASE_URL}/movie"


# Get API key from environment or config
def get_api_key():
    # First try environment variable
    api_key = os.environ.get("TMDB_API_KEY")

    # If not in environment, try config file
    if not api_key:
        try:
            import json

            config_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
            )
            config_path = os.path.join(config_dir, "config.json")

            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
                    api_key = config.get("tmdb_api_key")
        except Exception as e:
            logger.error(f"Error loading TMDB API key from config: {e}")

    return api_key


def search_movie(title, year=None):
    """
    Search for a movie on TMDB by title and optional year.

    Args:
        title (str): The movie title to search for
        year (int, optional): The release year to filter results

    Returns:
        dict: The first matching movie result, or None if no match found
    """
    api_key = get_api_key()
    if not api_key:
        logger.error("No TMDB API key found. Cannot search for movie.")
        return None

    params = {
        "api_key": api_key,
        "query": title,
        "language": "en-US",
        "page": 1,
        "include_adult": False,
    }

    # Add year filter if provided
    if year:
        params["year"] = year

    try:
        response = requests.get(SEARCH_MOVIE_URL, params=params)
        response.raise_for_status()

        results = response.json().get("results", [])
        if results:
            return results[0]  # Return the first (most relevant) result
        return None

    except Exception as e:
        logger.error(f"Error searching TMDB for '{title}' ({year}): {e}")
        return None


def get_movie_details(title, year=None):
    """
    Get detailed information about a movie from TMDB.

    Args:
        title (str): The movie title to search for
        year (int, optional): The release year to filter results

    Returns:
        dict: Detailed movie information, or None if not found
    """
    # First search for the movie to get its ID
    movie = search_movie(title, year)
    if not movie:
        return None

    movie_id = movie.get("id")
    if not movie_id:
        return None

    api_key = get_api_key()
    if not api_key:
        return movie  # Return just the search result if no API key for detailed fetch

    # Fetch detailed movie information
    try:
        url = f"{MOVIE_DETAILS_URL}/{movie_id}"
        params = {"api_key": api_key, "language": "en-US", "append_to_response": "credits,keywords"}

        response = requests.get(url, params=params)
        response.raise_for_status()

        return response.json()

    except Exception as e:
        logger.error(f"Error fetching TMDB details for movie ID {movie_id}: {e}")
        return movie  # Return just the search result if detailed fetch fails


def main():
    """
    Main entry point for the Letterboxd Friend Check application
    """
    try:
        # Add the parent directory to the path so we can import the LBoxFriendCheck module
        parent_dir = str(Path(__file__).resolve().parent.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        # Import the main application from LBoxFriendCheck
        from LBoxFriendCheck import main as app_main

        # Run the application
        app_main()

    except Exception as e:
        logger.error(f"Error in application startup: {e}")
        import traceback

        logger.error(traceback.format_exc())
        print(f"Error starting the application: {e}")
        print(traceback.format_exc())

    logger.info("Application closed")


# Allow running directly with "python -m letterboxd_friend_check.app"
if __name__ == "__main__":
    main()
