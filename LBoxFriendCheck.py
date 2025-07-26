#!/usr/bin/env python
# type: ignore[attr-defined, misc]
"""
Letterboxd Friend Check Application

This application compares a Letterboxd user's watchlist with their friends' watchlists
and displays common movies in a visual drill-down interface using Tkinter.

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

import os
import sys
import time
import logging
import datetime
import requests
import itertools
import tkinter as tk
from bs4 import BeautifulSoup
from tkinter import ttk, messagebox
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import sqlite3
import json
import random
import re
import threading
import queue

# Add the current directory to the path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
# Try different import approaches
try:
    from tmdb_api import get_movie_details, enrich_movie_data, bulk_enrich_movies
except ImportError:
    # Define empty placeholder functions if the module isn't available
    def get_movie_details(*args, **kwargs):
        return {}

    def enrich_movie_data(*args, **kwargs):
        return args[0] if args else {}

    def bulk_enrich_movies(*args, **kwargs):
        return args[0] if args else []


# --- Secure Input Validation Functions ---
def validate_username_input(prompt: str, max_length: int = 50) -> str:
    """
    Securely get username input with validation.
    
    Args:
        prompt: The prompt to display to the user
        max_length: Maximum allowed length for the input
        
    Returns:
        Validated username string
    """
    while True:
        try:
            user_input = input(prompt).strip()  # nosec B601 # Safe CLI input validation
            
            # Check for exit command
            if user_input.lower() == 'exit':
                return user_input
            
            # Validate length
            if len(user_input) > max_length:
                print(f"❌ Username too long (max {max_length} characters)")
                continue
                
            # Validate username format (alphanumeric, underscore, hyphen)
            if not re.match(r'^[a-zA-Z0-9_-]+$', user_input):
                print("❌ Username can only contain letters, numbers, underscores, and hyphens")
                continue
                
            # Check minimum length
            if len(user_input) < 1:
                print("❌ Username cannot be empty")
                continue
                
            return user_input
            
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Input cancelled by user")
            return 'exit'
        except Exception as e:
            print(f"❌ Input error: {e}")
            continue


def validate_menu_choice(prompt: str, valid_choices: list) -> str:
    """
    Securely get menu choice input with validation.
    
    Args:
        prompt: The prompt to display to the user
        valid_choices: List of valid choice strings
        
    Returns:
        Validated choice string
    """
    while True:
        try:
            choice = input(prompt).strip()  # nosec B601 # Safe CLI menu validation
            
            if choice in valid_choices:
                return choice
                
            print(f"❌ Invalid choice. Please select one of: {', '.join(valid_choices)}")
            
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Input cancelled by user")
            return valid_choices[-1] if valid_choices else ""
        except Exception as e:
            print(f"❌ Input error: {e}")
            continue


def validate_confirmation_input(prompt: str, expected_values: list = None) -> str:
    """
    Securely get confirmation input with validation.
    
    Args:
        prompt: The prompt to display to the user
        expected_values: List of valid confirmation values (default: ['y', 'yes', 'n', 'no'])
        
    Returns:
        Validated confirmation string (lowercase)
    """
    if expected_values is None:
        expected_values = ['y', 'yes', 'n', 'no']
    
    while True:
        try:
            response = input(prompt).strip().lower()  # nosec B601 # Safe confirmation input
            
            if response in expected_values:
                return response
                
            print(f"❌ Please respond with one of: {', '.join(expected_values)}")
            
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Input cancelled by user")
            return 'n'  # Default to 'no' for safety
        except Exception as e:
            print(f"❌ Input error: {e}")
            continue


# --- Constants and Global Configuration ---
BASE_URL = "https://letterboxd.com"
# Use a single global session for requests
session = requests.Session()

# --- Setup Logging ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# Prevent duplicate handlers if the script is reloaded
if not logger.handlers:
    # Use a path relative to the script file for portability
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_log_path = os.path.join(script_dir, "Output.txt")

    # File handler for detailed logs
    file_handler = logging.FileHandler(output_log_path, encoding="utf-8", mode="a")
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler for user-facing messages
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


# ASCII spinner animation for loading
def spinner_animation(message, stop_event):
    spinner = itertools.cycle(["|", "/", "-", "\\"])
    while not stop_event.is_set():
        print(f"\r{message} {next(spinner)}", end="", flush=True)
        time.sleep(0.1)
    print(f"\r{message} Done!        ")


# --- Automated login and cookie extraction using Selenium ---
def get_letterboxd_session_cookie_via_selenium():
    """
    Automates Google Chrome browser login to Letterboxd and extracts the session cookie.
    Uses webdriver-manager to automatically handle chromedriver.
    Returns the value of the letterboxd_session cookie.
    """
    logger.info("Launching Google Chrome for automated login...")

    # --- Adherence to PEP 8 and Best Practices ---
    # Using a 'with' statement is not applicable here as the driver's lifecycle
    # is manually managed to allow for user interaction.

    try:
        # --- Performance and Security ---
        # Initialize Chrome options for a streamlined, secure browsing session.
        chrome_options = Options()
        # Running in headless mode can be faster but is not suitable for manual login.
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        # Using an incognito window helps isolate the session.
        chrome_options.add_argument("--incognito")

        # --- Zen of Python: "Simple is better than complex." ---
        # Automatically manage chromedriver instead of hardcoding paths.
        # This is more robust and user-friendly.
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

    except Exception as e:
        logger.error(f"Failed to initialize Chrome WebDriver: {e}")
        messagebox.showerror(
            "WebDriver Error",
            "Could not launch Google Chrome. Please ensure it is installed.",
        )
        return None

    try:
        # Navigate to the Letterboxd login page
        driver.get(f"{BASE_URL}/sign-in/")

        # Wait for the user to manually log in
        logger.info("Please log in to your Letterboxd account in the new Chrome window...")
        wait = WebDriverWait(driver, 300)  # 5-minute timeout for login
        # Wait for the user's avatar to appear, indicating a successful login
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.avatar.-a11y")))

        logger.info("Login successful. Extracting session cookie...")

        # Extract the session cookie
        session_cookie = driver.get_cookie("letterboxd_session")
        if session_cookie:
            logger.info("Successfully extracted 'letterboxd_session' cookie.")
            return session_cookie.get("value")
        else:
            logger.error("Could not find 'letterboxd_session' cookie after login.")
            return None

    except Exception as e:
        logger.error(f"An error occurred during the login process: {e}")
        return None
    finally:
        # Ensure the browser is closed
        driver.quit()


# --- Database Module ---
def init_db(db_path="letterboxd.db"):
    """
    Initializes the SQLite database and tables if they do not exist.
    """
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


def sync_watchlist_to_db(username, movies, db_path="letterboxd.db"):
    """
    Syncs the user's watchlist to the database.
    """
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


def sync_friends_to_db(username, friends, db_path="letterboxd.db"):
    """
    Syncs the user's friends to the database.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("DELETE FROM friends WHERE username=?", (username,))
    c.executemany(
        "INSERT INTO friends (username, friend_username) VALUES (?, ?)",
        [(username, friend) for friend in friends],
    )
    conn.commit()
    conn.close()


def get_watchlist_from_db(username, db_path="letterboxd.db"):
    """
    Retrieves the user's watchlist from the database.
    """
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
    return movies


def get_friends_from_db(username, db_path="letterboxd.db"):
    """
    Retrieves the user's friends from the database.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT friend_username FROM friends WHERE username=?", (username,))
    friends = [row[0] for row in c.fetchall()]
    conn.close()
    return friends


def should_resync(username, db_path="letterboxd.db", threshold_hours=24):
    """
    Determines if the user's data should be resynced based on last_sync timestamp.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT last_sync FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if not row or not row[0]:
        return None
    last_sync = datetime.datetime.fromisoformat(row[0])
    return last_sync


# --- Web Scraping Module ---
def get_watchlist(username, limit=None):
    """
    Fetches the watchlist for a given Letterboxd username using the CSV export feature.
    Returns a set of movie titles.
    """
    movies = set()
    page = 1
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; LetterboxdWatchlistBot/1.0; "
            "+https://github.com/yourusername)"
        )
    }
    logger.info(f"Starting to fetch watchlist for {username}...")
    # Get total movie count for percentage display
    total_count = get_watchlist_count(username)
    last_percent = -1

    def print_progress(fetched, total):
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
            sleep_time = random.uniform(1, 1.5)
            logger.debug(f"Sleeping for {sleep_time:.2f} seconds to avoid rate limiting.")
            time.sleep(sleep_time)
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                logger.warning(
                    "Rate limited by Letterboxd (429 Too Many Requests) on page "
                    f"{page}. Stopping further requests."
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


def get_friends(username):
    """
    Fetches the complete list of friends for a given Letterboxd username by handling pagination.
    Returns a set of unique friend usernames to prevent duplicates.
    Signature: Copilot (2025-07-21T00:00:00Z)
    """
    friends = set()
    page = 1
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; LetterboxdFriendCheck/2.0; "
            "+https://github.com/yourusername/repo)"
        )
    }
    logger.info(f"Starting to fetch friends for {username}...")

    while True:
        url = f"{BASE_URL}/{username}/following/page/{page}/"
        logger.debug(f"Fetching friends page {page} for {username}: {url}")
        try:
            response = session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            person_divs = soup.select(".person-summary")
            if not person_divs:
                logger.info(
                    f"No more friends found for {username} on page {page}. Ending pagination."
                )
                break

            page_friends_found = 0
            for div in person_divs:
                a_tag = div.find("a", class_="avatar")
                if a_tag and a_tag.has_attr("href"):
                    friend_username = a_tag["href"].strip("/").split("/")[0]
                    if friend_username:
                        friends.add(friend_username)
                        page_friends_found += 1

            logger.info(f"Found {page_friends_found} friends on page {page}.")
            page += 1
            time.sleep(random.uniform(0.5, 1.5))  # Respectful delay

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching friends page {page} for {username}: {e}")
            break
        except Exception as e:
            logger.error(f"Error scraping friends page {page} for {username}: {e}")
            break

    logger.info(
        f"Finished fetching friends for {username}. Total unique friends found: {len(friends)}."
    )
    return friends


