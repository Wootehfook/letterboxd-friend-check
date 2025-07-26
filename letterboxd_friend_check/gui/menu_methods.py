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
    """

    def create_menubar(self):
        """Create application menu bar"""
        # Type checking note: 'self' will be a Tkinter widget when this class is used properly
        menubar = tk.Menu(self)  # type: ignore
        self.config(menu=menubar)  # type: ignore

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
        self.wait_window(setup_dialog)

    def show_database_dialog(self):
        """Show database management dialog"""
        messagebox.showinfo(
            "Database Management",
            "Database management features will be available in a future update.",
        )

    def export_results(self):
        """Export results to file"""
        # Check if we have results to export
        if not hasattr(self, "results_tree") or not self.results_tree.get_children():
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
                for item_id in self.results_tree.get_children():
                    values = self.results_tree.item(item_id, "values")
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
            # Save config
            self.save_config()

            # Import database functions locally to avoid circular imports
            from letterboxd_friend_check.data.database import (
                sync_watchlist_to_db,
                sync_friends_to_db,
            )

            # Save any in-memory data to the database if needed
            if hasattr(self, "user_watchlist") and self.user_watchlist and self.username:
                sync_watchlist_to_db(self.username, self.user_watchlist)

            if hasattr(self, "friends") and self.friends and self.username:
                sync_friends_to_db(self.username, self.friends)

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
