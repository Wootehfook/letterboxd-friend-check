"""
TMDB API Integration for Letterboxd Friend Check App

This module provides functions to fetch movie details from the TMDB API.
"""

import os
import logging
import requests
import json

logger = logging.getLogger(__name__)

# TMDB API base URL and endpoints
TMDB_BASE_URL = "https://api.themoviedb.org/3"
SEARCH_MOVIE_URL = f"{TMDB_BASE_URL}/search/movie"
MOVIE_DETAILS_URL = f"{TMDB_BASE_URL}/movie"

# Request timeout constant (in seconds)
REQUEST_TIMEOUT = 10


# Get API key from environment or config
def get_api_key():
    # First try environment variable
    api_key = os.environ.get("TMDB_API_KEY")

    # If not in environment, try config file
    if not api_key:
        try:
            # Try different config locations
            config_paths = [
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"),
                os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "letterboxd_friend_check",
                    "data",
                    "config.json",
                ),
            ]

            for config_path in config_paths:
                if os.path.exists(config_path):
                    with open(config_path, "r") as f:
                        config = json.load(f)
                        if "tmdb_api_key" in config:
                            api_key = config["tmdb_api_key"]
                            break
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
        logger.warning("No TMDB API key found. Movie details will be limited to basic information.")
        logger.info("To get enhanced movie details from TMDB:")
        logger.info("1. Sign up for a free account at https://www.themoviedb.org/")
        logger.info("2. Get your API key from https://www.themoviedb.org/settings/api")
        logger.info("3. Add 'tmdb_api_key': 'your_key_here' to your config.json file")
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
        response = make_request(SEARCH_MOVIE_URL, params=params)
        if not response:
            return None

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

        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        return response.json()

    except Exception as e:
        logger.error(f"Error fetching TMDB details for movie ID {movie_id}: {e}")
        return movie  # Return just the search result if detailed fetch fails


def enrich_movie_data(movie_dict):
    """
    Enrich movie data with details from TMDB.

    Args:
        movie_dict (dict): Movie data dict with at least a 'title' key

    Returns:
        dict: The input dict enriched with TMDB data
    """
    if not movie_dict or not isinstance(movie_dict, dict) or "title" not in movie_dict:
        return movie_dict

    title = movie_dict["title"]
    year = None

    # Check if the title includes a year in parentheses
    import re

    match = re.search(r"(.+)\s+\((\d{4})\)$", title)
    if match:
        title = match.group(1)
        year = int(match.group(2))

    try:
        # Get movie details from TMDB
        tmdb_result = get_movie_details(title, year)
        if tmdb_result:
            # Add TMDB data to the movie dict
            movie_dict["tmdb_id"] = tmdb_result.get("id")
            movie_dict["overview"] = tmdb_result.get("overview")
            movie_dict["poster_path"] = tmdb_result.get("poster_path")
            movie_dict["backdrop_path"] = tmdb_result.get("backdrop_path")
            movie_dict["tmdb_rating"] = tmdb_result.get("vote_average")
            movie_dict["release_date"] = tmdb_result.get("release_date")
            movie_dict["runtime"] = tmdb_result.get("runtime")

            # Add genres if not already present
            if "genres" in tmdb_result and not movie_dict.get("genres"):
                movie_dict["genres"] = ", ".join([g["name"] for g in tmdb_result.get("genres", [])])
    except Exception as e:
        logger.error(f"Error enriching movie data for '{title}': {e}")

    return movie_dict


def bulk_enrich_movies(movies_list):
    """
    Enrich a list of movies with details from TMDB.

    Args:
        movies_list (list): List of movie dicts or strings

    Returns:
        list: Enriched list of movie dicts
    """
    if not movies_list:
        return []

    # Convert any string items to dicts with title key
    processed_movies = []
    for movie in movies_list:
        if isinstance(movie, str):
            processed_movies.append({"title": movie})
        elif isinstance(movie, dict) and "title" in movie:
            processed_movies.append(movie)

    # Enrich each movie
    enriched_movies = []
    for movie in processed_movies:
        enriched_movies.append(enrich_movie_data(movie))

    return enriched_movies
