"""
TMDB API integration for Letterboxd Friend Check App
Fetches movie details from The Movie Database (themoviedb.org)
"""

import re
import time
import logging
import requests
from typing import Dict, List, Optional

# Configure logging
logger = logging.getLogger(__name__)


class TMDBApi:
    """Class to handle TMDB API requests and data processing"""

    BASE_URL = "https://api.themoviedb.org/3"

    def __init__(self, api_key):
        """Initialize with API key"""
        self.api_key = api_key
        self.session = requests.Session()

        # Set up request parameters that will be used in all requests
        self.params = {"api_key": self.api_key, "language": "en-US", "include_adult": "false"}

        # Cache to avoid repeated API calls for the same movie
        self.movie_cache = {}

    def search_movie(self, title: str, year: Optional[int] = None) -> Optional[Dict]:
        """
        Search for a movie by title and optionally year
        Returns the best match movie data or None if not found
        """
        # Check cache first
        cache_key = f"{title}_{year if year else 'no_year'}"
        if cache_key in self.movie_cache:
            logger.debug(f"Using cached data for {title}")
            return self.movie_cache[cache_key]

        # Build search params
        search_params = self.params.copy()
        search_params["query"] = title
        if year:
            search_params["year"] = year

        try:
            # Make API request
            response = self.session.get(f"{self.BASE_URL}/search/movie", params=search_params)

            if response.status_code != 200:
                logger.error(f"TMDB API error: {response.status_code}, {response.text}")
                return None

            data = response.json()
            results = data.get("results", [])

            if not results:
                logger.warning(f"No TMDB results found for '{title}'")
                return None

            # Get the best match (first result)
            movie = results[0]

            # Fetch more details if we have an ID
            if movie.get("id"):
                details = self.get_movie_details(movie["id"])
                if details:
                    movie.update(details)

            # Save in cache
            self.movie_cache[cache_key] = movie

            # Be nice to the API - don't hammer it
            time.sleep(0.25)

            return movie

        except Exception as e:
            logger.error(f"Error searching TMDB for {title}: {str(e)}")
            return None

    def get_movie_details(self, movie_id: int) -> Optional[Dict]:
        """
        Get detailed information for a specific movie by ID
        Returns additional movie data or None if error
        """
        try:
            # Make API request
            response = self.session.get(f"{self.BASE_URL}/movie/{movie_id}", params=self.params)

            if response.status_code != 200:
                logger.error(f"TMDB API error: {response.status_code}, {response.text}")
                return None

            return response.json()

        except Exception as e:
            logger.error(f"Error fetching TMDB details for movie ID {movie_id}: {str(e)}")
            return None

    def enrich_movie_data(self, movie_data: Dict) -> Dict:
        """
        Enrich existing movie data with TMDB information
        Returns the original data updated with TMDB info
        """
        title = movie_data.get("title", "")
        year = None

        # Try to extract year if it's in the title format "Movie Title (YYYY)"
        year_match = re.search(r"\((\d{4})\)$", title)
        if year_match:
            year = int(year_match.group(1))
            # Clean title of the year part
            title = re.sub(r"\s*\(\d{4}\)$", "", title)

        # Search TMDB
        tmdb_data = self.search_movie(title, year)

        if not tmdb_data:
            return movie_data

        # Update movie_data with TMDB information
        tmdb_info = {
            "tmdb_id": tmdb_data.get("id"),
            "poster_path": tmdb_data.get("poster_path"),
            "overview": tmdb_data.get("overview"),
            "tmdb_rating": tmdb_data.get("vote_average"),
            "release_date": tmdb_data.get("release_date"),
            "runtime": tmdb_data.get("runtime"),
            "genres": (
                [genre["name"] for genre in tmdb_data.get("genres", [])]
                if "genres" in tmdb_data
                else None
            ),
            "backdrop_path": tmdb_data.get("backdrop_path"),
        }

        # Update director info if available
        if "credits" in tmdb_data:
            directors = [
                crew["name"]
                for crew in tmdb_data["credits"].get("crew", [])
                if crew.get("job") == "Director"
            ]
            if directors:
                tmdb_info["director"] = ", ".join(directors)

        # Update the movie data with TMDB info
        movie_data.update(tmdb_info)

        return movie_data

    def bulk_enrich_movies(self, movies: List[Dict]) -> List[Dict]:
        """
        Enrich a list of movie data with TMDB information
        Returns the updated list with TMDB details
        """
        enriched_movies = []

        for i, movie in enumerate(movies):
            if i % 10 == 0:
                logger.info(f"Enriching movie {i + 1}/{len(movies)} with TMDB data")

            enriched = self.enrich_movie_data(movie)
            enriched_movies.append(enriched)

        return enriched_movies


# Helper functions for external use
def create_tmdb_api(api_key: str) -> TMDBApi:
    """Create a new TMDB API instance with the given API key"""
    return TMDBApi(api_key=api_key)


def get_movie_details(
    title: str, year: Optional[int] = None, api_key: Optional[str] = None
) -> Optional[Dict]:
    """Get movie details from TMDB by title and optional year"""
    from letterboxd_friend_check.config import Config

    # Get API key from config if not provided
    if not api_key:
        config = Config()
        api_key = config.get("tmdb_api_key", "")

    # Ensure we have a valid API key
    if not api_key:
        raise ValueError("TMDB API key is required but was not provided")

    # Create a temporary API instance if no global one exists
    tmdb_api = create_tmdb_api(api_key)
    return tmdb_api.search_movie(title, year)


def enrich_movie_data(movie_data: Dict, api_key: Optional[str] = None) -> Dict:
    """Enrich existing movie data with TMDB info"""
    from letterboxd_friend_check.config import Config

    # Get API key from config if not provided
    if not api_key:
        config = Config()
        api_key = config.get("tmdb_api_key", "")

    # Ensure we have a valid API key
    if not api_key:
        raise ValueError("TMDB API key is required but was not provided")

    # Create a temporary API instance and enrich movie data
    tmdb_api = create_tmdb_api(api_key)
    return tmdb_api.enrich_movie_data(movie_data)


def bulk_enrich_movies(movies: List[Dict], api_key: Optional[str] = None) -> List[Dict]:
    """Enrich a list of movies with TMDB data"""
    from letterboxd_friend_check.config import Config

    # Get API key from config if not provided
    if not api_key:
        config = Config()
        api_key = config.get("tmdb_api_key", "")

    # Ensure we have a valid API key
    if not api_key:
        raise ValueError("TMDB API key is required but was not provided")

    # Create a temporary API instance if no global one exists
    tmdb_api = create_tmdb_api(api_key)
    return tmdb_api.bulk_enrich_movies(movies)
