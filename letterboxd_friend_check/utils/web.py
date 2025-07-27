"""
Web scraping utilities for the Letterboxd Friend Check application.

This module handles all web-related functionality, including scraping of movie
and user data from Letterboxd. All functionality works without requiring authentication
as Letterboxd allows unauthenticated access to public user data.
"""

import time
import random
import re
import logging
import requests
from bs4 import BeautifulSoup
from typing import Set, List, Optional, Dict, Any

# Configure logger
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://letterboxd.com"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (compatible; LetterboxdWatchlistBot/1.0; +https://github.com/yourusername)"
)

# Global session for requests
session = requests.Session()
# Set default headers
session.headers.update({"User-Agent": DEFAULT_USER_AGENT})


def get_watchlist_count(username: str) -> Optional[int]:
    """
    Scrapes the user's watchlist page for the js-watchlist-count element
    to get the total number of movies.

    Args:
        username: Letterboxd username

    Returns:
        Total count of movies in the watchlist, or None if not found
    """
    url = f"{BASE_URL}/{username}/watchlist/"
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    try:
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        count_tag = soup.find("span", class_="js-watchlist-count")
        if count_tag:
            # Extract digits from text, e.g. '7,727 films' or '7,727\u00a0films'
            match = re.search(r"([\d,]+)", count_tag.text)
            if match:
                count_str = match.group(1).replace(",", "")
                return int(count_str)
        return None
    except Exception as e:
        logger.error(f"Error fetching watchlist count for {username}: {e}")
        return None


def get_watchlist(username: str, limit: Optional[int] = None) -> Set[str]:
    """
    Fetches the watchlist for a given Letterboxd username using pagination.

    Args:
        username: Letterboxd username
        limit: Optional limit on number of movies to fetch (for testing)

    Returns:
        Set of movie titles in the watchlist
    """
    movies = set()
    page = 1
    headers = {"User-Agent": DEFAULT_USER_AGENT}

    logger.info(f"Starting to fetch watchlist for {username}...")
    # Get total movie count for percentage display
    total_count = get_watchlist_count(username)
    last_percent = -1

    def print_progress(fetched: int, total: Optional[int]) -> None:
        nonlocal last_percent
        if total and isinstance(total, int) and total > 0:
            percent = min(100, int((fetched / total) * 100))
            if percent != last_percent:
                print(
                    f"\rFetching watchlist for {username}: {percent}% ({fetched}/{total})",
                    end="",
                    flush=True,
                )
                last_percent = percent
        else:
            if fetched % 10 == 0 or fetched == 1:
                print(
                    f"\rFetching watchlist for {username}: {fetched} movies fetched",
                    end="",
                    flush=True,
                )

    while True:
        # Check if we've reached the specified limit
        if limit and len(movies) >= limit:
            logger.info(f"Reached specified limit of {limit} movies for {username}")
            break

        url = f"{BASE_URL}/{username}/watchlist/page/{page}/"
        logger.debug(f"Fetching page {page} for {username}: {url}")

        try:
            response = session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            poster_items = soup.select("li.poster-container")

            if not poster_items:
                logger.info(
                    f"No more movies found for {username} on page {page}. Ending pagination."
                )
                break

            page_movie_count = 0
            for item in poster_items:
                anchor = item.find("a", attrs={"data-film-name": True})
                if anchor:
                    title = anchor.get("data-film-name")
                    if title:
                        movies.add(title)
                        page_movie_count += 1
                        print_progress(len(movies), total_count)
                else:
                    img = item.find("img", alt=True)
                    if img:
                        title = img.get("alt")
                        if title:
                            movies.add(title)
                            page_movie_count += 1
                            print_progress(len(movies), total_count)

                # Check if we've reached the specified limit
                if limit and len(movies) >= limit:
                    break

            logger.info(f"Fetched {page_movie_count} movies from page {page} for {username}.")

            page += 1
            # nosec B311: random used for rate limiting, not cryptography
            sleep_time = random.uniform(1, 1.5)  # nosec B311
            logger.debug(f"Sleeping for {sleep_time:.2f} seconds to avoid rate limiting.")
            time.sleep(sleep_time)

        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                logger.warning(
                    f"Rate limited by Letterboxd (429 Too Many Requests) on page {page}. "
                    "Stopping further requests."
                )
                break
            else:
                logger.error(f"HTTP error scraping watchlist page {page} for {username}: {e}")
                break

        except KeyboardInterrupt:
            print("\nFetch interrupted by user (Ctrl+C). Exiting...")
            raise

        except Exception as e:
            logger.error(f"Error scraping watchlist page {page} for {username}: {e}")
            break

    if (
        total_count
        and isinstance(total_count, int)
        and total_count > 0
        and len(movies) == total_count
    ):
        print(
            f"\rFetching watchlist for {username}: 100% ({len(movies)}/{total_count}) Done!        "
        )
    else:
        print(f"\rFetching watchlist for {username}: {len(movies)} movies fetched. Done!        ")

    logger.info(f"Finished fetching watchlist for {username}. Total movies fetched: {len(movies)}.")
    return movies


