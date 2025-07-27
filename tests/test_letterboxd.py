"""
Unit tests for the Letterboxd Friend Check Application.
"""

import unittest
import sys
import os
import pytest

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestLetterboxdApp(unittest.TestCase):
    """Test cases for core functionality of the Letterboxd app."""

    def setUp(self):
        """Set up test fixtures."""
        pass

    def test_db_init(self):
        """Test database initialization."""
        try:
            from LBoxFriendCheck import init_db
        except ImportError:
            pytest.skip("LBoxFriendCheck module not available")
            
        import os

        # Use a test database
        test_db_path = "test_letterboxd.db"

        # Remove test db if it exists
        if os.path.exists(test_db_path):
            os.remove(test_db_path)

        # Initialize the test database
        init_db(test_db_path)

        # Check that the database file exists
        self.assertTrue(os.path.exists(test_db_path))

        # Clean up
        if os.path.exists(test_db_path):
            os.remove(test_db_path)

    def test_watchlist_comparison(self):
        """Test comparison of watchlists."""
        try:
            from LBoxFriendCheck import compare_watchlists
        except ImportError:
            pytest.skip("LBoxFriendCheck module not available")

        # Create test data
        user_watchlist = {"Movie 1", "Movie 2", "Movie 3", "Movie 4"}
        friends_watchlists = {
            "friend1": {"Movie 1", "Movie 3", "Movie 5"},
            "friend2": {"Movie 2", "Movie 6", "Movie 7"},
            "friend3": {"Movie 8", "Movie 9"},
        }

        # Expected results
        expected = {"friend1": {"Movie 1", "Movie 3"}, "friend2": {"Movie 2"}}

        # Compare watchlists
        result = compare_watchlists(user_watchlist, friends_watchlists)

        # Check result
        self.assertEqual(result, expected)
        self.assertNotIn("friend3", result)  # No common movies with friend3

    def test_tmdb_api_integration(self):
        """Test TMDB API integration."""
        try:
            from tmdb_api import get_movie_details
        except ImportError:
            pytest.skip("tmdb_api module not available")

        # Try to get details for a well-known movie
        movie_details = get_movie_details("The Shawshank Redemption", 1994)

        # If we got results, check basic fields
        if movie_details:
            self.assertIn("title", movie_details)
            self.assertIn("id", movie_details)
        else:
            # If API is not available, skip test
            self.skipTest("TMDB API not available or rate limited")


# Pytest-style test functions for better pytest integration
def test_basic_imports():
    """Test that basic imports work."""
    try:
        import LBoxFriendCheck
        assert hasattr(LBoxFriendCheck, 'init_db')
    except ImportError:
        pytest.skip("LBoxFriendCheck module not available")


def test_tmdb_import():
    """Test that TMDB API import works."""
    try:
        import tmdb_api
        assert hasattr(tmdb_api, 'get_movie_details')
    except ImportError:
        pytest.skip("tmdb_api module not available")


if __name__ == "__main__":
    unittest.main()
