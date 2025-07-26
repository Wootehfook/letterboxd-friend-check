"""
Menu methods for the Letterboxd Friend Check application.
Contains menu creation and related functions.
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import webbrowser


class MenuMethods:
    """
    A mixin class providing menu functionality for the Letterboxd Friend Check application.
    This class is meant to be inherited by the main application class (which must be a Tk widget).

    Note: This class assumes it will be mixed into a class that inherits from tk.Tk or another
    Tkinter widget class that has the necessary methods like config(), wait_window(), etc.
    It is not meant to be instantiated directly.

    Required attributes/methods that must be provided by the inheriting class:
    - friends_watchlists: dict containing friend watchlist data
    - on_close(): method to handle application closing

    Optional attributes that may be provided by the inheriting class:
    - username: str - current user's Letterboxd username
    - friends: list/dict - user's friends data
    - user_watchlist: list/dict - user's watchlist data
    - results_tree: tkinter.Treeview - results display widget
    - save_config(): method to save application configuration
    """

    @property
    def friends_watchlists(self):
        """
        Get friends watchlists data.
        Returns empty dict if not defined by the inheriting class.
        """
        return getattr(self, "_friends_watchlists", {})

    @friends_watchlists.setter
    def friends_watchlists(self, value):
        """Set friends watchlists data."""
        self._friends_watchlists = value

    def on_close(self):
        """
        Handle application closing.
        This method should be overridden by the inheriting class.
        """
        raise NotImplementedError(
            "on_close() must be implemented in the main application class. "
            "This method should handle proper cleanup and window destruction."
        )

    def create_menubar(self):
        """Create application menu bar"""
        # Type checking note: 'self' will be a Tkinter widget when this class is used properly
        menubar = tk.Menu(self)  # type: ignore
        self.config(menu=menubar)  # type: ignore[attr-defined]  # pylint: disable=no-member

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Results...", command=self.export_results)
        file_menu.add_separator()
        file_menu.add_command(label="Save All Data", command=self.save_all_data)
        file_menu.add_command(label="Save & Exit", command=self.save_all_and_exit)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)

        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Account Setup...", command=self.show_setup_dialog)
        settings_menu.add_command(label="Database Management...", command=self.show_database_dialog)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(
            label="Visit Letterboxd", command=lambda: self.open_url("https://letterboxd.com/")
        )

    def show_setup_dialog(self):
        """Show the setup dialog"""
        # Import locally to avoid circular imports
        from letterboxd_friend_check.gui.setup_dialog import SetupDialog

        setup_dialog = SetupDialog(self)
        self.wait_window(setup_dialog)  # pylint: disable=no-member

    def show_database_dialog(self):
        """Show database management dialog"""
        messagebox.showinfo(
            "Database Management",
            "Database management features will be available in a future update.",
        )

    def export_results(self):
        """Export results to file"""
        # Check if we have results to export
        results_tree = getattr(self, "results_tree", None)
        if not results_tree or not results_tree.get_children():
            messagebox.showinfo("Export", "No results to export.")
            return

        # Ask for filename
        filename = filedialog.asksaveasfilename(
            title="Export Results",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("Text Files", "*.txt"), ("All Files", "*.*")],
        )

        if not filename:
            return

        try:
            with open(filename, "w", encoding="utf-8") as f:
                # Write header
                f.write("Movie Title,Year,Rating,Common Friends,Director,Runtime,Genres\n")

                # Write data
                for item_id in results_tree.get_children():
                    values = results_tree.item(item_id, "values")
                    # Format and escape values properly for CSV
                    formatted_values = []
                    for val in values:
                        # Handle quotes in strings for CSV format
                        if isinstance(val, str) and ("," in val or '"' in val):
                            escaped_val = val.replace('"', '""')
                            formatted_values.append(f'"{escaped_val}"')
                        else:
                            formatted_values.append(str(val))

                    f.write(",".join(formatted_values) + "\n")

            messagebox.showinfo("Export Complete", f"Results exported to {filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Error exporting results: {str(e)}")

    def save_all_data(self):
        """Save all application data"""
        try:
            # Save config if the method exists
            if hasattr(self, "save_config"):
                self.save_config()

            # Import database functions locally to avoid circular imports
            from letterboxd_friend_check.data.database import (
                sync_watchlist_to_db,
                sync_friends_to_db,
            )

            # Save any in-memory data to the database if needed
            username = getattr(self, "username", None)
            user_watchlist = getattr(self, "user_watchlist", None)
            friends = getattr(self, "friends", None)

            if user_watchlist and username:
                sync_watchlist_to_db(username, user_watchlist)

            if friends and username:
                sync_friends_to_db(username, friends)

            if hasattr(self, "friends_watchlists") and self.friends_watchlists:
                for friend, watchlist in self.friends_watchlists.items():
                    if watchlist:
                        sync_watchlist_to_db(friend, watchlist)

            messagebox.showinfo("Save Complete", "All data has been saved successfully.")
        except Exception as e:
            messagebox.showerror("Save Error", f"Error saving data: {str(e)}")

    def show_about(self):
        """Show about dialog"""
        about_text = """Letterboxd Friend Check

    A tool to compare your Letterboxd watchlist with friends.

    © 2025 - Open Source

    This application is not affiliated with Letterboxd.
    Letterboxd is a trademark of Letterboxd Limited."""
        messagebox.showinfo("About Letterboxd Friend Check", about_text)

    def save_all_and_exit(self):
        """Save all data and exit the application"""
        try:
            # Save all data first
            self.save_all_data()
            # Then close the application
            self.on_close()
        except Exception as e:
            messagebox.showerror("Error", f"Error while saving data before exit: {str(e)}")
            # Ask if user still wants to exit
            if messagebox.askyesno(
                "Exit Anyway?", "There was an error saving data. Do you still want to exit?"
            ):
                self.on_close()

    def open_url(self, url):
        """Open a URL in the default web browser"""
        webbrowser.open(url)