def get_friends(username: str) -> List[str]:
    """
    Fetches the list of friends for a given Letterboxd username.

    Args:
        username: Letterboxd username

    Returns:
        List of friend usernames
    """
    url = f"{BASE_URL}/{username}/following/"
    friends = []
    headers = {"User-Agent": DEFAULT_USER_AGENT}

    try:
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all friend profile links
        for a in soup.select("a.avatar"):  # Updated selector for friend avatars
            href = a.get("href")
            if href:
                friend = href.strip("/").split("/")[0]
                if friend and friend != username:
                    friends.append(friend)

    except Exception as e:
        logger.error(f"Error fetching friends for {username}: {e}")

    return friends


def fetch_movie_data_from_letterboxd(url: str) -> Dict[str, Any]:
    """
    Fetch movie data from a Letterboxd movie page.

    Args:
        url: Full URL to the Letterboxd movie page

    Returns:
        Dictionary containing movie details (director, genres, rating, synopsis)
    """
    try:
        headers = {"User-Agent": DEFAULT_USER_AGENT}
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        movie_data = {}

        # Extract director
        director_elem = soup.select_one('span[itemprop="director"]')
        if director_elem:
            name_elem = director_elem.select_one('a[itemprop="name"]')
            if name_elem:
                movie_data["director"] = name_elem.text.strip()

        # Extract genres
        genre_elems = soup.select('div.text-sluglist a[href*="/films/genre/"]')
        if genre_elems:
            genres = [elem.text.strip() for elem in genre_elems]
            movie_data["genres"] = ", ".join(genres)

        # Extract rating
        rating_elem = soup.select_one('meta[name="twitter:data2"]')
        if rating_elem and "content" in rating_elem.attrs:
            movie_data["rating"] = rating_elem["content"].strip()

        # Extract synopsis
        synopsis_elem = soup.select_one('div[id="synopsis"] div.body-text')
        if synopsis_elem:
            movie_data["synopsis"] = synopsis_elem.text.strip()

        return movie_data

    except Exception as e:
        logger.error(f"Error fetching movie data from {url}: {e}")
        return {}


def generate_letterboxd_url(title: str, year: str = "") -> str:
    """
    Generate a Letterboxd URL for a movie.

    Args:
        title: Movie title
        year: Optional year of release

    Returns:
        URL to the movie's Letterboxd page
    """
    # Convert title to URL-friendly slug
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9\s]", "", slug)  # Remove non-alphanumeric
    slug = re.sub(r"\s+", "-", slug)  # Replace spaces with hyphens

    if year:
        return f"{BASE_URL}/film/{slug}-{year}/"
    else:
        return f"{BASE_URL}/film/{slug}/"
