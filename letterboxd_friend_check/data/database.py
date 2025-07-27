"""
Database operations for the Letterboxd Friend Check application
"""

import sqlite3
import logging
import datetime
from pathlib import Path
from typing import List, Set, Dict, Optional, Any

logger = logging.getLogger(__name__)


def get_db_path() -> str:
    """Get the path to the SQLite database file"""
    from letterboxd_friend_check.config import Config

    config = Config()
    db_path = config.get("database_path")

    if not db_path:
        # Use default path
        project_root = Path(__file__).parent.parent
        db_path = str(project_root / "data" / "letterboxd.db")

    return db_path


def init_db(db_path: Optional[str] = None) -> None:
    """
    Initialize the SQLite database and tables if they do not exist

    Args:
        db_path: Path to SQLite database file (if None, will use default)
    """
    if db_path is None:
        db_path = get_db_path()

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Create tables for users, movies, watchlists, and friends
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            last_sync TIMESTAMP
        )
    """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS movies (
            movie_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE,
            director TEXT,
            genres TEXT,
            rating TEXT,
            synopsis TEXT,
            tmdb_id INTEGER,
            tmdb_rating REAL,
            release_date TEXT,
            runtime INTEGER,
            poster_path TEXT,
            backdrop_path TEXT,
            overview TEXT,
            last_updated TIMESTAMP
        )
    """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS watchlists (
            username TEXT,
            movie_id INTEGER,
            FOREIGN KEY(username) REFERENCES users(username),
            FOREIGN KEY(movie_id) REFERENCES movies(movie_id)
        )
    """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS friends (
            username TEXT,
            friend_username TEXT,
            FOREIGN KEY(username) REFERENCES users(username)
        )
    """
    )

    conn.commit()
    conn.close()

    logger.info(f"Database initialized at {db_path}")


def sync_watchlist_to_db(username: str, movies: Set[str], db_path: Optional[str] = None) -> None:
    """
    Syncs the user's watchlist to the database

    Args:
        username: Letterboxd username
        movies: Set of movie titles in the watchlist
        db_path: Path to SQLite database file (if None, will use default)
    """
    if db_path is None:
        db_path = get_db_path()

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Upsert user
    c.execute(
        "INSERT OR REPLACE INTO users (username, last_sync) VALUES (?, ?)",
        (username, datetime.datetime.now()),
    )

    # Insert movies and get their IDs
    movie_ids = []
    for title in movies:
        c.execute("INSERT OR IGNORE INTO movies (title) VALUES (?)", (title,))
        c.execute("SELECT movie_id FROM movies WHERE title=?", (title,))
        movie_id = c.fetchone()[0]
        movie_ids.append(movie_id)

    # Remove old watchlist and insert new
    c.execute("DELETE FROM watchlists WHERE username=?", (username,))
    c.executemany(
        "INSERT INTO watchlists (username, movie_id) VALUES (?, ?)",
        [(username, mid) for mid in movie_ids],
    )

    conn.commit()
    conn.close()

    logger.info(f"Synced watchlist for {username} with {len(movies)} movies")


def sync_friends_to_db(username: str, friends: List[str], db_path: Optional[str] = None) -> None:
    """
    Syncs the user's friends to the database

    Args:
        username: Letterboxd username
        friends: List of friend usernames
        db_path: Path to SQLite database file (if None, will use default)
    """
    if db_path is None:
        db_path = get_db_path()

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("DELETE FROM friends WHERE username=?", (username,))
    c.executemany(
        "INSERT INTO friends (username, friend_username) VALUES (?, ?)",
        [(username, f) for f in friends],
    )

    conn.commit()
    conn.close()

    logger.info(f"Synced {len(friends)} friends for {username}")


def get_watchlist_from_db(username: str, db_path: Optional[str] = None) -> Set[str]:
    """
    Retrieves the user's watchlist from the database

    Args:
        username: Letterboxd username
        db_path: Path to SQLite database file (if None, will use default)

    Returns:
        Set of movie titles in the watchlist
    """
    if db_path is None:
        db_path = get_db_path()

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute(
        """
        SELECT m.title FROM watchlists w
        JOIN movies m ON w.movie_id = m.movie_id
        WHERE w.username=?
    """,
        (username,),
    )

    movies = set(row[0] for row in c.fetchall())
    conn.close()

    logger.debug(f"Retrieved {len(movies)} movies for {username} from database")
    return movies


def get_friends_from_db(username: str, db_path: Optional[str] = None) -> List[str]:
    """
    Retrieves the user's friends from the database

    Args:
        username: Letterboxd username
        db_path: Path to SQLite database file (if None, will use default)

    Returns:
        List of friend usernames
    """
    if db_path is None:
        db_path = get_db_path()

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("SELECT friend_username FROM friends WHERE username=?", (username,))
    friends = [row[0] for row in c.fetchall()]

    conn.close()

    logger.debug(f"Retrieved {len(friends)} friends for {username} from database")
    return friends


