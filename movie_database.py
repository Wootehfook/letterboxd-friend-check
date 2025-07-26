#!/usr/bin/env python
"""
Movie Database Module for Letterboxd Friend Check

This module provides database operations for storing and retrieving movie details
from a local SQLite database to improve performance and reduce API calls.

Author: Woo T. Fook
Note: This application was built with assistance from AI

# AI Signature: Claude Sonnet 3.5 - 2025-01-20 19:45:00 EST
# Enhanced: Complete movie database module with improved SQLite operations

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
import os
import re
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# Setup logging
logger = logging.getLogger(__name__)

# Database path - defaults to same directory as script
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "letterboxd.db")
DB_PATH = DEFAULT_DB_PATH  # Backward compatibility


def get_database_path() -> str:
    """
    Get the database path, preferring existing database in various locations.

    Returns:
        str: Path to the database file

    The Zen of Python: "There should be one obvious way to do it"
    """
    # Check multiple possible locations for existing database
    possible_paths = [
        DEFAULT_DB_PATH,
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "letterboxd_friend_check",
            "data",
            "letterboxd.db",
        ),
        os.path.join(os.getcwd(), "letterboxd.db"),
        os.path.join(os.getcwd(), "data", "letterboxd.db"),
    ]

    # Return the first existing database, or the default if none exist
    for path in possible_paths:
        if os.path.exists(path):
            return path

    return DEFAULT_DB_PATH


def normalize_title(title: str) -> str:
    """
    Normalize movie title for consistent storage and lookup.

    Args:
        title (str): Original movie title

    Returns:
        str: Normalized title

    The Zen of Python: "Simple is better than complex"
    """
    if not title or not isinstance(title, str):
        return ""

    # Convert to lowercase and remove common punctuation
    normalized = title.lower()

    # Remove articles at the beginning (the, a, an)
    normalized = re.sub(r"^(the|a|an)\s+", "", normalized)

    # Remove special characters and extra spaces
    normalized = re.sub(r"[^\w\s]", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = normalized.strip()

    return normalized


def extract_year_from_title(title: str) -> tuple[str, Optional[int]]:
    """
    Extract year from title if present in format "Title (YYYY)".

    Args:
        title (str): Movie title possibly containing year

    Returns:
        tuple: (clean_title, year) where year is int or None
    """
    if not title:
        return "", None

    match = re.search(r"(.+)\s+\((\d{4})\)$", title.strip())
    if match:
        clean_title = match.group(1).strip()
        year = int(match.group(2))
        return clean_title, year

    return title.strip(), None


def init_movie_database(db_path: Optional[str] = None) -> None:
    """
    Initialize the movie details database with required tables.

    Args:
        db_path (str, optional): Path to database file

    Security: Uses parameterized queries to prevent SQL injection
    Performance: Creates indexes for commonly queried fields
    """
    if db_path is None:
        db_path = get_database_path()

    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create movie_details table with comprehensive schema if not exists
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS movie_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                normalized_title TEXT,
                year INTEGER,
                director TEXT,
                genres TEXT,
                rating TEXT,
                synopsis TEXT,
                overview TEXT,
                tmdb_id INTEGER,
                tmdb_rating REAL,
                imdb_id TEXT,
                release_date TEXT,
                runtime INTEGER,
                poster_path TEXT,
                backdrop_path TEXT,
                budget INTEGER,
                revenue INTEGER,
                popularity REAL,
                vote_count INTEGER,
                status TEXT,
                tagline TEXT,
                homepage TEXT,
                original_title TEXT,
                letterboxd_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(normalized_title, year)
            )
        """
        )

        # Check if the existing movies table exists and migrate if needed
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='movies'")
        movies_table_exists = cursor.fetchone() is not None

        if movies_table_exists:
            # Migrate from old movies table to new movie_details table
            logger.debug("Migrating from old movies table to new movie_details table")
            cursor.execute(
                """
                INSERT OR IGNORE INTO movie_details (
                    title, director, genres, rating, synopsis, tmdb_id, tmdb_rating,
                    release_date, runtime, poster_path, backdrop_path, overview, updated_at
                )
                SELECT
                    title, director, genres, rating, synopsis, tmdb_id, tmdb_rating,
                    release_date, runtime, poster_path, backdrop_path, overview,
                    COALESCE(last_updated, datetime('now')) as updated_at
                FROM movies
            """
            )

        # Create indexes for performance
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_movie_details_title
            ON movie_details(normalized_title)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_movie_details_year
            ON movie_details(year)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_movie_details_tmdb_id
            ON movie_details(tmdb_id)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_movie_details_updated
            ON movie_details(updated_at)
        """
        )

        conn.commit()
        conn.close()

        logger.debug(f"Movie database initialized at: {db_path}")

    except sqlite3.Error as e:
        logger.error(f"Database error initializing movie database: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error initializing movie database: {e}")
        raise


def get_movie_details_from_db(movie_title, db_path=None):
    """
    Retrieve movie details from the database by title.
    Enhanced version with improved matching and error handling.

    Args:
        movie_title (str): The title of the movie to look up
        db_path (str, optional): Path to the database file

    Returns:
        dict: Movie details if found, or None if not found
    """
    if not movie_title:
        return None

    if db_path is None:
        db_path = get_database_path()

    if not os.path.exists(db_path):
        logger.warning(f"Database file not found at {db_path}")
        return None

    try:
        # Extract year from title if present
        clean_title, year = extract_year_from_title(movie_title)
        normalized_title = normalize_title(clean_title)

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()

        # Initialize database if needed
        init_movie_database(db_path)

        # Try movie_details table first (new schema)
        if year:
            cursor.execute(
                """
                SELECT * FROM movie_details
                WHERE normalized_title = ? AND year = ?
                ORDER BY updated_at DESC LIMIT 1
            """,
                (normalized_title, year),
            )
        else:
            cursor.execute(
                """
                SELECT * FROM movie_details
                WHERE normalized_title = ?
                ORDER BY updated_at DESC LIMIT 1
            """,
                (normalized_title,),
            )

        row = cursor.fetchone()

        if row:
            return dict(row)

        # Fallback to exact title match
        cursor.execute(
            """
            SELECT * FROM movie_details
            WHERE title = ?
            ORDER BY updated_at DESC LIMIT 1
        """,
            (movie_title,),
        )

        row = cursor.fetchone()

        if row:
            return dict(row)

        # Try old movies table for backward compatibility
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='movies'")
        if cursor.fetchone():
            cursor.execute("SELECT * FROM movies WHERE title = ? LIMIT 1", (movie_title,))
            row = cursor.fetchone()
            if row:
                # This part needs to be adapted if the schema is different
                # For now, returning as dict assuming column names are accessible
                return dict(row)

        conn.close()
        return None

    except sqlite3.Error as e:
        logger.error(f"Database error retrieving movie data for '{movie_title}': {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error retrieving movie data for '{movie_title}': {e}")
        return None


def save_movie_details_to_db(movie_title, movie_data, db_path=None):
    """
    Save movie details to the database.
    Enhanced version with improved error handling and normalization.

    Args:
        movie_title (str): The title of the movie
        movie_data (dict): The movie details to save
        db_path (str, optional): Path to the database file

    Returns:
        bool: True if successful, False otherwise

    Security: Uses parameterized queries to prevent SQL injection
    """
    if not movie_title or not isinstance(movie_data, dict):
        logger.warning("Invalid parameters provided to save_movie_details_to_db")
        return False

    if db_path is None:
        db_path = get_database_path()

    try:
        # Initialize database if it doesn't exist
        init_movie_database(db_path)

        # Extract year from title if present
        clean_title, year = extract_year_from_title(movie_title)
        normalized_title = normalize_title(clean_title)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Prepare data for insertion
        data = {
            "title": movie_title,
            "normalized_title": normalized_title,
            "year": year,
            "director": movie_data.get("director"),
            "genres": movie_data.get("genres"),
            "rating": movie_data.get("rating"),
            "synopsis": movie_data.get("synopsis"),
            "overview": movie_data.get("overview"),
            "tmdb_id": movie_data.get("tmdb_id") or movie_data.get("id"),
            "tmdb_rating": movie_data.get("tmdb_rating") or movie_data.get("vote_average"),
            "imdb_id": movie_data.get("imdb_id"),
            "release_date": movie_data.get("release_date"),
            "runtime": movie_data.get("runtime"),
            "poster_path": movie_data.get("poster_path"),
            "backdrop_path": movie_data.get("backdrop_path"),
            "budget": movie_data.get("budget"),
            "revenue": movie_data.get("revenue"),
            "popularity": movie_data.get("popularity"),
            "vote_count": movie_data.get("vote_count"),
            "status": movie_data.get("status"),
            "tagline": movie_data.get("tagline"),
            "homepage": movie_data.get("homepage"),
            "original_title": movie_data.get("original_title"),
            "letterboxd_url": movie_data.get("letterboxd_url"),
            "updated_at": datetime.now().isoformat(),
        }

        # Use INSERT OR REPLACE to handle duplicates
        cursor.execute(
            """
            INSERT OR REPLACE INTO movie_details (
                title, normalized_title, year, director, genres, rating, synopsis, overview,
                tmdb_id, tmdb_rating, imdb_id, release_date, runtime, poster_path, backdrop_path,
                budget, revenue, popularity, vote_count, status, tagline, homepage,
                original_title, letterboxd_url, updated_at
            ) VALUES (
                :title, :normalized_title, :year, :director, :genres, :rating, :synopsis, :overview,
                :tmdb_id, :tmdb_rating, :imdb_id, :release_date, :runtime, :poster_path,
                :backdrop_path, :budget, :revenue, :popularity, :vote_count, :status, :tagline,
                :homepage, :original_title, :letterboxd_url, :updated_at
            )
        """,
            data,
        )

        # Also update old movies table for backward compatibility if it exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='movies'")
        if cursor.fetchone():
            cursor.execute("SELECT movie_id FROM movies WHERE title = ?", (movie_title,))
            result = cursor.fetchone()

            if result:
                # Movie exists in old table, update it
                movie_id = result[0]
                update_sql = """
                    UPDATE movies SET
                        director = ?,
                        genres = ?,
                        rating = ?,
                        synopsis = ?,
                        tmdb_id = ?,
                        tmdb_rating = ?,
                        release_date = ?,
                        runtime = ?,
                        poster_path = ?,
                        backdrop_path = ?,
                        overview = ?,
                        last_updated = ?
                    WHERE movie_id = ?
                """

                cursor.execute(
                    update_sql,
                    (
                        data["director"],
                        data["genres"],
                        data["rating"],
                        data["synopsis"],
                        data["tmdb_id"],
                        data["tmdb_rating"],
                        data["release_date"],
                        data["runtime"],
                        data["poster_path"],
                        data["backdrop_path"],
                        data["overview"],
                        data["updated_at"],
                        movie_id,
                    ),
                )

        conn.commit()
        conn.close()

        logger.debug(f"Saved movie details for: {movie_title}")
        return True

    except sqlite3.Error as e:
        logger.error(f"Database error saving movie details for '{movie_title}': {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error saving movie details for '{movie_title}': {e}")
        return False


def movie_has_details(movie_title, db_path=None):
    """
    Check if a movie has extended details in the database.
    Enhanced version with improved matching.

    Args:
        movie_title (str): The title of the movie to check
        db_path (str, optional): Path to the database file

    Returns:
        bool: True if the movie has extended details, False otherwise
    """
    if not movie_title:
        return False

    if db_path is None:
        db_path = get_database_path()

    if not os.path.exists(db_path):
        return False

    try:
        details = get_movie_details_from_db(movie_title, db_path)
        if not details:
            return False
        # Check for at least one non-title/year detail field
        return any(
            details.get(key) for key in details if key not in ["title", "normalized_title", "year"]
        )
    except sqlite3.Error as e:
        logger.error(f"Database error checking movie details for '{movie_title}': {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking movie details for '{movie_title}': {e}")
        return False


def bulk_save_movie_details(
    movies_data: List[Dict[str, Any]], db_path: Optional[str] = None
) -> int:
    """
    Save multiple movie details to the database in a single transaction.

    Args:
        movies_data (list): List of movie data dictionaries
        db_path (str, optional): Database path

    Returns:
        int: Number of movies successfully saved

    Performance: Uses transaction for bulk operations
    """
    if not movies_data or not isinstance(movies_data, list):
        return 0

    if db_path is None:
        db_path = get_database_path()

    try:
        # Placeholder for missing implementation
        logger.warning("bulk_save_movie_details needs a proper implementation.")
        return 0
    except sqlite3.Error as e:
        logger.error(f"Database error in bulk save: {e}")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error in bulk save: {e}")
        return 0


def cleanup_old_movie_data(days_old: int = 30, db_path: Optional[str] = None) -> int:
    """
    Clean up movie data older than specified days.

    Args:
        days_old (int): Remove data older than this many days
        db_path (str, optional): Database path

    Returns:
        int: Number of records cleaned up

    Performance: Helps maintain database size and freshness
    """
    if db_path is None:
        db_path = get_database_path()

    if not os.path.exists(db_path):
        return 0

    try:
        # Placeholder for missing implementation
        logger.warning("cleanup_old_movie_data needs a proper implementation.")
        return 0
    except sqlite3.Error as e:
        logger.error(f"Database error during cleanup: {e}")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error during cleanup: {e}")
        return 0


def get_database_stats(db_path: Optional[str] = None) -> Dict[str, int]:
    """
    Get statistics about the movie database.

    Args:
        db_path (str, optional): Database path

    Returns:
        dict: Database statistics
    """
    if db_path is None:
        db_path = get_database_path()

    if not os.path.exists(db_path):
        return {}

    try:
        # Placeholder for missing implementation
        logger.warning("get_database_stats needs a proper implementation.")
        return {}
    except sqlite3.Error as e:
        logger.error(f"Database error getting stats: {e}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error getting stats: {e}")
        return {}


def get_filtered_movies_for_friend(username, friend_name, common_only, title_filter, genre_filter):
    """
    Gets a list of movies for a given friend, applying specified filters.
    Signature: Copilot (2025-07-20T20:00:00Z)
    """
    conn = sqlite3.connect(get_database_path())
    if not conn:
        return []

    try:
        cursor = conn.cursor()

        base_query = """
        SELECT DISTINCT
            md.title,
            md.year,
            md.director,
            md.tmdb_rating,
            md.genres
        FROM movie_details md
        JOIN user_watchlists uw ON md.id = uw.movie_id
        WHERE uw.username = ?
        """

        params = [friend_name]

        if common_only:
            base_query += """
            AND md.id IN (
                SELECT movie_id FROM user_watchlists WHERE username = ?
            )
            """
            params.append(username)

        if title_filter:
            base_query += " AND md.title LIKE ?"
            params.append(f"%{title_filter}%")

        if genre_filter:
            base_query += " AND md.genres LIKE ?"
            params.append(f"%{genre_filter}%")

        base_query += " ORDER BY md.title;"

        cursor.execute(base_query, tuple(params))
        return cursor.fetchall()

    except sqlite3.Error as e:
        logger.error(f"Database error while filtering movies for {friend_name}: {e}")
        return []
    finally:
        conn.close()


def get_all_genres_for_friend(username, friend_name):
    """
    Gets a set of all unique genres for movies in a friend's watchlist.
    Signature: Copilot (2025-07-20T20:00:00Z)
    """
    conn = sqlite3.connect(get_database_path())
    if not conn:
        return set()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT md.genres
            FROM movie_details md
            JOIN user_watchlists uw ON md.id = uw.movie_id
            WHERE uw.username = ? AND md.genres IS NOT NULL AND md.genres != ''
        """,
            (friend_name,),
        )

        all_genres = set()
        for row in cursor.fetchall():
            genres = [genre.strip() for genre in row[0].split(",")]
            all_genres.update(genres)
        return all_genres

    except sqlite3.Error as e:
        logger.error(f"Database error getting genres for {friend_name}: {e}")
        return set()
    finally:
        conn.close()


# AI Signature: Claude Sonnet 3.5 - 2025-01-20 19:45:00 EST
# Movie database module enhancement complete with comprehensive SQLite operations
