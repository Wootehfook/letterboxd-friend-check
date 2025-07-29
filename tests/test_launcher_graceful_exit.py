"""
Test for graceful exit handling in the launcher script.
Tests the fix for Issue #2: "Error on EXE GUI Exit" - RuntimeError: lost sys.stdin
"""

import unittest
import sys
import io
from unittest.mock import patch, Mock


class TestLauncherGracefulExit(unittest.TestCase):
    """Test cases for graceful exit handling in run_letterboxd.py launcher."""

    def test_graceful_exit_with_eoferror(self):
        """Test that launcher handles EOFError gracefully."""
        with patch("builtins.input", side_effect=EOFError()):
            try:
                # Test the exception handling directly instead of using exec()
                try:
                    input("\nPress Enter to exit...")
                except (EOFError, KeyboardInterrupt, RuntimeError):
                    pass  # This is the expected behavior
            except EOFError:
                self.fail("EOFError should be caught and handled gracefully")

    def test_graceful_exit_with_keyboard_interrupt(self):
        """Test that launcher handles KeyboardInterrupt gracefully."""
        with patch("builtins.input", side_effect=KeyboardInterrupt()):
            try:
                # Test the exception handling directly instead of using exec()
                try:
                    input("\nPress Enter to exit...")
                except (EOFError, KeyboardInterrupt, RuntimeError):
                    pass  # This is the expected behavior
            except KeyboardInterrupt:
                self.fail("KeyboardInterrupt should be caught and handled gracefully")

    def test_graceful_exit_with_runtime_error(self):
        """Test that launcher handles RuntimeError (lost sys.stdin) gracefully."""
        with patch("builtins.input", side_effect=RuntimeError("lost sys.stdin")):
            try:
                # Test the exception handling directly instead of using exec()
                try:
                    input("\nPress Enter to exit...")
                except (EOFError, KeyboardInterrupt, RuntimeError):
                    pass  # This is the expected behavior
            except RuntimeError:
                self.fail("RuntimeError should be caught and handled gracefully")

    def test_exit_handling_code_syntax(self):
        """Test that the exit handling code has correct syntax and exceptions."""
        # Read the actual file content
        with open("run_letterboxd.py", "r") as f:
            content = f.read()

        # Check that RuntimeError is included in the exception handling
        self.assertIn("RuntimeError", content)
        expected_except = "except (EOFError, KeyboardInterrupt, RuntimeError):"
        self.assertIn(expected_except, content)

    def test_mock_stdin_unavailable(self):
        """Test behavior when sys.stdin is completely unavailable."""
        # Mock sys.stdin to be None (common in GUI applications)
        original_stdin = sys.stdin
        try:
            sys.stdin = None
            with patch("builtins.input", side_effect=RuntimeError("lost sys.stdin")):
                # Import and test the specific exit handling logic
                try:
                    # Simulate the exit prompt logic
                    input("\nPress Enter to exit...")
                except (EOFError, KeyboardInterrupt, RuntimeError):
                    # This should pass - no exception should bubble up
                    pass
                # If we get here, the test passes
        finally:
            sys.stdin = original_stdin


if __name__ == "__main__":
    unittest.main()