def should_resync(
    username: str, db_path: Optional[str] = None, threshold_hours: int = 24
) -> Optional[datetime.datetime]:
    """
    Determines if the user's data should be resynced based on last_sync timestamp

    Args:
        username: Letterboxd username
        db_path: Path to SQLite database file (if None, will use default)
        threshold_hours: Number of hours after which data should be resynced

    Returns:
        Last sync datetime if available, otherwise None
    """
    if db_path is None:
        db_path = get_db_path()

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("SELECT last_sync FROM users WHERE username=?", (username,))
    row = c.fetchone()

    conn.close()

    if not row or not row[0]:
        return None

    last_sync = datetime.datetime.fromisoformat(row[0])
    return last_sync


def save_movie_data(title: str, data: Dict[str, Any], db_path: Optional[str] = None) -> None:
    """
    Saves movie data to the database

    Args:
        title: Movie title
        data: Dictionary of movie data
        db_path: Path to SQLite database file (if None, will use default)
    """
    if db_path is None:
        db_path = get_db_path()

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Get movie_id
    c.execute("SELECT movie_id FROM movies WHERE title=?", (title,))
    row = c.fetchone()

    if not row:
        # Insert new movie
        c.execute("INSERT INTO movies (title) VALUES (?)", (title,))
        movie_id = c.lastrowid
    else:
        movie_id = row[0]

    # Update movie data
    update_columns = []
    update_values = []

    # Map data dictionary to database columns
    column_map = {
        "director": "director",
        "genres": "genres",
        "rating": "rating",
        "synopsis": "synopsis",
        "tmdb_id": "tmdb_id",
        "tmdb_rating": "tmdb_rating",
        "release_date": "release_date",
        "runtime": "runtime",
        "poster_path": "poster_path",
        "backdrop_path": "backdrop_path",
        "overview": "overview",
    }

    for key, column in column_map.items():
        if key in data and data[key] is not None:
            update_columns.append(f"{column} = ?")

            # Handle list values
            if isinstance(data[key], list):
                update_values.append(", ".join(str(item) for item in data[key]))
            else:
                update_values.append(data[key])

    # Add last_updated timestamp
    update_columns.append("last_updated = ?")
    update_values.append(datetime.datetime.now().isoformat())

    # Add movie_id to values
    update_values.append(movie_id)

    # Execute update using explicit column updates to prevent SQL injection
    if update_columns:
        # Refactor to use a single parameterized UPDATE statement
        # Construct the SET clause dynamically
        set_clause = ", ".join(update_columns)

        # Prepare the SQL query
        query = f"UPDATE movies SET {set_clause} WHERE movie_id = ?"

        # Execute the query with parameterized values
        c.execute(query, update_values)

    conn.commit()
    conn.close()

    logger.debug(f"Saved data for movie: {title}")


def get_movie_data(title: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieves movie data from the database

    Args:
        title: Movie title
        db_path: Path to SQLite database file (if None, will use default)

    Returns:
        Dictionary of movie data if found, otherwise None
    """
    if db_path is None:
        db_path = get_db_path()

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute(
        """
        SELECT title, director, genres, rating, synopsis, tmdb_id, tmdb_rating,
               release_date, runtime, poster_path, backdrop_path, overview
        FROM movies
        WHERE title=?
    """,
        (title,),
    )

    row = c.fetchone()
    conn.close()

    if not row:
        return None

    # Map row to dictionary
    columns = [
        "title",
        "director",
        "genres",
        "rating",
        "synopsis",
        "tmdb_id",
        "tmdb_rating",
        "release_date",
        "runtime",
        "poster_path",
        "backdrop_path",
        "overview",
    ]

    return {columns[i]: row[i] for i in range(len(columns))}


def update_last_sync(username: str, timestamp: str, db_path: Optional[str] = None) -> None:
    """
    Updates the last_sync timestamp for a user

    Args:
        username: Letterboxd username
        timestamp: Timestamp in ISO format
        db_path: Path to SQLite database file (if None, will use default)
    """
    if db_path is None:
        db_path = get_db_path()

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("UPDATE users SET last_sync = ? WHERE username = ?", (timestamp, username))
    conn.commit()
    conn.close()

    logger.debug(f"Updated last_sync for {username} to {timestamp}")


def compare_watchlists(
    user_watchlist: Set[str], friends_watchlists: Dict[str, Set[str]]
) -> Dict[str, Set[str]]:
    """
    Compares the user's watchlist with each friend's watchlist

    Args:
        user_watchlist: Set of movie titles in the user's watchlist
        friends_watchlists: Dictionary mapping friend usernames to sets of movie titles

    Returns:
        Dictionary mapping friend usernames to sets of common movie titles
    """
    common = {}
    for friend, watchlist in friends_watchlists.items():
        common_movies = user_watchlist & watchlist
        if common_movies:
            common[friend] = common_movies
    return common


def movie_has_details(title: str, db_path: Optional[str] = None) -> bool:
    """
    Check if a movie already has details in the database

    Args:
        title: Movie title
        db_path: Path to SQLite database file (if None, will use default)

    Returns:
        True if movie has details, False otherwise
    """
    if db_path is None:
        db_path = get_db_path()

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Get movie_id and check if it has details
    c.execute(
        """
        SELECT movie_id, director, genres, rating, synopsis, tmdb_id
        FROM movies WHERE title=?
    """,
        (title,),
    )

    row = c.fetchone()
    conn.close()

    if not row:
        # Movie doesn't exist in database
        return False

    # Check if any details fields are populated
    # We just need one of the detail fields to be populated
    return any(row[1:])  # Check all columns after movie_id