def compare_watchlists(user_watchlist, friends_watchlists):
    """
    Compares the user's watchlist with each friend's watchlist.
    Returns a dict mapping friend usernames to sets of common movies.
    """
    common = {}
    for friend, watchlist in friends_watchlists.items():
        common_movies = user_watchlist & watchlist
        if common_movies:
            common[friend] = common_movies
    return common


def load_cookies_from_json(session_obj, cookie_path):
    """Loads cookies from a JSON file and adds them to a requests session."""
    try:
        with open(cookie_path, "r") as f:
            cookies = json.load(f)
            for cookie in cookies:
                session_obj.cookies.set(cookie["name"], cookie["value"])
    except Exception as e:
        logger.error(f"Error loading cookies from {cookie_path}: {e}")


def get_watchlist_count(username):
    """
    Scrapes the user's watchlist page for the js-watchlist-count element
    to get the total number of movies. Returns the count as an integer, or None if not found.
    """
    url = f"{BASE_URL}/{username}/watchlist/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; LetterboxdWatchlistBot/1.0; "
            "+https://github.com/yourusername)"
        )
    }
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


# --- GUI Application ---
class LetterboxdGUI(tk.Tk):
    """
    Main GUI application for Letterboxd Friend Check.
    """

    def __init__(self):
        """
        Initialize the main application window and its components.
        Signature: Copilot (2025-07-21T00:15:00Z)
        """
        super().__init__()
        self.title("Letterboxd Friend Check")
        self.geometry("800x600")

        # --- Theme Configuration ---
        self.dark_mode = tk.BooleanVar(value=False)  # Default to light mode
        self.theme_colors = {
            "dark": {
                "bg": "#0d1117",  # Very dark background (GitHub dark)
                "fg": "#f0f6fc",  # Light text for maximum contrast
                "select_bg": "#404040",  # Selection background
                "select_fg": "#ffffff",  # Selection text
                "entry_bg": "#ffffff",  # Entry field background - white for black text visibility
                "entry_fg": "#000000",  # Entry field text - black for readability
                "canvas_bg": "#0d1117",  # Canvas background
                "frame_bg": "#0d1117",  # Frame background
                "button_bg": "#58a6ff",  # Bright blue background for high contrast
                "button_fg": "#000000",  # Black text for maximum contrast
                "menu_bg": "#0d1117",  # Menu background
                "menu_fg": "#f0f6fc",  # Menu text
                "highlight": "#404040",  # Dark gray for selected elements
                "tab_selected_bg": "#e6e6e6",  # Light gray for black text visibility
                "tab_selected_fg": "#000000",  # Selected tab text - black (same as light mode)
                "tab_active_bg": "#58a6ff",  # Bright blue for active tabs
                "tab_active_fg": "#000000",  # Black text for contrast
            },
            "light": {
                "bg": "#ffffff",  # White background
                "fg": "#24292f",  # Dark gray text for better readability
                "select_bg": "#0969da",  # Selection background
                "select_fg": "#ffffff",  # Selection text
                "entry_bg": "#ffffff",  # Entry field background
                "entry_fg": "#24292f",  # Entry field text
                "canvas_bg": "#ffffff",  # Canvas background
                "frame_bg": "#f6f8fa",  # Very light gray frame background
                "button_bg": "#f6f8fa",  # Button background
                "button_fg": "#24292f",  # Button text
                "menu_bg": "#ffffff",  # Menu background
                "menu_fg": "#24292f",  # Menu text
                "highlight": "#e6e6e6",  # Light gray for selected elements
                "tab_selected_bg": "#e6e6e6",  # Selected tab - light gray background
                "tab_selected_fg": "#000000",  # Selected tab text - black (like unselected)
                "tab_active_bg": "#d0d7de",  # Active tab background
                "tab_active_fg": "#24292f",  # Active tab text
            },
        }

        # --- Initialize GUI State Variables ---
        self.username = tk.StringVar()
        self.remember_user = tk.BooleanVar()
        self.friends = []
        self.user_watchlist = set()
        self.friends_watchlists = {}
        self.common_movies = {}

        # --- Thread control variables ---
        self.sync_cancelled = threading.Event()  # For cancelling sync operations
        self.sync_in_progress = False
        self.gui_queue_active = True  # For controlling GUI queue processing
        self.gui_queue_after_id = None  # Store after() ID for cleanup

        # --- Thread-safe queue for GUI updates ---
        self.gui_queue = queue.Queue()

        self.protocol("WM_DELETE_WINDOW", self.save_all_and_exit)

        # Bind window resize events to handle canvas scaling
        self.bind("<Configure>", self._on_window_resize)

        self.create_menubar()
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both")

        # --- Setup Frames ---
        self.setup_setup_frame()
        self.setup_sync_frame()
        self.setup_results_frame()

        self.load_config()
        # Apply theme after loading config to ensure correct theme is applied
        self.apply_theme()
        self.load_previous_data_from_db()

        # Load saved data after frames are set up
        self.load_saved_data()

        # Check if user has saved config and skip setup tab if so
        self.check_and_skip_setup_if_configured()

        # Start the queue processor
        self.process_gui_queue()

    def process_gui_queue(self):
        """
        Process any pending GUI updates from the background threads.
        This is the standard thread-safe way to update Tkinter UIs.
        """
        if not self.gui_queue_active:
            return  # Stop processing if queue is deactivated

        try:
            while True:
                task, args, kwargs = self.gui_queue.get_nowait()
                task(*args, **kwargs)
        except queue.Empty:
            pass
        except tk.TclError:
            # Widget has been destroyed, stop processing
            self.gui_queue_active = False
            return

        # Only schedule next update if queue is still active
        if self.gui_queue_active:
            try:
                self.gui_queue_after_id = self.after(100, self.process_gui_queue)
            except tk.TclError:
                # Window is being destroyed, stop processing
                self.gui_queue_active = False

    def toggle_remember_user(self):
        self.save_config()

    def toggle_theme(self):
        """Toggle between light and dark themes."""
        new_mode = not self.dark_mode.get()
        self.dark_mode.set(new_mode)
        self.apply_theme()
        # Recreate menubar with new theme
        self.create_menubar()
        # Save the new theme preference immediately
        self.save_config()

    def apply_theme(self):
        """Apply the current theme to all widgets."""
        current_theme = "dark" if self.dark_mode.get() else "light"
        colors = self.theme_colors[current_theme]

        # Apply theme to root window
        self.configure(bg=colors["bg"])

        # Configure ttk styles for themed widgets
        style = ttk.Style()

        # Configure notebook style
        style.configure("TNotebook", background=colors["bg"], borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=colors["button_bg"],
            foreground=colors["button_fg"],
            padding=[12, 8, 12, 8],
        )
        style.map(
            "TNotebook.Tab",
            background=[
                ("selected", colors["tab_selected_bg"]),
                ("active", colors["tab_active_bg"]),
            ],
            foreground=[
                ("selected", colors["tab_selected_fg"]),
                ("active", colors["tab_active_fg"]),
            ],
        )

        # Configure frame style
        style.configure("TFrame", background=colors["bg"], borderwidth=0)

        # Configure label style
        style.configure("TLabel", background=colors["bg"], foreground=colors["fg"])

        # Configure labelframe style
        style.configure(
            "TLabelframe",
            background=colors["bg"],
            foreground=colors["fg"],
            borderwidth=1,
            relief="solid",
        )
        style.configure("TLabelframe.Label", background=colors["bg"], foreground=colors["fg"])

        # Configure button style
        style.configure(
            "TButton",
            background=colors["button_bg"],
            foreground=colors["button_fg"],
            borderwidth=1,
            focuscolor="none",
            relief="raised",
        )
        style.map(
            "TButton",
            background=[("active", colors["tab_active_bg"]), ("pressed", colors["highlight"])],
            foreground=[
                ("active", colors["tab_active_fg"]),
                ("pressed", colors["tab_selected_fg"]),
            ],
            relief=[("pressed", "sunken"), ("active", "raised")],
        )

        # Configure entry style
        style.configure(
            "TEntry",
            fieldbackground=colors["entry_bg"],
            foreground=colors["entry_fg"],
            borderwidth=1,
            insertcolor=colors["fg"],
        )
        style.map(
            "TEntry",
            fieldbackground=[("focus", colors["entry_bg"])],
            bordercolor=[("focus", colors["highlight"])],
        )

        # Configure checkbutton style
        style.configure(
            "TCheckbutton", background=colors["bg"], foreground=colors["fg"], focuscolor="none"
        )
        style.map(
            "TCheckbutton",
            background=[("active", colors["bg"])],
            foreground=[("active", colors["fg"])],
        )

        # Configure scrollbar style
        style.configure(
            "Vertical.TScrollbar",
            background=colors["button_bg"],
            troughcolor=colors["bg"],
            borderwidth=1,
            arrowcolor=colors["fg"],
        )

        # Configure separator style
        style.configure("TSeparator", background=colors["select_bg"])

        # Apply theme to any existing canvas widgets
        if hasattr(self, "friends_canvas"):
            self.friends_canvas.configure(bg=colors["canvas_bg"])

        # Apply theme to results canvas if it exists
        for widget in self._get_all_canvas_widgets():
            widget.configure(bg=colors["canvas_bg"])

        # Update any existing text widgets
        for widget in self._get_all_text_widgets():
            widget.configure(
                bg=colors["entry_bg"],
                fg=colors["entry_fg"],
                insertbackground=colors["fg"],
                selectbackground=colors["highlight"],
                selectforeground=colors["select_fg"],
            )

    def _get_all_text_widgets(self):
        """Helper method to find all text widgets for theme application."""
        text_widgets = []

        def find_text_widgets(parent):
            for child in parent.winfo_children():
                if isinstance(child, tk.Text):
                    text_widgets.append(child)
                find_text_widgets(child)

        try:
            find_text_widgets(self)
        except tk.TclError:
            # Widget might be destroyed, ignore
            pass

        return text_widgets

    def _get_all_canvas_widgets(self):
        """Helper method to find all canvas widgets for theme application."""
        canvas_widgets = []

        def find_canvas_widgets(parent):
            for child in parent.winfo_children():
                if isinstance(child, tk.Canvas):
                    canvas_widgets.append(child)
                find_canvas_widgets(child)

        try:
            find_canvas_widgets(self)
        except tk.TclError:
            # Widget might be destroyed, ignore
            pass

        return canvas_widgets

    def load_config(self):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                self.username.set(config.get("username", ""))
                self.remember_user.set(config.get("remember_user", False))
                self.dark_mode.set(config.get("dark_mode", False))  # Default to light mode
        except FileNotFoundError:
            self.username.set("")
            self.remember_user.set(False)
            self.dark_mode.set(False)  # Default to light mode

    def load_previous_data_from_db(self):
        username = self.username.get()
        if username:
            self.friends = get_friends_from_db(username)
            self.user_watchlist = get_watchlist_from_db(username)
            self.load_friends_watchlists()

    def check_and_skip_setup_if_configured(self):
        """
        Skip the setup tab if user has already saved configuration.
        Signature: Copilot (2025-07-24T20:00:00Z)
        """
        username = self.username.get()
        remember_user = self.remember_user.get()

        if username and remember_user:
            # User has saved configuration, enable sync tab and skip to it
            self.notebook.tab(1, state="normal")  # Enable sync tab
            self.notebook.select(1)  # Jump to sync tab
            # Optionally hide the setup tab entirely
            # self.notebook.forget(0)  # Uncomment to completely hide setup tab
        else:
            # No saved config, start with setup tab
            self.notebook.select(0)

    def create_menubar(self):
        current_theme = "dark" if self.dark_mode.get() else "light"
        colors = self.theme_colors[current_theme]

        menubar = tk.Menu(self, bg=colors["menu_bg"], fg=colors["menu_fg"])
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0, bg=colors["menu_bg"], fg=colors["menu_fg"])
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Change User", command=self.change_user)
        file_menu.add_separator()
        file_menu.add_command(label="Save & Exit", command=self.save_all_and_exit)

        view_menu = tk.Menu(menubar, tearoff=0, bg=colors["menu_bg"], fg=colors["menu_fg"])
        menubar.add_cascade(label="View", menu=view_menu)
        theme_text = "Switch to Light Theme" if self.dark_mode.get() else "Switch to Dark Theme"
        view_menu.add_command(label=theme_text, command=self.toggle_theme)

        help_menu = tk.Menu(menubar, tearoff=0, bg=colors["menu_bg"], fg=colors["menu_fg"])
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def validate_saved_username(self):
        username = self.username.get()
        if username:
            self.setup_auto_user(username)

    def setup_auto_user(self, username):
        self.username_entry.delete(0, tk.END)
        self.username_entry.insert(0, username)
        self.remember_user_var.set(self.remember_user.get())
        self.test_connection_dialog(username, "cookie", os.path.join(os.getcwd(), "Cookie.json"))

    def load_friends_watchlists(self):
        self.friends_watchlists = {}
        for friend in self.friends:
            self.friends_watchlists[friend] = get_watchlist_from_db(friend)

    def change_user(self):
        self.notebook.select(0)

    def show_about(self):
        messagebox.showinfo(
            "About",
            "Letterboxd Friend Check\n\n"
            "This application helps you find common movies between your watchlist "
            "and your friends' watchlists on Letterboxd.",
        )

    def save_config(self):
        config = {
            "username": self.username.get(),
            "remember_user": self.remember_user.get(),
            "tmdb_api_key": self.tmdb_api_key.get().strip(),
            "dark_mode": self.dark_mode.get(),
        }

        # Save friends list if available
        if hasattr(self, "friends") and self.friends:
            config["friends_list"] = self.friends

        # Save friends selection state if available
        if hasattr(self, "friend_check_vars") and self.friend_check_vars:
            selected_friends = [
                friend for friend, var in self.friend_check_vars.items() if var.get()
            ]
            config["selected_friends"] = selected_friends

        # Save last sync timestamp from database
        try:
            username = self.username.get()
            if username:
                last_sync = self.get_last_sync_from_db(username)
                if last_sync:
                    config["last_sync"] = last_sync.isoformat()
        except Exception:
            pass  # Don't fail if we can't get last sync time

        with open("config.json", "w") as f:
            json.dump(config, f, indent=4)

    def setup_setup_frame(self):
        """
        Set up the main user configuration frame, integrating all setup controls.
        This completely replaces the need for a separate pop-up dialog.
        Signature: Copilot (2025-07-20T23:20:00Z)
        """
        setup_frame = ttk.Frame(self.notebook, padding="20 10")
        self.notebook.add(setup_frame, text="Setup")

        # --- Variables for this frame ---
        self.auto_fetch_details_var = tk.BooleanVar(value=True)
        self.tmdb_api_key = tk.StringVar()
        self.status_var = tk.StringVar()

        # --- UI Widgets ---
        # Header
        header_label = ttk.Label(
            setup_frame, text="Letterboxd User Setup", font=("TkDefaultFont", 12, "bold")
        )
        header_label.pack(pady=(0, 15))

        # Input frame
        input_frame = ttk.Frame(setup_frame)
        input_frame.pack(fill="x", pady=5)

        # Username entry
        ttk.Label(input_frame, text="Letterboxd Username:").grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        username_entry = ttk.Entry(input_frame, textvariable=self.username, width=30)
        username_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        username_entry.focus_set()

        # Remember username checkbox
        remember_checkbox = ttk.Checkbutton(
            input_frame,
            text="Remember Username",
            variable=self.remember_user,
            command=self.toggle_remember_user,
        )
        remember_checkbox.grid(row=0, column=2, sticky=tk.W, pady=5, padx=10)

        # Help text
        help_text = ttk.Label(
            input_frame,
            text="Enter your public Letterboxd username. No login required for public data.",
            wraplength=400,
            justify="left",
            font=("TkDefaultFont", 9),
        )
        help_text.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=15)

        # Settings separator
        ttk.Separator(input_frame, orient="horizontal").grid(
            row=2, column=0, columnspan=3, sticky=tk.EW, pady=15
        )

        # Data settings
        ttk.Label(input_frame, text="Data Settings:").grid(row=3, column=0, sticky=tk.W, pady=5)
        auto_fetch_checkbox = ttk.Checkbutton(
            input_frame,
            text="Auto-fetch Movie Details during Sync",
            variable=self.auto_fetch_details_var,
        )
        auto_fetch_checkbox.grid(row=3, column=1, columnspan=2, sticky=tk.W, pady=5)

        # TMDB API Key separator
        ttk.Separator(input_frame, orient="horizontal").grid(
            row=4, column=0, columnspan=3, sticky=tk.EW, pady=15
        )

        # TMDB API Key section
        tmdb_label = ttk.Label(
            input_frame, text="TMDB API Key (Optional):", font=("TkDefaultFont", 10, "bold")
        )
        tmdb_label.grid(row=5, column=0, sticky=tk.W, pady=5)

        # API key entry
        self.tmdb_entry = ttk.Entry(
            input_frame,
            textvariable=self.tmdb_api_key,
            width=40,
            show="*",  # Hide the API key for security
        )
        self.tmdb_entry.grid(row=5, column=1, columnspan=2, sticky=tk.W, pady=5)

        # Show/Hide API key button
        self.show_api_key_var = tk.BooleanVar()
        show_key_button = ttk.Checkbutton(
            input_frame,
            text="Show",
            variable=self.show_api_key_var,
            command=self.toggle_api_key_visibility,
        )
        show_key_button.grid(row=6, column=1, sticky=tk.W, pady=2)

        # TMDB help text with clickable link
        tmdb_help = ttk.Label(
            input_frame,
            text="Enhanced movie details with posters, ratings, and descriptions.",
            font=("TkDefaultFont", 9),
            foreground="gray",
        )
        tmdb_help.grid(row=7, column=0, columnspan=3, sticky=tk.W, pady=2)

        # TMDB setup guide
        guide_frame = ttk.Frame(input_frame)
        guide_frame.grid(row=8, column=0, columnspan=3, sticky=tk.W, pady=5)

        ttk.Label(
            guide_frame, text="To get a free TMDB API key:", font=("TkDefaultFont", 9, "bold")
        ).pack(anchor="w")

        # Clickable link to TMDB
        link_label = ttk.Label(
            guide_frame,
            text="1. Visit TMDB Developer Portal",
            font=("TkDefaultFont", 9, "underline"),
            foreground="blue",
            cursor="hand2",
        )
        link_label.pack(anchor="w", padx=10)
        link_label.bind("<Button-1>", self.open_tmdb_signup)

        ttk.Label(
            guide_frame, text="2. Sign up for a free account", font=("TkDefaultFont", 9)
        ).pack(anchor="w", padx=10)

        ttk.Label(
            guide_frame, text="3. Go to Settings > API and request a key", font=("TkDefaultFont", 9)
        ).pack(anchor="w", padx=10)

        ttk.Label(guide_frame, text="4. Paste your API key above", font=("TkDefaultFont", 9)).pack(
            anchor="w", padx=10
        )

        # Test API key button
        test_api_frame = ttk.Frame(input_frame)
        test_api_frame.grid(row=9, column=0, columnspan=3, sticky=tk.W, pady=10)

        self.test_api_button = ttk.Button(
            test_api_frame, text="Test API Key", command=self.test_tmdb_api_key
        )
        self.test_api_button.pack(side=tk.LEFT)

        self.api_status_label = ttk.Label(test_api_frame, text="", font=("TkDefaultFont", 9))
        self.api_status_label.pack(side=tk.LEFT, padx=10)

        # Action Buttons
        button_frame = ttk.Frame(setup_frame)
        button_frame.pack(fill="x", pady=20)
        ttk.Button(button_frame, text="Verify Username", command=self.verify_username).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Save Configuration", command=self.save_configuration).pack(
            side=tk.LEFT, padx=5
        )

        # Status message
        status_label = ttk.Label(setup_frame, textvariable=self.status_var, foreground="green")
        status_label.pack(fill="x", pady=10)

        self.load_remembered_username()
        self.load_tmdb_config()

    def verify_username(self):
        """Verify that the Letterboxd username exists directly from the main window."""
        username = self.username.get().strip()
        if not username:
            messagebox.showerror("Error", "Please enter a Letterboxd username.")
            return

        self.status_var.set(f"Verifying '{username}'...")
        self.update_idletasks()

        try:
            response = requests.get(f"https://letterboxd.com/{username}/", timeout=10)
            if response.status_code == 200:
                self.status_var.set(f"Username '{username}' is valid!")
                messagebox.showinfo("Success", f"Successfully connected to '{username}'s profile.")
            else:
                self.status_var.set(f"Username '{username}' not found or profile is private.")
                messagebox.showerror(
                    "Error",
                    (
                        f"Username '{username}' not found on Letterboxd "
                        f"(Status: {response.status_code})."
                    ),
                )
        except requests.RequestException as e:
            self.status_var.set("Connection error.")
            messagebox.showerror("Error", f"A connection error occurred: {e}")

    def save_configuration(self):
        """Saves the current configuration and enables the next step."""
        username = self.username.get().strip()
        if not username:
            messagebox.showerror("Error", "Cannot save an empty username.")
            return

        self.save_config()
        self.status_var.set(
            f"Configuration saved for user '{username}'. You can now proceed to the 'Sync' tab."
        )
        self.notebook.tab(1, state="normal")  # Enable the Sync tab

        # Automatically navigate to the Sync Data tab
        self.notebook.select(1)

    def load_remembered_username(self):
        if self.remember_user.get() and self.username.get():
            # The username_entry is already linked to self.username, so no need to insert.
            # The checkbox is already linked to self.remember_user.
            pass

    def toggle_api_key_visibility(self):
        """Toggle visibility of the TMDB API key field."""
        if self.show_api_key_var.get():
            self.tmdb_entry.config(show="")
        else:
            self.tmdb_entry.config(show="*")

    def open_tmdb_signup(self, event):
        """Open TMDB developer signup page in default browser."""
        import webbrowser

        webbrowser.open("https://www.themoviedb.org/settings/api")

    def test_tmdb_api_key(self):
        """Test the TMDB API key by making a simple API call."""
        api_key = self.tmdb_api_key.get().strip()
        if not api_key:
            self.api_status_label.config(text="Please enter an API key first", foreground="red")
            return

        self.api_status_label.config(text="Testing...", foreground="blue")
        self.test_api_button.config(state="disabled")
        self.update()

        try:
            # Test the API key with a simple request
            import requests

            test_url = f"https://api.themoviedb.org/3/configuration?api_key={api_key}"
            response = requests.get(test_url, timeout=10)

            if response.status_code == 200:
                self.api_status_label.config(text="✓ Valid API key!", foreground="green")
            elif response.status_code == 401:
                self.api_status_label.config(text="✗ Invalid API key", foreground="red")
            else:
                self.api_status_label.config(
                    text=f"✗ Error: {response.status_code}", foreground="red"
                )
        except requests.RequestException:
            self.api_status_label.config(
                text="✗ Connection error - check internet", foreground="red"
            )
        except Exception:
            self.api_status_label.config(text="✗ Unexpected error", foreground="red")
        finally:
            self.test_api_button.config(state="normal")

    def load_tmdb_config(self):
        """Load existing TMDB API key from config if available."""
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                tmdb_key = config.get("tmdb_api_key", "")
                if tmdb_key:
                    self.tmdb_api_key.set(tmdb_key)
        except (FileNotFoundError, json.JSONDecodeError):
            pass  # No config file or invalid JSON, use empty key

    def get_last_sync_from_db(self, username):
        """Get last sync timestamp from database for the given username."""
        try:
            conn = sqlite3.connect("letterboxd.db")
            c = conn.cursor()
            c.execute("SELECT last_sync FROM users WHERE username=?", (username,))
            row = c.fetchone()
            conn.close()
            if row and row[0]:
                return datetime.datetime.fromisoformat(row[0])
        except Exception:
            pass
        return None

    def load_saved_data(self):
        """Load saved friends list and results from config file."""
        try:
            with open("config.json", "r") as f:
                config = json.load(f)

            # Load friends list if available and we have the UI components
            if (
                "friends_list" in config
                and config["friends_list"]
                and hasattr(self, "scrollable_friends_frame")
            ):
                self.friends = config["friends_list"]
                self._populate_friends_list(self.friends)

                # Restore friend selection state
                if "selected_friends" in config:
                    selected_friends = config["selected_friends"]
                    # Update checkboxes based on saved selection
                    for friend_name, var in self.friend_check_vars.items():
                        var.set(friend_name in selected_friends)
                    self.update_sync_stats()

            # Load and display results if they exist in database
            if hasattr(self, "friends") and self.friends:
                self.load_friends_watchlists()
                if self.friends_watchlists:
                    # Enable results tab
                    self.notebook.tab(2, state="normal")

        except (FileNotFoundError, json.JSONDecodeError):
            pass  # No saved data, start fresh

    def update_last_sync_display(self):
        """Update the display of last sync date and time."""
        try:
            username = self.username.get()
            if username:
                last_sync = self.get_last_sync_from_db(username)
                if last_sync:
                    # Format the datetime for display
                    formatted_time = last_sync.strftime("%B %d, %Y at %I:%M %p")
                    self.last_sync_var.set(f"Last sync: {formatted_time}")
                else:
                    self.last_sync_var.set("No previous sync found")
            else:
                self.last_sync_var.set("")
        except Exception:
            self.last_sync_var.set("")

    def setup_sync_frame(self):
        """
        Set up the frame for syncing data with Letterboxd.
        Provides friend selection, progress tracking, and statistics.
        Signature: Copilot (2025-07-20T23:45:00Z)
        """
        self.sync_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.sync_frame, text="Sync Data")
        self.notebook.tab(1, state="disabled")  # Disable until config is saved

        self.sync_frame.grid_columnconfigure(0, weight=1)
        self.sync_frame.grid_columnconfigure(1, weight=0)  # For last sync display
        self.sync_frame.grid_rowconfigure(1, weight=1)

        # --- Top Controls ---
        top_frame = ttk.Frame(self.sync_frame)
        top_frame.grid(row=0, column=0, sticky="ew", pady=5)

        ttk.Button(
            top_frame, text="Fetch Friends List", command=self.fetch_friends_for_sync_tab
        ).pack(side=tk.LEFT)
        self.sync_status_var = tk.StringVar(value="Ready. Fetch friends to begin.")
        ttk.Label(top_frame, textvariable=self.sync_status_var, wraplength=600).pack(
            side=tk.LEFT, padx=10
        )

        # --- Last Sync Info ---
        sync_info_frame = ttk.Frame(self.sync_frame)
        sync_info_frame.grid(row=0, column=1, sticky="e", pady=5)

        self.last_sync_var = tk.StringVar(value="")
        self.last_sync_label = ttk.Label(
            sync_info_frame,
            textvariable=self.last_sync_var,
            font=("TkDefaultFont", 9),
            foreground="gray",
        )
        self.last_sync_label.pack(anchor="e")

        # Update last sync display
        self.update_last_sync_display()

        # --- Friends List (Checkboxes) ---
        friends_frame = ttk.LabelFrame(self.sync_frame, text="Select Friends to Sync", padding="10")
        friends_frame.grid(row=1, column=0, sticky="nsew", pady=5)
        friends_frame.grid_rowconfigure(1, weight=1)
        friends_frame.grid_columnconfigure(0, weight=1)

        # Select All/None
        self.select_all_friends_var = tk.BooleanVar()
        select_all_check = ttk.Checkbutton(
            friends_frame,
            text="Select All / Deselect All",
            variable=self.select_all_friends_var,
            command=self.toggle_select_all_friends,
        )
        select_all_check.grid(row=0, column=0, sticky="w")

        # Canvas and Scrollbar for the list of friends
        current_theme = "dark" if self.dark_mode.get() else "light"
        colors = self.theme_colors[current_theme]
        canvas = tk.Canvas(friends_frame, highlightthickness=0, height=300, bg=colors["canvas_bg"])
        scrollbar = ttk.Scrollbar(friends_frame, orient="vertical", command=canvas.yview)
        self.scrollable_friends_frame = ttk.Frame(canvas)

        # Store canvas reference for proper cleanup
        self.friends_canvas = canvas

        # Configure scroll region when frame content changes
        def _update_scroll_region():
            """Update scroll region and ensure proper sizing."""
            # Force a proper update sequence
            self.scrollable_friends_frame.update_idletasks()
            canvas.update_idletasks()
            # Get the bounding box and configure scroll region
            bbox = canvas.bbox("all")
            if bbox:
                canvas.configure(scrollregion=bbox)
            else:
                # Fallback: use frame's required size
                frame_height = self.scrollable_friends_frame.winfo_reqheight()
                frame_width = self.scrollable_friends_frame.winfo_reqwidth()
                canvas.configure(scrollregion=(0, 0, frame_width, frame_height))

        self.scrollable_friends_frame.bind("<Configure>", lambda e: _update_scroll_region())

        # Create canvas window
        self.friends_canvas_window = canvas.create_window(
            (0, 0), window=self.scrollable_friends_frame, anchor="nw"
        )
        canvas.configure(yscrollcommand=scrollbar.set)

        # Configure canvas to resize content window when canvas size changes
        def _configure_friends_canvas(event):
            # Update scroll region
            _update_scroll_region()
            # Make the scrollable frame match the canvas width (minus scrollbar)
            canvas_width = event.width
            if canvas_width > 1:  # Valid width
                canvas.itemconfig(self.friends_canvas_window, width=canvas_width)

        canvas.bind("<Configure>", _configure_friends_canvas)

        # Ensure scrollable frame expands to fill canvas width
        def _configure_scrollable_friends_frame(event):
            # Set minimum width to match canvas
            canvas_width = canvas.winfo_width()
            if canvas_width > 1:  # Valid width
                min_width = max(canvas_width, self.scrollable_friends_frame.winfo_reqwidth())
                canvas.itemconfig(self.friends_canvas_window, width=min_width)

        self.scrollable_friends_frame.bind("<Configure>", _configure_scrollable_friends_frame)

        # Add mouse wheel scrolling support
        self._bind_mousewheel_to_canvas(canvas)

        canvas.grid(row=1, column=0, sticky="nsew")
        scrollbar.grid(row=1, column=1, sticky="ns")

        self.friend_check_vars = {}  # To hold {friend_name: tk.BooleanVar}

        # --- Bottom Controls ---
        bottom_frame = ttk.Frame(self.sync_frame)
        bottom_frame.grid(row=2, column=0, sticky="ew", pady=10)
        bottom_frame.grid_columnconfigure(2, weight=1)

        # Sync control buttons
        self.start_sync_button = ttk.Button(
            bottom_frame, text="Start Sync", command=self.perform_sync_selected
        )
        self.start_sync_button.grid(row=0, column=0, padx=(0, 5))

        self.cancel_sync_button = ttk.Button(
            bottom_frame, text="Cancel Sync", command=self.cancel_sync_operation, state="disabled"
        )
        self.cancel_sync_button.grid(row=0, column=1, padx=(0, 10))

        self.sync_progress_var = tk.DoubleVar()
        self.sync_progressbar = ttk.Progressbar(
            bottom_frame,
            orient="horizontal",
            length=300,
            mode="determinate",
            variable=self.sync_progress_var,
        )
        self.sync_progressbar.grid(row=0, column=2, sticky="ew", padx=10)

        self.sync_stats_var = tk.StringVar(value="Selected: 0 friends")
        ttk.Label(bottom_frame, textvariable=self.sync_stats_var).grid(
            row=1, column=2, sticky="w", padx=10
        )

    def setup_results_frame(self):
        """
        Set up the frame for displaying sync results and common movies with enhanced details.
        Signature: Copilot (2025-07-24T20:00:00Z)
        """
        self.results_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.results_frame, text="Results")
        self.notebook.tab(2, state="disabled")  # Disable until sync is complete

        # Results summary label at top
        self.results_summary_var = tk.StringVar(value="No results to display. Run a sync first.")
        summary_label = ttk.Label(
            self.results_frame,
            textvariable=self.results_summary_var,
            font=("TkDefaultFont", 10, "bold"),
        )
        summary_label.pack(pady=(0, 10))

        # Create paned window for main content and details
        paned_window = ttk.PanedWindow(self.results_frame, orient=tk.HORIZONTAL)
        paned_window.pack(expand=True, fill="both")

        # Left panel: Results list
        left_frame = ttk.Frame(paned_window)
        paned_window.add(left_frame, weight=3)

        # Canvas and scrollbar for scrollable results
        current_theme = "dark" if self.dark_mode.get() else "light"
        colors = self.theme_colors[current_theme]
        results_canvas = tk.Canvas(left_frame, bg=colors["canvas_bg"])
        results_scrollbar = ttk.Scrollbar(
            left_frame, orient="vertical", command=results_canvas.yview
        )
        self.scrollable_results_frame = ttk.Frame(results_canvas)

        self.scrollable_results_frame.bind(
            "<Configure>",
            lambda e: results_canvas.configure(scrollregion=results_canvas.bbox("all")),
        )

        results_canvas.create_window((0, 0), window=self.scrollable_results_frame, anchor="nw")
        results_canvas.configure(yscrollcommand=results_scrollbar.set)

        # Configure canvas to resize content window when canvas size changes
        def _configure_results_canvas(event):
            # Update scroll region
            results_canvas.configure(scrollregion=results_canvas.bbox("all"))
            # Make the scrollable frame match the canvas width (minus scrollbar)
            canvas_width = event.width
            if results_canvas.find_all():  # Check if window exists
                results_canvas.itemconfig(results_canvas.find_all()[0], width=canvas_width)

        results_canvas.bind("<Configure>", _configure_results_canvas)

        # Ensure scrollable frame expands to fill canvas width
        def _configure_scrollable_results_frame(event):
            # Set minimum width to match canvas
            canvas_width = results_canvas.winfo_width()
            if canvas_width > 1:  # Valid width
                min_width = max(canvas_width, self.scrollable_results_frame.winfo_reqwidth())
                if results_canvas.find_all():
                    results_canvas.itemconfig(results_canvas.find_all()[0], width=min_width)

        self.scrollable_results_frame.bind("<Configure>", _configure_scrollable_results_frame)

        # Add mouse wheel scrolling to results
        self._bind_mousewheel_to_canvas(results_canvas)

        results_canvas.pack(side="left", fill="both", expand=True)
        results_scrollbar.pack(side="right", fill="y")

        # Right panel: Movie details
        right_frame = ttk.LabelFrame(paned_window, text="Movie Details", padding="10")
        paned_window.add(right_frame, weight=1)

        # Details display area
        current_theme = "dark" if self.dark_mode.get() else "light"
        colors = self.theme_colors[current_theme]
        self.details_text = tk.Text(
            right_frame,
            wrap="word",
            height=15,
            width=30,
            state="disabled",
            bg=colors["entry_bg"],
            fg=colors["entry_fg"],
            insertbackground=colors["fg"],
            selectbackground=colors["highlight"],
            selectforeground=colors["select_fg"],
        )
        details_text_scrollbar = ttk.Scrollbar(
            right_frame, orient="vertical", command=self.details_text.yview
        )
        self.details_text.configure(yscrollcommand=details_text_scrollbar.set)

        self.details_text.pack(side="left", fill="both", expand=True)
        details_text_scrollbar.pack(side="right", fill="y")

        # Initialize with placeholder text
        self.details_text.config(state="normal")
        self.details_text.insert(
            "1.0", "Click 'Details' next to any movie to view information here."
        )
        self.details_text.config(state="disabled")

        # Store canvas reference for updating
        self.results_canvas = results_canvas

    def _bind_mousewheel_to_canvas(self, canvas):
        """
        Bind mouse wheel scrolling to a canvas widget.
        Simple reliable approach using global binding with canvas tracking.
        Signature: Copilot (2025-07-24T22:00:00Z)
        """

        def _on_mousewheel(event):
            # Simple and reliable: just scroll this canvas
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except tk.TclError:
                pass  # Canvas might be destroyed

        def _bind_to_mousewheel(event):
            # Use global binding (which we know works)
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")

        canvas.bind("<Enter>", _bind_to_mousewheel)
        canvas.bind("<Leave>", _unbind_from_mousewheel)

    def _on_window_resize(self, event):
        """
        Handle main window resize events to properly scale canvas content.
        Only processes resize events for the main window, not child widgets.
        Signature: Copilot (2025-07-24T22:50:00Z)
        """
        # Only handle resize events for the main window
        if event.widget == self:
            # Small delay to batch resize events
            self.after_idle(self._update_canvas_scaling)

    def _update_canvas_scaling(self):
        """
        Update canvas content scaling after window resize.
        Signature: Copilot (2025-07-24T22:50:00Z)
        """
        try:
            # Update friends canvas if it exists
            if hasattr(self, "scrollable_friends_frame"):
                # Force canvas to reconfigure its scroll region
                for child in self.sync_frame.winfo_children():
                    if isinstance(child, ttk.Frame):
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, tk.Canvas):
                                grandchild.update_idletasks()
                                grandchild.configure(scrollregion=grandchild.bbox("all"))

            # Update results canvas if it exists
            if hasattr(self, "results_canvas"):
                self.results_canvas.update_idletasks()
                self.results_canvas.configure(scrollregion=self.results_canvas.bbox("all"))

        except (tk.TclError, AttributeError):
            # Ignore errors if widgets don't exist or are being destroyed
            pass

    def fetch_friends_for_sync_tab(self):
        """Fetches the user's friends and populates the checklist on the Sync tab."""
        username = self.username.get()
        if not username:
            messagebox.showerror("Error", "Please set a username in the Setup tab first.")
            return

        self.sync_status_var.set(f"Fetching friends for {username}...")
        self.update_idletasks()

        # Run in a separate thread to keep the GUI responsive
        threading.Thread(
            target=self._fetch_and_populate_friends, args=(username,), daemon=True
        ).start()

    def _fetch_and_populate_friends(self, username):
        """
        Worker method to fetch friends and then queue the GUI update.
        The fetched friends list is passed through the queue.
        Signature: Copilot (2025-07-21T00:30:00Z)
        """
        friends_set = get_friends(username)
        sorted_friends = sorted(list(friends_set))

        # Use the queue to schedule the GUI update, passing the result directly.
        self.gui_queue.put((self._populate_friends_list, (sorted_friends,), {}))

    def _populate_friends_list(self, friends_list):
        """
        This method runs on the main GUI thread to update the friends checklist.
        It receives the list of friends directly from the queue.
        Enhanced with better scroll region management.
        Signature: Copilot (2025-07-24T21:00:00Z)
        """
        self.friends = friends_list
        # Clear previous friend checkboxes
        for widget in self.scrollable_friends_frame.winfo_children():
            widget.destroy()
        self.friend_check_vars.clear()

        # Populate with new friends
        for friend_name in self.friends:
            var = tk.BooleanVar(value=True)
            cb = ttk.Checkbutton(
                self.scrollable_friends_frame,
                text=friend_name,
                variable=var,
                command=self.update_sync_stats,
            )
            cb.pack(anchor="w", padx=5, pady=1)  # Added pady for better spacing
            self.friend_check_vars[friend_name] = var

        # Force update scroll region after populating
        # Use a more robust update sequence
        self.update_idletasks()
        self.scrollable_friends_frame.update_idletasks()

        if hasattr(self, "friends_canvas"):
            # Multiple update calls to ensure proper sizing
            self.friends_canvas.update_idletasks()

            # Get the actual bounding box
            bbox = self.friends_canvas.bbox("all")
            if bbox:
                self.friends_canvas.configure(scrollregion=bbox)
            else:
                # Fallback calculation
                frame_height = self.scrollable_friends_frame.winfo_reqheight()
                frame_width = self.scrollable_friends_frame.winfo_reqwidth()
                self.friends_canvas.configure(scrollregion=(0, 0, frame_width, frame_height))

            # Reset scroll position to top
            self.friends_canvas.yview_moveto(0)

        self.select_all_friends_var.set(True)
        self.update_sync_stats()
        self.sync_status_var.set(f"Found {len(self.friends)} friends. Ready to sync.")

    def toggle_select_all_friends(self):
        """
        Toggle selection of all friends in the sync tab.
        """
        select_all = self.select_all_friends_var.get()
        for var in self.friend_check_vars.values():
            var.set(select_all)
        self.update_sync_stats()

    def update_sync_stats(self):
        """
        Updates the statistics display showing how many friends are selected.
        Signature: Copilot (2025-07-24T12:00:00Z)
        """
        if hasattr(self, "friend_check_vars"):
            selected_count = sum(1 for var in self.friend_check_vars.values() if var.get())
            total_count = len(self.friend_check_vars)
            self.sync_stats_var.set(f"Selected: {selected_count} of {total_count} friends")
        else:
            self.sync_stats_var.set("Selected: 0 friends")

    def perform_sync_selected(self):
        """Performs the sync operation for the friends selected in the checklist."""
        selected_friends = [name for name, var in self.friend_check_vars.items() if var.get()]
        if not selected_friends:
            messagebox.showwarning("Warning", "No friends selected to sync.")
            return

        # Get username from GUI thread before starting the background thread
        username = self.username.get()
        if not username:
            messagebox.showerror("Error", "Username is not set.")
            return

        # Set sync state and update UI
        self.sync_in_progress = True
        self.sync_cancelled.clear()  # Reset cancel flag
        self.start_sync_button.config(state="disabled")
        self.cancel_sync_button.config(state="normal")

        # Run sync in a thread to not freeze the GUI
        threading.Thread(
            target=self._sync_worker, args=(username, selected_friends), daemon=True
        ).start()

    def cancel_sync_operation(self):
        """
        Cancel the ongoing sync operation.
        Signature: Copilot (2025-07-24T22:00:00Z)
        """
        if self.sync_in_progress:
            self.sync_cancelled.set()  # Signal the worker thread to stop
            self.sync_status_var.set("Cancelling sync operation...")

            # Disable cancel button to prevent multiple clicks
            self.cancel_sync_button.config(state="disabled")

            logger.info("User requested sync cancellation")

    def _finish_sync_operation(self, cancelled=False):
        """
        Reset UI state after sync completion or cancellation.
        Signature: Copilot (2025-07-24T22:00:00Z)
        """
        self.sync_in_progress = False
        self.start_sync_button.config(state="normal")
        self.cancel_sync_button.config(state="disabled")

        if cancelled:
            self.sync_status_var.set("Sync cancelled by user. Partial results available.")

        # Update last sync display and save current state
        self.update_last_sync_display()
        self.save_config()

    def _handle_large_watchlist(self, friend_name, movie_count):
        """
        Handle friends with large watchlists (500+ movies) by asking user preference.
        Returns: "skip", "limit", or "full"
        Signature: Copilot (2025-07-24T22:30:00Z)
        """
        # Create a dialog to ask the user what to do
        dialog = tk.Toplevel(self)
        dialog.title("Large Watchlist Detected")
        dialog.geometry("500x250")
        dialog.transient(self)
        dialog.grab_set()

        # Center the dialog on parent window
        dialog.update_idletasks()
        x = (self.winfo_x() + (self.winfo_width() // 2)) - (dialog.winfo_width() // 2)
        y = (self.winfo_y() + (self.winfo_height() // 2)) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Store the user's choice
        user_choice = {"value": "skip"}  # Default to skip

        # Message frame
        message_frame = ttk.Frame(dialog, padding="20")
        message_frame.pack(fill="both", expand=True)

        # Title
        title_label = ttk.Label(
            message_frame,
            text=f"Large Watchlist: {friend_name}",
            font=("TkDefaultFont", 12, "bold"),
        )
        title_label.pack(pady=(0, 10))

        # Message
        message_text = (
            f"{friend_name} has {movie_count:,} movies in their watchlist.\n"
            f"Fetching all movies may take several minutes.\n\n"
            f"What would you like to do?"
        )
        message_label = ttk.Label(message_frame, text=message_text, justify="center")
        message_label.pack(pady=(0, 20))

        # Button frame
        button_frame = ttk.Frame(message_frame)
        button_frame.pack(fill="x")

        def set_choice(choice):
            user_choice["value"] = choice
            dialog.destroy()

        # Buttons
        skip_btn = ttk.Button(
            button_frame, text="Skip This Friend", command=lambda: set_choice("skip")
        )
        skip_btn.pack(side="left", padx=(0, 10))

        limit_btn = ttk.Button(
            button_frame, text="Get First 500 Movies", command=lambda: set_choice("limit")
        )
        limit_btn.pack(side="left", padx=(0, 10))

        full_btn = ttk.Button(
            button_frame, text="Get All Movies (Wait It Out)", command=lambda: set_choice("full")
        )
        full_btn.pack(side="left")

        # Wait for dialog to close
        dialog.wait_window()

        return user_choice["value"]

    def _sync_worker(self, username, friends_to_sync):
        """
        The actual sync logic that runs in a background thread.
        All GUI updates are put into a queue to be processed by the main thread.
        Signature: Copilot (2025-07-21T00:15:00Z)
        """

        def queue_update(task, *args, **kwargs):
            """Helper to put a GUI update task into the queue."""
            self.gui_queue.put((task, args, kwargs))

        queue_update(self.sync_progress_var.set, 0)
        queue_update(self.notebook.tab, 2, state="disabled")

        # 1. Sync user's own watchlist
        if self.sync_cancelled.is_set():
            queue_update(self._finish_sync_operation, True)
            return

        queue_update(self.sync_status_var.set, f"Fetching your watchlist ({username})...")
        try:
            self.user_watchlist = get_watchlist(username)
            sync_watchlist_to_db(username, self.user_watchlist)
        except Exception as e:
            logger.error(f"Error fetching user watchlist: {e}")
            if self.sync_cancelled.is_set():
                queue_update(self._finish_sync_operation, True)
                return

        # 2. Sync friends' watchlists
        self.friends_watchlists = {}
        total_friends = len(friends_to_sync)
        friends_completed = 0

        for i, friend in enumerate(friends_to_sync):
            # Check for cancellation before each friend
            if self.sync_cancelled.is_set():
                logger.info(
                    "Sync cancelled after processing "
                    f"{friends_completed} of {total_friends} friends"
                )
                break

            status_msg = f"Checking watchlist size for '{friend}' ({i + 1}/{total_friends})..."
            queue_update(self.sync_status_var.set, status_msg)

            try:
                # Check watchlist count first
                watchlist_count = get_watchlist_count(friend)

                # Handle large watchlists (500+ movies)
                if watchlist_count and watchlist_count >= 500:
                    # Ask user what to do with large watchlist
                    user_choice = self._handle_large_watchlist(friend, watchlist_count)

                    if user_choice == "skip":
                        logger.info(
                            f"Skipping {friend} due to large watchlist ({watchlist_count} movies)"
                        )
                        continue
                    elif user_choice == "limit":
                        # Fetch first 500 movies
                        status_msg = (
                            f"Fetching first 500 movies for '{friend}' ({i + 1}/{total_friends})..."
                        )
                        queue_update(self.sync_status_var.set, status_msg)
                        watchlist = get_watchlist(friend, limit=500)
                    else:  # user_choice == "full"
                        # Fetch all movies
                        status_msg = (
                            f"Fetching all {watchlist_count} movies for '{friend}' "
                            f"({i + 1}/{total_friends})... This may take a while."
                        )
                        queue_update(self.sync_status_var.set, status_msg)
                        watchlist = get_watchlist(friend)
                else:
                    # Normal size watchlist
                    status_msg = f"Fetching watchlist for '{friend}' ({i + 1}/{total_friends})..."
                    queue_update(self.sync_status_var.set, status_msg)
                    watchlist = get_watchlist(friend)

                self.friends_watchlists[friend] = watchlist
                sync_watchlist_to_db(friend, watchlist)
                friends_completed += 1
            except Exception as exc:
                logger.error(f"'{friend}' generated an exception during sync: {exc}")
                # Continue with next friend even if one fails

            progress = ((i + 1) / total_friends) * 100
            queue_update(self.sync_progress_var.set, progress)

            # Check cancellation after each friend is processed
            if self.sync_cancelled.is_set():
                logger.info(
                    f"Sync cancelled after processing "
                    f"{friends_completed} of {total_friends} friends"
                )
                break

        # 3. Finalize and update UI
        cancelled = self.sync_cancelled.is_set()
        if cancelled:
            status_msg = (
                f"Sync cancelled. Processed {friends_completed} of {total_friends} friends."
            )
        else:
            status_msg = "Comparing watchlists and finalizing..."
        queue_update(self.sync_status_var.set, status_msg)

        # Compare watchlists with whatever data we have
        self.common_movies = compare_watchlists(self.user_watchlist, self.friends_watchlists)

        def update_results_tab():
            """
            Updates the results tab with detailed movie information and links.
            Signature: Copilot (2025-07-24T20:00:00Z)
            """
            # Clear existing results
            for widget in self.scrollable_results_frame.winfo_children():
                widget.destroy()

            total_common_movies = 0
            friend_count = len(self.common_movies)

            # Update summary
            if friend_count > 0:
                total_common_movies = sum(len(movies) for movies in self.common_movies.values())
                self.results_summary_var.set(
                    f"Found {total_common_movies} common movies with {friend_count} friends"
                )

                # Create detailed results display
                for i, (friend, movies) in enumerate(sorted(self.common_movies.items())):
                    # Friend header frame
                    friend_frame = ttk.LabelFrame(
                        self.scrollable_results_frame,
                        text=f"{friend} ({len(movies)} common movies)",
                        padding="10",
                    )
                    friend_frame.pack(fill="x", padx=5, pady=5)

                    # Movies grid
                    movies_frame = ttk.Frame(friend_frame)
                    movies_frame.pack(fill="x")

                    # Configure grid to be responsive
                    movies_frame.grid_columnconfigure(0, weight=1)

                    for j, movie in enumerate(sorted(movies)):
                        movie_row = ttk.Frame(movies_frame)
                        movie_row.grid(row=j, column=0, sticky="ew", pady=2)
                        movie_row.grid_columnconfigure(1, weight=1)

                        # Movie title
                        movie_label = ttk.Label(
                            movie_row, text=f"• {movie}", font=("TkDefaultFont", 9)
                        )
                        movie_label.grid(row=0, column=0, sticky="w")

                        # Letterboxd link
                        link_button = ttk.Button(
                            movie_row,
                            text="View on Letterboxd",
                            width=18,
                            command=lambda m=movie: self._open_letterboxd_movie(m),
                        )
                        link_button.grid(row=0, column=1, sticky="e", padx=(10, 0))

                        # Details button - shows details in same window
                        details_button = ttk.Button(
                            movie_row,
                            text="Details",
                            width=8,
                            command=lambda m=movie: self._show_movie_details_inline(m),
                        )
                        details_button.grid(row=0, column=2, sticky="e", padx=(5, 0))
            else:
                self.results_summary_var.set("No common movies found")
                no_results_label = ttk.Label(
                    self.scrollable_results_frame,
                    text="No common movies were found with the selected friends.",
                    font=("TkDefaultFont", 10),
                )
                no_results_label.pack(pady=20)

            # Update canvas scroll region
            self.scrollable_results_frame.update_idletasks()
            self.results_canvas.configure(scrollregion=self.results_canvas.bbox("all"))

            self.sync_status_var.set(
                f"Sync complete! Found common movies with {friend_count} friends."
            )
            self.notebook.tab(2, state="normal")
            self.notebook.select(2)

        queue_update(update_results_tab)

        # Reset sync state
        queue_update(self._finish_sync_operation, cancelled)

    def _open_letterboxd_movie(self, movie_title):
        """
        Open the movie's direct Letterboxd film page in the default web browser.
        Converts movie title to Letterboxd URL slug format with year disambiguation.
        Signature: Copilot (2025-07-24T22:15:00Z)
        """
        import webbrowser
        import re

        # Try to get movie details from TMDB to include year for accurate URL
        movie_year = None
        try:
            movie_details = get_movie_details(movie_title)
            if movie_details and movie_details.get("release_date"):
                # Extract year from release_date (format: YYYY-MM-DD)
                release_date = movie_details["release_date"]
                movie_year = release_date.split("-")[0] if release_date else None
                logger.debug(f"Found release year {movie_year} for '{movie_title}'")
        except Exception as e:
            logger.warning(f"Could not fetch TMDB details for '{movie_title}': {e}")

        # Convert movie title to Letterboxd URL slug format
        slug = movie_title.lower()
        # Replace spaces and multiple whitespace with hyphens
        slug = re.sub(r"\s+", "-", slug)
        # Remove special characters except hyphens and alphanumeric
        slug = re.sub(r"[^a-z0-9\-]", "", slug)
        # Remove multiple consecutive hyphens
        slug = re.sub(r"-+", "-", slug)
        # Remove leading/trailing hyphens
        slug = slug.strip("-")

        # For better accuracy, try including the year if available
        # Many Letterboxd URLs include the year for disambiguation
        primary_url = None
        fallback_url = None

        if movie_year:
            # Primary attempt: title-year format (e.g., hamilton-2020)
            slug_with_year = f"{slug}-{movie_year}"
            primary_url = f"https://letterboxd.com/film/{slug_with_year}/"
            # Fallback: title only format (e.g., hamilton)
            fallback_url = f"https://letterboxd.com/film/{slug}/"
        else:
            # No year available, try title only
            primary_url = f"https://letterboxd.com/film/{slug}/"

        # Try opening the primary URL
        success = False
        try:
            webbrowser.open(primary_url)
            logger.info(f"Opened Letterboxd film page for '{movie_title}': {primary_url}")
            success = True
        except Exception as e:
            logger.warning(f"Failed to open primary Letterboxd URL '{primary_url}': {e}")

        # If primary failed and we have a fallback, try that
        if not success and fallback_url:
            try:
                webbrowser.open(fallback_url)
                logger.info(
                    f"Opened fallback Letterboxd film page for '{movie_title}': {fallback_url}"
                )
                success = True
            except Exception as e:
                logger.warning(f"Failed to open fallback Letterboxd URL '{fallback_url}': {e}")

        # If both direct URLs failed, fall back to search
        if not success:
            import urllib.parse

            search_query = urllib.parse.quote(movie_title)
            search_url = f"https://letterboxd.com/search/films/{search_query}/"
            try:
                webbrowser.open(search_url)
                logger.info(f"Fallback: Opened Letterboxd search for '{movie_title}': {search_url}")
            except Exception as e:
                logger.error(f"Failed to open search fallback: {e}")
                messagebox.showerror(
                    "Browser Error", f"Could not open web browser.\nSearch for: {movie_title}"
                )

    def _show_movie_details_inline(self, movie_title):
        """
        Show detailed movie information in the inline details panel.
        Signature: Copilot (2025-07-24T21:00:00Z)
        """
        try:
            # Clear current details
            self.details_text.config(state="normal")
            self.details_text.delete("1.0", tk.END)

            # Show loading message
            self.details_text.insert("1.0", f"Loading details for '{movie_title}'...")
            self.details_text.config(state="disabled")
            self.details_text.update_idletasks()

            # Try to get movie details from TMDB if available
            movie_details = None
            try:
                movie_details = get_movie_details(movie_title)
                logger.debug(f"TMDB details for '{movie_title}': {movie_details}")
            except Exception as e:
                logger.error(f"Error fetching TMDB details for '{movie_title}': {e}")

            # Clear loading message and show results
            self.details_text.config(state="normal")
            self.details_text.delete("1.0", tk.END)

            # Insert movie title header
            self.details_text.insert("1.0", f"{movie_title}\n")
            self.details_text.insert("2.0", "=" * len(movie_title) + "\n\n")

            if movie_details and isinstance(movie_details, dict) and movie_details:
                # Format movie details nicely
                details_content = []

                if movie_details.get("release_date"):
                    details_content.append(f"Release Date: {movie_details['release_date']}")

                if movie_details.get("runtime"):
                    details_content.append(f"Runtime: {movie_details['runtime']} minutes")

                if movie_details.get("genres"):
                    genres = movie_details["genres"]
                    if isinstance(genres, list):
                        genres_str = ", ".join(
                            [g["name"] if isinstance(g, dict) else str(g) for g in genres]
                        )
                    else:
                        genres_str = str(genres)
                    details_content.append(f"Genres: {genres_str}")

                if movie_details.get("vote_average"):
                    details_content.append(f"TMDB Rating: {movie_details['vote_average']}/10")

                if movie_details.get("vote_count"):
                    details_content.append(f"Vote Count: {movie_details['vote_count']}")

                if movie_details.get("director"):
                    details_content.append(f"Director: {movie_details['director']}")

                if movie_details.get("overview"):
                    details_content.append(f"\nOverview:\n{movie_details['overview']}")
                elif movie_details.get("synopsis"):
                    details_content.append(f"\nSynopsis:\n{movie_details['synopsis']}")

                if details_content:
                    self.details_text.insert(tk.END, "\n".join(details_content))
                else:
                    self.details_text.insert(
                        tk.END, "Movie found in TMDB but no detailed information available."
                    )
            else:
                # Show troubleshooting information
                self.details_text.insert(tk.END, "Movie details are not available from TMDB.\n\n")
                self.details_text.insert(
                    tk.END, "This movie is on your watchlist, but additional details "
                )
                self.details_text.insert(tk.END, "require TMDB API integration.\n\n")
                self.details_text.insert(tk.END, "To enable detailed movie information:\n\n")
                self.details_text.insert(tk.END, "1. Get a free API key from themoviedb.org:\n")
                self.details_text.insert(tk.END, "   • Go to https://www.themoviedb.org/\n")
                self.details_text.insert(tk.END, "   • Create an account\n")
                self.details_text.insert(tk.END, "   • Go to Settings > API\n")
                self.details_text.insert(tk.END, "   • Request an API key\n\n")
                self.details_text.insert(tk.END, "2. Add your API key to config.json:\n")
                self.details_text.insert(tk.END, "   • Open config.json\n")
                self.details_text.insert(
                    tk.END, '   • Update: "tmdb_api_key": "paste_your_key_here"\n\n'
                )
                self.details_text.insert(tk.END, "3. Restart the application\n\n")
                self.details_text.insert(tk.END, "Without TMDB integration, you can still:\n")
                self.details_text.insert(
                    tk.END, "• View movies on Letterboxd (click 'View on Letterboxd')\n"
                )
                self.details_text.insert(tk.END, "• See all common movies with friends")

            self.details_text.config(state="disabled")

        except Exception as e:
            logger.error(f"Error showing movie details for '{movie_title}': {e}")
            self.details_text.config(state="normal")
            self.details_text.delete("1.0", tk.END)
            self.details_text.insert(
                "1.0", f"Error loading details for '{movie_title}':\n\n{str(e)}"
            )
            self.details_text.config(state="disabled")

    def _show_movie_details(self, movie_title):
        """
        Show detailed movie information in a popup dialog.
        Signature: Copilot (2025-07-24T20:00:00Z)
        """
        try:
            # Try to get movie details from TMDB if available
            movie_details = get_movie_details(movie_title)

            # Create details window
            details_window = tk.Toplevel(self)
            details_window.title(f"Movie Details: {movie_title}")
            details_window.geometry("500x400")
            details_window.resizable(True, True)

            # Main frame with scrollbar
            main_frame = ttk.Frame(details_window)
            main_frame.pack(fill="both", expand=True, padx=10, pady=10)

            # Movie title header
            title_label = ttk.Label(
                main_frame, text=movie_title, font=("TkDefaultFont", 14, "bold"), wraplength=480
            )
            title_label.pack(pady=(0, 10))

            # Details text area
            current_theme = "dark" if self.dark_mode.get() else "light"
            colors = self.theme_colors[current_theme]
            details_text = tk.Text(
                main_frame,
                wrap="word",
                height=15,
                width=60,
                bg=colors["entry_bg"],
                fg=colors["entry_fg"],
                insertbackground=colors["fg"],
                selectbackground=colors["highlight"],
                selectforeground=colors["select_fg"],
            )
            details_scrollbar = ttk.Scrollbar(
                main_frame, orient="vertical", command=details_text.yview
            )
            details_text.configure(yscrollcommand=details_scrollbar.set)

            if movie_details and isinstance(movie_details, dict):
                # Format movie details nicely
                details_content = []

                if movie_details.get("release_date"):
                    details_content.append(f"Release Date: {movie_details['release_date']}")

                if movie_details.get("runtime"):
                    details_content.append(f"Runtime: {movie_details['runtime']} minutes")

                if movie_details.get("genres"):
                    genres = movie_details["genres"]
                    if isinstance(genres, list):
                        genres_str = ", ".join(genres)
                    else:
                        genres_str = str(genres)
                    details_content.append(f"Genres: {genres_str}")

                if movie_details.get("vote_average"):
                    details_content.append(f"TMDB Rating: {movie_details['vote_average']}/10")

                if movie_details.get("overview"):
                    details_content.append(f"\nOverview:\n{movie_details['overview']}")

                if details_content:
                    details_text.insert("1.0", "\n".join(details_content))
                else:
                    details_text.insert("1.0", "No additional details available from TMDB.")
            else:
                details_text.insert(
                    "1.0",
                    "Movie details are not available.\n\n"
                    "This could be because:\n"
                    "• TMDB API is not configured\n"
                    "• Movie not found in TMDB database\n"
                    "• Network connection issues",
                )

            details_text.config(state="disabled")  # Make read-only
            details_text.pack(side="left", fill="both", expand=True)
            details_scrollbar.pack(side="right", fill="y")

            # Buttons frame
            buttons_frame = ttk.Frame(details_window)
            buttons_frame.pack(fill="x", padx=10, pady=(0, 10))

            # Open on Letterboxd button
            ttk.Button(
                buttons_frame,
                text="Open on Letterboxd",
                command=lambda: self._open_letterboxd_movie(movie_title),
            ).pack(side="left", padx=(0, 5))

            # Close button
            ttk.Button(buttons_frame, text="Close", command=details_window.destroy).pack(
                side="right"
            )

        except Exception as e:
            logger.error(f"Error showing movie details for '{movie_title}': {e}")
            messagebox.showerror("Error", f"Could not load movie details.\nError: {str(e)}")

    def fetch_movie_details_background(self, movies_list):
        with ThreadPoolExecutor(max_workers=4) as executor:
            executor.map(get_movie_details, movies_list)

    def save_all_and_exit(self):
        """
        Save configuration and exit the application cleanly.
        Signature: Copilot (2025-07-24T23:00:00Z)
        """
        # Stop GUI queue processing to prevent after() calls on destroyed widgets
        self.gui_queue_active = False

        # Cancel any pending after() calls for GUI queue processing
        if hasattr(self, "gui_queue_after_id") and self.gui_queue_after_id:
            try:
                self.after_cancel(self.gui_queue_after_id)
                self.gui_queue_after_id = None
            except tk.TclError:
                pass  # Already destroyed or invalid

        # Cancel any ongoing sync operations
        if self.sync_in_progress:
            self.sync_cancelled.set()

        # Save configuration
        self.save_config()

        # Log application close
        logger.info("Application has been closed.")

        # Clean up and destroy the window
        self.destroy()

    def clear_database_contents(self):
        if messagebox.askyesno(
            "Confirm", "Are you sure you want to clear all data from the database?"
        ):
            try:
                conn = sqlite3.connect("letterboxd.db")
                c = conn.cursor()
                c.execute("DELETE FROM users")
                c.execute("DELETE FROM movies")
                c.execute("DELETE FROM watchlists")
                c.execute("DELETE FROM friends")
                conn.commit()
                conn.close()
                messagebox.showinfo("Success", "Database cleared.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear database: {e}")


class DrillDownGUI(tk.Toplevel):
    """
    Tkinter GUI for visual drill-down of common movies.
    Now a dialog instead of a main window.
    """

    def __init__(self, parent, common_movies):
        super().__init__(parent)
        self.parent = parent
        self.common_movies = common_movies
        self.title("Common Movies Drill-Down")
        self.geometry("600x400")
        self.create_widgets()

    def create_widgets(self):
        self.tree = ttk.Treeview(self, columns=("friend", "movie"), show="headings")
        self.tree.heading("friend", text="Friend")
        self.tree.heading("movie", text="Common Movie")
        self.tree.pack(expand=True, fill="both")
        for friend, movies in self.common_movies.items():
            for movie in movies:
                self.tree.insert("", "end", values=(friend, movie))


# --- Utility Functions ---
def clear_output_file():
    """Clear the contents of the output log file."""
    try:
        with open("Output.txt", "w"):
            pass
    except Exception as e:
        logger.error(f"Failed to clear output file: {e}")


# --- Main Application Logic ---
def main():
    """
    Main function to run the program with GUI interface.
    """
    clear_output_file()
    init_db()

    # Create and run the GUI application
    try:
        app = LetterboxdGUI()
        app.mainloop()
    except Exception as e:
        logger.critical(f"A critical error occurred in the GUI application: {e}")
    finally:
        logger.info("Application has been closed.")


def cli_main():
    """
    Legacy command-line interface version of the application.
    Kept for compatibility or when GUI is not desired.
    """
    max_workers = 4  # Safe limit for concurrent requests
    clear_output_file()
    init_db()
    while True:
        username = validate_username_input("Enter your Letterboxd username (or 'exit' to quit): ")
        if username.lower() == "exit":
            break
        if not username:
            continue
        break

    # Use a path relative to the script file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cookie_path = os.path.join(script_dir, "Cookie.json")
    load_cookies_from_json(session, cookie_path)

    while True:
        print("\n--- Menu ---")
        print("1. Fetch my watchlist")
        print("2. Fetch my friends' watchlists")
        print("3. Compare watchlists")
        print("4. Exit")
        choice = validate_menu_choice("Enter your choice: ", ["1", "2", "3", "4"])
        if choice == "1":
            user_watchlist = get_watchlist(username)
            print(f"\nFound {len(user_watchlist)} movies in your watchlist.")
        elif choice == "2":
            friends = get_friends(username)
            print(f"\nFound {len(friends)} friends.")
            friends_watchlists = {}
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_friend = {
                    executor.submit(get_watchlist, friend): friend for friend in friends
                }
                for future in as_completed(future_to_friend):
                    friend = future_to_friend[future]
                    try:
                        watchlist = future.result()
                        friends_watchlists[friend] = watchlist
                        print(f"Found {len(watchlist)} movies for {friend}.")
                    except Exception as exc:
                        print(f"{friend} generated an exception: {exc}")
        elif choice == "3":
            if "user_watchlist" not in locals():
                print("\nPlease fetch your watchlist first (Option 1).")
                continue
            if "friends_watchlists" not in locals():
                print("\nPlease fetch your friends' watchlists first (Option 2).")
                continue
            common_movies = compare_watchlists(user_watchlist, friends_watchlists)
            print("\n--- Common Movies ---")
            for friend, movies in common_movies.items():
                print(f"\n{friend} ({len(movies)} common movies):")
                for movie in sorted(movies):
                    print(f"  - {movie}")
        elif choice == "4":
            break
        else:
            print("Invalid choice. Please try again.")


# --- Entry Point ---
if __name__ == "__main__":
    main()  # Launch the GUI version by default
